"""Tests for tools/rooms.py (plan 0040 Phase 2): the reference walk, the save rule, the item expiry, the record
parser and a small synthetic log through the checker. Run: python3 -I tools/test_rooms.py"""
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rooms  # noqa: E402


def snap(rooms_):
    """{id: [refs0..3, status, fl, a30, type, lid, cl, near]} from {id: (refs, status, near)}."""
    return {str(k): list(r) + [s, 0, 0, 1, 1, 0, n] for k, (r, s, n) in rooms_.items()}


class RefWalk(unittest.TestCase):
    def test_first_entry_activates_the_near_list(self):
        # a line of rooms 1-2-3-4-5, each near list = itself and its neighbours
        near = {1: [1, 2], 2: [1, 2, 3], 3: [2, 3, 4], 4: [3, 4, 5], 5: [4, 5]}
        before = snap({k: ([0, 0, 0, 0], 4, v) for k, v in near.items()})
        M = rooms.RefModel(before, before)
        M.move(0, 1, lambda i: {"fl": 0x1000000, "ty": 1, "a30": 0})
        # room 1: distance 0 (status 0); room 2: distance 1 (status 1); room 3: 2; room 4: 3; room 5: none
        self.assertEqual(M.r[1]["st"], 0)
        self.assertEqual(M.r[2]["st"], 1)
        self.assertEqual(M.r[3]["st"], 2)
        self.assertEqual(M.r[4]["st"], 3)
        self.assertEqual(M.r[5]["st"], 4)
        kinds = [c[0] for c in M.calls]
        self.assertIn("e1", kinds)
        self.assertEqual(kinds[-1], "e0")          # the room itself last
        # leaving again releases everything back to status 4
        M.move(1, 0, lambda i: None)
        self.assertTrue(all(M.r[k]["st"] == 4 and M.r[k]["refs"] == [0, 0, 0, 0] for k in near))

    def test_refs_count_paths(self):
        near = {1: [1, 2], 2: [1, 2]}
        M = rooms.RefModel(snap({k: ([0, 0, 0, 0], 4, v) for k, v in near.items()}), {})
        M.move(0, 1, lambda i: {"fl": 0, "ty": 1, "a30": 0})
        # room 1: d0 once; d1 from its own list (1, 2) -> rooms 1 and 2 at d1; d2 from both; d3 from four paths
        self.assertEqual(M.r[1]["refs"], [1, 1, 2, 4])
        self.assertEqual(M.r[2]["refs"], [0, 1, 2, 4])


class SaveRule(unittest.TestCase):
    U = {"t": 1, "c": 5, "m": 1, "c4": 0, "d0": 11}

    def test_alive_pool_monster(self):
        self.assertEqual(rooms.monster_save(dict(self.U), {"sm": 1, "dead": 0, "mt18": 0, "rb": 1}), (1, 0))
        self.assertEqual(rooms.monster_save(dict(self.U), {"sm": 0, "dead": 0, "mt18": 0, "rb": 1}), (0, 0))
        self.assertEqual(rooms.monster_save(dict(self.U, c4=0x2000000), {"sm": 0, "dead": 0, "mt18": 0, "rb": 1}),
                         (1, 0))

    def test_dead_draw_and_overrides(self):
        u = dict(self.U, m=12)
        self.assertEqual(rooms.monster_save(u, {"sm": 1, "dead": 1, "draw": [0, ""], "ud": 0, "al": 0, "mt18": 0,
                                                "rb": 1}), (1, 0))
        self.assertEqual(rooms.monster_save(u, {"sm": 1, "dead": 1, "draw": [1, ""], "ud": 0, "al": 0, "mt18": 0,
                                                "rb": 1}), (0, 0))
        self.assertEqual(rooms.monster_save(u, {"sm": 1, "dead": 1, "draw": [0, ""], "ud": 0, "al": 0, "mt18": 1,
                                                "rb": 1}), (0, 0))
        # restore 2 overrides every earlier test
        self.assertEqual(rooms.monster_save(u, {"sm": 0, "dead": 1, "draw": [2, ""], "ud": 1, "al": 2, "mt18": 1,
                                                "rb": 2}), (1, 0))

    def test_owned_pet_is_kept(self):
        u = dict(self.U, c4=0x80000000)
        self.assertEqual(rooms.monster_save(u, {"sm": 1, "dead": 0, "mt18": 0, "own": [1234, 0], "pet": 1, "rb": 1}),
                         (0, 1))

    def test_objects(self):
        o = {"t": 2, "c": 5, "m": 0, "c4": 0}
        self.assertEqual(rooms.other_save(o, {"sm": 1, "orow": [1, 0], "spk": 0}), (1, 0))
        self.assertEqual(rooms.other_save(o, {"sm": 1, "orow": [0, 0], "spk": 0}), (0, 0))
        self.assertEqual(rooms.other_save(dict(o, m=1), {"sm": 1, "orow": [1, 1], "spk": 0}), (0, 0))
        self.assertEqual(rooms.other_save(dict(o, c=59), {"sm": 0}), (1, 1))


class Expiry(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(rooms.item_expiry(100, {"quest": 1}), 0)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 4}), 30100)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 7}), 45100)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 2, "bt": 4, "gold": 20000}), 45100)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 2, "bt": 4, "gold": 50}), 15100)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 2, "bt": 50, "filler": 1}), 30100)
        self.assertEqual(rooms.item_expiry(100, {"quest": 0, "q": 2, "bt": 50, "filler": 0}), 15100)


class Records(unittest.TestCase):
    def test_mrec_parse(self):
        b = bytearray(0x5C)
        struct.pack_into("<iiiiII", b, 0, 10, 20, 5, 77, 0x2000000, 0x200)
        struct.pack_into("<I", b, 0x18, 0x206)
        b[0x32:0x3B] = bytes([1, 2, 3, 4, 5, 0, 0, 0, 0])
        struct.pack_into("<iiii", b, 0x40, 9, 2560, 1280, 0)
        struct.pack_into("<i", b, 0x54, 1234)
        r = rooms.mrec_parse(b.hex())
        self.assertEqual((r["x"], r["y"], r["c"], r["id"], r["fl"], r["s13"], r["maxhp"], r["hp"], r["fr"]),
                         (10, 20, 5, 77, 0x206, 9, 2560, 1280, 1234))
        self.assertEqual(rooms.rec_align(0x100), 2)
        self.assertEqual(rooms.rec_align(0x80), 1)
        self.assertEqual(rooms.rec_align(0x200), 0)


class Seeds(unittest.TestCase):
    def test_steps_between(self):
        a = (0x12345678, 666)
        self.assertEqual(rooms.steps_between(a, rooms.nth(a, 3)), 3)
        self.assertIsNone(rooms.steps_between(a, (1, 2), 10))


if __name__ == "__main__":
    unittest.main()

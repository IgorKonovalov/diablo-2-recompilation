"""Synthetic tests for the plan 0038 batch S2b pieces: python3 -I tools/test_items_sweep.py

No game file is read: the item tables, the logs and the creation lines are built in memory or in a temporary file.
  - affixes.staff_mods (ITEMS_RollStaffMods modelled): no class -> no draw; the mods count, the per-mod tier window,
    the level range, no repeat without the 6-try fallback, one step per draw; the low-quality expansion item draws no
    level and caps the tier at 4; the classic tier stops at 4; the counterfactual switches change the result;
  - items_sweep.blocks: the IIS lines before IC0 and the LX line after ICX join the creation, the CPRE window marks
    a drop, GAME lines pass through;
  - items_chain.check_staff_lx: the 107 entries at LX against the predicted staff-mod writes (last write wins);
  - props.trunc_div and its FLOOR_CF counterfactual.
"""
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import affixes  # noqa: E402
import items_chain  # noqa: E402
import items_sweep  # noqa: E402
import props  # noqa: E402
import rng  # noqa: E402


class FakeT:
    """Seven classes of 30 skills from id 6 (as Skills.md), skill 66 (class 2's first) needs item type 3; the item is
    of type 3 when cls is 1. StaffMods class 2 for cls 0 and 1, none (7) for cls 2."""
    nskills = 300
    skill_itype = [0] * 300

    def __init__(self):
        self.skill_itype = [0] * 300
        self.skill_itype[66] = 3

    def tbyte(self, cls, off, missing=0):
        assert off == 0x1F
        return 7 if cls == 2 else 2

    def class_skill_count(self, c):
        return 30

    def first_class_skill(self, c):
        return 6 + 30 * c

    def is_type(self, cls, t):
        return cls == 1 and t == 3


class Item:
    def __init__(self, cls=0, ilvl=40, ver=101, q=2, rfl=0):
        self.cls, self.ilvl, self.ver, self.q, self.rfl = cls, ilvl, ver, q, rfl


def steps_between(a, b, limit=200):
    s = a
    for n in range(limit):
        if s == b:
            return n
        s = rng.step(*s)
    return None


class StaffMods(unittest.TestCase):
    def setUp(self):
        self.T = FakeT()
        self.rnd = random.Random(38)

    def seeds(self, n=400):
        return [(self.rnd.getrandbits(32), self.rnd.getrandbits(32)) for _ in range(n)]

    def test_no_class(self):
        s = (123, 666)
        self.assertEqual(affixes.staff_mods(self.T, Item(cls=2), s), (s, [], None))

    def test_ranges_and_draws(self):
        counts = set()
        for s in self.seeds():
            it = Item(ilvl=40)
            new, out, info = affixes.staff_mods(self.T, it, s)
            counts.add(len(out))
            if out:
                self.assertEqual(info["tier"], 5)
            n = steps_between(s, new)
            self.assertIsNotNone(n)
            # 1 count draw, then per mod: 1 tier draw, 1..6 skill draws, 1 level draw
            self.assertGreaterEqual(n, 1 + 3 * len(out))
            self.assertLessEqual(n, 1 + 8 * len(out))
            first = 6 + 30 * 2
            for sk, lv in out:
                self.assertTrue(first <= sk < first + 30, sk)
                self.assertIn(lv, (1, 2, 3))
            if not info.get("fallback"):
                self.assertEqual(len(set(sk for sk, _ in out)), len(out))
        self.assertEqual(counts, {0, 1, 2, 3})

    def test_low_quality_expansion(self):
        for s in self.seeds():
            new, out, info = affixes.staff_mods(self.T, Item(q=1, ilvl=60), s)
            for sk, lv in out:
                self.assertEqual(lv, 1)
                self.assertLess(sk, 6 + 60 + 20)          # tier <= 4: skills of the first four 5-id tiers
            if out:
                self.assertEqual(info["lownodraw"], len(out))
                cf, _, _ = affixes.staff_mods(self.T, Item(q=1, ilvl=60), s, cf="lowdraw")
                self.assertNotEqual(cf, new)

    def test_classic_tier(self):
        for s in self.seeds(50):
            _, _, info = affixes.staff_mods(self.T, Item(ilvl=60, ver=99), s)
            if info.get("mods"):
                self.assertEqual(info["tier"], 4)
            _, _, info5 = affixes.staff_mods(self.T, Item(ilvl=60, ver=99), s, cf="tier-noexp")
            if info5.get("mods"):
                self.assertEqual(info5["tier"], 5)

    def test_type_requirement(self):
        refused = 0
        for s in self.seeds(2000):
            _, out, info = affixes.staff_mods(self.T, Item(cls=0, ilvl=1), s)
            refused += info.get("typerefused", 0) if info else 0
            if not info or not info.get("fallback"):
                self.assertNotIn(66, [sk for sk, _ in out])   # skill 66 needs type 3, which cls 0 is not
        self.assertGreater(refused, 0)

    def test_version0_refused(self):
        with self.assertRaises(affixes.Mismatch):
            affixes.staff_mods(self.T, Item(ver=0), (1, 666))


LOG = """GAME override=1 seed=00000001:0000029a
IIS0 {"it":7,"cls":3,"useed":"00000010:0000029a","iseed":"00000020:0000029a","q":0}
IIS1 {"it":7,"useed":"00000011:0000029a","iseed":"00000020:0000029a","b":[]}
CPRE item=3 q=2 uidx=0 up=0 seed=1:2
IC0 {"it":7,"cls":3,"q":0,"seed":"00000020:0000029a","rq":2,"ver":101,"ilvl":5,"rest":0,"fl":16,"rfl":0}
ICQ {"q":2,"iq":2,"rq":2}
ICJ {"seed":"00000020:0000029a","q":2,"rq":2,"fi":0}
ICX {"ret":1,"seed":"00000020:0000029a","q":2,"fi":0}
LX {"seed":"00000020:0000029a","q":2,"fi":0,"fl":16,"b":[[70,0,1]],"sub":[]}
CPOST
IC0 {"it":8,"cls":4,"q":0,"seed":"00000030:0000029a","rq":7,"ver":101,"ilvl":5,"rest":0,"fl":16,"rfl":0}
ICQ {"q":7,"iq":7,"rq":2}
ICJ {"seed":"00000030:0000029a","q":7,"rq":7,"fi":-1}
ICX {"ret":1,"seed":"00000030:0000029a","q":7,"fi":-1}
GAME override=1 seed=00000002:0000029a
"""


class Blocks(unittest.TestCase):
    def test_blocks(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(LOG)
        try:
            out = list(items_sweep.blocks(f.name))
        finally:
            os.unlink(f.name)
        self.assertEqual(out[0], ("GAME", None))
        b1, d1 = out[1]
        self.assertEqual([t for t, _ in b1], ["IIS0", "IIS1", "IC0", "ICQ", "ICJ", "ICX", "LX"])
        self.assertEqual(d1["q"], "2")
        b2, d2 = out[2]
        self.assertEqual([t for t, _ in b2], ["IC0", "ICQ", "ICJ", "ICX"])
        self.assertIsNone(d2)
        self.assertEqual(out[3], ("GAME", None))
        self.assertEqual(len(out), 4)


class StaffLX(unittest.TestCase):
    def ev(self, ents):
        return [("ICJ", {}), ("LX", {"sub": [[0, 64, ents]]})]

    def test_last_write_wins(self):
        import collections
        S = collections.Counter()
        items_chain.check_staff_lx(self.ev([[107, 70, 2], [16, 0, 5]]), [(70, 1), (70, 2)], S)
        self.assertEqual(S["staff mods vs LX: 107 lists compared"], 1)

    def test_mismatch(self):
        import collections
        with self.assertRaises(affixes.Mismatch):
            items_chain.check_staff_lx(self.ev([[107, 70, 2]]), [(71, 2)], collections.Counter())

    def test_property_write_skips(self):
        import collections
        S = collections.Counter()
        ev = self.ev([[107, 70, 2]]) + [("WR", {"stat": 107})]
        items_chain.check_staff_lx(ev, [], S)
        self.assertEqual(S["staff mods vs LX: not compared (a property wrote stat 107)"], 1)


class TruncDiv(unittest.TestCase):
    def test_trunc_and_floor(self):
        self.assertEqual(props.trunc_div(-7, 2), -3)
        self.assertEqual(props.trunc_div(7, -2), -3)
        self.assertEqual(props.trunc_div(7, 2), 3)
        props.FLOOR_CF = True
        try:
            self.assertEqual(props.trunc_div(-7, 2), -4)
        finally:
            props.FLOOR_CF = False


if __name__ == "__main__":
    unittest.main()

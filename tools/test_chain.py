"""Synthetic tests for tools/chain.py (plan 0048 Phase 1): python3 -I tools/test_chain.py

No game file is read.
  - chain.game_seeds and rng.act_seeds on the rng/seeds worked example (-seed 12345 and -seed 34844169): the game seed,
    the act bases, the Act II tombs, level 1's and level 134's create seeds;
  - the four game-creation draws are consecutive steps of Init(N), each the Init of its low word;
  - chain.line_sets on synthetic logs: affix lines, property lines, world lines, none;
  - the items oracle switch: chain.py check's default is the staff-mods model (oracle 2 retired);
  - oracle 14: monstats.Model.init_seed's draw count on a stub table (variant set, per-component counts, doomknight,
    an HP range below 1, MonProp off) and the MonEquip oracle it raises;
  - oracle 13: monstats.Tables' MonEquip row walk (oninit at +0x04, the level skip) and Model.monequip's draws;
  - oracle 16: monspawn.PresetMonPass's class chain (sub_00651040), LevelClassVariant and PresetFallenVariant on stub
    MonStats / Levels records.
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import chain  # noqa: E402
import rng  # noqa: E402


class GameSeeds(unittest.TestCase):
    def test_worked_example(self):
        g = chain.game_seeds(12345)
        self.assertEqual(g["game_seed"], (0x3039, 0x29A))
        self.assertEqual(g["map_seed"], 0x3039)
        base = rng.act_seeds(12345, 0)[0]
        self.assertEqual(base, 0x015B2E77)
        self.assertEqual((base + 1) & rng.MASK, 0x015B2E78)               # level 1 seed (rng/seeds step 4)
        a2 = rng.act_seeds(12345, 1)
        self.assertEqual((a2[3], a2[4]), (72, 71))
        self.assertEqual((a2[1], a2[2]), (0xB7A5C418, 0x63A93A78))
        self.assertEqual((rng.act_seeds(34844169, 0)[0] + 134) & rng.MASK, 0x0000000D)

    def test_draw_order(self):
        for n in (1, 12345, 0x7FFFFFFF):
            g = chain.game_seeds(n)
            s = (n, rng.INIT_HIGH)
            for k in ("monster_regions", "object_region", "store", "quest"):
                s = rng.step(*s)
                self.assertEqual(g[k], (s[0], rng.INIT_HIGH))
            self.assertEqual(g["game_seed_after_creation"], s)
        # draw 1 of the game seed equals the act base under an override (the same Init(N))
        self.assertEqual(chain.game_seeds(12345)["monster_regions"][0], rng.act_seeds(12345, 0)[0])


class LineSets(unittest.TestCase):
    def sets(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write(text)
        try:
            return chain.line_sets(f.name)
        finally:
            os.unlink(f.name)

    def test_sets(self):
        self.assertEqual(self.sets('IC0 {}\nAF0 {"x":1}\n'), (True, False, False))
        self.assertEqual(self.sets('AF0 {"x":1}\n'), (False, False, False))           # no creation: not an item log
        self.assertEqual(self.sets('IC0 {}\nAPE {"x":1}\nICJ {}\n'), (False, True, False))
        self.assertEqual(self.sets('RW1 {"room":1}\n'), (False, False, True))
        self.assertEqual(self.sets('RL {"room":1}\nICJ {}\nSTF0 {}\n'), (False, False, False))
        self.assertEqual(self.sets('APR0 {}\nSLOT {}\nP0 {}\nIC0 {}\n'), (True, True, True))


class Switches(unittest.TestCase):
    def test_staff_default(self):
        ns = chain.build_parser().parse_args(["check", "a.log"])
        self.assertEqual(ns.staff, "model")
        ns = chain.build_parser().parse_args(["check", "a.log", "--staff", "oracle"])
        self.assertEqual(ns.staff, "oracle")


class InitSeed(unittest.TestCase):
    def model(self, comps, hp=(10, 20), oninit=False):
        import monstats

        class T:
            def m2(self, c):
                b = bytearray(0x134)
                b[0x15:0x15 + len(comps)] = bytes(comps)
                return bytes(b)

            def monequip_oninit(self, c):
                return oninit

        M = monstats.Model(T())
        M.level = lambda cls, lid, g6d, exp: (5, 0)
        M.monlvl_stats = lambda cls, L, d, lvl: [hp[0], hp[1], 0, 0]
        M.monprop = lambda seed, cls, d: ({}, [])
        return monstats, M

    def steps(self, M, cls, nvar):
        import monstats
        s0 = (0x1234, rng.INIT_HIGH)
        sd = monstats.Seed(s0)
        M.init_seed(sd, cls, 2, 0, 1, 1, nvar)
        n, t = 0, s0
        while t != sd.t():
            t = rng.step(*t)
            n += 1
        return n

    def test_draws(self):
        _, M = self.model([3, 1, 0, 2])
        self.assertEqual(self.steps(M, 5, 2), 2)            # one variant-set pick + the HP draw
        self.assertEqual(self.steps(M, 5, 0), 4)            # three components with a count >= 1 + the HP draw
        self.assertEqual(self.steps(M, 311, 0), 5)          # + the doomknight Range(4)
        _, M = self.model([3], hp=(20, 18))
        self.assertEqual(self.steps(M, 5, 0), 1)            # hi - lo + 1 < 1: no HP draw

    def test_monequip(self):
        monstats, M = self.model([1], oninit=True)
        monstats.MONEQUIP_MODEL = False                  # the switch restores the seed oracle
        try:
            with self.assertRaises(monstats.MonEquipOracle):
                M.init_seed(monstats.Seed((1, rng.INIT_HIGH)), 5, 2, 0, 1, 1, 0)
        finally:
            monstats.MONEQUIP_MODEL = True


class MonEquip(unittest.TestCase):
    def tables(self):
        import struct
        import monstats

        def row(mon, lvl, oninit, locs):
            r = bytearray(0x1C)
            struct.pack_into("<hh", r, 0, mon, lvl)
            r[4] = oninit
            for i, l in enumerate(locs):
                r[0x14 + i] = l
            return bytes(r)
        T = monstats.Tables.__new__(monstats.Tables)
        T.ms = [bytes(0x1A8)] * 20
        T.me = [row(5, 0, 1, [4]), row(7, 30, 1, [1, 2, 3]), row(7, 10, 0, [1, 1]), row(7, 0, 0, [11]),
                row(8, 0, 0, [4]), row(-1, 0, 0, [])]
        return monstats, T

    def test_rows(self):
        monstats, T = self.tables()
        self.assertTrue(T.monequip_oninit(5))
        self.assertTrue(T.monequip_oninit(7))           # only the class's first row is tested
        self.assertFalse(T.monequip_oninit(8))
        self.assertEqual(len(T.monequip_rows(7, 40)), 3)
        self.assertEqual(len(T.monequip_rows(7, 20)), 2)  # the level-30 row is skipped
        self.assertEqual(len(T.monequip_rows(9, 20)), 0)

    def test_draws(self):
        monstats, T = self.tables()
        M = monstats.Model(T)
        sd = monstats.Seed((7, rng.INIT_HIGH))
        self.assertEqual(M.monequip(sd, 7, 20), 1)       # row (1, 1): one draw over two locations, one item;
        self.assertEqual(sd.t(), rng.step(7, rng.INIT_HIGH))   # row (11): no location in 1..10, no draw
        T.me[3] = T.me[2]                                # a second row on the same location: a draw, no item
        sd = monstats.Seed((7, rng.INIT_HIGH))
        self.assertEqual(M.monequip(sd, 7, 20), 1)
        self.assertEqual(sd.t(), rng.step(*rng.step(7, rng.INIT_HIGH)))
        sd = monstats.Seed((7, rng.INIT_HIGH))
        self.assertEqual(M.monequip(sd, 5, 1), 1)        # one location: a draw all the same
        self.assertEqual(sd.t(), rng.step(7, rng.INIT_HIGH))


class PresetVariants(unittest.TestCase):
    def pass_(self, lid, mon, lvlex):
        import struct
        import monspawn

        def rec(base, nxt, level):
            r = bytearray(0x1A8)
            struct.pack_into("<hh", r, 2, base, nxt)
            struct.pack_into("<h", r, 0xAA, level)
            return bytes(r)
        ms = [rec(i, -1, 1) for i in range(70)]
        # a chain 19 -> 20 -> 21 (levels 1, 5, 9) and 58 -> 59 -> 60 (levels 2, 6, 30)
        ms[19], ms[20], ms[21] = rec(19, 20, 1), rec(19, 21, 5), rec(19, 21, 9)
        ms[58], ms[59], ms[60] = rec(58, 59, 2), rec(58, 60, 6), rec(58, -1, 30)
        lv = bytearray(0x220)
        struct.pack_into("<h", lv, 0x16, lvlex)

        class Pool:
            def slots(self, lid_, off):
                return list(mon)

        class T:
            pass
        t = T()
        t.ms, t.lv, t.pool = ms, {lid: bytes(lv)}, Pool()
        t.valid = lambda c: 0 <= c < len(ms)
        t.m = lambda c, off, f: struct.unpack_from(f, ms[c], off)[0]
        P = monspawn.PresetMonPass.__new__(monspawn.PresetMonPass)
        P.t, P.lid = t, lid
        return P

    def test_chain_len(self):
        P = self.pass_(2, [], 0)
        self.assertEqual(P.chain_len(19), 3)       # 19, 20, 21 (21 is its own next)
        self.assertEqual(P.chain_len(58), 3)       # 58, 59, 60 (next -1)
        self.assertEqual(P.chain_len(5), 1)

    def test_level_class_variant(self):
        self.assertEqual(self.pass_(2, [], 0).level_class_variant(19), 19)          # no mon entries: unchanged
        self.assertEqual(self.pass_(2, [3, 20], 0).level_class_variant(19), 20)     # the entry with BaseId 19
        self.assertEqual(self.pass_(2, [3], 4).level_class_variant(19), 20)         # chain: level 5 <= 4 + 1
        self.assertEqual(self.pass_(2, [3], 3).level_class_variant(19), 19)         # level 5 > 3 + 1: first step refused
        self.assertEqual(self.pass_(2, [3], 8).level_class_variant(19), 21)         # both steps accepted
        self.assertEqual(self.pass_(2, [3], 8).level_class_variant(58), 59)         # 60 has level 30

    def test_fallen_variant(self):
        self.assertEqual(self.pass_(6, [], 0).fallen_variant(19), 0x14)
        self.assertEqual(self.pass_(12, [], 0).fallen_variant(20), 0x15)          # by BaseId
        self.assertEqual(self.pass_(7, [], 0).fallen_variant(58), 0x3B)
        self.assertEqual(self.pass_(16, [], 0).fallen_variant(58), 0x3C)
        self.assertEqual(self.pass_(5, [], 0).fallen_variant(19), 19)


if __name__ == "__main__":
    unittest.main()

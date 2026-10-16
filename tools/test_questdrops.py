"""Test vectors for the quest seed and the scripted quest draws: python3 -I tools/test_questdrops.py
(or python3 -I -m unittest discover -s tools -p test_questdrops.py).

The four worked examples of docs/specs/items/quest-drops.md (plan 0032 Phase 3), copied from the raw logs of
run:2026-10-16-quest-drops (quests-s3-3344-andy-normal, quests-s3-3311-svc-normal, quests-s3-3315-svc-normal; pinned
by the run's manifest), so that they survive without workspace/. Each vector is the logged entry and exit seed and
the logged result; the test recomputes the draws with tools/rng.py and the B6 test with tools/tc.py's b6_model, and
needs no game data. The log line each value comes from is named beside it (docs/findings/items/0010 § Phase 2,
"Test vectors"). Stdlib only.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import questdrops  # noqa: E402
import rng  # noqa: E402
import tc  # noqa: E402


def sp(s):
    return questdrops.sp(s)


def mod_draw(seed, n):
    """One quest-seed step, then low32 mod n (the inlined LCG of the Andariel and Hellforge scripts)."""
    lo, hi = rng.step(*seed)
    return lo % n, (lo, hi)


class QuestSeedInitTest(unittest.TestCase):
    """QUESTS_InitGame: one game-seed step, the quest seed is (low, 666) of it (QI0 -> QI1)."""

    CASES = [
        # session, QI0 gs, QI1 qs, QI1 gs
        ("3344", "42d5289c:02eff907", "5877f913:0000029a", "5877f913:1be01979"),
        ("3315", "990e7bfc:2b3308f2", "55fe31de:0000029a", "55fe31de:3fd6b718"),
        ("3311", "adc6f16a:55926933", "9371cfc5:0000029a", "9371cfc5:487b2a1a"),
    ]

    def test_init(self):
        for sess, gs0, qs, gs1 in self.CASES:
            with self.subTest(session=sess):
                lo, hi = rng.step(*sp(gs0))
                self.assertEqual((lo, hi), sp(gs1))
                self.assertEqual((lo, rng.INIT_HIGH), sp(qs))


class AndarielGemsTest(unittest.TestCase):
    """Session 3344 (Normal, expansion): B6 takes TreasureClass4, then the death script's three gem draws (QGS/QDI/QDX
    lines 4092-4136): two chipped picks, one standard, low mod 7 each; every creation keeps the quest seed."""

    B6 = [("B60", {"mon": [1, 156, 139], "qid": 6, "cp": 1, "diff": 0, "tc4": 833, "tc": 830, "ctx": 2291420,
                   "killer": [0, 1, 1]}),
          ("B6P", {"unit": [0, 1, 1], "rec": 33234496, "word": 24}),
          ("B6G", {"k": 15, "r": 0}),
          ("B6G", {"k": 1, "r": 0}),
          ("B6G", {"k": "cp", "r": 0}),
          ("B6X", {"tc": 48169084, "killer": [0, 1, 1]})]     # the game pointer: a log before the B6X fix
    START = "5877f913:0000029a"
    DRAWS = [  # table, seed after (QDI qs = QDX qs), code
        (questdrops.CHIPPED, "131f5e39:24e64bf4", "gcy"),
        (questdrops.CHIPPED, "fb1fddd1:07f9d216", "skc"),
        (questdrops.STANDARD, "4deb13eb:68bdfa81", "gsg"),
    ]

    def test_b6(self):
        want, taken, why = tc.b6_model(self.B6)
        self.assertEqual((want, taken), (833, True), why)

    def test_gems(self):
        seed = sp(self.START)
        for table, after, code in self.DRAWS:
            r, seed = mod_draw(seed, 7)
            self.assertEqual(seed, sp(after))
            self.assertEqual(table[r], code)


class HellforgeTest(unittest.TestCase):
    """Session 3315 (Normal, expansion, one player): four waves (perfect, flawless, flawless, standard; low mod 7)
    and the rune RNG_Range(quest seed, 11) into the Normal table (QGS/QDI lines 6387-6472)."""

    START = "55fe31de:0000029a"     # QUESTS_InitGame's value: Hephasto's hammer (QDI 5410) drew nothing
    WAVES = [  # waves, seed after, code
        (4, "a65d4270:23ddf3e1", "gpv"),
        (3, "61a11411:4563a7b8", "glw"),
        (2, "90c7a8cd:28b86c1a", "glw"),
        (1, "51dea1db:3c62f831", "gsb"),
    ]
    RUNE = ("5522b5b8:2225af82", "r07")

    def test_waves_and_rune(self):
        seed = sp(self.START)
        for waves, after, code in self.WAVES:
            r, seed = mod_draw(seed, 7)
            self.assertEqual(seed, sp(after))
            self.assertEqual(questdrops.FORGE_WAVE[waves][1][r], code)
        r, lo, hi = rng.rng_range(seed[0], seed[1], 11)
        self.assertEqual((lo, hi), sp(self.RUNE[0]))
        self.assertEqual(questdrops.RUNES[0][r], self.RUNE[1])


class ServicesTest(unittest.TestCase):
    """Session 3311 (Normal): Charsi's imbue (IMB0/IMBL/IMB1/IC0/IMBX lines 927-976) and Larzuk's socket of a magic
    cap (LZ0..LZY lines 2097-2101)."""

    def test_imbue_record_and_seeds(self):
        clvl = 80
        ilvl = clvl + 4 if clvl > 5 else clvl
        self.assertEqual(ilvl, 84)                         # IMB1 ilvl
        flags80 = 0x20 | 0x02                              # IMB0 fl 0x00880010: not ethereal (0x400000 clear)
        self.assertFalse(0x00880010 & 0x400000)
        self.assertEqual(flags80, 0x22)                    # IMB1 f80
        gs = sp("c4763324:169bee5b")                       # IMB1 gs, the game seed at the record
        gs = rng.step(*gs)                                 # SUnitCreate: the new unit's seed
        self.assertEqual(gs, sp("382d890f:51f153b2"))
        gs = rng.step(*gs)                                 # ItemSeedInit: the start seed
        self.assertEqual(gs, sp("61ae3c3d:176e6dbd"))      # IMBX gs
        self.assertEqual((gs[0], rng.INIT_HIGH), sp("61ae3c3d:0000029a"))   # IC0 seed (rq 6, ilvl 84)
        self.assertNotEqual(gs[0], 0x7103e9b3)             # a fresh seed, not the old item's

    def test_larzuk_magic(self):
        seed = sp("a02949bd:0000029a")                     # LZS seed (the copy's item seed), bound min(2, 2)
        r, lo, hi = rng.rng_range(seed[0], seed[1], min(2, 2))
        self.assertEqual((lo, hi), sp("c36e110b:42cd5309"))   # LZR seed
        self.assertEqual(r, 1)                             # LZR r
        self.assertEqual(1 + r, 2)                         # LZX n, LZY sockets


if __name__ == "__main__":
    unittest.main()

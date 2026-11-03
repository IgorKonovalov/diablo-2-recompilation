"""No-game tests of tools/ai.py (plan 0052 Phase 2): python3 -I tools/test_ai.py.

The model is run against its own inputs: tools/ai.py synth_log writes a fake tools/gdb/ai.gdb log in which every
decision is built from the input of an emulation case writer (tools/ai_cat_emu*.py) and the first boundary its model
predicts, and `check` must find 0 mismatches; a corrupted log (a seed, a site, an argument, a control word) must find
them. Nothing here starts a game.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402


class SynthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.path = os.path.join(cls.tmp, "synth.log")
        cls.n = ai.synth_log(cls.path, ai.TIER_MODELS)

    def test_roundtrip_zero_mismatches(self):
        text, r = ai.run_check([self.path])
        self.assertEqual(r["decisions"], self.n)
        self.assertEqual(r["decisions"], 14 * 60)
        self.assertEqual(r["mismatches"], 0, text[:2000])
        self.assertEqual(r["acc"], 0)

    def _corrupt(self, tag, key, fn):
        out = os.path.join(self.tmp, "bad-%s-%s.log" % (tag, key))
        lines = []
        with open(self.path) as fh:
            for ln in fh:
                if ln.startswith(tag + " "):
                    d = json.loads(ln[len(tag) + 1:])
                    fn(d)
                    ln = tag + " " + json.dumps(d) + "\n"
                lines.append(ln)
        with open(out, "w") as fh:
            fh.writelines(lines)
        return ai.run_check([out])[1]

    def test_site_control(self):
        r = self._corrupt("AIB", "ra", lambda d: d.__setitem__("ra", d["ra"] + 1))
        self.assertEqual(r["mismatches"], self.n)

    def test_seed_control(self):
        # the boundary seed one LCG step on: every model case whose boundary seed is read is separated
        def f(d):
            d["s"] = "%08x:%08x" % ai.step(ai.seedval(d["s"]))
        r = self._corrupt("AIB", "seed", f)
        self.assertEqual(r["mismatches"], self.n)

    def test_fn_control(self):
        r = self._corrupt("AIB", "fn", lambda d: d.__setitem__("fn", d["fn"] ^ 0x10))
        self.assertEqual(r["mismatches"], self.n)

    def test_aip_control(self):
        # a different aip block changes the decisions of the models that read it, not those that read none
        def f(d):
            d["aip"] = "00" * 48
        r = self._corrupt("AID", "aip", f)
        self.assertGreater(r["mismatches"], 0)
        self.assertLess(r["mismatches"], self.n)

    def test_model_registry_covers_the_tier(self):
        mods = ai.load_mods()
        reg = mods["_reg"]
        for mn, fam in ai.TIER_MODELS:
            self.assertEqual(reg[mods[mn].FNS[fam]][1] in mods[mn].FNS, True)
        # the 13 emulated tier AIs of the 18 (ai/0001 § 13 and the P1.1 review ruling 1), by think address
        for th in (0x005EFCF0, 0x005F0A20, 0x005F2540, 0x005F2850, 0x005F2B10, 0x005F6070, 0x005F96C0, 0x005E4CF0,
                   0x005E52D0, 0x005F5830, 0x005E0C80, 0x005E36F0):
            self.assertIn(th, reg)
        # the five without an emulation have a hand map
        for th in (0x005F02C0, 0x005F1440, 0x005F4A70, 0x005F5040, 0x005F5A20):
            self.assertIn(th, ai.HAND)
            self.assertNotIn(th, reg)


class PartsTest(unittest.TestCase):
    def test_reach(self):
        s = (123, 456)
        t = s
        for _ in range(5):
            t = ai.step(t)
        self.assertEqual(ai.reach(s, t), 5)
        self.assertEqual(ai.reach(s, s), 0)
        self.assertIsNone(ai.reach(s, (1, 2)))

    def test_step_matches_the_game_lcg(self):
        # seed (+0x20, +0x24) -> low*0x6AC690C5 + high, low word and carry
        self.assertEqual(ai.step((1, 0)), (0x6AC690C5, 0))
        self.assertEqual(ai.step((0x10000, 7)), ((0x10000 * 0x6AC690C5 + 7) & 0xFFFFFFFF,
                                                 (0x10000 * 0x6AC690C5 + 7) >> 32))

    def test_hand_models(self):
        i = {"m": 12, "seed": (1, 2), "melee": 0, "aip": [[0] * 3] * 8, "diff": 0, "dist": 5}
        self.assertIsNone(ai.hand_fallen(i))
        i["m"] = 1
        self.assertEqual(ai.hand_fallen(i)[:2], (0x00540E60, 0x005F02FD))
        # FallenShaman: a melee draw below aip3 attacks, else MonTypeFlag
        i["melee"] = 1
        i["aip"] = [[0] * 3, [0] * 3, [100, 100, 100]] + [[0] * 3] * 5
        self.assertEqual(ai.hand_shaman(i)[0], 0x005DDF90)
        i["aip"] = [[0] * 3] * 8
        self.assertEqual(ai.hand_shaman(i)[0], 0x005A0180)
        self.assertEqual(ai.hand_vampire(i)[1], 0x005F4AD5)

    def test_chain_counts(self):
        def dec(n, u, s0, s, sx, nx):
            return {"log": "x", "aid": {"n": n, "u": u, "id": 5, "ai": 2, "s0": s0, "s": s}, "aix": {"s": sx, "n": nx}}
        a = dec(10, 1, "00000001:00000000", "00000001:00000000", "0000000a:00000000", 12)
        b = dec(20, 1, "0000000a:00000000", "0000000a:00000000", "0000000b:00000000", 22)
        c = dec(30, 1, "0000000c:00000000", "0000000c:00000000", "0000000d:00000000", 32)
        pairs, skill = ai.chains([a, b, c], [{"log": "x", "u": 1, "id": 5, "n": 13, "s": "0000000a:00000000"}])
        self.assertEqual(pairs, {2: [1, 1]})
        self.assertEqual(skill, {2: [1, 1]})

    def test_parse_skips_foreign_lines(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as fh:
            fh.write('PLR {"x":1}\nAID {"n":3,"ai":2}\nAIB {"k":3,"fn":1}\nAIB {"k":99,"fn":2}\nnoise\n')
            p = fh.name
        r = ai.parse(p)
        os.unlink(p)
        self.assertEqual(len(r["dec"]), 1)
        self.assertEqual(len(r["dec"][0]["aib"]), 1)


if __name__ == "__main__":
    unittest.main()

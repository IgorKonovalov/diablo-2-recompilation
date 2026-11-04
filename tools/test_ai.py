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

    def test_rev2_marks_the_unlogged_sites(self):
        # a rev 2 log: a model whose first boundary is at a call site the rev 2 window does not cover is "unlogged"
        p = os.path.join(self.tmp, "rev2.log")
        ai.synth_log(p, [("ai_cat_emu2", "scarab")], rev=2)
        text, r = ai.run_check([p])
        self.assertEqual(r["mismatches"], 0)
        self.assertRegex(text, r"unlogged=[1-9]")
        p3 = os.path.join(self.tmp, "rev3.log")
        ai.synth_log(p3, [("ai_cat_emu2", "scarab")], rev=3)
        self.assertIn("unlogged=0", ai.run_check([p3])[0])

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


def fallen_log(path, modes):
    """A fake log of Fallen decisions (hand map, row 6): one per mode in `modes`, each with the boundary the map
    predicts (CancelEvents at 0x005F02FD, or none in modes 0 and 12)."""
    seed = "00000001:00000002"
    out = ["AI logger armed rev 3"]
    for k, m in enumerate(modes):
        n = 10 * (k + 1)
        aid = {"u": 0x2000, "id": k + 1, "c": 7, "ai": 6, "st": 0, "th": 0x005F02C0, "cx": 0x7000, "g": 0x1000,
               "mdp": 0x5000, "ctlp": 0x4000, "hp": 0, "md": 0, "m": m, "c4": 0, "x": 1, "y": 1, "s0": seed, "s": seed,
               "fr": 100, "diff": 0, "ms": 0x6000, "ms2": 0x2E0, "ctx": [0x4000, 0, 0x3000, 0, 0, 0, 0, 0x6000, 0],
               "ctl": "00" * 0x40, "head": None, "aip": "00" * 48, "sk": "00" * 24, "ad": [0, 0], "t": None,
               "pl": [0, 0], "n": n}
        out.append("AID " + json.dumps(aid))
        if m not in (0, 12):
            out.append("AIB " + json.dumps({"k": n, "fn": 0x00540E60, "ra": 0x005F02FD, "ecx": 0x1000, "edx": 0x2000,
                                            "a": [2, 0, 0, 0, 0, 0], "b": {}, "s": seed, "c": [0, 0, 0], "c4": 0,
                                            "fr": 100, "n": n + 1}))
        out.append("AIX " + json.dumps({"k": n, "s": seed, "nb": 0 if m in (0, 12) else 1, "fr": 100, "n": n + 2}))
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")


class MixControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.synth = os.path.join(cls.tmp, "synth.log")
        ai.synth_log(cls.synth, ai.TIER_MODELS)
        cls.fal = os.path.join(cls.tmp, "fallen.log")
        fallen_log(cls.fal, [1, 1, 1, 4, 4])            # no decision in mode 0 or 12: one outcome

    def test_mix_counts_outcomes_per_ai(self):
        text, r = ai.run_check([self.synth])
        self.assertIn("MIX ", text)
        self.assertEqual(sum(sum(v.values()) for v in r["mix"].values()), r["decisions"])
        self.assertRegex(text, r"MIXSUM tier_ais_with_one_outcome=\d+")

    def test_one_outcome_ai_is_flagged(self):
        text, r = ai.run_check([self.fal])
        self.assertEqual(r["mismatches"], 0)
        self.assertRegex(text, r"MIX 6 th=005f02c0 .*ONE-OUTCOME: 00540e60@005f02fd=5")
        self.assertIn("rows=6", text.split("MIXSUM")[1].split("\n")[0])

    def test_mode_0_and_12_make_a_second_outcome(self):
        p = os.path.join(self.tmp, "fallen2.log")
        fallen_log(p, [1, 4, 0, 12])
        text, r = ai.run_check([p])
        self.assertEqual(r["mismatches"], 0)
        self.assertRegex(text, r"MIX 6 th=005f02c0 .*outcomes=2")
        self.assertIn("return@-=2", text)

    def test_controls_fail_on_the_kept_shape(self):
        text, r = ai.run_check([self.fal], controls=True)
        ctl = dict(r["controls"])
        self.assertTrue(ctl["site"] and ctl["fallen"])
        self.assertRegex(text, r"CONTROL site compared=5 failed=5")
        self.assertRegex(text, r"CONTROL fallen compared=5 failed=5")
        # the melee control does not separate Fallen: nothing in the decision reads the flag
        self.assertRegex(text, r"CONTROL-ROW melee 6 Fallen\s+compared=5 failed=0")

    def test_a_log_cut_inside_its_last_decision_is_unlogged_not_a_mismatch(self):
        # the game exits while the last decision is open: its AID line is the log's last AI line, with no AIB, AIR or AIX
        p = os.path.join(self.tmp, "cut.log")
        fallen_log(p, [1])
        lines = open(p).readlines()
        last = max(i for i, ln in enumerate(lines) if ln.startswith("AID "))
        open(p, "w").writelines(lines[:last + 1])
        text, r = ai.run_check([p])
        self.assertEqual(r["mismatches"], 0, text[:1500])
        self.assertIn("unlogged=1", text)
        # the same decision in the middle of a log (more decisions after it) with its boundary missing is a mismatch
        q = os.path.join(self.tmp, "mid.log")
        fallen_log(q, [1, 1])
        lines = open(q).readlines()
        first = min(i for i, ln in enumerate(lines) if ln.startswith("AID "))
        out = [ln for i, ln in enumerate(lines) if not (ln.startswith("AIB ") and i > first and
                                                         min(j for j, x in enumerate(lines) if x.startswith("AIB ")) == i)]
        open(q, "w").writelines(out)
        text, r = ai.run_check([q])
        self.assertGreater(r["mismatches"], 0, text[:1500])

    def test_a_control_that_passes_is_reported_wrongly_passed(self):
        # the inverted Fallen map predicts a return in modes other than 0 and 12; a log whose decisions in those modes
        # carry no boundary makes it match: the control then PASSES and the run says so
        p = os.path.join(self.tmp, "fallen3.log")
        fallen_log(p, [1, 4])
        lines = [ln for ln in open(p) if not ln.startswith("AIB ")]
        open(p, "w").writelines(lines)
        text, r = ai.run_check([p], controls=True)
        self.assertGreater(r["mismatches"], 0)           # the real map fails (it predicts CancelEvents)
        self.assertIn("fallen=PASSED-WRONGLY", text)


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
        def dec(n, u, s0, s, sx, nx, sst=()):
            return {"log": "x", "aid": {"n": n, "u": u, "id": 5, "ai": 2, "s0": s0, "s": s}, "aix": {"s": sx, "n": nx},
                    "aib": [], "msm": [], "pp": [], "sst": list(sst)}
        a = dec(10, 1, "00000001:00000000", "00000001:00000000", "0000000a:00000000", 12)
        b = dec(20, 1, "0000000a:00000000", "0000000a:00000000", "0000000b:00000000", 22)
        c = dec(30, 1, "0000000c:00000000", "0000000c:00000000", "0000000d:00000000", 32)
        pairs, skill = ai.chains([a, b, c], [])
        self.assertEqual(pairs, {2: [1, 1]})
        self.assertEqual(skill, {})
        # a skill start inside a decision: entry two LCG steps on from the decision's seed, exit seed = the event's
        s1 = ai.step(ai.step((5, 0)))
        s2 = "%08x:%08x" % ai.step(s1)
        t = {"n": 41, "u": 1, "id": 5, "s": "%08x:%08x" % s1, "exit": {"n": 42, "s": s2}}
        d = dec(40, 1, "00000005:00000000", "00000005:00000000", s2, 43, [t])
        pairs, skill = ai.chains([d], [t])
        self.assertEqual(skill, {2: [1, 1, 1, {2: 1}]})
        steps, bad = ai.accounting(dict(d, sst=[t]))
        self.assertEqual(bad, [])

    def test_parse_reads_air_lines_and_the_bmax_of_the_logger_line(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as fh:
            fh.write('AI logger armed rev 4 bmax 48\nAID {"n":3,"ai":2}\nAIB {"k":3,"fn":1,"n":4}\n'
                     'AIR {"k":3,"b":4,"eax":7,"n":5}\nAIR {"k":99,"b":4,"n":6}\n')
            p = fh.name
        r = ai.parse(p)
        os.unlink(p)
        self.assertEqual(r["dec"][0]["bmax"], 48)
        self.assertEqual(r["dec"][0]["air"][4]["eax"], 7)
        self.assertEqual(len(r["dec"][0]["air"]), 1)

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

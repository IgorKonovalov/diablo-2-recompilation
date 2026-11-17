"""Tests of the DRLG schematic animations (plan 0070 Phase 11, batch 2): tools/links_anim.py (the act link builder, rows 11
and 14: placements, and with --warps the warp points and their pairing) and tools/preset_anim.py (a preset's keep/drop
rolls, row 13).

Run: python3 -I tools/test_drlg_anim.py     (needs workspace/merged and the game image beside it: skipped without them)

Each tool: the same arguments give the same bytes, in both themes; every file carries the marker; the folder passes the
export check's illustration rules (with the allow-hex list); no art decoder is imported; no text line runs past the
canvas and no caption is cut. The numbers: the traced placements equal a plain run of the model's link builder (rects,
level 27's index) and the spec's worked example (warps, map seed 2027, Act I); the warp points and the pairing equal
the warps spec's worked example; the preset rolls equal the preset spec's worked example (Lut Gholein) and the model.
"""
import hashlib
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
OUT = os.path.join(ROOT, "workspace", "render", "test-drlg-anim")
sys.path.insert(0, HERE)
import drlg  # noqa: E402
import export_check  # noqa: E402
import links_anim  # noqa: E402
import preset_anim  # noqa: E402
import schematic_kit as K  # noqa: E402

export_check.set_allow(export_check.load_allow(os.path.join(ROOT, "docs", "export", "allow-hex.txt")))
ART = ("dt1", "dc6", "item_art", "palette", "maze_render")
HAVE = os.path.isdir(DATA) and os.path.isfile(EXE)


def run(tool, args, name):
    out = os.path.join(OUT, name)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.unlink(os.path.join(out, f))
    code = ("import sys; sys.path.insert(0, %r); import %s as m; rc = m.main(sys.argv[1:]); "
            "bad = [x for x in %r if x in sys.modules]; assert not bad, bad; sys.exit(rc)" % (HERE, tool[:-3], ART))
    r = subprocess.run([sys.executable, "-I", "-c", code, DATA] + args + ["--schematic", "--out", out],
                       capture_output=True, text=True)
    assert r.returncode == 0, (tool, args, r.stderr[-600:])
    return out


def hashes(out):
    h = {}
    for n in sorted(os.listdir(out)):
        with open(os.path.join(out, n), "rb") as fh:
            h[n] = hashlib.sha256(fh.read()).hexdigest()
    return h


def steps(out):
    with open(os.path.join(out, "steps.json")) as fh:
        return json.load(fh)["steps"]


@unittest.skipUnless(HAVE, "needs workspace/merged and the game image")
class Links(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ARGS = ["0xC0FFEE"]
        cls.a = run("links_anim.py", cls.ARGS, "l-a")
        cls.b = run("links_anim.py", cls.ARGS, "l-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("links.gif", ok)

    def test_both_themes_and_other_acts(self):
        for name, args in (("l-light", ["0xC0FFEE", "--theme", "light"]), ("l-act2", ["0xC0FFEE", "--act", "1", "--diff", "2"]),
                           ("l-act4", ["0xC0FFEE", "--act", "3", "--theme", "light"]),
                           ("l-act5", ["12345", "--act", "4", "--diff", "1"])):
            out = run("links_anim.py", args, name)
            self.assertEqual(export_check.verify_illustration(out, identity=())[0], [], name)

    def test_traced_placements_equal_a_plain_run_of_the_model(self):
        for act, seed, diff in ((0, 0xC0FFEE, 0), (0, 2027, 0), (1, 0xC0FFEE, 2), (3, 0xC0FFEE, 1), (4, 12345, 0)):
            A, tables = links_anim.trace(DATA, act, seed, diff)
            P = drlg.Act(act, seed, diff)
            drlg.act_links(P)
            self.assertEqual(A.rect, P.rect)
            self.assertEqual(A.idx27, P.idx27)
            self.assertEqual((A.seed.lo, A.seed.hi), (P.seed.lo, P.seed.hi))
            for tb in tables:
                kept = links_anim.entry_state(tb, len(tb["events"]))
                self.assertEqual(sorted(kept), list(range(len(tb["t"]))))
                for i, r in kept.items():
                    self.assertEqual(r, tb["B"].rect[i])
                    self.assertEqual(r, P.rect[tb["t"][i][1]])
                # every draw of an event is the next step of the copy of the act seed
                s = tb["seed_in"].copy()
                for e in tb["events"]:
                    for d in e["draws"]:
                        self.assertEqual(d, s.step())

    def test_the_warps_spec_worked_example(self):
        # warps.md Worked example 1: map seed 2027, normal, Act I (table 0x006F0750 and 0x006F0840)
        A, tables = links_anim.trace(DATA, 0, 2027, 0)
        t1, t2 = tables
        ev = [(e["i"], e["rect"][:4], e["ok"]) for e in t1["events"]]
        self.assertIn((1, [1016, 920, 80, 80], True), ev)                     # Cold Plains, draw & 3 = 2
        self.assertIn((2, [1056, 1000, 56, 96], False), ev)                   # Blood Moor (0, 0): overlap, rejected
        self.assertIn((2, [920, 904, 96, 56], True), ev)                      # Blood Moor (1, 1) accepted
        self.assertIn((3, [864, 912, 56, 40], True), ev)                      # Rogue Encampment, side-pair table
        self.assertIn((4, [1072, 872, 40, 48], True), ev)                     # Burial Grounds
        ev2 = [(e["i"], e["rect"][:4], e["ok"]) for e in t2["events"]]
        self.assertIn((3, [3016, 938, 80, 80], False), ev2)                   # Black Marsh side 2 overlaps 26
        self.assertIn((3, [3080, 1034, 80, 80], True), ev2)
        self.assertEqual(A.idx27, 1)                                          # (~0x2FAADC42) & 1
        self.assertEqual(links_anim.reject_reason([e for e in t2["events"] if e["i"] == 3][0])[0], "OVERLAPS 26")
        self.assertEqual(t1["events"][1]["draws"], [0x2FAADC42])

    def test_every_reject_has_a_reason_of_the_spec(self):
        for seed in (0xC0FFEE, 2027, 52, 17, 5):
            A, tables = links_anim.trace(DATA, 0, seed, 0)
            for tb in tables:
                for e in tb["events"]:
                    if e["pick"] and not e["ok"]:
                        self.assertNotEqual(links_anim.reject_reason(e)[0], "CHECK REJECTS", (seed, e["i"]))

    def test_no_clipped_text_and_no_cut_caption(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for args in ((0xC0FFEE, 0, 0), (2027, 0, 0), (0xC0FFEE, 0, 2), (0xC0FFEE, 1, 0), (0xC0FFEE, 3, 1), (12345, 4, 2)):
            for th in ("dark", "light"):
                links_anim.build_links(DATA, args[1], args[0], args[2], th)
        for th in ("dark", "light"):
            links_anim.build_warps(DATA, th)
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_bad_arguments(self):
        self.assertEqual(links_anim.main([DATA, "x"]), 2)
        self.assertEqual(links_anim.main([DATA, "5", "--act", "2"]), 2)
        self.assertEqual(links_anim.main([DATA, "5", "--theme", "blue"]), 2)
        self.assertEqual(links_anim.main([DATA]), 2)


@unittest.skipUnless(HAVE, "needs workspace/merged and the game image")
class Warps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = ["--warps"]
        cls.a = run("links_anim.py", cls.args, "w-a")
        cls.b = run("links_anim.py", cls.args, "w-b")

    def test_deterministic_and_clean(self):
        self.assertEqual(hashes(self.a), hashes(self.b))
        self.assertEqual(export_check.verify_illustration(self.a, identity=())[0], [])
        out = run("links_anim.py", self.args + ["--theme", "light"], "w-light")
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])

    def test_points_and_pairing_equal_the_spec_example(self):
        frames, caps, t = links_anim.build_warps(DATA, "dark")
        self.assertEqual(len(frames), 3)
        # warps.md Worked example 2: points (7880, 6520) and (7640, 6840)
        self.assertEqual([p[4] for p in t["pts"]], [(7880, 6520), (7640, 6840)])
        # level 3's link list after the builder: Vis 4, 2, 17, 9, 9, 9, 9, 0 and Warp -1, -1, -1, 0, 1, 2, 3, -1
        self.assertEqual(t["v3"], [4, 2, 17, 9, 9, 9, 9, 0])
        self.assertEqual(t["w3"], [-1, -1, -1, 0, 1, 2, 3, -1])
        (s1, m1, k1, want1, walk1, got1), (s2, m2, k2, want2, walk2, got2) = t["pairs"]
        # from 3 slot 6: k = 3, no rank slot, fallback takes slot 0
        self.assertEqual((s1, m1, k1, want1, walk1, got1), (3, 6, 3, None, [0], 0))
        # from 9 slot 0: k = 0, the rank slot 3 has no room, the walk 3, 4, 5 finds none and slot 6 pairs
        self.assertEqual((s2, m2, k2, want2, walk2, got2), (9, 0, 0, 3, [3, 4, 5, 6], 6))
        st = steps(self.a)
        self.assertIn("(1572 + 4) * 5, (1300 + 4) * 5 = (7880, 6520)", " ".join(st[0]["calc"]))

    def test_pair_rule_on_a_rank_hit(self):
        v = [2, 2, 0, 0, 0, 0, 0, 0]
        d = [0, 0, 1, 1, 0, 0, 0, 0]
        # source slot 1 names 2: k = 1, the second slot of the destination naming 1 is slot 3
        self.assertEqual(links_anim.pair(v, d, 1, 1, lambda j: True), (1, 3, [], 3))
        self.assertEqual(links_anim.pair(v, d, 1, 1, lambda j: j == 2), (1, 3, [2], 2))
        self.assertEqual(links_anim.pair(v, d, 1, 1, lambda j: False), (1, 3, [2, 3], None))
        self.assertEqual(links_anim.warp_point((10, 20, 9, 9)), ((10 + 4) * 5, (20 + 4) * 5))      # w / 2 truncates


@unittest.skipUnless(HAVE, "needs workspace/merged and the game image")
class Preset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ARGS = ["0xC0FFEE"]
        cls.a = run("preset_anim.py", cls.ARGS, "p-a")
        cls.b = run("preset_anim.py", cls.ARGS, "p-b")

    def test_deterministic_and_clean(self):
        self.assertEqual(hashes(self.a), hashes(self.b))
        self.assertEqual(export_check.verify_illustration(self.a, identity=())[0], [])
        for name, args in (("p-light", ["0xC0FFEE", "--theme", "light"]), ("p-lutn", ["12345", "--preset", "lutn"]),
                           ("p-cat", ["0xC0FFEE", "--preset", "catne", "--theme", "light"])):
            out = run("preset_anim.py", args, name)
            self.assertEqual(export_check.verify_illustration(out, identity=())[0], [], name)

    def test_rolls_equal_the_model(self):
        T = preset_anim.trace(DATA, 0xC0FFEE, "lutw")
        pu = T["pu"]
        units = pu.ds1("Act2\\Town\\LutW.ds1")["units"]
        inst, send, draws = pu.drop_rolls(units, (0xC0FFEE, 666), 0, 0)
        self.assertEqual(T["send"], send)
        self.assertEqual([r["draw"] for r in T["rows"]], draws)
        self.assertEqual(T["kept"], inst)
        st = steps(self.a)
        self.assertEqual(len(st), 2 + len(draws))
        for j, (typ, uid, r, keep) in enumerate(draws):
            txt = " ".join(st[1 + j]["calc"])
            self.assertIn("r = low word of the new seed = %d;" % r, txt)
            self.assertIn("result: %s." % ("kept" if keep else "dropped"), txt)
            lo, hi = T["rows"][j]["after"]
            self.assertIn("{%08x:%08x}" % (lo, hi), txt)

    def test_the_preset_spec_worked_example(self):
        # preset.md Worked example, Lut Gholein: level seed in {015B2E9F, 666}, LutW: 204 draws 3A5E52F5, 205 draws 954E7521,
        # r mod 3 = 2 both, neither kept; LutN with D58D244C: 205 draws 44CFB116, 204 draws 3385BAE3, both kept
        w = preset_anim.trace(DATA, 0x015B2E9F, "lutw")
        self.assertEqual([(r["draw"][1], r["draw"][2], r["draw"][3]) for r in w["rows"]],
                         [(204, 0x3A5E52F5, False), (205, 0x954E7521, False)])
        self.assertEqual(w["send"][0], 0x954E7521)
        n = preset_anim.trace(DATA, 0xD58D244C, "lutn")
        self.assertEqual([(r["draw"][1], r["draw"][2], r["draw"][3]) for r in n["rows"]],
                         [(205, 0x44CFB116, True), (204, 0x3385BAE3, True)])
        self.assertEqual(n["send"][0], 0x3385BAE3)

    def test_the_tests_shown_are_the_specs(self):
        # each rule's chance and answer on r values over a full period of 12 (the lcm of the moduli)
        R = preset_anim.RULES
        for key, rule in R.items():
            kept = sum(1 for r in range(12) if rule[1](r))
            self.assertEqual(kept * rule[3], 12 * rule[2], key)
        self.assertEqual(sorted(R), [("m", 204), ("m", 205), ("m", 371), ("m", 372), ("o", 196), ("o", 261), ("o", 581),
                                      ("p", 33), ("p", 34), ("p", 35)])

    def test_no_clipped_text_and_no_cut_caption(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for preset in ("lutw", "lutn", "catne"):
            for th in ("dark", "light"):
                preset_anim.build(DATA, 0xC0FFEE, preset, th)
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_bad_arguments(self):
        self.assertEqual(preset_anim.main([DATA, "x"]), 2)
        self.assertEqual(preset_anim.main([DATA, "5", "--preset", "nope"]), 2)
        self.assertEqual(preset_anim.main([DATA, "5", "--theme", "blue"]), 2)


if __name__ == "__main__":
    unittest.main()

"""Tests of tools/outdoor_anim.py (plan 0070 Phase 11, batch 2, row 12): the Burial Grounds' cell grid, outline, seam mark,
border pass, preset and final cell bits, as a schematic animation.

Run: python3 -I tools/test_outdoor_anim.py     (needs workspace/merged and the game image beside it: skipped without them)

Determinism in both themes; every file carries the marker; the folder passes the export check's illustration rules (with
the allow-hex list); no art, tile or preset-file decoder is imported; no text line runs past the canvas and no caption is
cut; no tool name, path or method word in a step text. The numbers: the recorded run equals a plain run of the model (the
cell grids, the seed, the draws) for several map seeds and difficulties, and the spec's outdoor worked example 1 (map
seed 3103, normal): the nine draws, the opening cell's 0x40601, the seam's grid0 flag 0x40 on cells (0..2, 5).
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
OUT = os.path.join(ROOT, "workspace", "render", "test-outdoor-anim")
sys.path.insert(0, HERE)
import drlg  # noqa: E402
import export_check  # noqa: E402
import outdoor_anim  # noqa: E402
import schematic_kit as K  # noqa: E402

export_check.set_allow(export_check.load_allow(os.path.join(ROOT, "docs", "export", "allow-hex.txt")))
ART = ("dt1", "dc6", "item_art", "palette", "maze_render", "preset_render")   # ds1 is the model's own import; the tool imports none
HAVE = os.path.isdir(DATA) and os.path.isfile(EXE)
TOOL_WORDS = ("drlg", ".py", "tools/", "python", "workspace", "Outdoor(", "Seed(", "O.place", "ring_build", "seam_mark",
              "border_build", "corner_flood", "snapshot", "wrapper")


def run(args, name):
    out = os.path.join(OUT, name)
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.unlink(os.path.join(out, f))
    code = ("import sys; sys.path.insert(0, %r); import outdoor_anim as m; rc = m.main(sys.argv[1:]); "
            "bad = [x for x in %r if x in sys.modules]; assert not bad, bad; sys.exit(rc)" % (HERE, ART))
    r = subprocess.run([sys.executable, "-I", "-c", code, DATA] + args + ["--schematic", "--out", out],
                       capture_output=True, text=True)
    assert r.returncode == 0, (args, r.stderr[-600:])
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


def plain(seed, diff):
    A = drlg.Act(0, seed, diff)
    drlg.act_links(A)
    O = drlg.Outdoor(A, 17, drlg.Seed(A.base + 17))
    O.seed.log = []
    O.run()
    return O


@unittest.skipUnless(HAVE, "needs workspace/merged and the game image")
class Outdoor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = run(["0xC0FFEE"], "o-a")
        cls.b = run(["0xC0FFEE"], "o-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("outdoor.gif", ok)

    def test_both_themes_and_other_seeds(self):
        for name, args in (("o-light", ["0xC0FFEE", "--theme", "light"]), ("o-3103", ["3103"]),
                           ("o-h", ["2027", "--diff", "2", "--theme", "light"]), ("o-n", ["12345", "--diff", "1"])):
            out = run(args, name)
            self.assertEqual(export_check.verify_illustration(out, identity=())[0], [], name)

    def test_eleven_frames_and_no_clipping(self):
        del K.TEXT_CLIPPED[:], K.CAPTION_CUT[:]
        for seed, diff, theme in ((0xC0FFEE, 0, "dark"), (0xC0FFEE, 0, "light"), (3103, 0, "dark"), (2027, 1, "dark"),
                                  (12345, 2, "light"), (99, 0, "dark")):
            frames, caps, _R = outdoor_anim.build(DATA, seed, diff, theme)
            self.assertEqual(len(frames), 11)
            self.assertEqual(len(caps), 11)
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_no_tool_words_or_section_signs_in_the_step_texts(self):
        st = steps(self.a)
        for s in st:
            txt = s["text"] + " " + " ".join(s["calc"])
            for w in TOOL_WORDS:
                self.assertNotIn(w, txt, (w, txt))
            self.assertNotIn("§", s["text"])

    def test_the_recorded_run_equals_a_plain_run_of_the_model(self):
        for seed, diff in ((0xC0FFEE, 0), (3103, 0), (2027, 1), (12345, 2), (99, 0), (4242, 1)):
            R = outdoor_anim.trace(DATA, seed, diff)
            P = plain(seed, diff)
            self.assertEqual(R.O.cell, P.cell)
            self.assertEqual(R.O.g0, P.g0)
            self.assertEqual(R.O.defg, P.defg)
            self.assertEqual(R.seed_out, (P.seed.lo, P.seed.hi))
            self.assertEqual(R.draws, P.seed.log)
            # the model's methods are back: the instance holds no wrapper
            for n in ("place", "ring_build", "seam_mark", "border_build", "corner_flood"):
                self.assertNotIn(n, R.O.__dict__)
            # every recorded draw is a first use: the border pass and the preset draw once per distinct piece
            firsts = [e for k, e in R.events if k == "place" and e["first"]]
            self.assertEqual([d for e in firsts for d in e["draws"]], R.draws)
            self.assertEqual(len({e["d"] for e in firsts}), len(firsts))

    def test_every_placement_is_in_one_segment_or_the_preset(self):
        for seed in (0xC0FFEE, 3103, 2027, 12345):
            R = outdoor_anim.trace(DATA, seed, 0)
            segs = outdoor_anim.segments(R)
            border = [e for k, e in R.events if k == "place" and e["border"]]
            got = [e for s in segs for e in s["edge"] + ([s["corner"]] if s["corner"] else [])]
            self.assertEqual([id(e) for e in got], [id(e) for e in border])
            self.assertEqual(len(segs), len(R.ring))

    def test_the_spec_worked_example_1(self):
        # outdoor.md Worked example 1: Burial Grounds, map seed 3103, normal; level seed in 3CD4C686:0000029A
        R = outdoor_anim.trace(DATA, 3103, 0)
        segs = outdoor_anim.segments(R)
        self.assertEqual(R.seed_in, (0x3CD4C686, 0x29A))
        self.assertEqual(R.rect, [1136, 968, 40, 48])
        self.assertEqual((R.O.cw, R.O.ch), (5, 6))
        self.assertEqual(R.draws, [0x870C27B8, 0xC46159C3, 0x448D8B46, 0x65502E62, 0xA12E9953, 0x5D8E7562, 0xC1ADC517,
                                   0xE6652864, 0x28B0827C])
        self.assertEqual(R.seed_out, (0x28B0827C, 0x60189741))
        self.assertEqual(R.O.cell[5][1], 0x40601)                      # the opening cell
        self.assertEqual([R.O.g0[5][x] for x in range(5)], [0x40, 0x40, 0x40, 0, 0])
        self.assertEqual(sum(1 for r in R.O.g0 for v in r if v), 3)
        self.assertEqual(R.ring[-1], (2, 5, 1, 0))                      # the seam's start vertex
        self.assertEqual([(s["edge"][0]["d"] if s["edge"] else None, s["corner"]["d"] if s["corner"] else None)
                          for s in segs], [(5, 9), (6, 10), (7, 11), (4, 4), (4, 8)])
        # draw 1: W edge Def 5, Files 3, mod 3 = 1 -> (0, 4) index 2, (0, 3) 0, (0, 2) 1, (0, 1) 2
        idx = [(e["after"][0][e["y"]][e["x"]] >> 16) & 0xF for e in segs[0]["edge"]]
        self.assertEqual(idx[:4], [2, 0, 1, 2])
        self.assertEqual(segs[4]["open"], [(1, 5)])
        self.assertEqual(segs[3]["open"], [])
        pre = [e for k, e in R.events if k == "place" and not e["border"]][0]
        self.assertEqual((pre["x"], pre["y"], pre["d"], pre["w"], pre["h"]), (1, 1, 108, 3, 4))

    def test_the_frames_state_the_model_numbers(self):
        st = steps(self.a)
        R = outdoor_anim.trace(DATA, 0xC0FFEE, 0)
        self.assertIn("(%d, %d, %d, %d)" % tuple(R.rect), st[0]["calc"][0])
        self.assertIn("{%08x:%08x}" % R.seed_in, st[0]["calc"][2])
        self.assertIn("{%08x:%08x}" % R.seed_out, st[-1]["calc"][0])
        self.assertIn("0x40601", st[-1]["calc"][1])
        self.assertIn("slot 2", st[2]["text"])
        self.assertTrue(st[6]["text"].endswith("the edge piece again."), st[6]["text"])

    def test_the_module_imports_no_art_decoder(self):
        src = open(os.path.join(HERE, "outdoor_anim.py")).read()
        for n in ART + ("ds1", "dt1"):
            self.assertNotRegex(src, r"^\s*import %s\b" % n)
            self.assertNotRegex(src, r"^\s*from %s import" % n)

    def test_bad_arguments(self):
        for args in ([], ["0"], ["abc"], ["5", "--diff", "3"], ["5", "--theme", "blue"], ["5", "--diff"]):
            r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "outdoor_anim.py"), DATA] + args,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, args)


if __name__ == "__main__":
    unittest.main()

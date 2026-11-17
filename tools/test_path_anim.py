"""Tests of the batch 2 schematic generators (plan 0070 Phase 11, lane x12d): tools/path_anim.py (the search, the random
walk and the spiral on one toy grid), tools/runeword_anim.py (the runeword match) and tools/move_anim.py (a moving unit's
per-frame step).

Run: python3 -I tools/test_path_anim.py     (the runeword case needs workspace/merged: skipped without it)

Each generator: the same arguments give the same bytes, both themes pass the export check's illustration rules, no art
decoder is imported, no text runs past the canvas, no caption is cut, and no step text names a tool or a path. The numbers
equal the model: the search equals the emulation model of tools/path_emu2.py run on the same toy room with the spec's tables;
the walk equals search I's formula on tools/rng.py's step; the spiral takes the 94 iterations search J gives at the kept
start; the runeword match equals tools/sockets.py match; the step equals tools/anim.py step_model with the frame counts of
movement B3's worked example.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
sys.path.insert(0, HERE)
import anim  # noqa: E402
import move_anim  # noqa: E402
import path_anim  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402
import test_schematic_kit as TK  # noqa: E402

ARGS = {"search": ["--mode", "search"], "walk": ["--mode", "walk"], "spiral": ["--mode", "spiral"]}


def texts(out):
    return [s["text"] for s in TK.steps(out)] + TK.calc_text(out)


class Path(unittest.TestCase):
    def test_each_mode_is_deterministic_and_passes_the_export_check(self):
        for mode, a in ARGS.items():
            out = TK.same_both_themes(self, "path_anim.py", a, "pa-" + mode)
            self.assertTrue(len(TK.steps(out)) >= 5, mode)

    def test_search_equals_the_emulation_model(self):
        import path_emu2 as E

        class Img:                                           # the tables of the spec, in the model's own form
            rows = tuple(v for r in path_anim.TURN_ROWS for v in r) + (0,)
            add = (0,) * 32
            steps = list(path_anim.STEP8)
            dirs = list(path_anim.DIR_OCTANT)
        old, E.IMG = E.IMG, Img
        try:
            for b1c, walls in ((33, path_anim.WALL), (22, path_anim.WALL), (0, set()), (40, path_anim.WALL | {(7, 0)})):
                O = 100                                       # clear of the u16 wrap of the rectangle's margin
                cells = [1 if path_anim.blocked((x, y), walls) else 0 for y in range(path_anim.GH) for x in range(path_anim.GW)]
                R = E.Room(0, (O, O, path_anim.GW, path_anim.GH), cells)
                R.near = [R]
                c = dict(room=0, troom=0, pattern=0, mask=1, s=(2 + O) | (4 + O) << 16, t=(13 + O) | (4 + O) << 16, type=0,
                         b1C=b1c, refresh=0, seed=None)
                o = E.Search(c, {0: R}, {}).run()
                m = path_anim.search(b1c=b1c, walls=walls)
                self.assertEqual(sum(p["tries"] for p in m["passes"]), o["visits"], b1c)
                self.assertEqual(len(m["passes"]), o["iters"], b1c)
                self.assertEqual(max(p["nodes"] for p in m["passes"]), o["nodes"], b1c)
                pts = [((x & 0xFFFF) - O, (x >> 16) - O) for x in o["points"]] if o["points"] else []
                self.assertEqual(m["points"], pts, b1c)
        finally:
            E.IMG = old

    def test_search_default_numbers_are_in_the_steps(self):
        r = path_anim.search()
        self.assertEqual(r["h0"], 22)
        self.assertEqual([p["bound"] for p in r["passes"]], [22, 27, 32])
        self.assertEqual(r["points"], [(3, 4), (7, 0), (11, 0), (13, 2), (13, 4)])
        self.assertEqual([p["end"] for p in r["passes"]], ["exhausted", "exhausted", "target"])
        out = TK.run("path_anim.py", ARGS["search"], "pa-s")
        txt = " ".join(texts(out))
        for p in r["passes"]:
            self.assertIn("tries = %d" % p["tries"], txt)
        self.assertIn("(3, 4), (7, 0), (11, 0), (13, 2), (13, 4)", txt)

    def test_walk_equals_formula_on_the_rng_step(self):
        d, log, pts = path_anim.walk_points(12, 0xC0FFEE)
        self.assertEqual(d, 0)
        lo, hi, cur = 0xC0FFEE, 666, (2, 4)
        want = []
        for k in range(6):
            lo, hi = rng.step(lo, hi)
            add = [-1, 0, 1][(lo & 31) % 3] if (lo & 31) < 30 else (-1 if (lo & 31) == 30 else 1)
            dr = (0 + add) & 7
            want.append(cur)
            cur = (cur[0] + 2 * path_anim.STEP8[dr][0], cur[1] + 2 * path_anim.STEP8[dr][1])
        want.append(cur)
        self.assertEqual(pts, want)
        out = TK.run("path_anim.py", ARGS["walk"], "pa-w")
        st = TK.steps(out)
        self.assertEqual(len(st), 1 + 6 + 1)
        for kk, (_k, lo, hi, add, dr, c) in enumerate(log):
            self.assertIn("low word %d" % lo, st[1 + kk]["calc"][0])
            self.assertIn("add[%d] = %d" % (lo & 31, add), st[1 + kk]["calc"][1])

    def test_walk_add_table_is_the_spec_one(self):
        self.assertEqual(path_anim.ADD_WALK, [-1, 0, 1] * 10 + [-1, 1])
        self.assertEqual(sum(1 for a in path_anim.ADD_WALK if a == 0), 10)       # a straight step: chance 10 / 32

    def test_spiral_takes_94_iterations_for_77_points(self):
        pts, iters = path_anim.spiral_points((8, 4))
        self.assertEqual((len(pts), iters), (77, 94))
        self.assertEqual(pts[0], (8, 5))
        pts2, it2 = path_anim.spiral_points((2, 4))
        self.assertEqual(it2, 94)
        out = TK.run("path_anim.py", ARGS["spiral"], "pa-sp")
        self.assertIn("iteration 94", " ".join(texts(out)))
        self.assertNotRegex(" ".join(texts(out)), r"sin\(\d+\)")             # a table index, not radians (review of lane/x12d)
        self.assertIn("sine at 208 of 512", " ".join(texts(out)))

    def test_no_label_uses_x_for_times_and_no_text_is_clipped_or_cut(self):
        with open(os.path.join(HERE, "path_anim.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", src), [])
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for mode in ("search", "walk", "spiral"):
            for theme in ("dark", "light"):
                path_anim.build(mode, 33, 12, 0xC0FFEE, theme)
        path_anim.build("search", 60, 12, 1, "dark")
        path_anim.build("walk", 33, 24, 0xFFFFFFFF, "light")
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_texts_name_no_tool_and_bad_arguments(self):
        for mode in ARGS:
            out = TK.run("path_anim.py", ARGS[mode], "pa-t-" + mode)
            for t in texts(out):
                self.assertNotRegex(t, r"\.py|tools/|workspace")
        self.assertEqual(path_anim.main([DATA, "--mode", "other"]), 2)
        self.assertEqual(path_anim.main([DATA, "--limit", "1"]), 2)
        self.assertEqual(path_anim.main([DATA, "--seed", "zz"]), 2)


class Move(unittest.TestCase):
    def test_deterministic_and_export_check(self):
        TK.same_both_themes(self, "move_anim.py", [], "mv")

    def test_steps_equal_the_model_and_the_worked_example(self):
        for name, v, frames, steps_ in (("walk", 1536, 8, [24576] * 8), ("run", 2304, 6, [36864] * 5 + [12288]),
                                        ("knockback", 4096, 3, [65536] * 3)):
            fr = move_anim.walk_frames(v, 3)
            self.assertEqual(len(fr), frames, name)
            self.assertEqual([f["step"] for f in fr], steps_, name)
            self.assertEqual(fr[-1]["x"], (3 << 16) + 0x8000)
            self.assertEqual(fr[-1]["i"], 1)
            # each frame is a call of the model on the state before it
            p = dict(f34=0x20, np=1, v=v, d=(4096, 0), pt=(3, 0), ty=0, x=0x8000, y=0x8000, i=0, pts=[(3, 0)])
            for f in fr:
                r = anim.step_model(p, [(((p["x"] + f["step"]) >> 16) | 0, 1)])
                self.assertEqual((r[0], r[2]), (f["x"], f["i"]))
                p.update(x=r[0], y=r[1], i=r[2])
            out = TK.run("move_anim.py", ["--speed", name], "mv-" + name)
            st = TK.steps(out)
            self.assertEqual(len(st), 1 + frames + 1)
            self.assertIn("ceil(%d / %d) = %d frames" % (65536 * 3, steps_[0], frames), " ".join(st[0]["calc"]))
            self.assertIn("the same call runs PathStop", " ".join(st[-1]["calc"]))   # movement B1: no later call (review of lane/x12d)

    def test_closed_form_for_other_distances_and_bad_arguments(self):
        for v in (1536, 2304, 4096, 1000):
            for d in (1, 2, 5):
                sx = (4096 * (anim.s32(v * 0x400) >> 6)) >> 12
                self.assertEqual(len(move_anim.walk_frames(v, d)), -(-(65536 * d) // sx))
        self.assertEqual(move_anim.main([DATA, "--speed", "0"]), 2)
        self.assertEqual(move_anim.main([DATA, "--dist", "9"]), 2)
        self.assertEqual(move_anim.main([DATA, "--speed", "5"]), 2)          # too many frames

    def test_no_text_clipped_or_cut_and_no_tool_named(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for v in (1536, 2304, 4096):
            for theme in ("dark", "light"):
                move_anim.build(v, 3, theme)
        move_anim.build(1536, 5, "dark")
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        out = TK.run("move_anim.py", [], "mv-t")
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        with open(os.path.join(HERE, "move_anim.py"), encoding="utf-8") as fh:
            self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", fh.read()), [])


@unittest.skipUnless(os.path.isdir(DATA), "no workspace/merged (game data)")
class Runeword(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sockets
        cls.sockets = sockets
        cls.T = sockets.Tables(os.path.join(DATA, "data", "global", "excel"))

    def test_deterministic_and_export_check(self):
        TK.same_both_themes(self, "runeword_anim.py", [], "rw")

    def test_match_equals_the_model(self):
        import runeword_anim as R
        T = self.T
        for base, runes, q, row in (("lrg", ["KO", "KO", "MAL"], 2, 41), ("lsd", ["TIR", "EL"], 2, 18),
                                    ("lrg", ["KO", "MAL", "KO"], 2, None), ("lrg", ["KO", "KO", "MAL"], 4, None),
                                    ("lsd", ["KO", "KO", "MAL"], 2, None), ("lrg", ["KO", "KO", "MAL"], 1, 41),
                                    ("lrg", ["KO", "KO", "MAL"], 3, 41)):
            cls = R.class_of(T, base)
            kids = [R.class_of(T, "r%02d" % (R.RUNES.index(r) + 1)) for r in runes]
            want, _why = self.sockets.match(T, cls, q, kids, len(kids), [0] * 6)
            self.assertEqual(want, row)
            got = R.build(T, base, runes, q, "dark")[3]
            self.assertEqual(got[0], want)

    def test_sanctuary_steps_and_scan_counts(self):
        import runeword_anim as R
        T = self.T
        out = TK.run("runeword_anim.py", [], "rw-s")
        st = TK.steps(out)
        self.assertEqual(len(st), 8)
        self.assertEqual([s["text"] for s in st[1:3]], ["Insert 1: 1 of 3 sockets filled, no match.",
                                                        "Insert 2: 2 of 3 sockets filled, no match."])
        ahead, ncomp = R.scan(T, [R.class_of(T, "r18"), R.class_of(T, "r18"), R.class_of(T, "r23")], 3, 41)
        self.assertEqual(sum(ahead.values()), sum(1 for i in range(41) if T.rune(i)["complete"]))
        self.assertNotIn("type", ahead)
        self.assertEqual(R.type_chain(T, R.class_of(T, "lrg"), 51)[-1], "SHLD")
        txt = " ".join(texts(out))
        self.assertIn("Record 41, Sanctuary", txt)
        self.assertIn("The scan skips 41 complete rows.", txt)
        self.assertEqual(R.rune_name(T, 627), "KO")
        self.assertEqual(R.rune_name(T, 632), "MAL")

    def test_no_text_clipped_or_cut_and_no_tool_named(self):
        import runeword_anim as R
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for base, runes, q in (("lrg", ["KO", "KO", "MAL"], 2), ("lrg", ["KO", "MAL", "KO"], 2), ("lrg", ["KO", "KO", "MAL"], 4),
                               ("lsd", ["TIR", "EL"], 2), ("lsd", ["KO", "KO", "MAL"], 2), ("lrg", ["EL"] * 6, 2)):
            for theme in ("dark", "light"):
                R.build(self.T, base, runes, q, theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        out = TK.run("runeword_anim.py", [], "rw-t")
        for t in texts(out):
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        self.assertEqual(R.main([DATA, "--runes", "ko,zz"]), 2)
        self.assertEqual(R.main([DATA, "--base", "zzz"]), 2)


if __name__ == "__main__":
    unittest.main()

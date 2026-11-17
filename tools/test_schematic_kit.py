"""Tests of the schematic kit and the generators built on it (plan 0070 Phase 11, batch 1: tools/schematic_kit.py,
tools/rng_anim.py, tools/seedtree_anim.py, and the new blocks of tools/tc_anim.py and tools/maze_anim.py).

Run: python3 -I tools/test_schematic_kit.py     (the tc and maze cases need workspace/merged: skipped without it)

The kit: both palettes have the same names in the same order, the dark one is the palette of the maze and drop
illustrations, and the text colours reach a contrast of 4.5 on the frame's ground in both themes. The generators: the
same arguments give the same bytes; every file carries the marker and schematic.json matches the files; the folder
passes the export check's illustration rules (tools/export_check.py verify_illustration); no art decoder is imported;
the numbers in the steps equal the model's (rng.py for the draws, drlg.py for the seed tree, with the seeds.md worked
example for seed 12345 as a fixed anchor). The tc players run: every scaled NoDrop in the steps equals tc.nodrop_scaled.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
OUT = os.path.join(ROOT, "workspace", "render", "test-kit")
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import drlg  # noqa: E402
import export_check  # noqa: E402
import rng  # noqa: E402
import rng_anim  # noqa: E402
import schematic_kit as K  # noqa: E402
import seedtree_anim  # noqa: E402

export_check.set_allow(export_check.load_allow(os.path.join(ROOT, "docs", "export", "allow-hex.txt")))
ART = ("dt1", "dc6", "item_art", "palette", "maze_render")


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


def lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Kit(unittest.TestCase):
    def test_palettes_same_names_same_order(self):
        self.assertEqual(list(K.DARK), list(K.LIGHT))
        self.assertEqual(K.palette("dark")[1], anim_common.schem_palette()[1])     # the maze and drop palette, unchanged
        self.assertNotEqual(K.palette("dark")[1], K.palette("light")[1])

    def test_text_colours_legible_on_the_ground(self):
        for theme, t in K.THEMES.items():
            for name in ("txt", "dim", "acc", "good", "bad", "blue"):
                for ground in ("bg", "panel"):
                    self.assertGreaterEqual(contrast(t[name], t[ground]), 4.5, "%s %s on %s" % (theme, name, ground))
            self.assertGreaterEqual(contrast(t["txt"], t["cur"]), 4.5, theme)

    def test_widgets_draw_inside_the_canvas(self):
        k = K.Kit(200, 120, "light")
        k.box(10, 10, 80, 30, ["AB", ("CD", "acc")])
        k.cellgrid(100, 10, 3, 2, 20, 20, {(0, 0): "1", (1, 1): ("2", "cur")})
        k.bar(10, 60, 100, 10, 1, 3)
        k.tape(10, 80, ["1", None, "3"], 30, 20, cur=0)
        k.legend(10, 108, [("good", "OK")])
        k.arrow(150, 60, 150, 100, "txt")
        k.arrow(120, 90, 180, 90, "txt")
        k.text(190, 110, "XY")                                       # clipped, no error
        self.assertEqual(len(k.cv), 200 * 120)
        self.assertEqual(k.cv[65 * 200 + 10 + 32], k.C["good"])       # the bar's third is exact: 1 * 100 // 3 = 33 columns
        self.assertEqual(k.cv[65 * 200 + 10 + 33], k.C["grey"])


class Rng(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = run("rng_anim.py", ["12345", "--count", "8", "--range", "100"], "rng-a")
        cls.b = run("rng_anim.py", ["12345", "--count", "8", "--range", "100"], "rng-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_numbers_equal_the_model(self):
        lo, hi = 12345, 666
        want = []
        for _ in range(8):
            r, lo, hi = rng.rng_range(lo, hi, 100)
            want.append((r, lo, hi))
        self.assertEqual(want[0], (87, 0x015B2E77, 0x0000141D))      # randomness page, worked example step 1
        self.assertEqual((want[1][1], want[1][2]), (0x8B57C5B0, 0x0090CE87))   # the example's step 4 state (draw 2 here)
        st = steps(self.a)
        self.assertEqual(len(st), 10)
        for i, (r, lo, hi) in enumerate(want):
            txt = " ".join(st[i + 1]["calc"])
            self.assertIn("seed = {%08x:%08x}" % (lo, hi), txt)
            self.assertIn("= %d." % r, st[i + 1]["calc"][3])
            self.assertIn("new low = its bits 0 to 31 = %d; new high = its bits 32 to 63 = %d." % (lo, hi), txt)
            self.assertIn("%d x %d + " % (12345 if i == 0 else want[i - 1][1], rng.MULT), txt)
        self.assertIn(", ".join(str(w[0]) for w in want), st[9]["calc"][0])

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("rng.gif", ok)

    def test_marker_and_list(self):
        with open(os.path.join(self.a, "schematic.json")) as fh:
            sj = json.load(fh)
        self.assertEqual(sj["marker"], anim_common.MARKER)
        self.assertEqual(sj["args"], ["12345", "--count", "8", "--range", "100"])
        self.assertEqual(sorted(list(sj["files"]) + ["schematic.json"]), sorted(os.listdir(self.a)))
        for n, sha in sj["files"].items():
            with open(os.path.join(self.a, n), "rb") as fh:
                data = fh.read()
            self.assertEqual(hashlib.sha256(data).hexdigest(), sha)
            self.assertIn(anim_common.MARKER.encode(), data, n)
        pal = K.palette("dark")[1]
        with open(os.path.join(self.a, "frame-001.png"), "rb") as fh:
            data = fh.read()
        self.assertEqual(data[data.index(b"PLTE") + 4:][:768], pal)

    def test_light_theme_and_bad_arguments(self):
        out = run("rng_anim.py", ["12345", "--theme", "light"], "rng-light")
        with open(os.path.join(out, "frame-001.png"), "rb") as fh:
            data = fh.read()
        self.assertEqual(data[data.index(b"PLTE") + 4:][:768], K.palette("light")[1])
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])
        self.assertEqual(rng_anim.main([DATA, "12345", "--range", "0"]), 2)
        self.assertEqual(rng_anim.main([DATA]), 2)


class SeedTree(unittest.TestCase):
    ARGS = ["12648430", "--act", "0", "--levels", "1,2,3", "--rooms", "3"]

    @classmethod
    def setUpClass(cls):
        cls.a = run("seedtree_anim.py", cls.ARGS, "st-a")
        cls.b = run("seedtree_anim.py", cls.ARGS, "st-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_spec_worked_example(self):
        """seeds.md worked example (logged in a recorded game, -seed 12345): the model's tree equals it."""
        T = seedtree_anim.trace(12345, 0, [1, 2, 3], 3)
        self.assertEqual(T["acts"][0]["base"], 0x015B2E77)
        self.assertEqual(T["acts"][1]["tombs"], (72, 71))
        self.assertEqual(T["acts"][1]["seed"], (0xB7A5C418, 0x63A93A78))
        self.assertEqual(T["levels"][0]["seed"], (0x015B2E78, 0x29A))
        self.assertEqual([r["level"][0] for r in T["rooms"]], [0xF61E44F2, 0xF3CFFCC1, 0x6B277FA8])
        self.assertEqual(T["rooms"][2]["room"], (0xF923BEE2, 0x2CB17800))
        self.assertEqual(T["rooms"][2]["r04"], 0xF923BEE2)

    def test_steps_equal_an_independent_walk(self):
        n = 12648430
        base = rng.step(n, rng.INIT_HIGH)[0]                      # step 3a, 3b with rng.py only
        low, high = n, rng.INIT_HIGH
        lo, hi = rng.step(low, high)
        st = steps(self.a)
        self.assertEqual(len(st), 1 + 5 + 1 + 3 + 1)
        self.assertIn("level seed base = its low word = %d." % base, " ".join(st[1]["calc"]))
        for i in range(5):
            b, alo, ahi, t94, t484, bit = rng.act_seeds(n, i)       # the rng model's own act seeds
            self.assertEqual(b, base)
            txt = " ".join(st[1 + i]["calc"])
            if i == 1:
                self.assertIn("tombs = %d and %d" % (t94, t484), txt)
                self.assertIn("{%08x:%08x}" % (alo, ahi), txt)
            if i == 2:
                self.assertIn("gate bit = low word and 1 = %d" % bit, txt)
        lv = st[6]["calc"]
        for j, lid in enumerate((1, 2, 3)):
            s = (base + lid) & rng.MASK
            self.assertIn("Level %d: Init(%d + %d) = Init(%d) = {%08x:%08x}" % (lid, base, lid, s, s, rng.INIT_HIGH), lv[1 + j])
        llo, lhi = (base + 1) & rng.MASK, rng.INIT_HIGH
        for r in range(3):
            llo, lhi = rng.step(llo, lhi)                           # one level draw
            rlo, rhi = rng.step(llo, rng.INIT_HIGH)                 # Init(room, level low), one step
            c = st[7 + r]["calc"]
            self.assertIn("{%08x:%08x}" % (llo, lhi), c[1])
            self.assertIn("room seed = {%08x:%08x}" % (rlo, rhi), c[2])
            self.assertIn("first value %d" % rlo, c[3])

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("seedtree.gif", ok)

    def test_options(self):
        out = run("seedtree_anim.py", ["12345", "--act", "1", "--levels", "66", "--rooms", "1", "--theme", "light"], "st-c")
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])
        self.assertEqual(seedtree_anim.main([DATA, "12345", "--rooms", "9"]), 2)
        self.assertEqual(seedtree_anim.main([DATA, "x"]), 2)


@unittest.skipUnless(os.path.isdir(DATA), "no workspace/merged (game data)")
class Blocks(unittest.TestCase):
    def test_tc_players_scaled_nodrop_equals_the_model(self):
        import tc
        out = run("tc_anim.py", ["andariel", "0xc0ffee", "--difficulty", "2", "--mf", "200", "--players", "8"], "tc8")
        again = run("tc_anim.py", ["andariel", "0xc0ffee", "--difficulty", "2", "--mf", "200", "--players", "8"], "tc8b")
        self.assertEqual(hashes(out), hashes(again))
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])
        seen = 0
        for s in steps(out):
            for c in s["calc"]:
                m = re.search(r"n = party \+ \(PlayerCount - party\) / 2 = (\d+); n > 1 so NoDrop is scaled .*: NoDrop (\d+), "
                              r"total (\d+) -> NoDrop' (\d+)\.", c)
                if m:
                    n, nd, tot, got = map(int, m.groups())
                    self.assertEqual(n, 4)                          # 1 + (8 - 1) / 2
                    self.assertEqual(tc.nodrop_scaled(nd, tot, n, 53), got)
                    seen += 1
        self.assertGreater(seen, 3)

    def test_maze_level_47_is_another_start_shape_and_theme_count(self):
        a = run("maze_anim.py", ["47", "0xc0ffee"], "mz47")
        b = run("maze_anim.py", ["47", "0xc0ffee"], "mz47b")
        c = run("maze_anim.py", ["36", "0xc0ffee"], "mz36")
        self.assertEqual(hashes(a), hashes(b))
        self.assertEqual(export_check.verify_illustration(a, identity=())[0], [])
        sa, sc = steps(a), steps(c)
        ring = lambda st: any("a ring of rooms is grown first" in x for s in st for x in s["calc"])
        self.assertTrue(ring(sa))
        self.assertFalse(ring(sc))
        themes = lambda st: sum("theme step sets" in s["text"] for s in st)
        rooms = lambda st: int(re.search(r"(\d+) rooms", st[-1]["text"]).group(1))
        for st in (sa, sc):
            self.assertEqual(themes(st), max(2, rooms(st) // 5 + 1))      # maze.md H1: want = max(2, count / 5 + 1)
        self.assertNotEqual(themes(sa), themes(sc))
        # maze.md H1 themes only rooms not locked, so a themed room's placement step must not say locked; a parent
        # whose Def a special's new room recomputes is not "set by the special" (review of lane/x11a)
        for st in (sa, sc):
            locked = {int(m.group(1)) for s in st for m in [re.match(r"Room (\d+) placed .*\(locked\)", s["text"])] if m}
            themed = {int(m.group(1)) for s in st for m in [re.match(r"Room (\d+): theme step", s["text"])] if m}
            self.assertTrue(locked)
            self.assertFalse(locked & themed, (locked, themed))
            self.assertTrue(any("so its Def is recomputed from its open sides" in s["text"] for s in st))
        self.assertEqual({int(m.group(1)) for s in sa for m in [re.match(r"Room (\d+) placed .*\(locked\)", s["text"])] if m},
                         {9, 12, 14})     # level 47: Prev E and the dock (maze.md F2 AddFixed) and the Next special's new room


# ---------------------------------------------------------------- batch 1 part 2: rows 5-8 (lane x11b)
def calc_text(out):
    return [c for s in steps(out) for c in s["calc"]]


def same_both_themes(case, tool, args, name):
    a, b = run(tool, args, name + "-a"), run(tool, args, name + "-b")
    case.assertEqual(hashes(a), hashes(b))
    case.assertEqual(export_check.verify_illustration(a, identity=())[0], [])
    lt = run(tool, args + ["--theme", "light"], name + "-light")
    case.assertEqual(export_check.verify_illustration(lt, identity=())[0], [])
    with open(os.path.join(lt, "frame-001.png"), "rb") as fh:
        data = fh.read()
    case.assertEqual(data[data.index(b"PLTE") + 4:][:768], K.palette("light")[1])
    return a


@unittest.skipUnless(os.path.isdir(DATA), "no workspace/merged (game data)")
class Quality(unittest.TestCase):
    ARGS = ["lsd", "28", "0xc0ffee", "--mf", "200"]

    def test_numbers_equal_the_model(self):
        import quality
        out = same_both_themes(self, "quality_anim.py", self.ARGS, "ql")
        T = quality.Tables(os.path.join(DATA, "data", "global", "excel"))
        codes = {bytes(r[0x80:0x84]).decode("latin-1").strip(): i for i, r in reversed(list(enumerate(T.items)))}
        tr = []
        code, seed_out, why, nd, ri = quality.roll(T, codes["lsd"], 28, [0, 0, 0, 0, 0, 0], (0xC0FFEE, 666), 200, trace=tr)
        st = steps(out)
        self.assertEqual(len(st), 2 + len(tr))
        for i, (name, c, x, won) in enumerate(tr):
            txt = " ".join(st[1 + i]["calc"])
            self.assertIn("draw RangeB(c = %d)" % c, txt)
            self.assertIn("x = new low mod %d = %d" % (c, x), txt)
            self.assertIn("x = %d %s 128" % (x, "<" if won else ">="), txt)
            self.assertIn(name, st[1 + i]["text"])
        self.assertIn("result code = %d" % code, st[-1]["calc"][0])
        self.assertIn("draws = %d" % nd, st[-1]["calc"][0])
        self.assertIn("{%08x:%08x}" % seed_out, st[-1]["calc"][1])
        self.assertEqual(code, 4)                                   # magic, after unique, set and rare are lost

    def test_magic_find_factor_is_the_models(self):
        import quality
        out = run("quality_anim.py", self.ARGS, "ql-f")
        txt = " ".join(calc_text(out))
        for k, name in ((250, "unique"), (500, "set"), (600, "rare")):
            self.assertIn("Diminish(300, %d) = %d" % (k, quality.diminish(300, k)), txt)
        self.assertIn("m100 = 300 (no diminishing) = 300", txt)

    def test_early_return_and_bad_arguments(self):
        import quality_anim
        self.assertEqual(quality_anim.main([DATA, "nosuch", "28", "1"]), 2)
        self.assertEqual(quality_anim.main([DATA, "lsd", "28", "1", "--ratio", "1,2,3"]), 2)
        self.assertEqual(quality_anim.main([DATA]), 2)


@unittest.skipUnless(os.path.isdir(DATA), "no workspace/merged (game data)")
class Special(unittest.TestCase):
    def test_unique_picks_equal_the_model(self):
        import monspecial
        out = same_both_themes(self, "special_anim.py", ["zombie1", "0xc0ffee", "--difficulty", "hell"], "sp")
        d = monspecial.Data(os.path.join(DATA, "data", "global", "excel"))
        mods = [0] * 9
        s = monspecial.Seed((0xC0FFEE, 666))
        o = d.mods_roll(s, mods, 2, 1, 5, 1)
        st = steps(out)
        self.assertFalse(o["champion"])
        self.assertEqual(len(st), 3 + len(o["picks"]) + 1)
        self.assertIn("Range(unit.seed, 100) = %d" % o["r100"], " ".join(st[1]["calc"]))
        for i, p in enumerate(o["picks"]):
            txt = " ".join(st[3 + i]["calc"])
            self.assertIn("total = %d; x = Range(unit.seed, %d) = %d; seed = {%08x:%08x}" % (
                p["total"], p["total"], p["x"], p["us"][0], p["us"][1]), txt)
            self.assertIn("%d candidates" % len(p["cands"]), st[3 + i]["text"])
            self.assertIn("row %d," % p["res"], txt)
        self.assertIn("steps of the unit seed = %d" % (2 + len(o["picks"])), " ".join(st[-1]["calc"]))
        self.assertIn("{%08x:%08x}" % s.t(), " ".join(st[-1]["calc"]))

    def test_champion_branch_and_no_weight_table(self):
        import monspecial
        out = run("special_anim.py", ["zombie1", "4", "--difficulty", "nightmare"], "sp-c")
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])
        st = steps(out)
        self.assertEqual(len(st), 4)                                 # inputs, champion draw, one pick, the list
        self.assertIn("champion (flag 0x04)", " ".join(st[1]["calc"]))
        # special.md D's per-mod table stays out of the export (Phase 9): a frame names the winner's weight, never a table
        for o in (out, run("special_anim.py", ["zombie1", "0xc0ffee", "--difficulty", "hell"], "sp-w")):
            for stp in steps(o):
                weights = [c for c in stp["calc"] if "weight" in c.lower()]
                self.assertLessEqual(len(weights), 2, stp["text"])
        d = monspecial.Data(os.path.join(DATA, "data", "global", "excel"))
        o = d.mods_roll(monspecial.Seed((4, 666)), [0] * 9, 1, 1, 5, 1)
        self.assertTrue(o["champion"])

    def test_bad_arguments(self):
        import special_anim
        self.assertEqual(special_anim.main([DATA, "nosuch", "4"]), 2)
        self.assertEqual(special_anim.main([DATA, "zombie1", "4", "--difficulty", "3"]), 2)


class Timing(unittest.TestCase):
    def test_worked_example_and_model(self):
        import anim
        import anim_rates
        out = same_both_themes(self, "timing_anim.py", [], "tm")
        st = steps(out)
        r = anim_rates.rate_cast(256, anim_rates.bonus(2, 20))
        self.assertEqual(r, 299)                                      # timing.md worked example 1: FCR 20 -> r = 299
        q = anim.schedule(0, 0, r, 14 << 8, lambda f: 1 if f == 7 else 0)
        self.assertEqual(q, [(0, 6, 1, 0), (1, 12, 0, 0)])             # the do at T + 6, the end at T + 12 (n = 12)
        self.assertIn("r = speed x X / 100 = 256 x 117 / 100 = 299", " ".join(st[0]["calc"]))
        self.assertEqual(len(st), 1 + 11 + 1)                          # N = 11 scan steps
        self.assertIn("UnitQueueEvent(kind 0, frame T + 6, a 1, b 0)", " ".join(st[6]["calc"]))
        self.assertIn("kind 1 at T + 12", " ".join(st[-1]["calc"]))
        for i in range(1, 12):
            self.assertIn("= %d < L = 3584" % (i * 299), " ".join(st[i]["calc"]))

    def test_other_rate_branch_and_bad_arguments(self):
        import anim
        import anim_rates
        out = run("timing_anim.py", ["--mode", "gethit", "--stat", "7", "--frames", "5", "--event", "2"], "tm-g")
        self.assertEqual(export_check.verify_illustration(out, identity=())[0], [])
        r = anim_rates.rate_gethit(256, anim_rates.bonus(1, 7))
        self.assertEqual(r, 143)                                       # worked example 2: FHR 7 -> r = 143, n = 9
        self.assertIn("kind 1 at T + 9", " ".join(calc_text(out)))
        self.assertEqual(anim.schedule(0, 0, r, 5 << 8, lambda f: 0)[-1], (1, 9, 0, 0))
        import timing_anim
        self.assertEqual(timing_anim.main([DATA, "--mode", "attack"]), 2)
        self.assertEqual(timing_anim.main([DATA, "--frames", "1"]), 2)


class Frame(unittest.TestCase):
    def test_pass_list_equals_the_spec_listing(self):
        import frame_anim
        with open(os.path.join(ROOT, "docs", "specs", "sim", "frame.md"), encoding="utf-8") as fh:
            spec = fh.read()
        b1 = spec[spec.index("B1. GameTick(game):"):spec.index("Rank 21 is everything")]
        d1 = spec[spec.index("D1. GameRunUnitEvents(game):"):spec.index("D2. Each runner")]
        ranks = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\s+(\d+)\s+(?:if [^:]*: )?(?:for [^:]*: if [^:]*: )?(\w+)", b1, re.M)}
        for rank, name, *_ in frame_anim.PASSES:
            self.assertEqual(ranks[rank], name, rank)
        self.assertEqual([p[0] for p in frame_anim.PASSES], [1, 2, 3, 14, 15, 16, 17, 18, 19, 20])
        d_ranks = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\s+(\d+)\s+(\w+)", d1, re.M)}
        for rank, runner, _ut, mode in frame_anim.WALKS:
            self.assertEqual(d_ranks[rank], runner, rank)
        self.assertEqual([w[0] for w in frame_anim.WALKS], list(range(4, 14)))
        self.assertEqual([w[3] for w in frame_anim.WALKS], [0, 1] * 5)          # every-frame walk, then the slot walk
        for p in re.findall(r"if frame % (\d+) = 0", b1):
            self.assertIn(int(p), [x[3] for x in frame_anim.PASSES])

    def test_outputs_and_periodic_passes(self):
        out = same_both_themes(self, "frame_anim.py", [], "fr")
        st = steps(out)
        self.assertEqual(len(st), 18)
        txt = " ".join(calc_text(out))
        self.assertIn("1320 % 20 = 0", txt)
        self.assertIn("curSlot = game.frame % 64 = 1320 % 64 = 40", txt)
        sk = run("frame_anim.py", ["--frame", "1321"], "fr-s")
        t2 = " ".join(calc_text(sk))
        self.assertNotIn("1321 % 20 = 0", t2)
        self.assertIn("runs when frame % 12 = 0 (1321 % 12 = 1)", t2)
        self.assertTrue(any("skipped at counter 1321" in s["text"] for s in steps(sk)))
        import frame_anim
        self.assertEqual(frame_anim.main([DATA, "--frame", "0"]), 2)


class Captions(unittest.TestCase):
    def test_no_caption_is_cut(self):
        import frame_anim
        import quality_anim
        import special_anim
        import timing_anim
        K.CAPTION_CUT.clear()
        frame_anim.build(1320, "dark")
        frame_anim.build(1321, "light")
        timing_anim.build("cast", 20, 14, 256, 0, 7, "dark")
        timing_anim.build("gethit", 0, 5, 256, 0, 2, "light")
        if os.path.isdir(DATA):
            import quality
            T = quality.Tables(os.path.join(DATA, "data", "global", "excel"))
            quality_anim.build(T, quality_anim.code_index(T), "lsd", 28, [0, 0, 0, 0], 0xC0FFEE, 200, "dark")
            for diff, seed in ((2, 0xC0FFEE), (1, 4), (0, 4)):
                special_anim.build(DATA, "zombie1", diff, 1, seed, "dark")
        self.assertEqual(K.CAPTION_CUT, [])


if __name__ == "__main__":
    unittest.main()

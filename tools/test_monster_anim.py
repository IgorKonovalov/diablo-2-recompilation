"""Tests of the monster schematic animations (plan 0070 Phase 11, batch 2): tools/pack_anim.py (a normal group placed on
a toy room, row 9) and tools/pool_anim.py (the region seed and one level's pool pick by pick, row 10), and of the
two position rules they share with the log checker (tools/spawn_place.py).

Run: python3 -I tools/test_monster_anim.py     (the tool cases need workspace/merged: skipped without it)

Each tool: the same arguments give the same bytes, in both themes; the folder passes the export check's illustration
rules (with the allow-hex list); no art decoder is imported; no text line runs past the canvas and no caption is cut; no
tool, module or path name is in a step text. The numbers: the ring walk reproduces the member walks of the spawn
specification's worked example (cells, refusals, seeds); the group size, the leader's tries and the members equal a
second run of the model; the pool equals tools/monpool.py's build for every level of several seeds and the
specification's worked example (seed 1, levels 1 to 3).
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
OUT = os.path.join(ROOT, "workspace", "render", "test-monster-anim")
sys.path.insert(0, HERE)
import export_check  # noqa: E402
import pack_anim  # noqa: E402
import pool_anim  # noqa: E402
import schematic_kit as K  # noqa: E402
import spawn_place  # noqa: E402

export_check.set_allow(export_check.load_allow(os.path.join(ROOT, "docs", "export", "allow-hex.txt")))
ART = ("dt1", "dc6", "item_art", "palette", "maze_render")
HAVE = os.path.isdir(DATA)
NAMES = (".py", "tools/", "spawn_place", "monpool", "monspawn", "collision.py", "ring_search", "near_point", "pack_anim",
         "pool_anim", "build_all", "build_pool", "python", "workspace")


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


def texts(out):
    st = steps(out)
    return [s["text"] for s in st] + [c for s in st for c in s["calc"]]


class Shared(unittest.TestCase):
    """The functions the log checker and the animation both call (tools/spawn_place.py)."""

    def test_the_checker_calls_the_same_functions(self):
        import collision
        import monspawn
        self.assertIs(monspawn.ring_search, spawn_place.ring_search)
        self.assertIs(monspawn.S, spawn_place.S)
        self.assertIs(monspawn.MASK_BY_SPAWNCOL, spawn_place.MASK_BY_SPAWNCOL)
        self.assertIs(collision.near_point, spawn_place.near_point)

    def test_ring_walk_equals_the_spec_worked_example(self):
        # spawn.md Worked example (Dark Wood, hell): the leader stands at (15557, 5612), the box is the tile rectangle
        # (3104, 1122)-(3112, 1130), i.e. x in [15520, 15560), y in [5610, 5650). Member 1 starts from the room seed
        # 8ED5D56C:09A88AA0 and tests (15559, 5615) collision 39, (15560, 5615) outside, (15559, 5615) again 39,
        # (15558, 5615) 0: created; the room seed after is 7F5E6B22:2560059C.
        def inside(x, y):
            return 15520 <= x < 15560 and 5610 <= y < 5650
        marks = {}
        tested = []

        def accept(x, y):
            if not inside(x, y):
                tested.append((x, y, "out"))
                return False
            v = marks.get((x, y), 0)
            tested.append((x, y, v))
            return v == 0
        marks[(15559, 5615)] = 39
        rs = spawn_place.S((0x8ED5D56C, 0x09A88AA0))
        got = spawn_place.ring_search(rs, 15557, 5612, 3, accept)
        self.assertEqual(got, (15558, 5615))
        self.assertEqual(tested, [(15559, 5615, 39), (15560, 5615, "out"), (15559, 5615, 39), (15558, 5615, 0)])
        self.assertEqual(rs.t(), (0x7F5E6B22, 0x2560059C))
        # member 2: starts above the box at (15555, 5609); member 1 stands at (15558, 5615), the cells read 4135, 4096,
        # 4096 and 0 at 15559, 15558, 15557, 15556; the room seed after is EB2F2AF7:5D62BD2A
        marks = {(15559, 5615): 4135, (15558, 5615): 4096, (15557, 5615): 4096}
        tested.clear()
        got = spawn_place.ring_search(rs, 15557, 5612, 3, accept)
        self.assertEqual(got, (15556, 5615))
        self.assertEqual([t for t in tested if t[2] != "out"],
                         [(15559, 5615, 4135), (15558, 5615, 4096), (15557, 5615, 4096), (15556, 5615, 0)])
        self.assertEqual(rs.t(), (0xEB2F2AF7, 0x5D62BD2A))
        # the group size of that example: k = 0 + Range(leader seed, 3) = 2, leader seed D496D6A5:212B878A -> E7998483:58AB59C2
        us = spawn_place.S((0xD496D6A5, 0x212B878A))
        self.assertEqual(us.rangeb(3), 2)
        self.assertEqual(us.t(), (0xE7998483, 0x58AB59C2))

    def test_an_exact_placement_makes_three_draws(self):
        rs = spawn_place.S((1, 666))
        n = []
        orig = rs.step
        rs.step = lambda: (n.append(1), orig())[1]
        self.assertEqual(spawn_place.ring_search(rs, 10, 10, -1, lambda x, y: True), (10, 10))
        self.assertEqual(len(n), 3)

    def test_near_point_is_a_strict_squared_distance(self):
        self.assertTrue(spawn_place.near_point([0], [0], 100, 6, 8) is False)
        self.assertTrue(spawn_place.near_point([0], [0], 101, 6, 8))
        self.assertFalse(spawn_place.near_point([], [], 100, 0, 0))


@unittest.skipUnless(HAVE, "needs workspace/merged")
class Pack(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = run("pack_anim.py", [], "p-a")
        cls.b = run("pack_anim.py", [], "p-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("pack.gif", ok)

    def test_both_themes_and_a_second_seed(self):
        for name, args in (("p-light", ["--theme", "light"]), ("p-seed", ["--seed", "12345"]),
                           ("p-cls", ["mummy4", "--seed", "7", "--theme", "light"])):
            out = run("pack_anim.py", args, name)
            self.assertEqual(export_check.verify_illustration(out, identity=())[0], [], name)

    def test_no_tool_names_in_step_texts(self):
        for out in (self.a,):
            for t in texts(out):
                for n in NAMES:
                    self.assertNotIn(n, t, t)

    def test_the_numbers_equal_a_second_run_of_the_model(self):
        for seed in (0xC0FFEE, 12345, 7):
            ci = pack_anim.class_info(DATA, "swarm1")
            toy = pack_anim.Toy(spawn_place.MASK_BY_SPAWNCOL[0], 2)
            rs, us = pack_anim.Counting((seed, 666)), pack_anim.Counting((seed, 666))
            rec = pack_anim.place(toy, rs, us, ci["mn"], ci["mx"])
            frames, caps, _pal, rec2 = pack_anim.build(DATA, "swarm1", seed, "dark")
            self.assertEqual(rec["leader"], rec2["leader"])
            self.assertEqual([m["found"] for m in rec["members"]], [m["found"] for m in rec2["members"]])
            self.assertEqual(rec["k"], (ci["mn"] - 1) + rec["r"])
            self.assertTrue(ci["mn"] - 1 <= rec["k"] <= ci["mx"] - 1)
            # the group size is the next draw of the leader's own seed
            s = spawn_place.S((seed, 666))
            self.assertEqual(rec["r"], s.rangeb(ci["mx"] - ci["mn"] + 1))
            # every refused try is either near the warp point or has a probe that found nothing; the taken one is the
            # last, with the 20-try limit
            last = rec["tries"][-1]
            self.assertEqual(last["probe"], rec["leader"])
            self.assertLessEqual(len(rec["tries"]), 20)
            for t in rec["tries"][:-1]:
                self.assertTrue(t["near"] or not t["probe"])
                self.assertEqual(t["near"], t["d2"] < pack_anim.WARP_DIST)
            # no member stands on a blocked cell, on the leader, on another member, or outside the box
            stood = {rec["leader"]}
            for m in rec["members"]:
                if m["found"]:
                    self.assertNotIn(m["found"], stood)
                    self.assertTrue(pack_anim.BOX[0] <= m["found"][0] < pack_anim.BOX[2]
                                    and pack_anim.BOX[1] <= m["found"][1] < pack_anim.BOX[3])
                    self.assertEqual(m["cells"][-1][2], "ok")
                    stood.add(m["found"])
                else:
                    self.assertTrue(all(c[2] != "ok" for c in m["cells"]))
                self.assertTrue(all(c[2] != "ok" for c in m["cells"][:-1]))
            # room draws: 2 a try, 3 more for each probe, 3 for the exact placement, the members' rings
            self.assertEqual(rs.n, sum(2 + (0 if t["near"] else 3) for t in rec["tries"]) + 3
                             + sum(m["draws"] for m in rec["members"]))

    def test_the_toy_follows_the_collision_rules(self):
        toy = pack_anim.Toy(0x3C01, 2)
        x, y = pack_anim.GX + 24, pack_anim.GY + 8          # a wall cell
        self.assertNotEqual(toy.test(x, y), 0)
        self.assertNotEqual(toy.test(x, y + 1), 0)          # the plus reaches the wall (size 2)
        self.assertEqual(toy.test(x, y + 2), 0)
        toy.mark(x, y + 5)
        self.assertNotEqual(toy.test(x + 1, y + 5), 0)      # a created monster's centre blocks its neighbours' plus
        self.assertEqual(toy.test(x + 2, y + 5), 0)
        self.assertEqual(toy.cell(0, 0), 0x27)              # a cell in no room adds 0x27

    def test_no_clipped_text_and_no_cut_caption(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for seed in (0xC0FFEE, 12345, 7):
            for th in ("dark", "light"):
                pack_anim.build(DATA, "swarm1", seed, th)
        pack_anim.build(DATA, "mummy4", 0xC0FFEE, "dark")
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_bad_arguments(self):
        self.assertEqual(pack_anim.main([DATA, "nosuchclass"]), 2)
        self.assertEqual(pack_anim.main([DATA, "brute1"]), 2)           # a footprint of 3
        self.assertEqual(pack_anim.main([DATA, "--seed", "0"]), 2)
        self.assertEqual(pack_anim.main([DATA, "--theme", "blue"]), 2)
        self.assertEqual(pack_anim.main([]), 2)


@unittest.skipUnless(HAVE, "needs workspace/merged")
class Pool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ARGS = ["0xC0FFEE"]
        cls.a = run("pool_anim.py", cls.ARGS, "q-a")
        cls.b = run("pool_anim.py", cls.ARGS, "q-b")

    def test_deterministic(self):
        self.assertEqual(hashes(self.a), hashes(self.b))

    def test_folder_passes_the_export_check(self):
        probs, ok = export_check.verify_illustration(self.a, identity=())
        self.assertEqual(probs, [])
        self.assertIn("pool.gif", ok)

    def test_both_themes_and_other_levels(self):
        for name, args in (("q-light", ["0xC0FFEE", "--theme", "light"]),
                           ("q-hell", ["12345", "--level", "40", "--difficulty", "hell"]),
                           ("q-rng", ["0xC0FFEE", "--level", "110", "--theme", "light"]),
                           ("q-2", ["1", "--level", "2"])):
            out = run("pool_anim.py", args, name)
            self.assertEqual(export_check.verify_illustration(out, identity=())[0], [], name)

    def test_no_tool_names_in_step_texts(self):
        for out in (self.a,):
            for t in texts(out):
                for n in NAMES:
                    self.assertNotIn(n, t, t)

    def test_the_pool_equals_the_models_build_for_every_level(self):
        import monpool
        t = monpool.Tables(os.path.join(DATA, "data", "global", "excel"))
        for seed, diff in ((0xC0FFEE, 0), (1, 0), (12345, 2)):
            low = monpool.first_draw_low(seed, 1).low
            want = {lid: (reg, s) for lid, reg, s in monpool.build_all(t, low, diff, 1)}
            for lid in (2, 3, 29, 110):
                tr = pool_anim.trace(t, seed, diff, lid)
                self.assertEqual(tr["reg"], want[lid][0])
                self.assertEqual(tr["per"][-1]["seed"], tuple(int(x, 16) for x in want[lid][1].split(":")))
                self.assertEqual(tr["game"], (low, monpool.first_draw_low(seed, 1).high))
                self.assertEqual(tr["region"], (low, 666))
                kept = [p["c"] for p in tr["picks"] if p["kept"]]
                self.assertEqual(kept, [e[0] for e in want[lid][0]["ents"]])

    def test_the_spec_worked_example(self):
        # pool.md Worked example: -seed 1, normal: the game seed after its draw 6ac6935f:00000000, the region seed
        # 6ac6935f:0000029a; level 1 no draw; level 2 pool [5, 19, 63], seed after d52ffc3b:270b4ee5 (26 draws);
        # level 3 pool [28, 58, 165], seed after 679fafd2:63e02d41 (picks 0, 1, 1 of 4, 3, 2 candidates)
        import monpool
        t = monpool.Tables(os.path.join(DATA, "data", "global", "excel"))
        tr = pool_anim.trace(t, 1, 0, 3)
        self.assertEqual(tr["game"], (0x6AC6935F, 0))
        self.assertEqual(tr["region"], (0x6AC6935F, 0x29A))
        self.assertEqual(tr["per"][0]["draws"], 0)
        self.assertEqual(tr["per"][0]["seed"], (0x6AC6935F, 0x29A))
        self.assertEqual(tr["per"][1]["seed"], (0xD52FFC3B, 0x270B4EE5))
        self.assertEqual(tr["per"][1]["draws"], 26)
        self.assertEqual(tr["per"][2]["seed"], (0x679FAFD2, 0x63E02D41))
        self.assertEqual([(p["count"], p["i"], p["c"]) for p in tr["picks"]], [(4, 0, 28), (3, 1, 58), (2, 1, 165)])
        self.assertEqual(tr["npick"], 3)
        self.assertEqual(tr["varsdraws"], 17)                      # cr_lancer1's appearance sets (pool D worked example)
        self.assertEqual([e[0] for e in tr["reg"]["ents"]], [28, 58, 165])
        self.assertEqual(tr["reg"]["rsum"], 4)

    def test_the_ranged_rule_shows_every_redraw(self):
        import monpool
        t = monpool.Tables(os.path.join(DATA, "data", "global", "excel"))
        tr = pool_anim.trace(t, 0xC0FFEE, 0, 110)
        first = tr["picks"][0]
        self.assertGreater(len(first["draws"]), 1)
        self.assertTrue(t.ranged(first["c"]) or len(first["draws"]) == 21)
        self.assertEqual(len(tr["picks"][1]["draws"]), 1)
        frames, caps, _p, _t = pool_anim.build(DATA, 0xC0FFEE, 110, 0, "dark")
        self.assertTrue(any("C6: %d draws" % len(first["draws"]) in " ".join(c["calc"]) for c in caps))

    def test_no_clipped_text_and_no_cut_caption(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for lid in (2, 3, 5, 29, 60, 110, 136):
            for diff in (0, 2):
                for th in ("dark", "light"):
                    pool_anim.build(DATA, 0xC0FFEE, lid, diff, th)
        self.assertEqual(K.TEXT_CLIPPED, [])
        self.assertEqual(K.CAPTION_CUT, [])

    def test_bad_arguments(self):
        self.assertEqual(pool_anim.main([DATA]), 2)
        self.assertEqual(pool_anim.main([DATA, "x"]), 2)
        self.assertEqual(pool_anim.main([DATA, "5", "--level", "1"]), 2)
        self.assertEqual(pool_anim.main([DATA, "5", "--level", "137"]), 2)
        self.assertEqual(pool_anim.main([DATA, "5", "--difficulty", "easy"]), 2)
        self.assertEqual(pool_anim.main([DATA, "5", "--theme", "blue"]), 2)
        self.assertEqual(pool_anim.main([DATA, "0"]), 2)


if __name__ == "__main__":
    unittest.main()

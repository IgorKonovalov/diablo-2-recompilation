"""Tests of the batch 4 schematic generators (plan 0070 Phase 11, lane x17b): tools/quest_anim.py (a quest word's bits as
events arrive), tools/cube_anim.py (one cube transmute: the scan, the inputs, the output and every draw) and
tools/collision_anim.py (the four spawn tests on a toy room's subtiles), and the model entry points they added
(tools/quests.py rec_load, rec_apply, talk_writes; tools/cube.py vector_data, match_input's claims; tools/collision.py
World.logic_id, World.class_cell_base, near_waypoint).

Run: python3 -I tools/test_quest_cube_collision_anim.py     (the cube and collision cases need workspace/merged and
workspace/logs: skipped without them)

Each generator: the same arguments give the same bytes, both themes pass the export check's illustration rules, no art
decoder is imported, no text runs past the canvas, no caption is cut, no step text names a tool or a path, and no step text
holds a hex number of six digits or more. The numbers equal the model: the quest words equal the worked example's (word 1 =
0x0002 -> 0x8002 -> 0x8003 -> 0x8001; word 41 -> 0x2000 -> 0x2002, saved, then 0x8002); the cube's draws equal
`cube.py vector` on the same transmute; the collision tests equal the model's functions on the toy grid.
"""
import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
sys.path.insert(0, HERE)
import collision  # noqa: E402
import collision_anim  # noqa: E402
import quest_anim  # noqa: E402
import quests  # noqa: E402
import schematic_kit as K  # noqa: E402
import test_schematic_kit as TK  # noqa: E402

HAVE_DATA = os.path.isdir(DATA) and os.path.isdir(os.path.join(ROOT, "workspace", "logs"))


def texts(out):
    return [s["text"] for s in TK.steps(out)] + TK.calc_text(out)


def clean(case, out):
    for t in texts(out):
        case.assertNotRegex(t, r"\.py|tools/|workspace")
        case.assertNotRegex(t, r"\b(?=[0-9a-fA-F]*[a-fA-F])[0-9a-fA-F]{6,}\b|0x[0-9a-fA-F]{6,}")


class QuestModel(unittest.TestCase):
    def test_loader_rule(self):
        self.assertEqual(quests.rec_load(0x0002), 0x8002)
        self.assertEqual(quests.rec_load(0x6002), 0x8002)          # bits 13 and 14 cleared, bit 15 from bit 1
        self.assertEqual(quests.rec_load(0x2000), 0x0000)
        self.assertEqual(quests.rec_load(0x0001), 0x0001)
        self.assertEqual(quests.rec_load(0x8001), 0x8001)          # bit 15 already in the file stays

    def test_record_writes(self):
        self.assertEqual(quests.rec_apply(0, "QS", 13), 0x2000)
        self.assertEqual(quests.rec_apply(0x8003, "QC", 1), 0x8001)
        self.assertEqual(quests.rec_apply(0xFFFF, "QK"), 0xF003)   # bits 2..11
        self.assertEqual(quests.STEP_MASK, 0x0FFC)

    def test_reward_message_writes_in_call_order(self):
        rec = [0] * 48
        rec[1] = 0x8002
        w = quests.talk_writes(rec, 148, 0x4C)
        self.assertEqual([(a, b, c) for a, b, c, _ in w],
                         [(1, "QS", 0), (1, "QC", 1), (41, "QS", 13), (41, "QS", 1), (1, "QK", None)])
        self.assertEqual([x[3] for x in w], sorted(x[3] for x in w))
        rec[1] = 0x8001                                            # bit 1 clear: the message writes nothing
        self.assertEqual(quests.talk_writes(rec, 148, 0x4C), [])
        self.assertEqual(quests.talk_writes([0] * 48, 148, 0x4D), [])


class Quest(unittest.TestCase):
    def test_deterministic_and_export_check(self):
        out = TK.same_both_themes(self, "quest_anim.py", [], "qa")
        self.assertEqual(len(TK.steps(out)), 9)

    def test_words_equal_the_worked_example(self):
        steps = quest_anim.model()
        self.assertEqual([(s["words"][1], s["words"][41]) for s in steps],
                         [(0x0002, 0), (0x8002, 0), (0x8003, 0), (0x8001, 0), (0x8001, 0x2000), (0x8001, 0x2002),
                          (0x8001, 0x2002), (0x8001, 0x2002), (0x8001, 0x8002)])
        self.assertEqual(steps[3]["ch"], {(1, 1)})
        self.assertEqual(steps[1]["ch"], {(1, 15)})
        self.assertEqual(steps[6]["ch"], set())                    # ClearSteps with no step bit set changes nothing
        self.assertEqual(steps[8]["ch"], {(41, 13), (41, 15)})

    def test_text(self):
        out = TK.run("quest_anim.py", [], "qa-t")
        clean(self, out)
        txt = " ".join(texts(out))
        for w in ("0x8002", "0x8003", "0x8001", "0x2000", "0x2002"):
            self.assertIn(w, txt)
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for th in ("dark", "light"):
            quest_anim.build(th)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(quest_anim.main([DATA, "--theme", "x"]), 2)


class CollisionModel(unittest.TestCase):
    def test_logic_id_g4(self):
        self.assertEqual(collision.World.logic_id({"fl": 1, "first": 7}, 0, 0), 7)
        self.assertEqual(collision.World.logic_id({"fl": 1, "first": None}, 0, 0), -1)
        lg = {"fl": 2, "t": (20, 10), "grid": (None, None, [[1, 2], [None, 3]])}
        self.assertEqual(collision.World.logic_id(lg, 100, 50), 1)
        self.assertEqual(collision.World.logic_id(lg, 105, 50), 2)
        self.assertEqual(collision.World.logic_id(lg, 100, 55), -1)
        self.assertEqual(collision.World.logic_id(lg, 109, 59), 3)

    def test_near_waypoint_i1(self):
        self.assertFalse(collision.near_waypoint(0, 5, 100, 0, 25))     # a point with x or y not above 0 is none
        self.assertFalse(collision.near_waypoint(5, -1, 100, 25, -5))
        self.assertTrue(collision.near_waypoint(2, 2, 100, 10, 10))      # distance 0
        self.assertTrue(collision.near_waypoint(2, 2, 100, 19, 10))      # 81 < 100
        self.assertFalse(collision.near_waypoint(2, 2, 100, 20, 10))     # 100 is not below 100

    def test_class_cell_h1_and_the_log_path_agree(self):
        cells = [0] * (40 * 30)
        cells[19 * 40 + 9] = 0x0001
        w = collision.World.one_room(1, 100, 50, 40, 30, cells)
        self.assertEqual(w.class_cell_base(298, 1, 107, 65, 1), 1)         # 298 passes with flag 1
        self.assertEqual(w.class_cell_base(1, 1, 107, 65, 0), 1)           # a BaseId not in the table passes
        self.assertEqual(w.class_cell_base(528, 1, 107, 65, 1), 0)         # (x+2, y+4) is the block
        self.assertEqual(w.class_cell_base(528, 1, 117, 65, 1), 1)
        self.assertEqual(w.class_cell_base(528, 1, 139, 79, 1), 0)         # the offset cell is outside the room: false

        class T:
            def valid(self, cls):
                return True

            def m(self, cls, off, fmt):
                return cls
        w.t = T()
        w.hit = lambda *a, **k: None
        for b in (206, 228, 298, 334, 528, 1):
            for x, y in ((107, 65), (117, 65), (125, 70), (139, 79)):
                for flag in (0, 1):
                    self.assertEqual(w.spawn_class_cell_test(b, 1, x, y, flag), w.class_cell_base(b, 1, x, y, flag), (b, x, y, flag))


class Collision(unittest.TestCase):
    def test_deterministic_and_export_check(self):
        out = TK.same_both_themes(self, "collision_anim.py", [], "ca")
        self.assertEqual(len(TK.steps(out)), 9)

    def test_each_point_stops_at_its_test(self):
        want = ["NEARWARPTEST", "NEARWARPTEST", "LOGICREGIONIDAT", "SPAWNCLASSCELLTEST", "COLLISIONTEST", "COLLISIONTEST", None]
        toy = collision_anim.Toy(528)
        got = []
        for x, y, _note in collision_anim.POINTS:
            res = toy.tests(collision_anim.GX + x, collision_anim.GY + y)
            ff = next((r[0] for r in res if r[1] and not r[2]), None)
            got.append(ff)
            self.assertEqual([r[1] for r in res], [True] * (1 + next((i for i, r in enumerate(res) if r[1] and not r[2]), 3)) +
                             [False] * (3 - next((i for i, r in enumerate(res) if r[1] and not r[2]), 3)))
        self.assertEqual(got, want)

    def test_tests_equal_the_model_on_the_toy_grid(self):
        toy = collision_anim.Toy(528)
        G = collision_anim
        for x, y, _n in G.POINTS:
            ax, ay = G.GX + x, G.GY + y
            res = {r[0]: r for r in toy.tests(ax, ay)}
            if res["COLLISIONTEST"][1]:
                v = toy.world.collision_test(G.ROOM, ax, ay, G.SIZE, G.MASK)
                self.assertEqual(res["COLLISIONTEST"][2], v == 0)
            if res["SPAWNCLASSCELLTEST"][1]:
                self.assertEqual(res["SPAWNCLASSCELLTEST"][2], bool(toy.world.class_cell_base(528, G.ROOM, ax, ay, 1)))
            if res["LOGICREGIONIDAT"][1]:
                self.assertEqual(res["LOGICREGIONIDAT"][2], toy.world.logic_id(toy.lg, ax, ay) == G.BOX_ID)
        # the plus footprint: the centre is clear and the right arm is the wall at x = 24
        self.assertEqual(toy.world.collision_test(G.ROOM, G.GX + 23, G.GY + 22, 2, G.MASK), 1)
        self.assertEqual(toy.world.cell_test(G.ROOM, G.GX + 23, G.GY + 22, 0xFFFF), 0)

    def test_every_class_builds_and_no_text_is_clipped_or_cut(self):
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for base in (528, 206, 228, 298, 334, 1):
            for th in ("dark", "light"):
                collision_anim.build(base, th)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        out = TK.run("collision_anim.py", [], "ca-t")
        clean(self, out)
        self.assertEqual(collision_anim.main([DATA, "--base", "x"]), 2)
        a = TK.run("collision_anim.py", ["--base", "206"], "ca-206")
        self.assertEqual(len(TK.steps(a)), 9)


@unittest.skipUnless(HAVE_DATA, "no workspace/merged or workspace/logs (game data)")
class Cube(unittest.TestCase):
    ARGS = ["--run", "kinds2", "--n", "4"]

    @classmethod
    def setUpClass(cls):
        import cube
        import cube_anim
        cls.cube, cls.ca = cube, cube_anim
        cls.excel = os.path.join(DATA, "data", "global", "excel")
        cls.D = cube.vector_data(cls.excel, cube_anim.find_log("kinds2"), 4)

    def test_deterministic_and_export_check(self):
        out = TK.same_both_themes(self, "cube_anim.py", self.ARGS, "cu")
        self.assertEqual(len(TK.steps(out)), 4 + 8 + 1)

    def test_scan_inputs_output_equal_the_model(self):
        F = self.ca.facts(self.D)
        self.assertEqual((F["row"], F["reached"], F["ilvl"]), (19, [1, 15, 16, 17, 19], 50))
        self.assertEqual([i["claims"] for i in F["ins"]], [[1], [2], [3], [4]])
        self.assertEqual(F["reasons"], {"numinputs": 15})
        T = self.D["T"]
        self.assertEqual([self.ca.code(T, it["cls"]) for it in self.D["c"]["items"]], ["KRI", "GPW", "SST", "LBL"])
        self.assertEqual([i["ask"] for i in F["ins"]], ["KRI", "TYPE GEMD", "TYPE STAF", "TYPE BELT"])
        # a claim list of match_input equals what it returns for the first input
        items = self.D["c"]["items"]
        claims = []
        self.assertTrue(self.cube.match_input(T, T.rows[19], 0, items, [False] * 48, [[0, 0, 0] for _ in range(3)], self.D["c"], claims))
        self.assertEqual(claims, [1])

    def test_draws_equal_the_vector_output(self):
        buf = io.StringIO()
        ns = type("NS", (), dict(excel=self.excel, log=self.ca.find_log("kinds2"), n=4))
        with redirect_stdout(buf):
            self.assertEqual(self.cube.cmd_vector(ns), 0)
        printed = [ln for ln in buf.getvalue().splitlines() if re.match(r"^\d+\s+(game|unit|item)\s", ln)]
        draws = [e for e in self.D["seq"] if e[0] == "draw"]
        self.assertEqual(len(printed), len(draws))
        self.assertEqual(len(draws), 8)
        out = TK.run("cube_anim.py", self.ARGS, "cu-n")
        st = TK.steps(out)
        for i, e in enumerate(draws):
            _, n, seed, bf, af, what, rg, r = e
            self.assertIn("%s seed after the step: low word %d, high word %d" % (seed, af[0], af[1]), st[4 + i]["calc"][0])
            self.assertTrue(printed[i].split()[1] == seed)
        self.assertEqual([(e[2], e[6], e[7]) for e in draws[:2]], [("game", "n 659", "192"), ("game", "n 10", "2")])
        self.assertIn("result 192", st[4]["text"])
        self.assertIn("result 2", st[5]["text"])
        self.assertEqual(self.D["final"][0]["p"][0], 938)
        # review of lane/x17b: the two roll tests name their side, and the forced prefix's must-roll
        self.assertIn("prefix pick: roll test, must roll", st[9]["text"])
        self.assertIn("suffix pick: roll test, low & 1, result 0 -> no affix", st[11]["text"])
        txt = " ".join(texts(out))
        self.assertIn("SCY q4 ilvl 50", txt)
        clean(self, out)

    def test_vector_prints_the_draws_before_a_refusal(self):
        # review of lane/x17b: before vector_data, `vector` printed the draws up to a refusal; it still does
        buf = io.StringIO()
        ns = type("NS", (), dict(excel=self.excel, log=self.ca.find_log("cowopen"), n=5))
        with redirect_stdout(buf), self.assertRaises(self.cube.Mismatch):
            self.cube.cmd_vector(ns)
        printed = [ln for ln in buf.getvalue().splitlines() if re.match(r"^\d+\s+(game|unit|item)\s", ln)]
        self.assertEqual(len(printed), 14)
        self.assertNotIn("game seed at CUBX", buf.getvalue())

    def test_other_transmutes_build_and_refusals(self):
        import cube_anim
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for run, n in (("kinds2", 4), ("sock1", 1), ("classic", 2), ("kinds1", 4), ("upg1", 3)):
            D = self.cube.vector_data(self.excel, cube_anim.find_log(run), n)
            for th in ("dark", "light"):
                cube_anim.build(D, th)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(cube_anim.main([DATA, "--run", "nomatch", "--n", "1"]), 2)
        self.assertEqual(cube_anim.main([DATA, "--n", "0"]), 2)
        self.assertEqual(cube_anim.main([DATA, "--theme", "x"]), 2)
        with self.assertRaises(SystemExit):
            cube_anim.find_log("nosuchrun")


if __name__ == "__main__":
    unittest.main()

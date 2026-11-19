"""Tests of tools/objects_anim.py (plan 0070 Phase 11, batch 4 row 38, lane x17c): one toy room's eight slots, member
picks and spot searches (docs/specs/objects/README.md D1, E (handler 3), F1, F6).

Run: python3 -I tools/test_objects_anim.py     (needs no game data: the tool reads none)

The tool: the same arguments give the same bytes, both themes pass the export check's illustration rules, no art decoder
is imported, no text runs past the canvas, no caption is cut, no step text names a tool or a path. The numbers equal the
model: the slot loop's draws are fed to tools/objects.py's own solver (objects.solve: every way the loop can turn the
start seed into the end seed, with its picks) and must be among them; the placer calls are replayed on the model's seed
class (objects.Seed: Range, P100) with a second, separately written position test; the room seed is never drawn by the
placement and the object-region seed never by the slot loop.
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "workspace", "merged")
sys.path.insert(0, HERE)
import objects  # noqa: E402
import objects_anim as A  # noqa: E402
import schematic_kit as K  # noqa: E402
import test_schematic_kit as TK  # noqa: E402

SEEDS = ((0xC0FFEE, 12345), (1, 2), (7, 99), (0xDEADBEEF, 77), (12, 99), (555, 4242), (5, 12345), (31, 8), (999, 1000))


def toy_tables():
    """The toy level, groups and objects as the model's solver reads them."""
    lv = {}
    for k, (g, p) in enumerate(A.SLOTS):
        lv["ObjGrp%d" % k], lv["ObjPrb%d" % k] = g, p
    groups = {0: {}}
    for g, mem in A.GROUPS.items():
        d = {}
        for i in range(8):
            d["ID%d" % i], d["PROB%d" % i] = (mem[i][0], mem[i][1]) if i < len(mem) else (0, 0)
        groups[g] = d
    for g in range(1, 200):
        groups.setdefault(g, {"ID0": 0, "PROB0": 0})
    objs = {}
    for g in range(0, 200):
        objs[g] = {"SubClass": 0, "Gore": 0, "PopulateFn": 3, "InitFn": 0}
    for cls in A.SIZES:
        objs[cls] = {"SubClass": 0, "Gore": 0, "PopulateFn": 3, "InitFn": 0}
    return lv, groups, objs


class Objects(unittest.TestCase):
    def test_deterministic_both_themes_and_clean(self):
        out = TK.same_both_themes(self, "objects_anim.py", [], "obj")
        self.assertEqual(len(TK.steps(out)), 14)
        for t in TK.calc_text(out) + [s["text"] for s in TK.steps(out)]:
            self.assertNotRegex(t, r"\.py|tools/|workspace")
        K.TEXT_CLIPPED.clear()
        K.CAPTION_CUT.clear()
        for s, o in SEEDS:
            for theme in ("dark", "light"):
                A.build(s, o, theme)
        self.assertEqual((K.TEXT_CLIPPED, K.CAPTION_CUT), ([], []))
        self.assertEqual(A.main([DATA, "--seed", "0"]), 2)
        self.assertEqual(A.main([DATA, "--oseed", "zz"]), 2)
        self.assertEqual(A.main([DATA, "--theme", "grey"]), 2)
        self.assertEqual(A.main([DATA, "extra"]), 2)

    def test_slot_loop_is_one_of_the_models_solutions(self):
        lv, groups, objs = toy_tables()
        for s, o in SEEDS:
            tr = A.run(s, o)
            sols = objects.solve((s, 666), tr["S"], lv, groups, objs, tr["forced"])
            want = [(sl["k"], sl["g"], sl.get("cls"), 3 if sl.get("cls") else None) for sl in tr["slots"] if sl["passes"]]
            got = [[(k, g, oid, fn) for (k, g, oid, fn) in t] for _b, t in sols]
            self.assertEqual(len(got), 1, (s, o))
            self.assertEqual([(k, g, oid, fn) for k, g, oid, fn in got[0]],
                             [(k, g, oid, fn if oid else None) for k, g, oid, fn in
                              [(a, b, c, objs[c]["PopulateFn"] if c else None) for a, b, c, _d in want]])
            self.assertFalse(tr["forced"])
            self.assertEqual(tr["s_draws"], 8 + sum(1 for sl in tr["slots"] if sl["passes"]))

    def test_placements_replay_on_the_models_seed_class(self):
        rx, ry, rw, rh = A.RECT
        placed_any = rejected = nospot = 0
        for s, o in SEEDS:
            tr = A.run(s, o)
            O = objects.Seed((o, 666), "O")
            grid = set(tr["walls"])
            calls = iter(tr["places"])
            for sl in tr["slots"]:
                if sl.get("cls") is None:
                    continue
                self.assertEqual(O.p100(), sl["p100"])
                sx, sy = A.SIZES[sl["cls"]]
                self.assertEqual(sl["cnt"], (((rw * rh) >> 7) * sl["dens"]) >> 8)
                for _ in range(sl["cnt"]):
                    call = next(calls)
                    spot = None
                    n = 0
                    for a in range(5):
                        x = rx + O.rng(rw - sx - 1)
                        y = ry + O.rng(rh - sy - 1)
                        n += 1
                        ok = rx + 1 <= x < rx + rw - 1 and ry + 1 <= y < ry + rh - 1
                        w_, h_ = sx + 6, sy + 6
                        free = ok and not any((cx, cy) in grid for cx in range(x - w_ // 2, x - w_ // 2 + w_)
                                              for cy in range(y - h_ // 2, y - h_ // 2 + h_))
                        at = call["attempts"][a]
                        self.assertEqual((at["x"], at["y"], at["inside"]), (x, y, ok))
                        self.assertEqual(at["res"] == 0 if ok else at["res"] is None, free if ok else True)
                        if not ok:
                            rejected += 1
                        elif not free:
                            rejected += 1
                        if free:
                            spot = (x, y)
                            break
                    self.assertEqual(call["spot"], spot)
                    self.assertEqual(len(call["attempts"]), n)
                    if spot:
                        placed_any += 1
                        x, y = spot
                        for cx in range(x - sx // 2, x - sx // 2 + sx):
                            for cy in range(y - sy // 2, y - sy // 2 + sy):
                                grid.add((cx, cy))
                    else:
                        nospot += 1
            self.assertEqual(tr["O"], O.s)                 # the same draws, in the same count
            self.assertEqual(grid, tr["blocked"])
        self.assertGreater(placed_any, 5)
        self.assertGreater(rejected, 3)                    # the rejection branches run

    def test_no_seed_is_drawn_by_the_other_side(self):
        for s, o in SEEDS:
            tr = A.run(s, o)
            S = (s, 666)
            for _ in range(tr["s_draws"]):
                S = objects.step(S)
            self.assertEqual(S, tr["S"])
            O = (o, 666)
            for _ in range(tr["o_draws"]):
                O = objects.step(O)
            self.assertEqual(O, tr["O"])

    def test_nothing_placed_when_the_sum_is_at_most_the_roll_and_a_spot_can_be_missing(self):
        none_pick = [(s, o) for s, o in SEEDS if any(sl["passes"] and sl["pick"] is None for sl in A.run(s, o)["slots"])]
        self.assertTrue(none_pick)
        for s, o in none_pick:
            for sl in A.run(s, o)["slots"]:
                if sl["passes"] and sl["pick"] is None:
                    self.assertLessEqual(sl["sum"], sl["r2"])
        # a room full of walls: five attempts, no spot, no object (F1: no fallback)
        old = A.WALLS
        try:
            A.WALLS = [(0, 0, A.RECT[2] - 1, A.RECT[3] - 1)]
            tr = A.run(0xC0FFEE, 12345)
            self.assertTrue(tr["places"])
            for c in tr["places"]:
                self.assertIsNone(c["spot"])
                self.assertEqual(len(c["attempts"]), 5)
            _f, caps, _p, _t = A.build(0xC0FFEE, 12345, "dark")
            flat = " ".join(c["text"] + " " + " ".join(c["calc"]) for c in caps)
            self.assertIn("no fallback", flat)
        finally:
            A.WALLS = old

    def test_labels_use_no_x_for_times(self):
        with open(os.path.join(HERE, "objects_anim.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(re.findall(r"(?:%d|[0-9)]) [Xx] |[A-Z] X [A-Z] /| [Xx] (?:%d|[0-9(])", src), [])


if __name__ == "__main__":
    unittest.main()

"""No-game tests of tools/ai_tour.py (plan 0069 Phase 1a): python3 -I tools/test_ai_tour.py.

The waypoint ranks and warps on hand-built Levels rows, the caller read's majority rule, the case table's shape (every
aim is an entry of the tour's batches or a code placement, every group has a seed, every pool aim is in the case's
aims), and that no moved entry is also a case's aim. Nothing is launched; the excel and DS1 data are not read.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_tour as T  # noqa: E402


def lv(lid, act, wp, vis=(), warp=()):
    x = {"Id": str(lid), "Act": str(act), "Waypoint": str(wp)}
    for k in range(8):
        x["Vis%d" % k] = str(vis[k]) if k < len(vis) else "0"
        x["Warp%d" % k] = str(warp[k]) if k < len(warp) else "-1"
    return x


class Tables(unittest.TestCase):
    def test_waypoint_rank_within_the_act(self):
        rows = {1: lv(1, 0, 0), 3: lv(3, 0, 1), 4: lv(4, 0, 2), 2: lv(2, 0, 255), 40: lv(40, 1, 9), 42: lv(42, 1, 10)}
        self.assertEqual(T.waypoints(rows), {1: (1, 1), 3: (1, 2), 4: (1, 3), 40: (2, 1), 42: (2, 2)})

    def test_warps_skip_borders(self):
        rows = {3: lv(3, 0, 1, vis=(0, 0, 0, 9, 9), warp=(-1, -1, -1, 0, 1))}
        self.assertEqual(T.warps(rows, 3), [(9, 0), (9, 1)])

    def test_conv_read_majority(self):
        sites = [(1, True, False, 2), (2, True, True, 2), (3, False, False, 3)]
        self.assertEqual(T.conv_read(sites), (True, False, 2))


class CaseTable(unittest.TestCase):
    def test_groups_have_seeds(self):
        for c, t in T.TOUR.items():
            self.assertIsInstance(T.seed_of(t["group"]), int, c)

    def test_pool_aims_are_aims(self):
        for c, t in T.TOUR.items():
            for lid, es in t["pool"].items():
                for e in es:
                    self.assertIn(e, t["aims"], (c, lid, e))

    def test_moves_are_not_aimed(self):
        for e in T.MOVES:
            self.assertEqual(T.cases_of(e), [], e)

    def test_nightmare_cases_say_so(self):
        for c, t in T.TOUR.items():
            self.assertEqual(c.startswith("nm-"), t.get("diff", "normal") == "nightmare", c)

    def test_route_steps_are_known(self):
        kinds = {"stage", "descend", "border", "hunt", "town", "stay", "loot", "rerun"}
        for c, t in T.TOUR.items():
            for st in t["route"]:
                self.assertIn(st[0], kinds, c)

    def test_every_aim_is_a_tour_entry(self):
        ents = set(T.entries())
        for c, t in T.TOUR.items():
            for e in t["aims"]:
                self.assertIn(e, ents, (c, e))


if __name__ == "__main__":
    unittest.main()

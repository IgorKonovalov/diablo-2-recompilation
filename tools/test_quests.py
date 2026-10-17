"""Tests of tools/quests.py (plan 0042 Phase 2): the LCG step, the free-cell search, the point pick, and a synthetic
log through the checker (a dispatch, a join, a town portal, a level-point lookup, the gates). Stdlib only:
    python3 -I tools/test_quests.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import quests  # noqa: E402


class FakeData:
    position = {1: 1, 2: 0, 40: 1}
    wpidx = {1: 0, 3: 1}
    sync = {119: 1, 59: 0}
    groups = [(1, 0), (0, 0), (0, 0), (0, 0), (0, 0), (1, 1), (0, 1), (0, 1), (0, 1), (0, 1), (0, 2), (0, 3), (0, 4),
              (0, 5)]
    descs = [{"row": 0, "act": 0, "flag": 1, "id": 0, "word": 0}, {"row": 1, "act": 0, "flag": 0, "id": 1, "word": 1},
             {"row": 2, "act": 0, "flag": 0, "id": 2, "word": 2}]

    point_match = quests.Data.point_match


def s(t):
    return "%08x:%08x" % t


class Model(unittest.TestCase):
    def test_step(self):
        self.assertEqual(quests.step((1, 0)), (0x6AC690C5, 0))
        self.assertEqual(quests.nsteps((5, 7), quests.step((5, 7), 3)), 3)

    def test_free_near_in_place_and_ring(self):
        w = 3
        cells = [0] * 49
        win = quests.Window(10, 10, w, cells)
        self.assertEqual(quests.free_near(win, 10, 10, 1, 1, 50, 1), (10, 10, 0))
        cells[3 * 7 + 3] = 1                       # the start cell blocked
        x, y, best = quests.free_near(win, 10, 10, 1, 1, 50, 1)
        self.assertEqual((x, y, best), (9, 10, 1))  # ring 1: (9, 9) is found first, (9, 10) is nearer
        cells2 = [1] * 49
        cells2[3 * 7 + 4] = 0                      # only (11, 10) free
        self.assertEqual(quests.free_near(quests.Window(10, 10, w, cells2), 10, 10, 1, 1, 50, 1)[:2], (11, 10))

    def test_point_match(self):
        d = FakeData()
        self.assertTrue(d.point_match(0, 3))       # type 0 has a group: 0..4
        self.assertTrue(d.point_match(5, 7))
        self.assertFalse(d.point_match(11, 5))
        self.assertFalse(d.point_match(5, 0))


class CheckerLog(unittest.TestCase):
    def run_lines(self, lines):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            for tag, d in lines:
                f.write("%s %s\n" % (tag, json.dumps(d)))
        try:
            return quests.Checker(FakeData()).run([f.name])
        finally:
            os.unlink(f.name)

    def test_dispatch_and_deactivated(self):
        g = s((1, 2))
        qobj = [[40, 4, 0, 1, 0, 42], [2, 0, 0, 0, 0, 2], [1, 0, 1, 1, 0, 1], [0, 0, 1, 1, 0, 0]]
        e = {"k": "de", "ph": 0, "ev": 0, "force": 1, "actf": 1, "unit": [1, 148, 3], "ucls": 148, "lid": 1,
             "qobj": qobj, "slots": [2, 1, 0], "gs": g, "qs": g, "ps": g}
        lines = [("EV", e), ("QCB", {"id": 2, "a9": 0, "aA": 0, "ev": 0, "unit": "de"}),
                 ("QCB", {"id": 1, "a9": 1, "aA": 1, "ev": 0, "unit": "de"}),
                 ("QCB", {"id": 0, "a9": 1, "aA": 1, "ev": 0, "unit": "de"}),
                 ("EV", {"k": "de", "ph": 1, "gs": g, "qs": g, "ps": g})]
        c = self.run_lines(lines)
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["forced e0 callbacks of deactivated quests"], 1)
        bad = self.run_lines(lines[:1] + lines[2:])          # quest 2's forced callback missing
        self.assertTrue(any("dispatch order" in b for b in bad.bad))

    def test_join(self):
        g = s((1, 2))
        rec = [0] * 48
        rec[1] = 1
        e = {"k": "join", "ph": 0, "rejoin": 0, "ready": 0, "b150c": 1, "rec": rec,
             "qobj": [[2, 0, 1, 1, 0, 2], [1, 0, 1, 1, 0, 1], [0, 0, 1, 1, 0, 0]], "gs": g}
        x = {"k": "join", "ph": 1, "qobj": [[2, 0, 1, 1, 0, 2], [1, 0, 0, 0, 0, 1], [0, 0, 1, 1, 0, 0]],
             "grec": [0, 0x8000] + [0] * 46, "gs": g}
        c = self.run_lines([("EV", e), ("QS", {"ret": "0054633e", "w": 1, "b": 15}), ("EV", x)])
        self.assertEqual(c.bad, [])
        c = self.run_lines([("EV", e), ("EV", x)])
        self.assertTrue(any("game-record marks" in b for b in c.bad))

    def test_tp_and_lpf(self):
        gs0 = (0x11111111, 0x2222)
        g1, g2 = quests.step(gs0), quests.step(gs0, 2)
        f0 = (g1[0], 666)
        p0 = (g2[0], 666)
        ls = (0x1234, 0x5678)
        pts = [[100, 200, 0], [110, 210, 11]]
        lines = [
            ("EV", {"k": "tp", "ph": 0, "own": 0, "gs": s(gs0), "qs": s(gs0), "ps": s(gs0)}),
            ("PU", {"at": "field", "oinit": "%08x" % g1[0], "os": s(f0), "omode": 1}),
            ("PU", {"at": "field1", "os": s(f0)}),
            ("EV", {"k": "lpf", "ph": 0, "lvl": 40, "type": 11}),
            ("LPL", {"lid": 40, "ls": s(ls), "pts": pts}),
            ("EV", {"k": "lpf", "ph": 1, "tx": 110, "ty": 210, "ls": s(quests.step(ls))}),
            ("PU", {"at": "roomupdate", "gs": s(g1)}),
            ("PU", {"at": "partner", "oinit": "%08x" % g2[0], "os": s(p0), "omode": 0, "gs": s(g2)}),
            ("PU", {"at": "partner2", "os": s(quests.step(p0))}),
            ("EV", {"k": "tp", "ph": 1, "own": 7, "gs": s(g2), "qs": s(gs0), "ps": s(gs0)}),
        ]
        c = self.run_lines(lines)
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["level seed Position type 11 step 1"], 1)
        lines[5] = ("EV", {"k": "lpf", "ph": 1, "tx": 110, "ty": 210, "ls": s(ls)})
        self.assertTrue(any("level seed" in b for b in self.run_lines(lines).bad))

    def test_gate(self):
        c = self.run_lines([("GT", {"k": "portal", "tick": 4999, "stamp": 0, "pass": 0}),
                            ("GT", {"k": "p49", "tick": 20000, "stamp": 0, "pass": 1})])
        self.assertEqual(c.bad, [])


if __name__ == "__main__":
    unittest.main()

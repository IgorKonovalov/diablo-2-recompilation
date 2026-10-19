"""Tests of tools/quests.py (plan 0042 Phase 2): the LCG step, the free-cell search, the point pick, and a synthetic
log through the checker (a dispatch, a join, a town portal, a level-point lookup, the gates); part 2's rules (talk
steps, saved words, NPC 266's handler runs, word 40's message map) and part 3's (the eclipse arm, timers, the cairn
order, the Dark Wanderer's objects, Anya's reward, the town-portal refusal in a town). Stdlib only:
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


def join_lines(rec, g):
    """A first join (rejoin 0, byte set, nothing switched off: no word has bit 0 or 15) that sets the checker's
    player record to rec."""
    q = [[2, 0, 1, 1, 0, 2], [1, 0, 1, 1, 0, 1], [0, 0, 1, 1, 0, 0]]
    return [("EV", {"k": "join", "ph": 0, "rejoin": 0, "ready": 0, "b150c": 1, "rec": rec, "qobj": q, "gs": g,
                    "diff": 0}),
            ("EV", {"k": "join", "ph": 1, "qobj": q, "grec": [0] * 48, "gs": g})]


def de(ev, cls, msg, g, qobj=None, slots=None, qs=None, qx=None, lid=1, p14=None):
    e = {"k": "de", "ph": 0, "ev": ev, "force": 1, "actf": 0, "unit": [1, cls, 9], "ucls": cls, "lid": lid,
         "qobj": qobj or [], "slots": slots or [], "gs": g, "qs": qs or g, "ps": g,
         "p14": cls if p14 is None else p14, "p18": msg}
    return e, {"k": "de", "ph": 1, "gs": g, "qs": qx or qs or g, "ps": g}


class Part2Rules(unittest.TestCase):
    run_lines = CheckerLog.run_lines

    def test_talk_step_writes_at_call_sites(self):
        g = s((1, 2))
        rec = [0] * 48
        rec[1] = 2                                  # word 1 bit 1: Akara's 0x4C reward fires
        e, x = de(11, 148, 0x4C, g)
        ok = [("QS", {"ret": "%08x" % (0x0058FF11 + 5), "rec": 7, "w": 1, "b": 0}),
              ("QC", {"ret": "%08x" % (0x0058FF20 + 5), "rec": 7, "w": 1, "b": 1}),
              ("QK", {"ret": "%08x" % (0x0058FF4B + 5), "rec": 7, "w": 1})]
        c = self.run_lines(join_lines(rec, g) + [("EV", e)] + ok + [("EV", x)])
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["talk step w1 npc 148 msg 0x4c fires"], 1)
        bad = self.run_lines(join_lines(rec, g) + [("EV", e)] + ok[:2] + [("EV", x)])     # the steps clear missing
        self.assertTrue(any("talk step w1" in b for b in bad.bad))
        rec[1] = 0                                  # condition off: no write allowed
        bad = self.run_lines(join_lines(rec, g) + [("EV", e)] + ok + [("EV", x)])
        self.assertTrue(any("talk step w1" in b for b in bad.bad))

    def test_word40_message_map(self):
        g = s((1, 2))
        for msg, bit in ((0x4ECF, 7), (0x4ED2, 4), (0x4ED4, 8)):
            e, x = de(11, 511, msg, g)
            w = ("QS", {"ret": "%08x" % (0x0058D9C7 + 5), "rec": 7, "w": 40, "b": bit})
            self.assertEqual(self.run_lines(join_lines([0] * 48, g) + [("EV", e), w, ("EV", x)]).bad, [])
            w2 = ("QS", {"ret": "%08x" % (0x0058D9C7 + 5), "rec": 7, "w": 40, "b": 4 + (msg - 0x4ECF)})
            if w2[1]["b"] != bit:                    # the message-order reading is refused
                self.assertTrue(self.run_lines(join_lines([0] * 48, g) + [("EV", e), w2, ("EV", x)]).bad)

    def test_npc266_two_runs(self):
        g = s((1, 2))
        p0 = (0x1234, 0x29A)
        qcb = lambda: ("QCB", {"id": 25, "fn": "00596a90", "unit": "de", "ev": 0})
        e = {"k": "de", "ph": 0, "ev": 0, "force": 1, "actf": 0, "ucls": 266, "unit": [1, 266, 4], "qobj": [],
             "slots": None, "gs": g, "qs": g, "ps": s(p0)}
        x = {"k": "de", "ph": 1, "gs": g, "qs": g, "ps": s(quests.step(p0, 2))}
        c = self.run_lines([("EV", e), qcb(), qcb(), ("EV", x)])
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["NPC 266 talk: e0 handler 0x00596A90 runs 2"], 1)
        self.assertTrue(self.run_lines([("EV", e), qcb(), ("EV", x)]).bad)          # one run predicts one step

    def test_saved_words(self):
        import d2s
        g = s((1, 2))
        a = [[0] * 48 for _ in range(3)]
        a[0][4] = 0x2002                            # bit 13 is cleared and bit 15 set by the loader (bit 1 set)
        loaded = list(a[0])
        loaded[4] = 0x8002
        out = [list(r) for r in a]
        out[0][4] = 0x8003                          # + the logged write of bit 0
        out[0] = [(w & ~0x6000) | (0x8000 if w & 2 else 0) for w in out[0][:42]] + out[0][42:]
        out[1] = [(w & ~0x6000) | (0x8000 if w & 2 else 0) for w in out[1][:42]] + out[1][42:]
        out[2] = [(w & ~0x6000) | (0x8000 if w & 2 else 0) for w in out[2][:42]] + out[2][42:]
        old = d2s.quest_words
        files = {}
        d2s.quest_words = lambda b: files[b]
        try:
            with tempfile.TemporaryDirectory() as td:
                log = os.path.join(td, "s.log")
                with open(log, "w") as f:
                    for tag, d in join_lines(loaded, g) + [("QS", {"ret": "00592400", "rec": 7, "w": 4, "b": 0})]:
                        f.write("%s %s\n" % (tag, json.dumps(d)))
                for suf, words in ((".in.d2s", a), (".out.d2s", out)):
                    with open(log[:-4] + suf, "wb") as fh:
                        fh.write(suf.encode())
                    files[suf.encode()] = words
                c = quests.Checker(FakeData()).run([log])
                self.assertEqual(c.bad, [])
                self.assertEqual(c.n["saved words: player-record writes applied"], 1)
                files[b".out.d2s"] = [list(r) for r in a]          # the write missing from the save
                self.assertTrue(quests.Checker(FakeData()).run([log]).bad)
        finally:
            d2s.quest_words = old


class Part3Rules(unittest.TestCase):
    run_lines = CheckerLog.run_lines

    def test_eclipse_arm_and_timer(self):
        g = s((1, 2))
        q0 = (0x10000001, 0x29A)                     # low after the step decides the period
        q1 = quests.step(q0)
        per = 15 + (q1[0] & 1)
        qobj = [[10, 1, 1, 1, 0, 11, 0]]
        e, x = de(3, 0, 44, g, qobj=qobj, slots=[10], qs=s(q0), qx=s(q1), lid=44, p14=43)
        e["unit"] = 0
        tma = ("TMA", {"q": 10, "fn": "0059ed80", "per": per, "tick": 100, "qs": s(q1)})
        lines = [("EV", e), ("QCB", {"id": 10, "unit": "de", "ev": 3, "fn": "0059ee00"}), tma, ("EV", x),
                 ("TMR", {"fn": "0059ed80", "q": 10, "due": 100 + per, "per": per, "tick": 101 + per, "qs": s(q1),
                          "f": 20 * 7}),
                 ("TMX", {"fn": "0059ed80", "r": 1, "qs": s(q1)})]
        c = self.run_lines(lines)
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["eclipse armed (level 44)"], 1)
        bad = list(lines)
        bad[2] = ("TMA", dict(tma[1], per=31 - per))  # the other period
        self.assertTrue(self.run_lines(bad).bad)
        bad = list(lines)
        bad[4] = ("TMR", dict(lines[4][1], tick=100 + per))     # run one pass early
        self.assertTrue(self.run_lines(bad).bad)
        qobj2 = [[10, 1, 1, 1, 0, 11, 1]]           # state 1: no arm, no draw
        e2, x2 = de(3, 0, 44, g, qobj=qobj2, slots=[10], qs=s(q0), lid=44, p14=43)
        c = self.run_lines([("EV", e2), ("QCB", {"id": 10, "unit": "de", "ev": 3, "fn": "0059ee00"}), ("EV", x2)])
        self.assertEqual(c.bad, [])

    def test_cairn_order(self):
        q0 = (0x0BADF00D, 0x29A)
        sd, slots, k = q0, [0] * 5, 0
        while k < 5:
            sd = quests.step(sd)
            if not slots[sd[0] % 5]:
                slots[sd[0] % 5] = 17 + k
                k += 1
        lines = [("CRN0", {"a4a": 0, "qs": s(q0)}), ("QGS", {"ret": "00592ee6", "qs": s(q0)}),
                 ("CRN", {"order": slots, "qs": s(sd)}),
                 ("CRN0", {"a4a": 1, "qs": s(sd)}), ("CRN", {"order": slots, "qs": s(sd)})]
        c = self.run_lines(lines)
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["cairn order kept checks"], 1)
        bad = list(lines)
        bad[2] = ("CRN", {"order": slots[1:] + slots[:1], "qs": s(sd)})
        self.assertTrue(self.run_lines(bad).bad)

    def test_dark_wanderer(self):
        q0 = (0x0000F00D, 0x29A)
        lo = quests.step(q0)[0]
        tries = [("DWF", {"i": i, "room": 5, "x": 0, "y": 0}) for i in range(lo & 1, 8)]
        lines = [("TMA", {"q": 28, "fn": "005bd390", "per": 2, "tick": 10, "qs": s(q0)}),
                 ("TMR", {"fn": "005bd390", "q": 28, "due": 12, "per": 2, "tick": 13, "qs": s(q0), "f": 260}),
                 ("QGS", {"ret": "005bd3e2", "qs": s(q0)}),
                 ("DWS", {"low": lo, "pos": [1, 2], "qs": s(quests.step(q0))})] + tries + [
                 ("TMX", {"fn": "005bd390", "r": 1, "qs": s(quests.step(q0))})]
        c = self.run_lines(lines)
        self.assertEqual(c.bad, [])
        self.assertTrue(self.run_lines(lines[:4] + tries[1:] + lines[-1:]).bad)    # one try short

    def test_anya_reward(self):
        g = s((1, 2))
        q0 = (0x12345678, 0x29A)
        n = 3
        tbl = 0x00735F6C
        lo = quests.step(q0)[0]

        class D(FakeData):
            anya = {(tbl, 1): (n, ["aaa ", "bbb ", "ccc "])}
        rec = [0] * 48
        rec[37] = 0x8102                            # b1, b8, b15
        e, x = de(11, 512, 0x4EA8, g, qs=s(q0), qx=s(quests.step(q0)))
        x["gs"] = s((3, 4))                         # the item's creation draws the game seed (oracle)
        w = lambda t, b, a: (t, {"ret": "%08x" % (a + 5), "rec": 7, "w": 37, "b": b})
        lines = join_lines(rec, g) + [("EV", e), ("ANL", {"clvl": 80}),
                                      ("ANY", {"cls": 1, "tbl": "%08x" % tbl, "n": n, "r": lo % n,
                                               "code": "aaa bbb ccc ".split()[lo % n] + " ", "diff": 0, "g6a": 0}),
                                      w("QS", 9, 0x005899BA), w("QC", 1, 0x005899D2), w("QS", 0, 0x005899DC),
                                      w("QS", 10, 0x005899E6), ("EV", x)]
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            for tag, d in lines:
                f.write("%s %s\n" % (tag, json.dumps(d)))
        try:
            c = quests.Checker(D()).run([f.name])
        finally:
            os.unlink(f.name)
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["Anya reward draw checks"], 1)

    def test_tp_refused_in_town(self):
        g = s((1, 2))
        c = self.run_lines([("EV", {"k": "tp", "ph": 0, "own": 0, "lid": 109, "gs": g, "qs": g, "ps": g}),
                            ("EV", {"k": "tp", "ph": 1, "own": 0, "gs": g, "qs": g, "ps": g})])
        self.assertEqual(c.bad, [])
        self.assertEqual(c.n["town portal in a town refused checks"], 1)


if __name__ == "__main__":
    unittest.main()

"""No-game test of tools/quests_s3a.py: python3 -I tools/test_quests_s3a.py (written logs only, nothing launched).

The Run object is built without its __init__ (which reads the excel tables and the field image), so the rules under test
are the ones that read the log alone: brackets, timers, words and the revision 2 notes.
"""
import collections
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import quests_s3a as S  # noqa: E402


def bare_run(name="t.log"):
    r = S.Run.__new__(S.Run)
    r.n = collections.Counter()
    r.bad = []
    r.notes = collections.defaultdict(collections.Counter)
    r.name, r.ln = name, 0
    return r


def write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    with os.fdopen(fd, "w") as fh:
        fh.write("# header line, not JSON\n")
        for t, d in lines:
            fh.write("%s %s\n" % (t, json.dumps(d)))
        fh.write("QS {broken\n")
    return path


class Parse(unittest.TestCase):
    def test_parse_skips_non_json_and_numbers_lines(self):
        p = write_log([("TMA", {"tick": 1, "f": 20}), ("QS", {"ret": "x", "w": 1, "b": 0, "old": 0, "rec": 1})])
        try:
            L = S.parse(p)
        finally:
            os.unlink(p)
        self.assertEqual([(ln, t) for ln, t, d in L], [(2, "TMA"), (3, "QS")])

    def test_brackets_nest_by_kind(self):
        L = [(1, "EV", {"k": "p49", "ph": 0}), (2, "EV", {"k": "wptr", "ph": 0}), (3, "QS", {}),
             (4, "EV", {"k": "wptr", "ph": 1}), (5, "EV", {"k": "p49", "ph": 1})]
        out = S.brackets(L)
        self.assertEqual([(b.k, b.i0, b.i1) for b in out], [("wptr", 1, 3), ("p49", 0, 4)])
        self.assertIs(out[0].parent, out[1])
        self.assertEqual([i for i, t, d in S.inside(out[0], L)], [2])


class Timers(unittest.TestCase):
    def test_a_run_off_the_boundary_is_a_mismatch(self):
        r = bare_run()
        r.timers([(1, "TMA", {"tick": 3, "f": 61}), (2, "TMR", {"tick": 5, "f": 100, "due": 4}),
                  (3, "TMR", {"tick": 6, "f": 121, "due": 5})])
        self.assertEqual(r.n["P4/P8 timer add tick = frame // 20 checks"], 1)
        self.assertEqual(r.n["P4/P8 timer run on frame mod 20 = 0, tick = frame / 20 MISMATCH"], 1)
        self.assertEqual(len(r.bad), 1)


class Words(unittest.TestCase):
    def test_next_old_word_follows_set_clear_and_clearsteps(self):
        r = bare_run()
        L = [(1, "QS", {"rec": 7, "w": 4, "b": 13, "old": 0x0001, "ret": "a"}),
             (2, "QC", {"rec": 7, "w": 4, "b": 0, "old": 0x2001, "ret": "b"}),
             (3, "QK", {"rec": 7, "w": 4, "old": 0x2010, "ret": "c"}),
             (4, "QS", {"rec": 7, "w": 4, "b": 1, "old": 0x2000, "ret": "d"}),
             (5, "QS", {"rec": 7, "w": 4, "b": 2, "old": 0x0000, "ret": "e"})]    # stale: the QS left 0x2002
        r.words(L)
        self.assertEqual(r.n["P13 QS then the next write's old word checks"], 2)
        self.assertEqual(r.n["P13 QS then the next write's old word MISMATCH"], 1)
        self.assertEqual(r.n["P13 QC then the next write's old word checks"], 1)
        self.assertEqual(r.n["P13 QK then the next write's old word checks"], 1)
        self.assertEqual(r.n["P16 QK calls"], 1)


class Rev2(unittest.TestCase):
    def test_reward_w4_fail_w19_and_act_travel_notes(self):
        r = bare_run("2026-10-19-quests3-x-entry.log")
        L = [(1, "EV", {"rejoin": 0, "rec": [0, 0, 0, 0, 0]}),
             (2, "QS", {"rec": 9, "w": 4, "b": 0, "old": 2, "ret": "005923b1"}),
             (3, "QC", {"rec": 9, "w": 4, "b": 1, "old": 3, "ret": "005923bb"}),
             (4, "QK", {"rec": 9, "w": 1, "old": 1, "ret": "0058ff50"}),
             (5, "QS", {"rec": 9, "w": 1, "b": 0, "old": 0, "ret": "0054633e"}),          # the loader: left out
             (6, "EV", {"k": "chlevel", "ph": 0}),
             (7, "STALE", {"ret": 0x00537402}),
             (8, "QS", {"rec": 8, "w": 4, "b": 13, "old": 0, "ret": "0054475c"}),          # game record: left out
             (9, "QS", {"rec": 9, "w": 4, "b": 14, "old": 0, "ret": "00592b4b"}),
             (10, "EV", {"k": "chlevel", "ph": 1}),
             (11, "QS", {"rec": 9, "w": 19, "b": 8, "old": 0x40, "ret": "005b93f3"}),
             (12, "QS", {"rec": 9, "w": 10, "b": 0, "old": 0, "ret": "00546900"})]
        r.rev2(L, S.brackets(L))
        n = r.notes
        rew = n["P16/P56 player-record b0 sets, b1 clears, ClearSteps (tag, word, bit, site)"]
        self.assertEqual(sorted(rew), ["QC w04 b1 005923bb", "QK w01 - 0058ff50", "QS w04 b0 005923b1",
                                       "QS w10 b0 00546900"])
        fail = n["P96 w4 b14 writes (site, enclosing brackets outer to inner, a TownLevelLeave store line before it "
                 "inside, joiner's word 4)"]
        self.assertEqual(list(fail), ["00592b4b ['chlevel'] tll=True w4=0"])
        self.assertEqual(list(n["P200/P201 word 19 writes (log, tag, bit, site, old)"]),
                         ["s3-x-entry QS b8 005b93f3 0040"])
        self.assertEqual(list(n["T84 act-travel word writes (log, word, bit, site)"]), ["s3-x-entry w10 b0 00546900"])
        self.assertEqual(r.bad, [])


if __name__ == "__main__":
    unittest.main()

"""No-game tests of tools/trade_check.py (plan 0067 Phase 2): the placement models, the T13 layout search and the log
checker on synthetic host logs written in tools/gdb/two-trade.py's line format, each with a mutation that the checker
must name. Run: python3 -I tools/test_trade_check.py"""
import copy
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import trade_check as tc  # noqa: E402


class FakeItems:
    """Class index -> (code, w, h, quest), a few rows only."""
    ROWS = [("wnd", 1, 2, 0), ("gcv", 1, 1, 0), ("box", 2, 2, 10), ("gax", 2, 4, 0), ("cap", 2, 2, 0)]

    def __init__(self):
        self.rows = list(self.ROWS)

    def size(self, cls):
        return self.rows[cls][1:3]

    def code(self, cls):
        return self.rows[cls][0]

    def quest(self, cls):
        return self.rows[cls][3]


WND, GCV, BOX, GAX, CAP = range(5)
H, J = 1, 2                      # unit ids: the host's player, the joiner's


def plr(pid, st=0, gold=0, lvl=80, rec=0, partner=None, **kw):
    d = {"id": pid, "mode": 1, "b22": 0, "b23": 0, "ia": [partner, 0, 1] if partner else [0, 0, 0], "gold": gold,
         "lvl": lvl, "cur": 0, "st": st, "t54": 0, "t58": 0, "b4c": 0, "rec": rec}
    if rec:
        d.update(r0=900, off=0, g10=gold, lk=0, map=[], sha="aa" * 8)
    d.update(kw)
    return d


class Log:
    def __init__(self):
        self.lines = []
        self.f = 100

    def add(self, tag, d):
        self.lines.append("%s %s" % (tag, json.dumps(d)))

    def ev(self, tag, pl, inv, **kw):
        d = dict(kw, f=self.f, pl=copy.deepcopy(pl), inv=copy.deepcopy(inv))
        self.add(tag, d)

    def write(self, path):
        with open(path, "w") as f:
            f.write("TWO-TRADE logger armed\nTRDY {}\n")
            f.write("\n".join(self.lines) + "\n")


def t1_log(mutate=None):
    """MP31 as the finding predicts it: H requests J, J accepts, H gives a wand from (0, 0) to page 2 (2, 1), J offers
    500 gold, H accepts, J accepts (A = J). J's page 0 holds a cap at (0, 0)."""
    L = Log()
    invH = [[101, WND, 0, 0, 0, 0, 1], [102, GCV, 0, 5, 0, 0, 1]]
    invJ = [[201, CAP, 0, 0, 0, 0, 1]]
    inv = {str(H): invH, str(J): invJ}
    h, j = plr(H, gold=10000), plr(J, gold=100000)
    # the request
    L.ev("TRQ", [h, j], inv, req=H, tgt=J, site=0x548E70)
    L.add("TQT", {"t": 50000, "f": L.f})
    L.add("TQX", {"pc": 0x00567000, "f": L.f})
    h1, j1 = plr(H, 1, 10000, partner=J), plr(J, 2, 100000, partner=H)
    L.ev("TRQR", [h1, j1], inv, req=H, tgt=J, site=0x548E70, eax=0)
    # J opens (button 3)
    L.ev("TRB", [h1, j1], inv, p=J, button=3, param=0, site=0x54C7F5)
    L.ev("TRO", [h1, j1], inv)
    h2 = plr(H, 3, 10000, rec=0x1000, partner=J)
    j2 = plr(J, 3, 100000, rec=0x2000, partner=H)
    L.ev("TRA", [h1, j2], inv, p=J, ok=1)
    L.ev("TRA", [h2, j2], inv, p=H, ok=1)
    L.ev("TRBR", [h2, j2], inv, p=J, button=3, param=0, site=0x54C7F5, eax=0)
    # H picks the wand up (the change lock), then places it on page 2: its copy on J's page 1
    L.ev("TIT", [h2, j2], inv, p=H, item=[101, WND, 0, 0, 0, 0, 1], site=0x535700)
    h3, j3 = dict(h2, st=7, b22=1), dict(j2, st=7)
    L.ev("TITR", [h3, j3], inv, pc=0x00567826, eax=1)
    L.f += 1
    for p, s0, s1, b22 in ((H, 7, 8, 1), (J, 7, 8, 0)):
        x0 = dict(h3 if p == H else j3)
        x1 = dict(x0, st=s1)
        L.ev("TTK", [x0 if p == H else h3, x0 if p == J else j3], inv, p=p, site=0x541900)
        L.ev("TTKR", [x1 if p == H else h3, x1 if p == J else j3], inv, p=p, site=0x541900, eax=0)
        if p == H:
            h3 = x1
        else:
            j3 = x1
    L.f += 1
    h4, j4 = dict(h3, st=3, b22=0), dict(j3, st=3)
    for p in (H, J):
        L.ev("TTK", [h3 if p == H else h4, j3 if p == J else j4], inv, p=p, site=0x541900)
        L.ev("TTKR", [h4, j4 if p == J else j3], inv, p=p, site=0x541900, eax=0)
    invH2 = [[101, WND, 2, 2, 1, 4, 1], [102, GCV, 0, 5, 0, 0, 1]]
    invJ2 = [[201, CAP, 0, 0, 0, 0, 1], [301, WND, 1, 2, 1, 4, 1]]
    inv2 = {str(H): invH2, str(J): invJ2}
    L.ev("TSO", [h4, j4], inv2, p=H, item=[101, WND, 2, 2, 1, 4, 1], site=0x5603DE)
    L.add("TSP", {"ok": 1, "orig": 101, "copy": 301, "copy_item": [301, WND, 1, 2, 1, 4, 1], "partner": J,
                  "x": 2, "y": 1, "f": L.f})
    h5 = dict(h4, map=[[101, 301]])
    L.ev("TSOR", [h5, j4], inv2, p=H, item=[101, WND, 2, 2, 1, 4, 1], site=0x5603DE, eax=1)
    # J offers 500 gold
    L.ev("TRB", [h5, j4], inv2, p=J, button=8, param=500, site=0x54C7F5)
    j5 = dict(j4, off=500)
    L.ev("TRBR", [h5, j5], inv2, p=J, button=8, param=500, site=0x54C7F5, eax=0)
    # H accepts
    L.ev("TRB", [h5, j5], inv2, p=H, button=4, param=0, site=0x54C7F5)
    h6 = dict(h5, st=4)
    L.ev("TRBR", [h6, j5], inv2, p=H, button=4, param=0, site=0x54C7F5, eax=0)
    # J accepts: the commit, A = J, B = H
    L.ev("TRB", [h6, j5], inv2, p=J, button=4, param=0, site=0x54C7F5)
    j6 = dict(j5, st=4)
    L.ev("TCM", [h6, j6], inv2, a=J, b=H, site=0x568564)
    # the room test: A's (J's) offer is empty; B's (H's) wand into a FIRST copy of J's page 0 (cap at (0, 0))
    first = tc.place_seq(tc.grid_from([(0, 0, 2, 2)]), [(1, 2)], False)[0][0]
    L.add("SCP", {"ok": 1, "item": [101, WND, 2, 2, 1, 4, 1], "x": first[0], "y": first[1], "own": 0, "row_of": J,
                  "f": L.f})
    L.add("TRT", {"eax": 1, "side": 0, "a": J, "b": H, "f": L.f})
    L.add("TMV", {"dir": "ab", "al": 1, "f": L.f})
    # the real placement: BEST in J's page 0
    best = tc.place_seq(tc.grid_from([(0, 0, 2, 2)]), [(1, 2)], True)[0][0]
    L.add("TMP", {"ok": 1, "orig": 101, "copy": [401, WND, 0, best[0], best[1], 0, 1], "to": J, "f": L.f})
    L.add("TMV", {"dir": "ba", "al": 1, "f": L.f})
    h7 = plr(H, 9, 10500, b23=1)
    j7 = plr(J, 9, 99500, b23=1)
    inv3 = {str(H): [[102, GCV, 0, 5, 0, 0, 1]],
            str(J): [[201, CAP, 0, 0, 0, 0, 1], [401, WND, 0, best[0], best[1], 0, 1]]}
    L.add("TMS", {"code": 0x0D, "site": 0x0056801B, "f": L.f})
    L.add("TMS", {"code": 0x0D, "site": 0x00568035, "f": L.f})
    L.ev("TCMR", [h7, j7], inv3, a=J, b=H, site=0x568564, eax=0)
    L.ev("TRBR", [h7, j7], inv3, p=J, button=4, param=0, site=0x54C7F5, eax=0)
    if mutate:
        mutate(L)
    return L


def run(L, case="T1", items=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "host.log")
        L.write(p)
        out = []
        chk, unmet = tc.run_check(p, items or FakeItems(), case=case, out=out.append)
        return chk, unmet, out


def replace_tag(L, tag, fn):
    for k, ln in enumerate(L.lines):
        t, _, rest = ln.partition(" ")
        if t == tag:
            d = json.loads(rest)
            if fn(d) is not False:
                L.lines[k] = "%s %s" % (t, json.dumps(d))


class Models(unittest.TestCase):
    D1 = [(3, 1, 2, 2), (7, 0, 2, 4), (0, 1, 2, 3), (5, 0, 2, 3)]

    def test_first_and_best_disagree(self):
        g = tc.grid_from(self.D1)
        f, _ = tc.place_seq(g, [(1, 2)] * 4, False)
        b, _ = tc.place_seq(g, [(1, 2)] * 4, True)
        self.assertEqual(f, [(2, 0), (2, 2), (9, 0), (9, 2)])
        self.assertEqual(b, [(9, 0), (9, 2), (2, 1), None])
        self.assertEqual(tc.outcomes(g, [(1, 2)] * 4), {(True, False)})

    def test_room_test_sides(self):
        full = tc.grid_from([(c, 0, 2, 4) for c in range(0, 10, 2)])
        empty = tc.grid_from([])
        self.assertEqual(tc.room_test(empty, [(1, 1)], full, [])[:2], (False, 0))
        self.assertEqual(tc.room_test(full, [], empty, [(1, 1)])[:2], (False, 1))
        self.assertEqual(tc.room_test(empty, [(1, 1)], empty, [(2, 2)])[:2], (True, None))

    def test_place_stops_at_first_failure(self):
        g = tc.grid_from([(c, 0, 2, 4) for c in range(0, 8, 2)])      # two columns left
        s, _ = tc.place_seq(g, [(2, 4), (1, 1), (1, 1)], True)
        self.assertEqual(s, [(8, 0), None])

    def test_clip_and_gold(self):
        self.assertEqual(tc.clip_offer(5000, 799000, 80), 1000)
        self.assertEqual(tc.clip_offer(500, 799000, 80), 500)
        self.assertEqual(tc.gold_after(10000, 100000, 0, 500), (10500, 99500))
        self.assertEqual(tc.gold_after(100, 0, 500, 0), (100, 500))   # 0x00567F68: jl skips the take, not the give

    def test_layout_search_deterministic(self):
        sizes = [(1, 1), (1, 2), (2, 2), (2, 4), (1, 4)]
        a = tc.layout_search(sizes, seed=5, trials=300)[0]
        b = tc.layout_search(sizes, seed=5, trials=300)[0]
        self.assertEqual(a, b)
        self.assertGreater(a["trials"], 0)


class Checker(unittest.TestCase):
    def test_t1_clean(self):
        chk, unmet, out = run(t1_log())
        self.assertEqual(chk.mismatches, [], out)
        self.assertEqual(unmet, [], out)
        self.assertGreater(chk.n_checks, 20)

    def test_t1_gold_mutation(self):
        def m(L):
            replace_tag(L, "TCMR", lambda d: d["pl"][0].update(gold=10000))
        chk, _, out = run(t1_log(m))
        self.assertIn("R-commit/goldmove", [r for _, _, r, _ in chk.mismatches], out)

    def test_t1_scratch_best_mutation(self):
        def m(L):
            replace_tag(L, "SCP", lambda d: d.update(x=9, y=2))     # a cell FIRST does not give (it gives (0, 2))
        chk, _, out = run(t1_log(m))
        self.assertIn("R-commit/scratch", [r for _, _, r, _ in chk.mismatches], out)

    def test_t1_placement_mutation(self):
        def m(L):
            replace_tag(L, "TMP", lambda d: d["copy"].__setitem__(3, 2) or d["copy"].__setitem__(4, 0))
        chk, _, out = run(t1_log(m))
        self.assertIn("R-commit/placement", [r for _, _, r, _ in chk.mismatches], out)

    def test_gold_offer_unaccepts_mutation(self):
        """T6's separating claim: a gold offer moves no state. A log where the partner left 4 is named."""
        def m(L):
            seen = []

            def fn(d):
                if d["button"] != 8:
                    return False
                d["pl"][0]["st"] = 3
                seen.append(1)
            replace_tag(L, "TRBR", fn)
            for k, ln in enumerate(L.lines):            # put H at 4 before the offer
                if ln.startswith("TRB ") and '"button": 8' in ln:
                    d = json.loads(ln[4:])
                    d["pl"][0]["st"] = 4
                    L.lines[k] = "TRB " + json.dumps(d)
        chk, _, out = run(t1_log(m))
        self.assertIn("R-button8/nostate", [r for _, _, r, _ in chk.mismatches], out)

    def test_commit_messages(self):
        def m(L):
            L.lines = [ln for ln in L.lines if not ln.startswith("TMS ")]
        chk, _, out = run(t1_log(m))
        self.assertIn("R-commit/donemsgs", [r for _, _, r, _ in chk.mismatches], out)

    def test_show_cell_mutation(self):
        def m(L):
            replace_tag(L, "TSP", lambda d: d["copy_item"].__setitem__(3, 0))
        chk, _, out = run(t1_log(m))
        self.assertIn("R-show/cell", [r for _, _, r, _ in chk.mismatches], out)

    def test_unmet_expectation(self):
        chk, unmet, out = run(t1_log(), case="T4")
        self.assertIn(("T4", "E-room"), unmet)

    def test_tick_delay(self):
        L = Log()
        inv = {str(H): [], str(J): []}
        h = plr(H, 8, rec=1, partner=J, lk=123456)
        j = plr(J, 3, rec=2, partner=H)
        L.ev("TTK", [h, j], inv, p=H, site=1)
        h11 = dict(h, st=11, b22=0)
        L.ev("TTKR", [h11, j], inv, p=H, site=1, eax=0)
        L.f += 125
        L.ev("TTK", [h11, j], inv, p=H, site=1)
        L.ev("TTKR", [h11, j], inv, p=H, site=1, eax=0)
        L.f += 25
        L.ev("TTK", [h11, j], inv, p=H, site=1)
        h3 = dict(h11, st=3, lk=0, b23=0)
        L.ev("TTKR", [h3, j], inv, p=H, site=1, eax=0)
        chk, _, out = run(L, case="x")
        self.assertEqual(chk.mismatches, [], out)
        L.lines[2] = L.lines[2].replace('"f": 225', '"f": 224')     # the second tick one frame early
        chk, _, out = run(L, case="x")
        self.assertIn("R-tick/delay", [r for _, _, r, _ in chk.mismatches], out)

    def test_cancel_restores(self):
        L = Log()
        open_inv = [[101, WND, 0, 0, 0, 0, 1]]
        L.ev("TRA", [plr(H, 3, 100, rec=1, partner=J)], {str(H): open_inv}, p=H, ok=1)
        before = {str(H): [[101, WND, 2, 3, 0, 4, 1]], str(J): []}
        h = plr(H, 4, 100, rec=1, partner=J, off=0, g10=100)
        j = plr(J, 4, 50, rec=2, partner=H)
        L.ev("TCX", [h, j], before, a=J, b=H, site=0x00567E41)
        h1 = dict(h, st=5, b23=1)
        j1 = dict(j, st=5, b23=1)
        good = {str(H): [[150, WND, 0, 0, 0, 0, 1]], str(J): []}
        L.ev("TCXR", [h1, j1], good, a=J, b=H, site=0x00567E41, eax=0)
        chk, _, out = run(L, case="x")
        self.assertEqual(chk.mismatches, [], out)
        L.lines[-1] = L.lines[-1].replace("150", "101")         # an id kept through the restore
        chk, _, out = run(L, case="x")
        self.assertIn("R-cancel/newids", [r for _, _, r, _ in chk.mismatches], out)

    def test_marks_cut_cases(self):
        import harness_runner as hr
        L = t1_log()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "host.log")
            L.write(p)
            hr.mark(p[:-4], "T1", "start", log=None)            # line 0: the whole log is case T1
            out = []
            chk, unmet = tc.run_check(p, FakeItems(), out=out.append)
            self.assertTrue(any(o.startswith("CASE T1:") for o in out), out)
            self.assertEqual(unmet, [], out)


if __name__ == "__main__":
    unittest.main()

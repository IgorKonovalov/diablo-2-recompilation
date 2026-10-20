#!/usr/bin/env python3
"""Tests for tools/sweep_h2b.py (plan 0038 batch H2b): synthetic log lines through `logs`, one rule at a time.

    python3 -I tools/test_sweep_h2b.py
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
import sweep_h2b  # noqa: E402


def j(tag, **d):
    d.setdefault("th", 1)
    return "%s %s" % (tag, json.dumps(d))


def run(lines):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.log")
        with open(p, "w") as f:
            f.write("\n".join(lines) + "\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = sweep_h2b.main(["sweep_h2b.py", "logs", p])
        return rc, out.getvalue()


def seeds(g):
    g1 = rng.step(*g)
    g2 = rng.step(*g1)
    return g1, g2


def creation(g, unit=100, gs1_override=None, gs4_useed=None):
    g1, g2 = seeds(g)
    gs1 = dict(gseed=sweep_h2b.fmt(g2), unit=unit, utype=4, cls=10, useed=sweep_h2b.fmt((g1[0], 666)), u28=g1[0],
               iseed=sweep_h2b.fmt((g2[0], 666)), start=g2[0])
    if gs1_override:
        gs1.update(gs1_override)
    gs4 = dict(gs1)
    if gs4_useed:
        gs4["useed"] = gs4_useed
    return [j("GS0", ret=0x0055A6B4, arg=0, game=1, gseed=sweep_h2b.fmt(g), rec=2, idx=10, r2c=0, r48=0, r4c=0, exp=1),
            j("GS1", **gs1), j("GS2", **gs1), j("GS4", **gs4)]


class Seeds(unittest.TestCase):
    def test_model_holds(self):
        rc, out = run(["CPRE item=10 q=2 uidx=0 up=0 seed=00000001:00000002"] + creation((5, 7)) +
                      ["CPOST unit=00000064 seed=00000001:00000002 utype=4 uclass=10"])
        self.assertEqual(rc, 0, out)
        self.assertIn("drop creations: one ItemCreate call", out)

    def test_wrong_item_seed(self):
        rc, out = run(creation((5, 7), gs1_override={"iseed": "00000000:0000029a"}))
        self.assertEqual(rc, 1)
        self.assertIn("GS1 iseed", out)

    def test_gs4_differs_without_gs3(self):
        rc, out = run(creation((5, 7), gs4_useed="00000001:00000001"))
        self.assertEqual(rc, 1)
        self.assertIn("GS4 useed", out)

    def test_two_creations_in_one_drop(self):
        rc, out = run(["CPRE item=10 q=2 uidx=0 up=0 seed=00000001:00000002"] + creation((5, 7)) + creation((9, 9)) +
                      ["CPOST unit=00000064 seed=00000001:00000002 utype=4 uclass=10"])
        self.assertEqual(rc, 1)
        self.assertIn("2 GS0 lines", out)

    def test_unit_seed_stepped_outside_low(self):
        g = (5, 7)
        u = (11, 666)
        lines = [j("GQ0", gseed=sweep_h2b.fmt(g), unit=100, useed=sweep_h2b.fmt(u)),
                 j("BLD", k="magic", seed="0:0", q=4, rq=4, fi=0, start=0),
                 j("GQJ", gseed=sweep_h2b.fmt(g), unit=100, useed=sweep_h2b.fmt(rng.step(*u)))]
        rc, out = run(lines)
        self.assertEqual(rc, 1)
        lines[1] = j("BLD", k="low", seed="0:0", q=1, rq=1, fi=0, start=0)
        rc, out = run(lines)
        self.assertEqual(rc, 0, out)


class Builders(unittest.TestCase):
    def test_mbf_iff_both_zero(self):
        self.assertEqual(run([j("MB0", p=0, s=0), j("MBF")])[0], 0)
        self.assertEqual(run([j("MB0", p=0, s=5), j("MBF")])[0], 1)
        self.assertEqual(run([j("MB0", p=0, s=0), j("SSR")])[0], 1)

    def test_empty_name_scan_draws_nothing(self):
        a = j("RNE", v=1, n=0, iseed="00000001:0000029a")
        self.assertEqual(run([a, j("RNE", v=1, n=0, iseed="00000001:0000029a")])[0], 0)
        self.assertEqual(run([a, j("RNE", v=1, n=0, iseed="00000002:0000029a")])[0], 1)


class Tors(unittest.TestCase):
    def blk(self, exp, ms, sokr):
        I = sweep_h2b.Items(sweep_h2b.EXCEL)
        cls = next(i for i, r in enumerate(I.recs) if r["code"] == "qui")      # quilted armor, type tors
        lines = [j("IC0", cls=cls, q=0, exp=exp, ilvl=10, seed="00000001:0000029a", start=1),
                 j("SOK0", q=2, rfl=0, r44=0, seed="00000001:0000029a"), j("SOKM", ms=ms)]
        if sokr:
            lines.append(j("SOKR", r=50, seed="00000002:0000029a"))
        return lines + [j("ICJ", q=2, seed="00000003:0000029a"), j("ICX", ret=0)]

    def test_classic_reaching_the_test(self):
        rc, out = run(self.blk(0, 2, False))
        self.assertIn("reaching the tors test (SOKM ms > 0): yes, SOKR 0", out)

    def test_classic_roll_is_bad(self):
        rc, out = run(self.blk(0, 2, True))
        self.assertNotEqual(rc, 0)

    def test_expansion_control(self):
        rc, out = run(self.blk(1, 2, True))
        self.assertIn("control: expansion tors q2 past SOKM ms > 0, SOKR 1", out)


class Sockets(unittest.TestCase):
    def ss(self, q, n, p, cap, qcap, qn, maxs, ncap, w):
        out = [j("SS0", ret=0x00556C61, it=5, n=n, cls=0, q=q), j("SSP", p=p, cap=cap), j("SSQ", cap=qcap, n=qn),
               j("SSM", maxs=maxs, cap=qcap), j("SSN", cap=ncap, n=qn)]
        if w is not None:
            out.append(j("SSW", v=w))
        out.append(j("SSR"))
        return out

    def test_magic_clamp(self):
        # class 0 (hax) is 1 x 3 in the stock tables: p = 3
        self.assertEqual(run(self.ss(4, 6, 3, 3, 3, 6, 2, 2, 2))[0], 0)

    def test_superior_gets_no_quality_clamp(self):
        self.assertEqual(run(self.ss(3, 2, 3, 3, 2, 2, 2, 2, 2))[0], 1)

    def test_written_value(self):
        self.assertEqual(run(self.ss(2, 5, 3, 3, 3, 5, 2, 2, 3))[0], 1)


if __name__ == "__main__":
    unittest.main()

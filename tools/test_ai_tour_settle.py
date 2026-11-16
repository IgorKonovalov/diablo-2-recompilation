#!/usr/bin/env python3
"""Tests of tools/ai_tour_settle.py on synthetic inputs (no game data).

    python3 -I tools/test_ai_tour_settle.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai_tour_settle as S  # noqa: E402

MC = """ENTRY R9 think 005f0000 (inventory catalogue 1 (H1a)): decisions 40, ok 40 (fork-free 35, forked 5), mismatch 0, stop 0
  ARM 1.a true 10 false 25
  ARM 2.b true 35 false 0
  ARM 3.c true 0 false 35
  ARM set v14=0 true 35 false 0
  EDGE 1.a 2
  FLIP 1.a fail 35 of 35 (in the decision 35, at the next decision 0; stop 0)
  FLIP 2.b fail 3 of 35 (in the decision 3, at the next decision 0; stop 0)
  FLIP 3.c fail 0 of 35 (in the decision 0, at the next decision 0; stop 0)
  FLIP 4.d fail 0 of 0 (in the decision 0, at the next decision 0; stop 0)
  FLIP set v14=0 fail 1 of 35 (in the decision 0, at the next decision 1; stop 0)
  CONTROL le fail 2 of 35 (stop 0)
ENTRY R8 think 005f0700 (inventory catalogue 2 (H1a)): decisions 20, ok 20 (fork-free 20, forked 0), mismatch 0, stop 0
"""


def write(d, name, text):
    p = os.path.join(d, name)
    with open(p, "w") as fh:
        fh.write(text)
    return p


class Settle(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def test_classify(self):
        e = S.parse_model_check(write(self.d, "mc.txt", MC))["R9"]
        got = {n: c for n, c, *_ in S.classify(e)}
        self.assertEqual(got, {"1.a": "sep2", "2.b": "sep1-true", "3.c": "nosep", "4.d": "unrun", "set v14=0": "sep"})
        self.assertEqual(e["edge"], {"1.a": 2})

    def test_floor(self):
        p = write(self.d, "mc.txt", MC)
        o = os.path.join(self.d, "o.txt")
        S.main(["entries", p, "--out", o])
        text = open(o).read()
        self.assertIn("ENT R9 think 005f0000 dec 40 ff 35 forked 5 mm 0 stop 0 floor met", text)
        self.assertIn("ENT R8 think 005f0700 dec 20 ff 20 forked 0 mm 0 stop 0 floor not met", text)

    def test_h1(self):
        r = write(self.d, "r.txt", "RROW 7 th=005efb80 decisions=60 resumed_ok=60 mismatches=0 stopped=0 boundaries_matched=9 "
                                   "past_first=5 ambiguous_steps=0/5 distinct_logged_prefixes4=2\n"
                                   "RROW 8 th=005f0700 decisions=60 resumed_ok=59 mismatches=1 stopped=0 boundaries_matched=9 "
                                   "past_first=5 ambiguous_steps=0/5 distinct_logged_prefixes4=2\n")
        f = write(self.d, "f.txt", "FREE 7@5efb80 decisions=55 sampled=55 sites=3 sep=3 nosep=0 two_way=2 two_way_sep=2\n"
                                   "FREEPAST 7@5efb80 decisions=55 past_first=4 decisions_with_past=4 rows=7\n"
                                   "FREE 8@5f0700 decisions=55 sampled=55 sites=3 sep=2 nosep=1 two_way=2 two_way_sep=1\n"
                                   "FREEPAST 8@5f0700 decisions=55 past_first=0 decisions_with_past=0 rows=\n")
        o = os.path.join(self.d, "o.txt")
        S.main(["h1", r, f, "--out", o])
        lines = open(o).read().splitlines()
        self.assertTrue(lines[0].startswith("H1 7@5efb80") and lines[0].endswith("; met"))
        self.assertTrue(lines[1].endswith("not met: mismatch0, past>=1, twoway"))

    def test_inits(self):
        cw0 = "00" * 0x40
        cw1 = bytearray(0x40)
        cw1[0x14] = 0x68
        aii = {"u": 1, "id": 1, "c": 206, "fn": 0x5F6630, "ctl": 2, "st": 0, "cw": cw0, "fr": 0x68}
        aiq = {"u": 1, "ctl": 2, "cw": bytes(cw1).hex()}
        p = write(self.d, "a.log", "AII %s\nAIQ %s\n" % (json.dumps(aii), json.dumps(aiq)))
        o = os.path.join(self.d, "o.txt")
        S.main(["inits", p, "--out", o])
        self.assertIn("INIT 005f6630 pairs 1 in 1 logs; v14 = T after 1 (word before differs 1); v18 = 0 after 1 "
                      "(word before differs 0)", open(o).read())

    def test_tally_and_ready(self):
        inv = ("| # | Line | Section | Claim | Anchor | Class | Route | Batch | Count |\n"
               "| 1 | 10 | R9. Row 9 | x | – | a-run | route **Raised 2026-11-16 (`lane/n69g`, plan 0069 Phase 4; run:x).** "
               "paths a, b | H1a | 1 |\n"
               "| 2 | 11 | R9. Row 9 | y | – | a-run | route **Raised in part 2026-11-16 (`lane/n69g`, plan 0069 Phase 4; "
               "run:x).** path c | H1a | 1 |\n"
               "| 3 | 12 | R9. Row 9 | z | – | b | a `|` b **Kept `[I]` 2026-11-16 (`lane/n69g`, plan 0069 Phase 4).** "
               "not reached | H1h | 1 |\n"
               "| 4 | 13 | R9. Row 9 | w | – | c | other | S1f | 1 |\n")
        p = write(self.d, "inv.md", inv)
        o = os.path.join(self.d, "o.txt")
        S.main(["tally", p, "--out", o])
        text = open(o).read()
        self.assertIn("TALLY H1a stmts 2 raised 1 raised-in-part 1 kept 0 unsettled 0", text)
        self.assertIn("TALLY H1h stmts 1 raised 0 raised-in-part 0 kept 1 unsettled 0", text)
        self.assertIn("TOTAL stmts 3 raised 1 raised-in-part 1 kept 1 unsettled 0", text)
        S.main(["ready", p, "--out", o])
        lines = open(o).read().splitlines()
        self.assertEqual(lines[0], "READY row 1 line 10 R9. Row 9: raised; paths a, b")
        self.assertEqual(lines[1], "READY row 2 line 11 R9. Row 9: raised in part; path c")
        self.assertEqual(lines[2], "READY total 2")


if __name__ == "__main__":
    unittest.main()

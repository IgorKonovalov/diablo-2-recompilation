#!/usr/bin/env python3
"""Tests for tools/sweep_h2a.py `logs` on synthetic tc-h2a.gdb lines (plan 0038 batch H2a). Needs the stock excel
tables under workspace/merged (the `gld` record and the item types). Run: python3 -I tools/test_sweep_h2a.py"""
import os
import sys
import tempfile
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import quality  # noqa: E402
import sweep_h2a  # noqa: E402

T = quality.Tables(quality.EXCEL)
GLD = [i for i in range(len(T.items)) if T.items[i][0x80:0x84] == b"gld "][0]

DEATH = """MDD0 ret=005a702c mon=0a000000 cls=19 c4=00002003
MDDB bit17=0
MDDC coll=0000
MDDX
MDI ret=005a68d6 mon=0a000000 nonodrop=0
DROP base=430 lvl=0 src=0a000000
"""


def call(body, nonodrop=0, stype=1, pover=8, g6a=3):
    return ("TCR src=0a000000 stype=%d sclass=19 seed=1:2 killer=0b000000 tc=430 fq=0 ilvl=1 nonodrop=%d max=0 "
            "g6a=%d diff=0 exp=1 pover=%d mflags=00 suid=0 ktype=0 kclass=1\nPARTY party=1\nPLAYERS players=%d\n%s"
            "TCEND count=1 seed=1:2\n" % (stype, nonodrop, g6a, pover, max(1, pover) if g6a in (1, 2, 3) else 1, body))


def gold_unit(gold=100, factor=540, v=None, count=1, mx=6, kgf=440):
    v = quality.cdiv(gold * factor, 100) if v is None else v
    s = ("CPOST unit=0c000000 seed=1:2 utype=4 uclass=%d\nGTY unit=0c000000 uclass=%d is4=1\nGMAX count=%d max=%d\n"
         % (GLD, GLD, count, mx))
    if count < mx:
        s += ("GF0 ret=0055af5e killer=0b000000 unit=0c000000\nGF1 type=4\nGF2 kgf=%d\nGF3 owner=00000000\n"
              "GF5 gold=%d factor=%d\nGF6 v=%d\n" % (kgf, gold, factor, v))
    return s


def run(text):
    with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
        f.write(text)
    tot, bad = Counter(), []
    try:
        sweep_h2a.check_log(f.name, T, GLD, tot, bad)
    finally:
        os.unlink(f.name)
    return tot, bad


class T1(unittest.TestCase):
    def test_gold_find_ok(self):
        tot, bad = run(DEATH + call(gold_unit()))
        self.assertEqual(bad, [])
        self.assertEqual(tot["gold find products reproduced"], 1)

    def test_gold_find_wrong_product(self):
        _, bad = run(DEATH + call(gold_unit(v=541)))
        self.assertTrue(any("gold find" in b for b in bad))

    def test_max_skips_gold_find(self):
        tot, bad = run(DEATH + call(gold_unit(count=6, mx=6)))
        self.assertEqual(bad, [])
        self.assertEqual(tot["max reached on a gold unit"], 1)

    def test_gold_find_after_max_fails(self):
        text = DEATH + call(gold_unit(count=6, mx=6) + "GF0 ret=0055af5e killer=0b000000 unit=0c000000\n")
        _, bad = run(text)
        self.assertTrue(any("max" in b for b in bad))

    def test_bit17_skip(self):
        text = "MDD0 ret=005a702c mon=0a000000 cls=19 c4=04022003\nMDDB bit17=1\n" + call("")
        tot, bad = run(text)
        self.assertEqual(bad, [])
        self.assertEqual(tot["death drop skipped: bit 17"], 1)

    def test_bit17_disagrees(self):
        _, bad = run("MDD0 ret=005a702c mon=0a000000 cls=19 c4=00002003\nMDDB bit17=1\n")
        self.assertTrue(any("bit 17" in b for b in bad))

    def test_mdi_after_skip_fails(self):
        text = ("MDD0 ret=005a702c mon=0a000000 cls=19 c4=04022003\nMDDB bit17=1\n"
                "MDI ret=005a68d6 mon=0a000000 nonodrop=0\n")
        _, bad = run(text)
        self.assertTrue(bad)

    def test_players_override_only_types_1_3(self):
        _, bad = run(DEATH + call("", g6a=0))
        self.assertEqual(bad, [])
        text = DEATH + call("", g6a=0).replace("PLAYERS players=1", "PLAYERS players=8")
        _, bad = run(text)
        self.assertTrue(any("PLAYERS" in b for b in bad))

    def test_nonodrop_range(self):
        body = "NDP ndp=100 total=60\nPICK range=60 roll=52 ndp=100 seed=1:2\nSEL i=1\n"
        text = ("CFI ret=0056f96a\nMNN ret=005d8894 ecx=0 mon=0a000000\nMDI ret=005a801c mon=0a000000 nonodrop=1\n"
                "DROP base=430 lvl=0 src=0a000000\n" + call(body, nonodrop=1))
        tot, bad = run(text)
        self.assertEqual(bad, [])
        self.assertEqual(tot["nonodrop with nd' > 0"], 1)
        _, bad = run(text.replace("range=60", "range=160"))
        self.assertTrue(bad)


if __name__ == "__main__":
    unittest.main()

"""Synthetic tests for the plan 0038 batch S2a pieces: python3 -I tools/test_tc_sweep.py

No game file is read: the TCs, the PE image and the item tables are built in memory.
  - tc.nodrop_scaled / nodrop_ptq on the worked example of items/tc (100, 60, n = 4 -> 10) and an n = 1 pass-through;
  - tc_sweep.classic_sel: with and without the skip of expansion-only entries the classic scan returns the same entry
    for every roll of a TC whose entries mix classic and expansion-only ones, and never runs off the end;
  - tc.replay_call: a one-pick call replays, and its counterfactual switches change the result where they should
    (nomax ends a capped call later; nopop drops the parent's remaining pick);
  - xrefscan.scan: a rel32 call, a jcc and an absolute pointer to the target are found, a call elsewhere is not.
"""
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
import tc  # noqa: E402
import tc_sweep  # noqa: E402
import xrefscan  # noqa: E402


def entries(spec):
    """[(prob, exponly)] -> runtime entries with cumClassic/cumExp as tc.Tables.add builds them."""
    t = tc.Tables.new_tc("x", 1, 0, 0, [0] * 6, 0)
    for k, (p, x) in enumerate(spec):
        tc.Tables.add(t, k + 1, tc.F_EXPONLY if x else 0, p)
    return t


class NoDrop(unittest.TestCase):
    def test_worked_example(self):
        self.assertEqual(tc.nodrop_scaled(100, 60, 4, 53), 10)
        self.assertEqual(tc.nodrop_ptq(100, 60, 4, 53), 10)
        self.assertEqual(tc.nodrop_scaled(125, 38, 4, 53), 20)

    def test_n1_unscaled(self):
        self.assertEqual(tc.nodrop_scaled(100, 60, 1, 53), 100)
        self.assertEqual(tc.nodrop_ptq(100, 60, 1, 53), 100)


class ClassicScan(unittest.TestCase):
    def test_skip_is_invisible(self):
        for spec in ([(3, 1), (2, 0), (4, 1), (5, 0), (1, 1)], [(2, 0), (3, 1), (3, 1)], [(1, 1), (7, 0)],
                     [(4, 0), (4, 0), (2, 1)]):
            t = entries(spec)
            for roll in range(t["tclassic"]):
                a = tc_sweep.classic_sel(t["entries"], roll, True)
                b = tc_sweep.classic_sel(t["entries"], roll, False)
                self.assertEqual(a, b, (spec, roll))
                self.assertLess(a, len(t["entries"]))
                self.assertFalse(t["entries"][a]["flags"] & tc.F_EXPONLY)


class FakeT:
    """A runtime TC table of three TCs for replay_call: 1 = two picks over sub-TC 2 then item 7; 2 = one item 5."""
    n_auto_types = 0

    def __init__(self):
        self.items = [dict(version=0, type=0) for _ in range(10)]
        self.itypes = [dict(throwable=0)]
        t1 = tc.Tables.new_tc("root", 2, 0, 0, [0] * 6, 0)
        tc.Tables.add(t1, 2, tc.F_TC, 1)
        t2 = tc.Tables.new_tc("sub", 1, 0, 0, [0] * 6, 0)
        tc.Tables.add(t2, 5, 0, 1)
        self.tcs = [None, t1, t2]


def call_lines(seed, picks):
    """TCR .. TCEND lines of one call with forced quality 2: each pick draws Range(1) -> 0 on the source seed."""
    lo, hi = seed
    out = [("TCR", dict(seed="%08x:%08x" % (lo, hi), exp="1", nonodrop="0", max="1", fq="2", stype="1", sclass="0",
                        tc="1", ilvl="1", diff="0"))]
    made = 0
    for k in range(picks):
        out.append(("NDP", dict(ndp="0")))
        _, lo, hi = rng.rng_range(lo, hi, 1)
        out.append(("PICK", dict(roll="0", seed="%08x:%08x" % (lo, hi))))
        out.append(("SEL", dict(i="0")))
        out.append(("SUB", dict(tc="2")))
        out.append(("NDP", dict(ndp="0")))
        _, lo, hi = rng.rng_range(lo, hi, 1)
        out.append(("PICK", dict(roll="0", seed="%08x:%08x" % (lo, hi))))
        out.append(("SEL", dict(i="0")))
        out.append(("QOUT", dict(q="2", seed="%08x:%08x" % (lo, hi))))
        out.append(("CPRE", dict(item="5", q="2", uidx="0", up="0", seed="%08x:%08x" % (lo, hi))))
        out.append(("CPOST", dict(unit="1", seed="%08x:%08x" % (lo, hi))))
        made += 1
    out.append(("TCEND", dict(count=str(made), seed="%08x:%08x" % (lo, hi))))
    return out


class Replay(unittest.TestCase):
    def test_two_picks_and_pop(self):
        T = FakeT()
        call = call_lines((0x1234, 0x29A), 2)
        call[0][1]["max"] = "0"           # max < 1: 6
        st = {}
        s = tc.replay_call(T, call, st=st)
        self.assertEqual(s["count"], 2)
        self.assertEqual(st["push.new"], 1)   # first pick: the root still has a pick, so a new frame
        self.assertEqual(st["push.tail"], 1)  # second pick: the root has none left, the frame is reused
        self.assertEqual(st["pop.parent_resumes"], 1)
        with self.assertRaises(tc.Mismatch):
            tc.replay_call(T, call, cf={"nopop": True})

    def test_max_stop(self):
        T = FakeT()
        call = call_lines((0x1234, 0x29A), 1)  # max 1: the first item ends the call, one pick left at the root
        st = {}
        tc.replay_call(T, call, st=st)
        self.assertEqual(st["max.reached.picks_left"], 1)


class XrefScan(unittest.TestCase):
    def test_hits(self):
        base, va = 0x400000, 0x1000
        target = 0x401050
        code = bytearray(0x100)
        at = 0x10                         # call target
        struct.pack_into("<Bi", code, at, 0xE8, target - (base + va + at + 5))
        at2 = 0x30                        # jne target
        code[at2:at2 + 2] = b"\x0f\x85"
        struct.pack_into("<i", code, at2 + 2, target - (base + va + at2 + 6))
        at3 = 0x60                        # call elsewhere
        struct.pack_into("<Bi", code, at3, 0xE8, 0x10)
        struct.pack_into("<I", code, 0x80, target)   # a pointer
        data = bytes(0x1000) + bytes(code)
        secs = [dict(name=".text", raw=0x1000, rsize=len(code), vsize=len(code), va=va, flags=0x20000000)]
        hits = xrefscan.scan(data, base, secs, target)
        kinds = sorted((k, a - base - va) for k, a, _ in hits)
        self.assertEqual(kinds, [("abs32 in .text", 0x80), ("call", 0x10), ("jcc", 0x30)])


if __name__ == "__main__":
    unittest.main()

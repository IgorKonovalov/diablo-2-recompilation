"""Tests of tools/sweep2_s4cd.py (plan 0066 batches S4c and S4d): the helpers on synthetic input, and with workspace/
the r2 helpers on known sites of the pinned image (a good and a bad case each). No game is run.
Stdlib only (r2 and objdump for the image tests):
    python3 -I tools/test_sweep2_s4cd.py
"""
import base64
import json
import os
import shutil
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep2_s4cd as T  # noqa: E402

HAVE_EXE = os.path.exists(T.EXE) and shutil.which("r2") is not None and shutil.which("objdump") is not None


class Pure(unittest.TestCase):
    def test_imm(self):
        self.assertEqual(T.imm("0x3e01"), 0x3E01)
        self.assertEqual(T.imm("12"), 12)
        self.assertIsNone(T.imm("ecx"))

    def test_jl_and_unz(self):
        blob = base64.b64encode(zlib.compress(json.dumps([1, 2]).encode())).decode()
        self.assertEqual(T.unz(blob), [1, 2])
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as fh:
            fh.write('PKT {"op": 23}\nnoise line\nBAD {not json\n')
            p = fh.name
        try:
            self.assertEqual(list(T.jl(p)), [("PKT", {"op": 23})])
        finally:
            os.unlink(p)

    def test_rep_counts_bad(self):
        r = T.Rep("t", "x")
        r.add("ok", 3)
        self.assertEqual(r.c["bad"], 0)
        r.add("bad")
        self.assertEqual(r.c["bad"], 1)

    def test_rcg_summary(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write("0x00555DA0 622 summary: functions=567 rng=0 unclassified=0 indirect=54\nfn 0x1 x\n")
            p = fh.name
        try:
            self.assertEqual(T.rcg_summary(p), {0x00555DA0: (567, 0, 0, 54)})
        finally:
            os.unlink(p)


@unittest.skipUnless(HAVE_EXE, "needs workspace/ (the pinned image), r2 and objdump")
class Image(unittest.TestCase):
    def test_callee_pop(self):
        self.assertEqual(T.callee_pop(0x0055E9A0), 8)          # UnstackStub: xor eax, eax; ret 8
        self.assertNotEqual(T.callee_pop(0x0055E9A0), 0)

    def test_pushes_skip_an_inner_stdcall(self):
        # DropCreateItem's search call: 1, 1 pushed before a stdcall (0x00620BB0) whose own push is skipped
        p = T.pushes_before(0x0055A5AD, want=3)
        self.assertEqual(p[1:3], ["1", "1"])
        # the pair form at DropGoldAmount: fallback 0; at DropGoldPile: fallback 1
        self.assertEqual(T.pushes_before(0x0055A15C, want=8)[6], "0")
        self.assertEqual(T.pushes_before(0x005593F7, want=8)[6], "1")

    def test_owner(self):
        self.assertEqual(T.owner(0x0055A5AD)[0], 0x0055A550)
        self.assertNotEqual(T.owner(0x0055A5AD)[0], 0x0055A5AD)

    def test_r2_bytes_page_sizes(self):
        self.assertEqual(tuple(T.r2_bytes(0x0074479C, 2)), (13, 1))
        self.assertNotEqual(tuple(T.r2_bytes(0x007447B4, 2)), (13, 1))


if __name__ == "__main__":
    unittest.main()

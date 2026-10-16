"""Unit tests of the pure helpers of tools/sweep_s1b.py (no game files needed). Run: python3 -I tools/test_sweep_s1b.py"""
import contextlib
import io
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s1b as S  # noqa: E402


class T(unittest.TestCase):
    def test_step_matches_the_lcg(self):
        self.assertEqual(S.step(1, 666), (0x6AC6935F, 0))
        lo, hi = S.step(0xFFFFFFFF, 0xFFFFFFFF)
        v = 0xFFFFFFFF * 0x6AC690C5 + 0xFFFFFFFF
        self.assertEqual((lo, hi), (v & 0xFFFFFFFF, v >> 32))

    def test_line_parsers(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.log")
            with open(p, "w") as f:
                f.write('CE {"pool":"itemscode","off":3}\nCE not json\nROOM level=1 type=2 r04=ab\nX {"a":1}\n')
            self.assertEqual(list(S.jlines(p, ("CE",))), [("CE", {"pool": "itemscode", "off": 3})])
            self.assertEqual(list(S.kvlines(p, ("ROOM",))), [("ROOM", {"level": "1", "type": "2", "r04": "ab"})])

    def test_bin_recs(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.bin")
            with open(p, "wb") as f:
                f.write(struct.pack("<I", 2) + b"abcdef")
            n, rs, recs = S.bin_recs(p)
            self.assertEqual((n, rs, recs), (2, 3, [b"abc", b"def"]))

    def test_tc_indices(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "tc.log")
            with open(p, "w") as f:
                f.write("TCR src=1 tc=430 fq=0\nSUB tc=218\nSUB tc=218\nDROP base=0 lvl=0\nPICK range=3\n")
            c = S.tc_indices(p)
            self.assertEqual(c, {("TCR", 430): 1, ("SUB", 218): 2, ("DROP", 0): 1})

    def test_mirror_overrides_and_counts(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src")
            os.makedirs(os.path.join(src, "A"))
            for n in ("A/one.ds1", "two.txt"):
                with open(os.path.join(src, n), "w") as f:
                    f.write("src")
            alt = os.path.join(d, "alt.ds1")
            with open(alt, "w") as f:
                f.write("alt")
            dst = os.path.join(d, "dst")
            n = S.mirror(dst, src, {os.path.join("a", "one.ds1"): alt})
            self.assertEqual(n, 1)
            self.assertEqual(open(os.path.join(dst, "A", "one.ds1")).read(), "alt")
            self.assertEqual(open(os.path.join(dst, "two.txt")).read(), "src")

    def test_report_exit_status(self):
        R = S.Report("x")
        R.add("n", 2)
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(R.done(), 0)
        self.assertIn("S1B x bad=0 n=2", buf.getvalue())
        R.expect(False, "why")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(R.done(), 1)


if __name__ == "__main__":
    unittest.main()

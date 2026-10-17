"""Unit tests of the pure helpers of tools/sweep_s2c.py (no game files needed). Run: python3 -I tools/test_sweep_s2c.py"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sweep_s2c as X  # noqa: E402
import sweep_s4b as S4  # noqa: E402


class FakeAsm:
    def __init__(self, ins):
        self.ins = ins
        self._s = sorted(ins)

    def at(self, va):
        return self.ins.get(va)

    def next_va(self, va):
        for x in self._s:
            if x > va:
                return x
        return None


LISTING = """
00401000 <.text>:
  401000:\tsub    eax,0x93
  401005:\tje     0x401020
  401007:\tcmp    eax,0x2
  40100a:\tja     0x401030
  40100c:\tpush   0x7
  40100e:\tjmp    0x401020
  401020:\tmov    DWORD PTR [esi-0x8],0x1
  401027:\tret
  401030:\tret
"""

LISTING_CLOBBER = """
00402000 <.text>:
  402000:\tcmp    eax,0x1
  402003:\t%s
  402005:\tje     0x402010
  402007:\tjmp    0x402011
  402010:\tret
  402011:\tret
"""


class T(unittest.TestCase):
    def test_magic_exact(self):
        self.assertTrue(X.magic_exact(0xCCCCCCCD, 34, 5))           # unsigned / 5
        self.assertTrue(X.magic_exact(0x124924925, 35, 7))          # unsigned / 7 (the add-indicator form)
        self.assertFalse(X.magic_exact(0xCCCCCCCC, 34, 5))
        for n in (0, 1, 4, 5, 6, 0x7FFFFFFF, 0xFFFFFFFF, 123456789):
            self.assertEqual((n * 0xCCCCCCCD) >> 34, n // 5)
            self.assertEqual((n * 0x124924925) >> 35, n // 7)

    def test_set_sockets_model(self):
        # a normal 2 x 3 base: no quality clamp, the request below the cap
        self.assertEqual(X.set_sockets_model(2, 2, 3, 4, 3, 0), (3, "request"))
        # magic: 4 at most
        self.assertEqual(X.set_sockets_model(4, 2, 4, 6, 6, 0)[0], 4)
        # rare 2, crafted 3
        self.assertEqual(X.set_sockets_model(6, 2, 4, 6, 6, 0)[0], 2)
        self.assertEqual(X.set_sockets_model(8, 2, 4, 6, 6, 0)[0], 3)
        # set/unique with a current count keep it; without, 1
        self.assertEqual(X.set_sockets_model(7, 2, 4, 6, 1, 3)[0], 3)
        self.assertEqual(X.set_sockets_model(7, 2, 4, 6, 4, 0)[0], 1)
        # ItemMaxSockets 0: nothing written
        self.assertEqual(X.set_sockets_model(2, 2, 3, 0, 2, 0)[0], 0)
        # a request of 0 becomes 1
        self.assertEqual(X.set_sockets_model(2, 2, 3, 4, 0, 0)[0], 1)

    def test_s32v_and_imm(self):
        self.assertEqual(X.s32v(0xFFFFFFFF), -1)
        self.assertEqual(X.s32v(5), 5)
        self.assertEqual(X.imm("0x3c"), 0x3C)
        self.assertIsNone(X.imm("eax"))

    def test_emu_dispatch(self):
        A = FakeAsm(S4.parse_listing(LISTING))
        old = S4.asm
        S4.asm = lambda: A
        try:
            stop, R, pushes, calls, stores = X.emu(0x401000, {"eax": 0x93}, {0x401027, 0x401030})
            self.assertEqual(stop, 0x401027)
            self.assertEqual(stores, [("DWORD PTR [esi-0x8]", 1)])
            stop, R, pushes, _, _ = X.emu(0x401000, {"eax": 0x94}, {0x401027, 0x401030})
            self.assertEqual((stop, pushes), (0x401027, [7]))
            stop = X.emu(0x401000, {"eax": 0x96}, {0x401027, 0x401030})[0]       # 3 > 2: ja
            self.assertEqual(stop, 0x401030)
            stop = X.emu(0x401000, {"eax": 0x10}, {0x401027, 0x401030})[0]       # below 0x93: unsigned wrap, ja
            self.assertEqual(stop, 0x401030)
        finally:
            S4.asm = old

    def test_emu_flag_clobber(self):
        # a cmp, then an unmodelled flag setter: the jcc after it must raise, not reuse the cmp's flags
        for clob in ("test   eax,eax", "and    eax,0x1", "or     eax,0x1", "xor    eax,ecx", "shl    eax,0x2",
                     "inc    eax", "dec    eax", "neg    eax", "imul   eax,eax,0x3", "adc    eax,0x0", "sbb    eax,eax",
                     "cmp    DWORD PTR [ecx],0x1", "sub    DWORD PTR [ecx],0x1", "call   0x402010"):
            A = FakeAsm(S4.parse_listing(LISTING_CLOBBER % clob))
            old = S4.asm
            S4.asm = lambda: A
            try:
                with self.assertRaises(X.EmuError, msg=clob):
                    X.emu(0x402000, {"eax": 1, "ecx": 2}, {0x402010, 0x402011})
            finally:
                S4.asm = old
        # a self xor still sets known flags (result 0)
        A = FakeAsm(S4.parse_listing(LISTING_CLOBBER % "xor    eax,eax"))
        old = S4.asm
        S4.asm = lambda: A
        try:
            self.assertEqual(X.emu(0x402000, {"eax": 1}, {0x402010, 0x402011})[0], 0x402010)
        finally:
            S4.asm = old

    def test_tcr_ilvl(self):
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False) as f:
            f.write("TCR src=1 stype=1 sclass=156 seed=0:0 ilvl=12 tc=5\n")
            f.write("TCR src=2 stype=2 sclass=9 ilvl=3\n")
            f.write("QS {\"w\": 1}\n")
            path = f.name
        try:
            self.assertEqual(dict(X.tcr_ilvl(path)), {156: [12]})
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

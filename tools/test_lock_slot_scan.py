"""Synthetic listings for tools/lock_slot_scan.py: each case is a wrong dependency the walk must see, or an idiom it must not call a read."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lock_slot_scan as s

SLOT = 0x6CC218


def listing(*body):
    """(addr, text) pairs, or text at consecutive addresses from 0x1000; every instruction takes 4 units."""
    out, a = [], 0x1000
    for t in body:
        if isinstance(t, tuple):
            a, t = t
        out.append("  %x:\t%s" % (a, t))
        a += 4
    out.append("  %x:\tint3" % a)
    return s.Listing(text="\n".join(out))


def walk(*body, root=0x1000, start=0x1004):
    L = listing(*body)
    imports = {SLOT: ("KERNEL32.dll", "EnterCriticalSection"), 0x6CC300: ("KERNEL32.dll", "Other")}
    regs = s.slot_regs(L, imports)
    G = s.Graph(L, imports)
    clo = G.closure([root])
    w = s.Walker(L, G, imports, regs, {SLOT}, [root], scope=clo)
    reads, opens, ends = w.walk(start)
    m = 0
    for v in reads.values():
        m |= v[0]
    return m, opens, ends


CALL = "call   DWORD PTR ds:0x6cc218"


class Reads(unittest.TestCase):
    def test_direct_read(self):
        self.assertTrue(walk(CALL, "test   eax,eax", "ret")[0] & 0xF)

    def test_written_first(self):
        m, _, ends = walk(CALL, "mov    eax,0x1", "mov    ecx,0x1", "mov    edx,0x1", "cmp    eax,ecx", "ret")
        self.assertEqual(m & 0xFFF, 0)
        self.assertFalse(ends)

    def test_partial_write_leaves_the_upper_bytes(self):
        self.assertTrue(walk(CALL, "mov    al,0x1", "test   eax,eax", "ret")[0] & 0xF)

    def test_partial_then_al_only_is_no_read(self):
        self.assertFalse(walk(CALL, "mov    al,0x1", "test   al,al", "mov    eax,0x0", "mov    ecx,0x1", "mov    edx,0x1", "ret")[0] & 0xFFF)

    def test_zero_idiom(self):
        self.assertFalse(walk(CALL, "xor    eax,eax", "sub    ecx,ecx", "xor    edx,edx", "ret")[0] & 0xFFF)

    def test_memory_operand(self):
        self.assertTrue(walk(CALL, "mov    esi,DWORD PTR [edx+0x4]", "ret")[0] & 0xF00)

    def test_store(self):
        self.assertTrue(walk(CALL, "mov    DWORD PTR [esi],ecx", "ret")[0] & 0xF0)

    def test_shift_by_cl(self):
        self.assertTrue(walk(CALL, "shl    esi,cl", "ret")[0] & 0xF0)

    def test_rep_stos(self):
        self.assertEqual(walk(CALL, "rep stos DWORD PTR es:[edi],eax", "ret")[0] & 0xFF, 0xFF)

    def test_cdq_and_idiv(self):
        self.assertTrue(walk(CALL, "cdq", "ret")[0] & 0xF)
        self.assertTrue(walk(CALL, "idiv   esi", "ret")[0] & 0xF00)

    def test_unknown_mnemonic_fails_closed(self):
        self.assertTrue(walk(CALL, "xyzzy  ecx,esi", "ret")[0] & 0xF0)

    def test_flags(self):
        self.assertTrue(walk(CALL, "je     0x1010", "mov    eax,0x1", "int3", "int3")[0] & s.FLAGS)


class Flow(unittest.TestCase):
    def test_into_a_callee(self):
        m, _, _ = walk(CALL, "call   0x1020", "int3", "int3", "int3", "int3", "int3", (0x1020, "push   edx"), "ret")
        self.assertTrue(m & 0xF00)

    def test_back_from_a_callee(self):
        m, _, _ = walk(CALL, "call   0x1020", "test   eax,eax", "int3", "int3", "int3", "int3", (0x1020, "mov    ecx,0x1"), "ret")
        self.assertTrue(m & 0xF)
        self.assertFalse(m & 0xF0)

    def test_up_to_the_caller(self):
        # 0x1000 calls 0x1020, which takes the lock and returns: the caller reads EAX
        m, _, _ = walk("call   0x1020", "test   eax,eax", "int3", "int3", "int3", "int3", "int3", "int3", (0x1020, CALL), "ret", root=0x1000, start=0x1024)
        self.assertTrue(m & 0xF)

    def test_root_return_keeps_eax(self):
        _, _, ends = walk(CALL, "ret")
        self.assertTrue(ends)

    def test_second_lock_writes_nothing(self):
        self.assertTrue(walk(CALL, CALL, "test   eax,eax", "ret")[0] & 0xF)

    def test_other_import_ends_the_path(self):
        self.assertFalse(walk(CALL, "call   DWORD PTR ds:0x6cc300", "test   eax,eax", "ret")[0] & 0xF)

    def test_register_call_of_the_slot(self):
        L = listing("mov    esi,DWORD PTR ds:0x6cc218", "call   esi", "test   eax,eax", "ret")
        imports = {SLOT: ("K", "E")}
        self.assertEqual(s.slot_regs(L, imports), {0x1004: {SLOT}})
        self.assertEqual([a for a, _ in s.sites_of(L, s.slot_regs(L, imports), SLOT)], [0x1004])

    def test_indirect_call_is_open_not_a_pass(self):
        _, opens, _ = walk(CALL, "call   DWORD PTR [esi+0x4]", "ret")
        self.assertTrue(any("indirect" in v[1] for v in opens.values()))


if __name__ == "__main__":
    unittest.main()

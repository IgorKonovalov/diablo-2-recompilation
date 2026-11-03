"""No-game tests of tools/ai_resume.py (plan 0052 Phase 2, second run): the interpreter on a few hand-written instruction
streams (injected, so no game.exe and no objdump), then a decision resumed past its first boundary with a logged result.

    python3 -I tools/test_ai_resume.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai_resume as R  # noqa: E402

THINK, F1, F2, F3 = 0x1000, 0x2000, 0x3000, 0x4000     # the think function and three boundary functions
BND = {F1, F2, F3}
WIN = ((0x1000, 0x1100),)


def asm(base, lines):
    """{addr: (2, mnemonic, operands)}: every instruction two bytes long; `@name` at the start of a line is a label and
    `jxx @name` / `call @name` refer to it."""
    labels, addr = {}, base
    for ln in lines:
        if ln.startswith("@"):
            labels[ln.split()[0]] = addr
            ln = ln.split(None, 1)[1] if " " in ln else ""
        if ln:
            addr += 2
    out, addr = {}, base
    for ln in lines:
        if ln.startswith("@"):
            ln = ln.split(None, 1)[1] if " " in ln else ""
        if not ln:
            continue
        for k, v in labels.items():
            ln = ln.replace(k, "0x%x" % v)
        out[addr] = R.Code._parse(2, ln)
        addr += 2
    return out


def code_with(think_lines):
    ins = asm(THINK, think_lines)
    for f in BND:
        ins.update(asm(f, ["ret 0x4"]))
    return R.Code(inject=ins)


def aid(**kw):
    d = {"u": 0x1000000, "id": 9, "c": 5, "ai": 99, "st": 0, "th": THINK, "cx": 0x2000000, "g": 0x3000000,
         "mdp": 0x4000000, "ctlp": 0x5000000, "hp": 0, "md": 0, "m": 1, "c4": 0, "x": 10, "y": 20, "s0": "00000001:00000002",
         "s": "00000001:00000002", "fr": 100, "diff": 0, "ms": 0x6000000, "ms2": 734,
         "ctx": [0x5000000, 0, 0x7000000, 0, 0, 5, 1, 0x6000000, 0], "ctl": "00" * 0x40, "head": None,
         "aip": "00" * 48, "sk": "00" * 24, "ad": [0, 0], "t": [1, 7, 3, 1, 12, 22], "pl": [0, 0], "n": 10}
    d.update(kw)
    return d


def aib(n, fn, ra, a, s="00000001:00000002", ecx=None, edx=None):
    return {"k": 10, "fn": fn, "ra": ra, "ecx": ecx if ecx is not None else 0x3000000,
            "edx": edx if edx is not None else 0x1000000, "a": a + [0] * (6 - len(a)), "b": {}, "s": s, "c": [0, 0, 0],
            "c4": 0, "fr": 100, "n": n}


def air(b, eax, s="00000001:00000002"):
    return {"k": 10, "b": b, "n": b + 0.5, "eax": eax, "s": s, "c": [0, 0, 0], "c4": 0, "bl": {}}


# the think function: unit mode 1 calls F1(7); a result of 0 calls F2(1), else F3(2); then returns
THINK_CODE = [
    "push ebp", "mov ebp,esp", "push esi", "mov esi,edx",
    "cmp DWORD PTR [esi+0x10],0x1", "jne @out",
    "push 0x7", "call 0x2000", "@r1 test eax,eax", "je @zero",
    "push 0x2", "call 0x4000", "@r3 jmp @out",
    "@zero push 0x1", "call 0x3000", "@r2 jmp @out",
    "@out pop esi", "pop ebp", "ret 0x4",
]


def ra_of(code, target, nth=0):
    sites = sorted(a + 2 for a, (n, mn, ops) in code.ins.items() if mn == "call" and ops == ["0x%x" % target])
    return sites[nth]


class ResumeTest(unittest.TestCase):
    def setUp(self):
        self.code = code_with(THINK_CODE)
        self.m = R.Machine(self.code, BND, windows=WIN)
        self.ra1, self.ra2, self.ra3 = ra_of(self.code, F1), ra_of(self.code, F3), ra_of(self.code, F2)

    def dec(self, log, aids=None):
        return {"aid": aids or aid(), "aib": [b for b, r in log], "air": {b["n"]: r for b, r in log}, "log": "x",
                "bmax": 48}

    def test_first_boundary_and_a_branch_on_the_logged_result(self):
        b1 = aib(11, F1, self.ra1, [7])
        r = R.check_decision(self.m, self.dec([(b1, air(11, 0)), (aib(12, F2, self.ra3, [1]), air(12, 5))]))
        self.assertEqual((r.status, r.matched, r.end), ("ok", 2, True), r.why)
        r = R.check_decision(self.m, self.dec([(b1, air(11, 3)), (aib(12, F3, self.ra2, [2]), air(12, 5))]))
        self.assertEqual((r.status, r.matched, r.end), ("ok", 2, True), r.why)

    def test_the_result_decides_which_call_follows(self):
        b1 = aib(11, F1, self.ra1, [7])
        # result 0 -> F2; logging F3 after it is a mismatch, and so is a decision that ends when a call is due
        r = R.check_decision(self.m, self.dec([(b1, air(11, 0)), (aib(12, F3, self.ra2, [2]), air(12, 5))]))
        self.assertEqual(r.status, "mismatch", r.why)
        r = R.check_decision(self.m, self.dec([(b1, air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("offers another call", r.why)

    def test_a_wrong_argument_or_seed_is_a_mismatch(self):
        r = R.check_decision(self.m, self.dec([(aib(11, F1, self.ra1, [8]), air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("arg0", r.why)
        r = R.check_decision(self.m, self.dec([(aib(11, F1, self.ra1, [7], s="00000009:00000002"), air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("seed", r.why)

    def test_mode_not_1_returns_with_no_call(self):
        r = R.check_decision(self.m, self.dec([], aids=aid(m=4)))
        self.assertEqual((r.status, r.end), ("ok", True), r.why)
        r = R.check_decision(self.m, self.dec([(aib(11, F1, self.ra1, [7]), air(11, 0))], aids=aid(m=4)))
        self.assertEqual(r.status, "mismatch")

    def test_no_logged_result_is_a_stop_not_a_match(self):
        d = self.dec([(aib(11, F1, self.ra1, [7]), air(11, 0))])
        d["air"] = {}
        r = R.check_decision(self.m, d)
        self.assertEqual(r.status, "stop")
        self.assertIn("no AIR", r.why)

    def test_a_cap_says_so(self):
        d = self.dec([(aib(11, F1, self.ra1, [7]), air(11, 0)), (aib(12, F2, self.ra3, [1]), air(12, 0))])
        d["bmax"] = 2
        r = R.check_decision(self.m, d)
        self.assertEqual(r.status, "stop")
        self.assertIn("capped", r.why)

    def test_calls_made_inside_a_pending_boundary_call_are_not_offered(self):
        # the log holds F1's own AIB (n 11), a call made inside it (n 12, before F1's AIR at 11.5 ... here 13), F1's AIR (13)
        # and then F2: the nested line is dropped before matching
        b1 = aib(11, F1, self.ra1, [7])
        inner = aib(12, F3, 0x2222, [0])
        r1 = air(11, 0)
        r1["n"] = 13
        log = [(b1, r1), (inner, air(12, 0)), (aib(14, F2, self.ra3, [1]), air(14, 5))]
        d = self.dec(log)
        self.assertEqual([b["n"] for b in R.top_level(d)], [11, 14])
        r = R.check_decision(self.m, d)
        self.assertEqual((r.status, r.matched, r.end), ("ok", 2, True), r.why)

    def test_negative_control_inverts_the_known_branches(self):
        m = R.Machine(self.code, BND, invert=True, windows=WIN)
        b1 = aib(11, F1, self.ra1, [7])
        r = R.check_decision(m, self.dec([(b1, air(11, 0)), (aib(12, F2, self.ra3, [1]), air(12, 5))]))
        self.assertNotEqual(r.status, "ok")

    def test_unknown_values_fork_both_ways(self):
        # the unit's +0x40 is not in the logged inputs: a branch on it offers both calls and the log picks one
        code = code_with(["push ebp", "mov ebp,esp", "mov esi,edx", "cmp DWORD PTR [esi+0x40],0x0", "jne @b", "push 0x7",
                          "call 0x2000", "@b push 0x1", "call 0x3000", "pop ebp", "ret 0x4"])
        m = R.Machine(code, BND, windows=WIN)
        ra_f1, ra_f2 = ra_of(code, F1), ra_of(code, F2)
        d = self.dec([(aib(11, F2, ra_f2, [1]), air(11, 0))])
        r = R.check_decision(m, d)
        self.assertEqual((r.status, r.offers), ("ok", [2]), r.why)
        d = self.dec([(aib(11, F1, ra_f1, [7]), air(11, 0)), (aib(12, F2, ra_f2, [1]), air(12, 0))])
        r = R.check_decision(m, d)
        self.assertEqual((r.status, r.matched), ("ok", 2), r.why)

    def test_unsupported_instruction_is_a_stop(self):
        code = code_with(["push ebp", "mov ebp,esp", "fistp DWORD PTR [ebp-0x4]", "pop ebp", "ret 0x4"])
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([]))
        self.assertEqual(r.status, "stop")
        self.assertIn("unsupported", r.why)

    def test_a_drawn_seed_is_modelled(self):
        # one RNG step inline (the compiler's form: lo*0x6AC690C5 + hi), then a boundary call: the seed in the offered call
        code = code_with(["push ebp", "mov ebp,esp", "mov esi,edx", "mov eax,DWORD PTR [esi+0x20]", "mov edx,0x6ac690c5",
                          "mul edx", "mov ecx,eax", "mov eax,DWORD PTR [esi+0x24]", "xor ebx,ebx", "add ecx,eax", "adc edx,ebx",
                          "mov DWORD PTR [esi+0x24],edx", "mov DWORD PTR [esi+0x20],ecx", "mov ecx,esi", "mov edx,esi", "push 0x1", "call 0x3000", "pop ebp",
                          "ret 0x4"])
        lo, hi = 1, 2
        t = lo * 0x6AC690C5 + hi
        s1 = "%08x:%08x" % (t & 0xFFFFFFFF, t >> 32)
        ra = ra_of(code, F2)
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([(aib(11, F2, ra, [1], s=s1, ecx=0x1000000), air(11, 0, s=s1))]))
        self.assertEqual(r.status, "ok", r.why)
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([(aib(11, F2, ra, [1], ecx=0x1000000), air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("seed", r.why)


class PartsTest(unittest.TestCase):
    def test_flags_and_conditions(self):
        r, fl = R.alu("cmp", 5, 7, 4)
        self.assertEqual((r, fl["CF"], fl["ZF"], fl["SF"]), (0xFFFFFFFE, True, False, True))
        self.assertTrue(R.cond_value("jl", fl))
        self.assertTrue(R.cond_value("jb", fl))
        self.assertFalse(R.cond_value("jge", fl))
        r, fl = R.alu("add", 0xFFFFFFFF, 1, 4)
        self.assertEqual((r, fl["CF"], fl["ZF"]), (0, True, True))
        r, fl = R.alu("cmp", None, 7, 4)
        self.assertIsNone(R.cond_value("je", fl))

    def test_operand_parse(self):
        self.assertEqual(R.parse_op("DWORD PTR [ebx+ecx*2+0x56]"), ("m", 4, "ebx", "ecx", 2, 0x56))
        self.assertEqual(R.parse_op("WORD PTR [edi-0x4]"), ("m", 2, "edi", None, 1, -4))
        self.assertEqual(R.parse_op("al"), ("r", "eax", 1))

    def test_objdump_continuation_lines_extend_the_length(self):
        # objdump wraps an instruction's bytes after seven: the model must not read the second line as a new instruction
        c = R.Code(inject={})
        c.loaded = set()
        import subprocess
        real = subprocess.run
        sample = ("\n005f95ff <x>:\n  5f95ff:\t66 83 bf 70 01 00 00 \tcmp    WORD PTR [edi+0x170],0x0\n  5f9606:\t00 \n"
                  "  5f9607:\tc3                   \tret\n")

        class P:
            stdout = sample
        subprocess.run = lambda *a, **k: P()
        try:
            c._load(0x5f95ff)
        finally:
            subprocess.run = real
        self.assertEqual(c.ins[0x5f95ff][0], 8)
        self.assertEqual(c.ins[0x5f9607][1], "ret")


if __name__ == "__main__":
    unittest.main()

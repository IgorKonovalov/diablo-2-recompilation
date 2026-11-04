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


class FlipTest(unittest.TestCase):
    """tools/ai_resume_flip.py: one known branch reversed alone."""

    def test_one_branch_reversed_fails_only_where_it_decides(self):
        import ai_resume_flip as F
        code = code_with(THINK_CODE)
        ra1, ra2, ra3 = ra_of(code, F1), ra_of(code, F3), ra_of(code, F2)
        log = [(aib(11, F1, ra1, [7]), air(11, 0)), (aib(12, F2, ra3, [1]), air(12, 5))]
        dec = {"aid": aid(), "aib": [b for b, r in log], "air": {b["n"]: r for b, r in log}, "log": "x", "bmax": 48}
        base = R.check_decision(F.FlipMachine(code, BND, None, WIN), dec)
        self.assertEqual(base.status, "ok", base.why)
        out = F.flip_decision(code, BND, dec, base, WIN)
        self.assertEqual(sorted(out.values()), ["fail", "fail"], out)    # the mode test and the test of the result

    def test_a_branch_on_an_unknown_is_not_a_site_and_counts_as_unknown(self):
        import ai_resume_flip as F
        code = code_with(["push ebp", "mov ebp,esp", "mov esi,edx", "cmp DWORD PTR [esi+0x40],0x0", "jne @b", "@b push 0x1",
                          "call 0x3000", "pop ebp", "ret 0x4"])
        log = [(aib(11, F2, ra_of(code, F2), [1]), air(11, 0))]
        dec = {"aid": aid(), "aib": [b for b, r in log], "air": {b["n"]: r for b, r in log}, "log": "x", "bmax": 48}
        m = F.FlipMachine(code, BND, None, WIN)
        base = R.check_decision(m, dec)
        self.assertEqual((base.status, base.br), ("ok", {}), base.why)
        self.assertEqual(sum(m.unknown.values()), 1)
        self.assertEqual(F.flip_decision(code, BND, dec, base, WIN), {})

    def test_the_sample_takes_each_path(self):
        import ai_resume_flip as F

        class Rz:
            def __init__(self, p):
                self.log = [{"fn": 0, "ra": 0}, {"fn": p, "ra": p}]
        items = [("d%d" % k, Rz(k % 3)) for k in range(30)]
        got = F.sample(items, 1, 6)
        self.assertEqual(len(got), 6)
        self.assertEqual({r.log[1]["fn"] for _d, r in got}, {0, 1, 2})


class ReviewFixesTest(unittest.TestCase):
    """The six model fixes of the lane/p52b review (plan 0052 log; ai/0017 section 7), one test each."""

    def dec(self, log, aids=None, msm=()):
        return {"aid": aids or aid(), "aib": [b for b, r in log], "air": {b["n"]: r for b, r in log}, "log": "x", "bmax": 48,
                "msm": list(msm)}

    def test_P_the_thinks_argument_slot_takes_a_searchs_output(self):
        # lea eax,[ebp+0x8]; push eax; call F1; the think then branches on the distance F1 wrote into its own argument slot
        code = code_with(["push ebp", "mov ebp,esp", "lea eax,[ebp+0x8]", "push eax", "call 0x2000", "@r cmp DWORD PTR [ebp+0x8],0x6",
                          "jg @far", "push 0x1", "call 0x3000", "@far pop ebp", "ret 0x4"])
        m = R.Machine(code, BND, windows=WIN)
        ra1, ra2 = ra_of(code, F1), ra_of(code, F2)
        b1 = aib(11, F1, ra1, [0x7FF00004])
        b1["b"] = {"0": [8, 0, 0, 0, 0, 0, 0, 0]}
        r1 = air(11, 0)
        r1["bl"] = {"0": [5, 0, 0, 0, 0, 0, 0, 0]}
        d = self.dec([(b1, r1), (aib(12, F2, ra2, [1]), air(12, 0))])
        r = R.check_decision(m, d)
        self.assertEqual((r.status, r.matched), ("ok", 2), r.why)
        # the return address stays protected: the same block one slot lower must not move the return
        st = R.init_state(aid())
        self.assertIn(R.STK_TOP, st.prot)
        self.assertNotIn(R.STK_TOP + 4, st.prot)

    def test_C_an_opaque_callee_makes_c4_unknown(self):
        ins = asm(THINK, ["push ebp", "mov ebp,esp", "call 0x5000", "push 0x7", "call 0x2000", "pop ebp", "ret 0x4"])
        ins.update(asm(0x5000, ["ret"]))
        ins.update(asm(F1, ["ret 0x4"]))
        code = R.Code(inject=ins)
        m = R.Machine(code, BND, windows=WIN)
        b1 = aib(11, F1, ra_of(code, F1), [7])
        b1["c4"] = 0x82001
        r = R.check_decision(m, self.dec([(b1, air(11, 0))]))
        self.assertEqual(r.status, "ok", r.why)
        # with no opaque call between, the same changed word is a mismatch: the compare is still live
        code = code_with(["push ebp", "mov ebp,esp", "push 0x7", "call 0x2000", "pop ebp", "ret 0x4"])
        b1 = aib(11, F1, ra_of(code, F1), [7])
        b1["c4"] = 0x82001
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([(b1, air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("c4", r.why)

    def test_N_a_logged_call_inside_the_command_is_not_the_thinks(self):
        d = self.dec([(aib(11, F1, 0x1234, [7]), air(11, 0)), (aib(13, F3, 0x58F0FF, [0]), air(13, 0)),
                      (aib(16, F2, 0x1236, [1]), air(16, 0))], msm=[({"n": 12}, {"n": 15})])
        self.assertEqual([b["n"] for b in R.top_level(d)], [11, 16])
        d["msm"] = [({"n": 12}, None)]              # no MSM1: nothing proves the line is inside, it stays
        self.assertEqual([b["n"] for b in R.top_level(d)], [11, 13, 16])

    def test_B_the_position_block_forgets_its_8_bytes_only(self):
        # the frame of 0x005FB81F: [ebp-0xC] the block, [ebp-4] the control pointer the think goes on to use
        ins = asm(THINK, ["push ebp", "mov ebp,esp", "sub esp,0x20", "mov DWORD PTR [ebp-0x4],0x5000000", "mov DWORD PTR [ebp-0x8],0x9",
                          "lea ecx,[ebp-0xc]", "push ecx", "push 0x1", "call 0x620870", "mov ecx,DWORD PTR [ebp-0x4]",
                          "mov DWORD PTR [ecx+0x14],0x5", "push 0x7", "call 0x2000", "mov esp,ebp", "pop ebp", "ret 0x4"])
        ins.update(asm(R.POS_BLOCK, ["ret 0x8"]))
        ins.update(asm(F1, ["ret 0x4"]))
        code = R.Code(inject=ins)
        m = R.Machine(code, BND, windows=WIN)
        b1 = aib(11, F1, ra_of(code, F1), [7], ecx=0x5000000)
        b1["c"] = [5, 0, 0]                                             # the write of c0 went through the kept pointer
        r = R.check_decision(m, self.dec([(b1, air(11, 0))]))
        self.assertEqual(r.status, "ok", r.why)
        # the block's own word is forgotten: a branch on it forks
        ins2 = asm(THINK, ["push ebp", "mov ebp,esp", "sub esp,0x20", "mov DWORD PTR [ebp-0x8],0x9", "lea ecx,[ebp-0xc]", "push ecx",
                           "push 0x1", "call 0x620870", "cmp DWORD PTR [ebp-0x8],0x9", "jne @o", "push 0x7", "call 0x2000",
                           "@o mov esp,ebp", "pop ebp", "ret 0x4"])
        ins2.update(asm(R.POS_BLOCK, ["ret 0x8"]))
        ins2.update(asm(F1, ["ret 0x4"]))
        code = R.Code(inject=ins2)
        st = R.init_state(aid())
        ev, rets, stops = R.Machine(code, BND, windows=WIN).run(st)
        self.assertEqual((len(ev), len(rets)), (1, 1))

    def test_E_rng_randlohi_draws_from_the_seed(self):
        self.assertIn(0x004BC500, R.EXEC)
        # the instruction text of 0x004BC500's non-power-of-two path, range [edx, arg)
        ins = asm(0x004BC500, ["push ebp", "mov ebp,esp", "push ecx", "mov eax,DWORD PTR [ebp+0x8]", "push edi", "mov edi,edx",
                               "cmp eax,edi", "jg @go", "mov eax,edi", "pop edi", "mov esp,ebp", "pop ebp", "ret 0x4",
                               "@go sub eax,edi", "lea edx,[eax-0x1]", "push ebx", "xor ebx,ebx", "test eax,edx",
                               "mov DWORD PTR [ebp+0x8],eax", "mov eax,DWORD PTR [ecx]", "mov DWORD PTR [ebp-0x4],edx", "push esi",
                               "mov edx,0x6ac690c5", "mov esi,DWORD PTR [ecx+0x4]", "mul edx", "add eax,esi", "adc edx,ebx",
                               "mov DWORD PTR [ecx+0x4],edx", "mov DWORD PTR [ecx],eax", "xor edx,edx", "div DWORD PTR [ebp+0x8]",
                               "pop esi", "pop ebx", "mov eax,edx", "add eax,edi", "pop edi", "mov esp,ebp", "pop ebp", "ret 0x4"])
        ins.update(asm(THINK, ["push ebp", "mov ebp,esp", "mov esi,edx", "lea ecx,[esi+0x20]", "mov edx,0x0", "push 0x7",
                               "call 0x4bc500", "mov ecx,esi", "mov edx,esi", "push eax", "call 0x3000", "pop ebp", "ret 0x4"]))
        ins.update(asm(F2, ["ret 0x4"]))
        code = R.Code(inject=ins)
        t = 1 * 0x6AC690C5 + 2
        s1 = "%08x:%08x" % (t & 0xFFFFFFFF, t >> 32)
        want = (t & 0xFFFFFFFF) % 7
        b = aib(11, F2, ra_of(code, F2), [want], s=s1, ecx=0x1000000)
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([(b, air(11, 0, s=s1))]))
        self.assertEqual(r.status, "ok", r.why)
        b = aib(11, F2, ra_of(code, F2), [want], ecx=0x1000000)          # the seed before the draw: the model must see the step
        r = R.check_decision(R.Machine(code, BND, windows=WIN), self.dec([(b, air(11, 0))]))
        self.assertEqual(r.status, "mismatch")
        self.assertIn("seed", r.why)

    def test_D_the_absolute_operand_and_the_logged_record_count(self):
        self.assertEqual(R.parse_op("DWORD PTR ds:0x744304"), ("m", 4, None, None, 1, 0x744304))
        self.assertEqual(R.parse_op("ds:0x744304"), ("m", 4, None, None, 1, 0x744304))
        self.assertEqual(R.parse_op("BYTE PTR ds:0x744304"), ("m", 1, None, None, 1, 0x744304))
        # 0x005F2C1D: mov edx,ds:0x744304; cmp [edx+0xa80],0xe5; the branch is decided by AID's ms2
        lines = ["push ebp", "mov ebp,esp", "mov edx,DWORD PTR ds:0x744304", "cmp DWORD PTR [edx+0xa80],0xe5", "jg @big", "push 0x1",
                 "call 0x2000", "jmp @o", "@big push 0x2", "call 0x3000", "@o pop ebp", "ret 0x4"]
        code = code_with(lines)
        m = R.Machine(code, BND, windows=WIN)
        big = aib(11, F2, ra_of(code, F2), [2], edx=0)
        small = aib(11, F1, ra_of(code, F1), [1], edx=0)
        r = R.check_decision(m, self.dec([(big, air(11, 0))], aids=aid(ms2=734)))
        self.assertEqual((r.status, r.offers), ("ok", [1]), r.why)
        r = R.check_decision(m, self.dec([(small, air(11, 0))], aids=aid(ms2=100)))
        self.assertEqual((r.status, r.offers), ("ok", [1]), r.why)
        r = R.check_decision(m, self.dec([(small, air(11, 0))], aids=aid(ms2=734)))
        self.assertEqual(r.status, "mismatch")

    def test_the_loggers_limit_marker_is_a_stop_not_a_mismatch(self):
        code = code_with(THINK_CODE)
        m = R.Machine(code, BND, windows=WIN)
        b1 = aib(11, F1, ra_of(code, F1), [7])
        d = self.dec([(b1, air(11, 0))])
        self.assertEqual(R.check_decision(m, d).status, "mismatch")          # with no marker the missing call is a mismatch
        d["ail"] = [{"k": 10, "pend": 0, "n": 12}]
        r = R.check_decision(m, d)
        self.assertEqual(r.status, "stop")
        self.assertIn("AIL", r.why)
        d["ail"] = [{"k": 10, "pend": 1, "n": 12}]                           # re-armed when the pending call returned: nothing lost
        self.assertEqual(R.check_decision(m, d).status, "mismatch")

    def test_logger_rev5_source(self):
        src = open(os.path.join(HERE, "gdb", "ai.py")).read()
        self.assertIn("REV = 5", src)
        self.assertIn('emit("AIL"', src)
        # the MonSetMode line itself must still be logged: its AIB breakpoint is created before the MSM0 one at the same address
        self.assertLess(src.index("Bp(a, on_bnd(a), bnd_bps)"), src.index("Bp(0x005A7C20, on_msm0, bnd_bps)"))
        self.assertLess(src.index('st["pend"] and not NESTED'), src.index('cur["k"] in st["msm"].values()'))

    def test_a_tier_table_says_what_a_row_separates(self):
        def row(n, ok, mis=0, paths=None, br=None):
            sites = {}
            for p, k in (paths or {}).items():
                for c in p:
                    sites[c] = sites.get(c, 0) + k
            return {"n": n, "ok": ok, "mis": mis, "stop": {}, "matched": 0, "past": 0, "amb": 0, "steps": 0, "end": 0, "seqs": {},
                    "name": "", "paths": paths or {}, "sites": sites, "ends": {}, "br": br or {}}
        res = {"resume": {(2, 1): row(60, 60, paths={(): 60}),
                          (6, 2): row(60, 60, paths={((1, 2),): 40, ((1, 3),): 20}, br={0x10: 3, 0x12: 1}),
                          (9, 3): row(60, 60, paths={((1, 2),): 60}),
                          (13, 4): row(60, 59, mis=1, paths={((1, 2),): 59}),
                          (19, 5): row(82, 82, paths={(): 82}),
                          (28, 6): row(43, 43, paths={((1, 2),): 43})}}
        tier = {2: "Skeleton", 6: "Fallen", 9: "Wraith", 13: "FallenShaman", 20: "Scarab", 28: "Vampire"}
        t = {ln.split()[1]: ln for ln in R.tier_table(res, tier).splitlines() if ln.startswith("TIER")}
        self.assertIn("propose=weak(no-call-past-first)", t["2"])
        self.assertIn("propose=yes", t["6"])
        self.assertIn("paths=2 top=40/60", t["6"])
        self.assertIn("two_way=1 one_way=1", t["6"])
        self.assertIn("propose=weak(one-path)", t["9"])
        self.assertIn("propose=no(mismatches)", t["13"])
        self.assertIn("TIER 19 Swarm(not-tier)", t["19"])
        self.assertIn("propose=no(not-tier)", t["19"])
        self.assertIn("TIER 20 Scarab thinks=0 decisions=0", t["20"])
        self.assertIn("propose=no(short)", t["28"])


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
            c.loaded = set()
            c._load(0x5f95ff)          # a second sweep over the same bytes must not lengthen the instruction again
        finally:
            subprocess.run = real
        self.assertEqual(c.ins[0x5f95ff][0], 8)
        self.assertEqual(c.ins[0x5f9607][1], "ret")


if __name__ == "__main__":
    unittest.main()

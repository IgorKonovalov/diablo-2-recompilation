"""Synthetic tests for tools/frame.py (plan 0055 Phase 2a): python3 -I tools/test_frame.py

No game file is read: the binary's reach is a stub, and the logs are written to a temporary directory.
  - the placement: a logged order inside the pass order passes, one against it fails, the controls permute ranks;
  - the RNG step and the step count;
  - the kind rules: a site set, anim's EF phase (in a walk, outside, missing), a skipped line, an open reach;
  - a synthetic anim log: frames in order and out of order, nesting into a pair, the stamp falling (a new game),
    the slot dispatches against their queued records (oldest first; a cancelled record not matched);
  - the seed hand-off: handed, stepped, reversed;
  - the cross-type every-frame count;
  - the gap walk of `rechain`;
  - the dispatchers (plan 0055 P2a-ii): a declared table's entry called by its dispatcher, a callback passed to an
    iterator, the caller chain and its anchors, an orphan left open, a DEAD function with a reference refused; the rule
    classes 'reach', 'dispatch' and 'universal', and a universal event left out of the separating pairs.
"""
import collections
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame  # noqa: E402

HDR = "# d2run seed=1 gdb=tools/gdb/anim.gdb slot=2 t=2026-10-30T00:00:00\n"


class StubBin:
    """passes(): a fixed set per hook address, None (open) otherwise; with follow, `direct` gives the sets of the
    direct-call reach (a hook absent there closes only through a declared table)."""
    sha256 = "0" * 64

    def __init__(self, table=None, follow=False, direct=None):
        self.table = table or {}
        self.follow = follow
        self.direct = self.table if direct is None else direct

    def passes(self, addrs, utype=None, direct=False):
        out = set()
        for a in addrs:
            s = (self.direct if direct else self.table).get(a)
            if s is None:
                return None
            out |= s
        return frozenset(out)


def write(lines, hdr=HDR):
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.log")
    with open(p, "w") as fh:
        fh.write(hdr)
        for ln in lines:
            fh.write(ln + "\n")
    return d, "t.log"


def seed(lo, hi=0):
    return "%08x:%08x" % (lo, hi)


class Place(unittest.TestCase):
    def test_in_order(self):
        self.assertEqual(frame.place([(0, {7}), (1, {9}), (2, {21})]), [])

    def test_against_order(self):
        self.assertEqual(frame.place([(0, {9}), (1, {7})]), [1])

    def test_sets_take_the_lowest_rank_not_below(self):
        # {6,7} then {7} then {6,7}: placed 6, 7, 7
        self.assertEqual(frame.place([(0, {6, 7}), (1, {7}), (2, {6, 7})]), [])
        self.assertEqual(frame.place([(0, {7}), (1, {6})]), [1])

    def test_control_permutation(self):
        perm = frame.CONTROLS["monsters-before-players"]
        self.assertEqual(frame.place([(0, {7}), (1, {9})], perm), [1])
        self.assertEqual(frame.place([(0, {9}), (1, {7})], perm), [])
        drain = frame.CONTROLS["drain-before-the-tick"]
        self.assertEqual(frame.place([(0, {4}), (1, {21})], drain), [1])


class Rng(unittest.TestCase):
    def test_step_and_count(self):
        a = (0x12345678, 0x29A)
        b = frame.step(frame.step(a))
        self.assertEqual(frame.steps(a, b), 2)
        self.assertEqual(frame.steps(a, a), 0)
        self.assertIsNone(frame.steps(b, a, 10))
        v = a[0] * 0x6AC690C5 + a[1]
        self.assertEqual(frame.step(a), (v & 0xFFFFFFFF, v >> 32))


def ev(kind, line=2, raw=None, units=None, entry=None, exit_=None, end=None, frame_=1, utype=None):
    return frame.Ev(line, end, frame_, kind, utype, None, units or {}, entry or {}, exit_ or {}, raw or {})


class Rules(unittest.TestCase):
    def setUp(self):
        self.ut = frame.UnitTypes([])

    def test_site(self):
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("MDS"), self.ut), (frozenset({9}), "site"))

    def test_phase(self):
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("EF", raw={"ph": 4}), self.ut), (frozenset({7}), "ph"))
        s, c = frame.own_set(StubBin(), "anim", ev("EF", raw={"ph": 11}), self.ut)
        self.assertEqual(c, "ph-out")
        self.assertFalse(s & frozenset(range(4, 14)))
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("EF"), self.ut), (None, "no-ph"))

    def test_skip_open_reach(self):
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("WIN"), self.ut)[1], "skip")
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("FREE"), self.ut), (None, "open"))
        b = StubBin({0x00581490: frozenset({10, 11})})
        self.assertEqual(frame.own_set(b, "anim", ev("OEV"), self.ut), (frozenset({10, 11}), "reach"))

    def test_ra_and_client(self):
        b = StubBin({0x00549B0F: frozenset({21})})
        self.assertEqual(frame.own_set(b, "skills", ev("CU0", raw={"ret": 0x00549B0F}), self.ut),
                         (frozenset({21}), "ra"))
        self.assertEqual(frame.own_set(b, "skills", ev("CU0", raw={"ret": 0x00549B0F, "cl": 1}), self.ut),
                         (None, "client"))

    def test_type_rule(self):
        b = StubBin({0x00580610: frozenset({6, 7}), 0x005A6920: frozenset({8, 9})})
        self.assertEqual(frame.own_set(b, "combat", ev("RGN", raw={"t": 1}), self.ut)[0], frozenset({8, 9}))
        self.assertEqual(frame.own_set(b, "combat", ev("RGN", raw={"t": 0}), self.ut)[0], frozenset({6, 7}))


def run_check(lines, table=None, hdr=HDR, bin_=None):
    d, rel = write(lines, hdr)
    ck = frame.Check(bin_ or StubBin(table))
    ck._abs = os.path.join(d, rel)
    ck.log(d, rel, "anim.gdb")
    return ck


class AnimLog(unittest.TestCase):
    def test_order_ok_and_mismatch(self):
        ck = run_check([
            'PDS {"u":10,"m":1,"k":1,"a":0,"b":0,"fr":5,"n":1}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":5,"n":2}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":6,"n":3}',
            'PDS {"u":10,"m":1,"k":1,"a":0,"b":0,"fr":6,"n":4}',
        ])
        self.assertEqual(ck.c["frames2"], 2)
        self.assertEqual(ck.c["compared"], 4)
        self.assertEqual(ck.c["mismatch"], 1)
        self.assertEqual(ck.c["separating"], 1)
        self.assertEqual(ck.ctrl["monsters-before-players"], 1)

    def test_nesting_and_segments(self):
        # EF at phase 6 is the monster slot walk (rank 9); a pair with an open reach places nothing; the stamp falls
        # from 7 to 3 (a new game), where MDS before PDS fails
        ck = run_check([
            'EF {"u":30,"m":2,"fr":7,"ph":6,"n":1}',
            'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":2}' % seed(1),
            'PA1 {"k":2,"r":1,"s":"%s","n":3}' % seed(1),
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":7,"n":4}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":3,"n":5}',
            'PDS {"u":10,"m":1,"k":1,"a":0,"b":0,"fr":3,"n":6}',
        ])
        self.assertEqual(ck.c["segments"], 2)
        self.assertEqual(ck.c["mismatch"], 1)          # frame 3 of the second game: MDS then PDS
        self.assertEqual(ck.kind[("anim", "PA0")]["class open"], 1)

    def test_nested_takes_the_pair_set(self):
        pa0 = 'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":%d}'
        pa1 = 'PA1 {"k":%d,"r":1,"s":"%s","n":%d}'
        ck = run_check([pa0 % (seed(1), 1), 'FREE {"u":10,"t":0,"c":0,"m":1,"fr":7,"n":2}', pa1 % (1, seed(1), 3),
                        'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":7,"n":4}'], table={0x0057EEC0: frozenset({7})})
        self.assertEqual(ck.kind[("anim", "FREE")]["compared"], 1)
        self.assertEqual(ck.c["mismatch"], 0)
        ck = run_check([pa0 % (seed(1), 1), 'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":7,"n":2}', pa1 % (1, seed(1), 3),
                        'PDS {"u":10,"m":1,"k":1,"a":0,"b":0,"fr":7,"n":4}'], table={0x0057EEC0: frozenset({7})})
        self.assertEqual(ck.c["nesting conflicts"], 1)

    def test_slot_queue_order_and_cancel(self):
        ck = run_check([
            'SCH {"u":{"u":20,"t":1,"c":5,"id":2,"m":1},"fr":1,"T":1,"q":[[1,9,0,0]],"n":1}',
            'SCH {"u":{"u":21,"t":1,"c":5,"id":3,"m":1},"fr":2,"T":2,"q":[[1,9,0,0]],"n":2}',
            'CAN {"u":20,"k":1,"fr":3,"ra":0,"n":3}',
            'SCH {"u":{"u":20,"t":1,"c":5,"id":2,"m":1},"fr":3,"T":3,"q":[[1,9,0,0]],"n":4}',
            'MDS {"u":21,"m":1,"k":1,"a":0,"b":0,"fr":9,"n":5}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":9,"n":6}',
        ])
        self.assertEqual(ck.slot["MDS matched to a logged queue"], 2)
        self.assertEqual(ck.slot["MDS pairs in queue order"], 1)
        self.assertEqual(ck.slot["MDS pairs inverted"], 0)
        self.assertEqual(ck.slot["records cancelled (CAN)"], 1)

    def test_slot_raise(self):
        # a record queued for a frame <= the current one runs at the current + 1
        ck = run_check([
            'SCH {"u":{"u":20,"t":1,"c":5,"id":2,"m":1},"fr":4,"T":4,"q":[[1,2,0,0]],"n":1}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":5,"n":2}',
        ])
        self.assertEqual(ck.slot["MDS matched to a logged queue"], 1)

    def test_seed_handoff(self):
        s1 = (5, 7)
        s2 = frame.step(s1)
        f = lambda t: "%08x:%08x" % t  # noqa: E731
        ck = run_check([
            'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":1}' % f(s1),
            'PA1 {"k":1,"r":1,"s":"%s","n":2}' % f(s1),
            'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":3}' % f(s1),
            'PA1 {"k":3,"r":1,"s":"%s","n":4}' % f(s1),
            'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":5}' % f(s2),
            'PA1 {"k":5,"r":1,"s":"%s","n":6}' % f(s2),
            'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":7}' % f(s1),
            'PA1 {"k":7,"r":1,"s":"%s","n":8}' % f(s1),
        ])
        self.assertEqual(ck.seed[("anim", "unit", "handed")], 1)
        self.assertEqual(ck.seed[("anim", "unit", "stepped")], 1)
        self.assertEqual(ck.seed[("anim", "unit", "reversed")], 1)

    def test_cross_type(self):
        ck = run_check([
            'MSET {"u":{"u":20,"t":1,"c":5,"id":2,"m":1},"to":2,"fr":7,"ra":0,"n":1}',
            'EF {"u":20,"m":2,"fr":7,"ph":4,"n":2}',
            'EF {"u":20,"m":2,"fr":8,"ph":5,"n":3}',
            'MSET {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"to":2,"fr":8,"ra":0,"n":4}',
            'EF {"u":10,"m":2,"fr":8,"ph":11,"n":5}',
        ])
        self.assertEqual(ck.cross["monster cross-type, this frame"], 1)
        self.assertEqual(ck.cross["monster queued in its own or a later walk (mon-ef): next frame"], 1)
        self.assertEqual(ck.cross["player queued outside the walks (ph 11): next frame's walk"], 1)


class Classes(unittest.TestCase):
    def test_reach_dispatch_universal(self):
        ut = frame.UnitTypes([])
        b = StubBin({0x00581490: frozenset({10, 11}), 0x00555600: frozenset({7})}, follow=True,
                    direct={0x00581490: frozenset({10, 11})})
        self.assertEqual(frame.own_set(b, "anim", ev("OEV"), ut), (frozenset({10, 11}), "reach"))
        self.assertEqual(frame.own_set(b, "anim", ev("FREE"), ut), (frozenset({7}), "dispatch"))
        self.assertEqual(frame.own_set(b, "anim", ev("GH"), ut), (frame.ALL, "universal"))
        self.assertEqual(frame.own_set(StubBin(), "anim", ev("GH"), ut), (None, "open"))

    def test_universal_left_out_of_the_pairs(self):
        # PDS, an open (universal) FREE, MDS: one separating pair PDS -> MDS, two compared, the frame placed in full
        ck = run_check([
            'PDS {"u":10,"m":1,"k":1,"a":0,"b":0,"fr":5,"n":1}',
            'FREE {"u":10,"t":0,"c":0,"m":1,"fr":5,"n":2}',
            'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":5,"n":3}',
        ], bin_=StubBin(follow=True))
        self.assertEqual(ck.c["separating"], 1)
        self.assertEqual(ck.c["compared"], 2)
        self.assertEqual(ck.c["frames placed2 any"], 1)
        self.assertEqual(ck.c["frames2 all placed"], 1)
        self.assertEqual(ck.kind[("anim", "FREE")]["class universal"], 1)

    def test_universal_nested_takes_the_pair_set(self):
        pa0 = 'PA0 {"u":{"u":10,"t":0,"c":0,"id":1,"m":1},"fr":7,"s":"%s","n":1}' % seed(1)
        ck = run_check([pa0, 'FREE {"u":10,"t":0,"c":0,"m":1,"fr":7,"n":2}', 'PA1 {"k":1,"r":1,"s":"%s","n":3}' % seed(1),
                        'MDS {"u":20,"m":1,"k":1,"a":0,"b":0,"fr":7,"n":4}'],
                       bin_=StubBin({0x0057EEC0: frozenset({7})}, follow=True))
        self.assertEqual(ck.kind[("anim", "FREE")]["compared as nested"], 1)
        self.assertEqual(ck.c["separating"], 1)


def synthetic_binary():
    """A Binary over a made-up image: root R (rank 9) calls dispatcher D; D calls through table T (two entries E1, E2)
    at 0x401150 and passes callback C to iterator I; O has no caller."""
    b = frame.Binary.__new__(frame.Binary)
    b.follow = True
    b.img = bytearray(0x2D0010)
    for k, v in enumerate((0x401200, 0x401300)):
        b.img[0x2D0000 + 4 * k:0x2D0004 + 4 * k] = v.to_bytes(4, "little")
    code = [(0x401000, "push   ebp"), (0x401010, "call   0x401100"), (0x401100, "push   ebp"),
            (0x401120, "push   0x401500"), (0x401125, "call   0x401400"), (0x401150, "call   eax"),
            (0x401200, "push   ebp"), (0x401300, "push   ebp"), (0x401400, "push   ebp"),
            (0x401450, "call   DWORD PTR [ebp+0x8]"), (0x401500, "push   ebp"), (0x401600, "push   ebp"),
            (0x401700, "ret")]
    b.ia = [a for a, _t in code]
    b.it = [t for _a, t in code]
    b.funcs = {0x401000, 0x401100, 0x401200, 0x401300, 0x401400, 0x401500, 0x401600}
    b.flist = sorted(b.funcs)
    b.rev = collections.defaultdict(set, {0x401100: {0x401000}, 0x401400: {0x401100}})
    b.lab = {}
    b.reloc_refs = collections.defaultdict(list, {0x401500: [0x401121], 0x401200: [0x6D0000], 0x401300: [0x6D0004]})
    b.dead = set()
    b.unexplained = collections.defaultdict(list)
    b._cache = {}
    return b


class Dispatch(unittest.TestCase):
    DECL = dict(TABLES=(("T", 0x6D0000, 4, (0,), 2, ((0x401150, 0, None),), "idx", "D 0x401150"),),
                ITERATORS={0x401400: ((0x401450,), "Iter")}, REGISTRARS={}, QUEST_FIELDS={}, STORED=(), DEAD=(),
                DEAD_SELF=(), SEH_HANDLERS=(), BLOCKS={}, ARG_SITES={}, QUEST_CODE=())

    def setUp(self):
        self.saved = {k: getattr(frame, k) for k in self.DECL}
        for k, v in self.DECL.items():
            setattr(frame, k, v)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(frame, k, v)

    def test_table_and_callback_edges(self):
        b = synthetic_binary()
        b._follow()
        b.roots = {0x401000: (frozenset({9}), 1, "R")}
        self.assertEqual(b.passes([0x401300]), frozenset({9}))
        self.assertIsNone(b.passes([0x401300], direct=True))
        self.assertEqual(b.passes([0x401500]), frozenset({9}))
        ch = b.chain(0x401300)
        self.assertEqual([x for x, _l in ch], [0x401300, 0x401100, 0x401000])
        self.assertIn("T[1] @0x00401150", ch[0][1])
        self.assertIn("callback of Iter", b.chain(0x401500)[0][1])
        self.assertIsNone(b.passes([0x401600]))
        self.assertEqual(b.reach(0x401600)[1], [0x401600])
        self.assertEqual(frame.hook_status(b, 0x401300)[0], "dispatch")
        self.assertEqual(frame.hook_status(b, 0x401600)[0], "universal")
        self.assertEqual(frame._closed(b, [0x401200], None), (frozenset({9}), "dispatch"))
        b.unexplained[0x401200].append(0x6D1000)
        seen, unex = b.closure(0x401200)
        self.assertEqual(seen, {0x401200, 0x401100, 0x401000})
        self.assertEqual(unex, [(0x401200, 0x6D1000)])

    def test_site_and_dead_checks(self):
        frame.TABLES = (("T", 0x6D0000, 4, (0,), 2, ((0x401120, 0, None),), "idx", "a push is no call"),)
        with self.assertRaises(SystemExit):
            synthetic_binary()._follow()
        frame.TABLES = self.DECL["TABLES"]
        frame.DEAD = (0x401200,)
        with self.assertRaises(SystemExit):
            synthetic_binary()._follow()


class Gap(unittest.TestCase):
    def test_walk(self):
        a = (1, 2)
        b = frame.step(a)
        f = lambda t: "%08x:%08x" % t  # noqa: E731
        u = 77
        lines = [
            ("SDO0", {"u": {"u": u, "s": f(a)}, "n": 1}),
            ("SDO1", {"k": 1, "s": f(a), "n": 2}),
            ("THR", {"a": u, "sa": f(b), "n": 3}),
            ("SST0", {"u": {"u": u, "s": f(b)}, "n": 4}),
        ]
        self.assertEqual(frame._walk_gap(lines, 4, u)[0], "re-chained")
        lines2 = lines[:2] + [lines[3]]
        self.assertEqual(frame._walk_gap(lines2, 4, u)[0], "not re-chained")
        m = frame.RE_GAP.match("x.log n=4 player unit 77 [not attributed]: 1 steps; stopped")
        self.assertEqual(m.group(2), "4")


if __name__ == "__main__":
    unittest.main()

"""No-game tests of tools/ai_model_check.py (plan 0066 batch S1b): the engine on hand-built decisions (an AID line,
its AIB calls and AIR returns, an AIX exit), with the R3 Zombie and R12 Goatman models and two toy models.

    python3 -I tools/test_ai_model_check.py
    python3 -I tools/test_ai_model_check.py report          # revision 4: the recorder's per-entry branch summary

Plan 0069 Phase 1b adds a hand-built path per new entry and the recorder's branch controls (below `Revision3`).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_model_check as M  # noqa: E402

G, U, T, CTL = 0x3000000, 0x1000000, 0x7000000, 0x5000000
SEED = (0x00000001, 0x00000002)


def sx(s):
    return "%08x:%08x" % s


def aip_hex(vals):
    """`aip` K=1..8 for Normal only (the other two columns 0)."""
    w = []
    for k in range(8):
        w += [vals.get(k + 1, 0), 0, 0]
    return "".join("%02x%02x" % (v & 0xFF, (v >> 8) & 0xFF) for v in w)


def decision(calls, melee=0, dist=10, aip=None, seed=SEED, exit_seed=None, ctl14=0, sk="ff" * 16 + "00" * 8):
    """calls: [(fn, ecx, edx, args, eax, seed after)]. The AIB seed of each call is the previous call's AIR seed, or the
    think's seed for the first, unless the call tuple gives its own as a 7th element."""
    ctl = bytearray(0x40)
    ctl[0x14:0x18] = (ctl14 & 0xFFFFFFFF).to_bytes(4, "little")
    a = {"u": U, "id": 9, "c": 5, "ai": 3, "st": 0, "th": 0x005EFE20, "cx": 0x2000000, "g": G, "mdp": 0x4000000,
         "ctlp": CTL, "hp": 0, "md": 0, "m": 1, "c4": 0, "x": 10, "y": 20, "s0": sx(seed), "s": sx(seed), "fr": 100,
         "diff": 0, "ms": 0x6000000, "ms2": 734, "ctx": [CTL, 0, T, 0, 0, dist, melee, 0x6000000, 0], "ctl": ctl.hex(),
         "head": None, "aip": aip_hex(aip or {}), "sk": sk, "ad": [0, 0], "t": [0, 1, 4, 1, 12, 22], "pl": [0, 0], "n": 10}
    d = {"aid": a, "aib": [], "air": {}, "msm": [], "pp": [], "aix": None, "log": "test.log", "rev": 6, "bmax": 48}
    s = seed
    n = 11
    for c in calls:
        fn, ecx, edx, args, eax, after = c[:6]
        sat = c[6] if len(c) > 6 else s
        b = {"k": 10, "n": n, "fn": fn, "ra": 0x5F0000 + n, "ecx": ecx, "edx": edx, "a": list(args) + [0] * (6 - len(args)),
             "s": sx(sat), "c": [ctl14 & 0xFFFFFFFF, 0, 0], "c4": 0, "b": {}}
        d["aib"].append(b)
        d["air"][n] = {"k": 10, "b": n, "fn": fn, "ra": b["ra"], "eax": eax, "s": sx(after), "c": [ctl14 & 0xFFFFFFFF, 0, 0],
                       "c4": 0, "bl": {}, "n": n + 1}
        s = after
        n += 2
    d["aix"] = {"k": 10, "s": sx(exit_seed if exit_seed is not None else s), "nb": len(calls)}
    return d


ST3OR19, ROOM, LEVEL, RING, SETMODE, IDLE, WALK = 0x005DD2B0, 0x00620BB0, 0x0061A1B0, 0x005DE200, 0x005DDF90, 0x005DE080, 0x005DEC80


class Zombie(unittest.TestCase):
    """R3: not melee, not St3or19, not near: the room's level, then Ring(3) with no draw."""

    def ring_decision(self, lvl=4, ring_r=3, exit_seed=None):
        after = ai.step(ai.step(SEED))
        return decision([(ST3OR19, U, 0, [], 0, SEED), (ROOM, 0, 0, [U], 0x9000000, SEED),
                         (LEVEL, 0, 0, [0x9000000], lvl, SEED), (RING, G, U, [ring_r], 1, after)],
                        dist=30, aip={1: 50, 2: 5}, exit_seed=exit_seed)

    def test_ring_matches(self):
        o = M.check(M.m_r3, self.ring_decision())
        self.assertEqual(o.status, "ok")
        self.assertEqual(o.forks, 0)
        self.assertEqual([lb for lb, _ in o.run.labels], ["2.st3or19", "2.room", "2.level", "2.ring"])

    def test_wrong_word_fails(self):
        self.assertEqual(M.check(M.m_r3, self.ring_decision(ring_r=4)).status, "mismatch")

    def test_exit_seed_compared(self):
        self.assertEqual(M.check(M.m_r3, self.ring_decision(exit_seed=(5, 6))).status, "mismatch")

    def test_level_17_branch_flip_fails(self):
        o = M.check(M.m_r3, self.ring_decision(), flip="2.level!=17")
        self.assertEqual(o.status, "mismatch")

    def test_melee_draw(self):
        s1 = ai.step(SEED)
        mode = 4 if (s1[0] % 100) < 60 else 5
        d = decision([(SETMODE, G, U, [mode, T], 1, s1, s1)], melee=1, aip={4: 60})
        self.assertEqual(M.check(M.m_r3, d).status, "ok")
        d2 = decision([(SETMODE, G, U, [mode, T], 1, s1, SEED)], melee=1, aip={4: 60})
        self.assertEqual(M.check(M.m_r3, d2).status, "mismatch")     # the seed at the call has no draw: fails


class Goatman(unittest.TestCase):
    def test_idle_and_le_control(self):
        s1 = ai.step(SEED)
        low = s1[0] % 100
        # not melee, chance(1) with aip(1) = low: `<` is false (idle), `<=` would walk: an edge case
        d = decision([(IDLE, G, U, [7], 0, s1, s1)], melee=0, aip={1: low, 2: 7})
        o = M.check(M.m_r12, d)
        self.assertEqual(o.status, "ok")
        self.assertEqual(o.run.edges, ["1.chance(1)"])
        self.assertEqual(M.check(M.m_r12, d, ctl="le").status, "mismatch")


def toy_fork(r):
    if r.unknown("u"):
        r.call("a", "Idle", n=1)
    else:
        r.call("b", "Idle", n=2)


def toy_store(r):
    r.store("set v14=5", 0x14, 5)
    r.call("idle", "Idle", n=1)


class Engine(unittest.TestCase):
    def test_fork_takes_the_matching_side(self):
        d = decision([(IDLE, G, U, [2], 0, SEED)])
        o = M.check(toy_fork, d)
        self.assertEqual((o.status, o.forks), ("ok", 1))
        d3 = decision([(IDLE, G, U, [3], 0, SEED)])
        self.assertEqual(M.check(toy_fork, d3).status, "mismatch")

    def test_store_compared_at_the_call_and_flipped(self):
        d = decision([(IDLE, G, U, [1], 0, SEED)], ctl14=5)
        d["aid"]["ctl"] = "00" * 0x40          # v14 is 0 at the think call, 5 at the call: the store is seen
        self.assertEqual(M.check(toy_store, d).status, "ok")
        self.assertEqual(M.check(toy_store, d, flip="set v14=5").status, "mismatch")

    def test_no_air_stops(self):
        d = decision([(IDLE, G, U, [1], 0, SEED)])
        d["air"] = {}
        self.assertEqual(M.check(lambda r: r.call("idle", "Idle", n=1), d).status, "stop")


class Revision3(unittest.TestCase):
    """plan 0069 Phase 1a: the CONV additions, the SEP line and the regression filter."""

    def test_conv_addresses_and_names_are_unique(self):
        addrs = [v[0] for v in M.CONV.values()]
        self.assertEqual(len(addrs), len(set(addrs)))
        for name, (a, ecx, edx, st) in M.CONV.items():
            self.assertLessEqual(len(st), 6, name)          # the AIB line logs six stack words

    def test_new_conv_entry_is_compared(self):
        # UnitIsDead (0x005541B0): ECX the unit, no stack word (the caller read of tools/ai_tour.py conv)
        dead = M.CONV["UnitIsDead"][0]
        d = decision([(dead, U, 0, [], 0, SEED)])
        self.assertEqual(M.check(lambda r: r.call("dead", "UnitIsDead", c=r.U), d).status, "ok")
        self.assertEqual(M.check(lambda r: r.call("dead", "UnitIsDead", c=r.U + 4), d).status, "mismatch")

    def test_sep_line_counts_distinct_call_paths(self):
        class O:
            pass

        def free(paths):
            out = []
            for p in paths:
                o = O()
                o.run = O()
                o.run.labels = [(x, 0) for x in p]
                out.append((None, o))
            return out
        ln = M.sep_line("RX", free([["a", "b"], ["a", "b"], ["a"], []]))
        self.assertTrue(ln.startswith("  SEP RX outcomes 3 over 4 fork-free decisions: "))
        self.assertIn("a b: 2", ln)
        self.assertIn("(no call): 1", ln)
        self.assertEqual(M.sep_line("RY", []), "  SEP RY outcomes 0 over 0 fork-free decisions")

    def test_strip_sep_drops_only_sep_lines(self):
        text = "ENTRY R1 x\n  CALLS y\n  SEP R1 outcomes 1 over 2 fork-free decisions: a: 2\nENTRY R2 z\n"
        self.assertEqual(M.strip_sep(text), "ENTRY R1 x\n  CALLS y\nENTRY R2 z\n")


# ------------------------------------------------------------------------------------------------- plan 0069 Phase 1b
# Revision 4 (`lane/n69b`): the 29 models of batches H1a, H1b and H1d. Two kinds of test per entry:
#  * a hand-built path (`Paths`): the calls, words and draw counts written from the catalogue block, not from the model;
#  * the branch controls (`Branches`): a recorder runs the model on seeded random inputs and writes the calls it makes as a
#    logged decision (AIB/AIR lines, the oracle returns drawn at random); each such decision must match its model, and every
#    named branch the decisions run must make at least one fork-free decision fail when it alone is reversed.

import random  # noqa: E402

IMP = {k: ([5 * k + j for j in range(24)], [100 + k, -1, 300 + k, 400 + k, 500 + k, -1, -1, -1], [4, 5, 6, 7, 8, 9, 10, 11])
       for k in range(1, 5)}
IMP[1][0][3:6] = [14, 14, 14]          # R1.aip(2): the teleport radius (a power-of-two n = 28 is not; 16 below is)
POOL = (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 14, 15, 20, 24, 25, 30, 50, 66, 75, 100)


def conv_words(name, kw, G_, U_, rnd):
    """The AIB words of a call as the recorder logs it: the named words, else a filler."""
    fn, ecx, edx, names = M.CONV[name]

    def word(spec, reg):
        if spec in ("G", "U") and "_" + reg in kw:
            return kw["_" + reg]
        if spec == "G":
            return G_
        if spec == "U":
            return U_
        v = kw.get(spec) if spec else None
        return rnd.choice((0, 0x7300000)) if v is None else v
    a = []
    for nm in names:
        v = kw.get(nm)
        a.append(rnd.choice((0, 7)) if v is None else v)
    return fn, M.u32(word(ecx, "ecx")), M.u32(word(edx, "edx")), [M.u32(x) for x in a] + [0] * (6 - len(a))


class Recorder(M.Run):
    """Runs a model and writes each call it makes as a logged call, with a random oracle return; the answers it gives the
    unknown branches are kept (`answers`), as a rev 7 word would give them."""

    def __init__(self, dec, rnd):
        super().__init__(dec)
        self.rnd = rnd
        self.k = 11
        self.answers = []

    def call(self, label, name, blk=None, **kw):
        fn, ecx, edx, a = conv_words(name, kw, self.G, self.U, self.rnd)
        b = {"k": 10, "n": self.k, "fn": fn, "ra": 0x5F0000 + self.k, "ecx": ecx, "edx": edx, "a": a,
             "s": "%08x:%08x" % self.seed, "c": [M.u32(self.v[o]) for o in (0x14, 0x18, 0x1C)], "c4": self.c4, "b": {}}
        for i, words in (blk or {}).items():
            got = [self.rnd.choice(POOL) for _ in range(8)]
            for w, v in words.items():
                got[w] = M.u32(v)
            b["b"][str(i)] = got
        eax = self.rnd.choice((0, 0, 1, 1, 3, 5, 10, 20, 24, 25, 30, 60, 99, 1023, 1024, 3000, 0x7100000, 0x7200000))
        bl = {str(i): [self.rnd.choice(POOL + (0x7200000, 0x7FFFFFFF)) for _ in range(8)] for i in range(6)}
        self.dec["aib"].append(b)
        self.dec["air"][self.k] = {"k": 10, "b": self.k, "fn": fn, "ra": b["ra"], "eax": eax, "s": b["s"], "c": b["c"],
                                   "c4": self.c4, "bl": bl, "n": self.k + 1}
        self.labels.append((label, b["ra"]))
        self.k += 2
        self.i += 1
        return M.Ret(eax, bl)

    def unknown(self, name):
        v = self.rnd.random() < 0.5
        self.answers.append(v)
        return v

    def opaque(self, name):
        for _ in range(self.rnd.randrange(3)):
            self.seed = ai.step(self.seed)


def rand_decision(rnd, th):
    ctl = bytearray(0x40)
    T = rnd.choice((100, 134, 337, 674, 1000, 2010, 5000))
    for off in (0x14, 0x18, 0x1C):
        v = rnd.choice((-1, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 25, 29, T - 1, T, T + 1, T + 50))
        ctl[off:off + 4] = M.u32(v).to_bytes(4, "little")
    ctl[0x38:0x3C] = rnd.choice((0, 0x7400000)).to_bytes(4, "little")
    ctl[0x3C:0x40] = M.u32(rnd.choice((-1, 0, 453))).to_bytes(4, "little")
    aip = [rnd.choice(POOL) for _ in range(24)]
    sk = [rnd.choice((-1, 0, 5, 284, 300)) for _ in range(8)] + [rnd.choice((4, 5, 7, 0xFF)) for _ in range(8)]
    skb = b"".join(M.u32(v).to_bytes(4, "little")[:2] for v in sk[:8]) + bytes(sk[8:])
    tgt = rnd.choice((0, T_ := 0x7000000, T_))
    tt = [rnd.choice((0, 1)), 5, 0x99, rnd.choice((1, 2)), rnd.choice((10, 20, 30)), rnd.choice((20, 25))] + [0] if tgt else None
    head = None
    if rnd.random() < 0.8:
        head = b"".join(M.u32(v).to_bytes(4, "little") for v in
                        (0, 0, rnd.choice((1, 1, 2)), 1, 0x55, rnd.choice((T - 5, T + 5)), 0))
    s = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
    a = {"u": U, "id": 9, "c": rnd.choice((271, 270, 5, 0x1FF, 0xB2)), "ai": 3, "st": 0, "th": th, "cx": 0x2000000, "g": G,
         "mdp": 0x4000000, "ctlp": CTL, "hp": 0, "md": rnd.choice((0, 3)), "m": rnd.choice((1, 1, 2)), "c4": 0,
         "x": 10, "y": 20, "s0": sx(s), "s": sx(s), "fr": T, "diff": rnd.choice((0, 0, 1, 2)),
         "ms": 0x6000000, "ms2": rnd.choice((300, 734)),
         "ctx": [CTL, 0, tgt, 0, 0, rnd.choice(POOL + (-1, 200)), rnd.choice((0, 1)), 0x6000000, 0], "ctl": ctl.hex(),
         "head": head.hex() if head else None,
         "aip": "".join("%02x%02x" % (v & 0xFF, (v >> 8) & 0xFF) for v in aip), "sk": skb.hex(),
         "ad": [rnd.choice((3, 9, 15)), 0], "t": tt, "pl": [0, 0], "n": 10}
    return {"aid": a, "aib": [], "air": {}, "msm": [], "pp": [], "aix": None, "log": "rec.log", "rev": 6, "bmax": 48}


def record(model, th, rnd):
    """A decision written by running `model` with the recorder, and the recorder's answers to the unknown branches; None
    when the model stops on these inputs."""
    d = rand_decision(rnd, th)
    r = Recorder(d, rnd)
    try:
        model(r)
    except M.Stop:
        return None, None
    d["aix"] = {"k": 10, "s": "%08x:%08x" % r.seed, "nb": len(d["aib"])}
    return d, tuple(r.answers)


def check_given(model, dec, given, flip=None, limit=64):
    """`M.check` with the unknown branches answered as recorded (a later branch the flip opens still forks): the
    status of the first matching path, else mismatch or stop."""
    todo, stops = [given], 0
    while todo and limit:
        ch = todo.pop()
        limit -= 1
        r = M.Run(dec, ch, flip)
        try:
            model(r)
            r.finish()
        except M.NeedChoice:
            todo += [ch + (True,), ch + (False,)]
            continue
        except M.Mismatch:
            continue
        except M.Stop:
            stops += 1
            continue
        return "ok", r
    return ("stop" if stops or todo else "mismatch"), None


NEW = ("R8", "R16", "R142", "R17", "R18", "R24", "R25", "R27", "R72", "R74", "R115", "R116", "R117", "S15", "R119",
       "R120", "R122", "R123", "S16", "R126", "R129", "R136", "R137", "S5", "S6", "R41", "R42", "R58", "R60")
# branches no decision of the recorder can tell from their reverse, with the reason (a test of a value the block then
# does not read, or a path the block makes unreachable)
EXEMPT = {
    "R24": {"2.1.aip(5)<v18": "its stores follow the arm's last call: run_check's FLIP sees them at the next decision"},
    "R27": {"5.v14<1": "its store follows the block's last call: run_check's FLIP sees it at the next decision"},
    "R25": {"g.dead": "the grant is rarely reached by random inputs: Paths.test_r25_grant reverses it"},
}


def branch_report(name, n=1500, seed=6902):
    th, model, _ = M.MODELS[name]
    rnd = random.Random("%s/%d" % (name, seed))
    seen, failed, decided, stopped = set(), set(), 0, 0
    free = 0
    for _ in range(n):
        d, given = record(model, th, rnd)
        if d is None:
            stopped += 1
            continue
        o = M.check(model, d)
        if o.status != "ok":
            return {"bad": "%s: the recorded decision does not match its model: %s %s" % (name, o.status, o.why)}
        free += o.forks == 0
        st, run = check_given(model, d, given)
        if st != "ok":
            return {"bad": "%s: the recorded decision does not match its own answers: %s" % (name, st)}
        decided += 1
        names = {b for b, _ in run.arms if not b.startswith("set ")}
        seen |= names
        for b in names - failed:
            if check_given(model, d, given, flip=b)[0] == "mismatch":
                failed.add(b)
    return {"seen": seen, "failed": failed, "decided": decided, "stopped": stopped, "free": free}


class Branches(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = M.IMP_RECS
        M.IMP_RECS = IMP

    @classmethod
    def tearDownClass(cls):
        M.IMP_RECS = cls.saved

    def test_every_entry_is_listed(self):
        self.assertEqual(len(NEW), 29)
        for n in NEW:
            self.assertIn(n, M.MODELS)

    def test_each_branch_fails_when_reversed(self):
        for n in NEW:
            with self.subTest(entry=n):
                rep = branch_report(n)
                self.assertNotIn("bad", rep, rep.get("bad"))
                self.assertGreater(rep["decided"], 30, n)
                left = rep["seen"] - rep["failed"] - set(EXEMPT.get(n, {}))
                self.assertEqual(left, set(), "%s: branches no decision separates" % n)


def path(model, calls, draws_after=0, **kw):
    """A hand-built decision: `calls` = [(CONV name, ecx, edx, stack words, eax, draws before the call, bl)], the draws
    counted on the unit seed from the think's seed."""
    s = SEED
    rows = []
    for c in calls:
        nm, ecx, edx, args, eax, nd = c[:6]
        for _ in range(nd):
            s = ai.step(s)
        rows.append((M.CONV[nm][0], ecx, edx, args, eax, s, s))
    for _ in range(draws_after):
        s = ai.step(s)
    d = decision(rows, exit_seed=s, **{k: v for k, v in kw.items() if k in ("melee", "dist", "aip", "ctl14", "sk")})
    for i, c in enumerate(calls):
        if len(c) > 6 and c[6] is not None:
            before, after = c[6] if isinstance(c[6], tuple) else (c[6], c[6])
            d["air"][d["aib"][i]["n"]]["bl"] = after
            d["aib"][i]["b"] = {k: list(v) + [0] * (8 - len(v)) for k, v in before.items()}
        if len(c) > 7:
            d["aib"][i]["c"] = list(c[7])                    # the control words at the call (the block's stores before it)
            d["air"][d["aib"][i]["n"]]["c"] = list(c[7])
    for k, v in kw.items():
        if k not in ("melee", "dist", "aip", "ctl14", "sk"):
            d["aid"][k] = v
    return d


def sk_hex(skills, modes=(0,) * 8):
    return (b"".join(M.u32(v).to_bytes(4, "little")[:2] for v in skills) + bytes(modes)).hex()


def low(n, k=1):
    """The low word of the k-th step from SEED."""
    s = SEED
    for _ in range(k):
        s = ai.step(s)
    return s[0]


SETSTATE, OVERLAY, LIFEPCT, SEARCH, T56 = 0x00639DB0, 0x00621E40, 0x005DD280, 0x005DD0B0, 0x005DF7D0


class Paths(unittest.TestCase):
    """One path per entry, written from its block: the callee, the words and the draws before each call."""

    @classmethod
    def setUpClass(cls):
        cls.saved = M.IMP_RECS
        M.IMP_RECS = IMP

    @classmethod
    def tearDownClass(cls):
        M.IMP_RECS = cls.saved

    def ok(self, name, d, forks=0):
        o = M.check(M.MODELS[name][1], d)
        self.assertEqual((o.status, o.forks), ("ok", forks), o.why)
        return o

    def bad(self, name, d):
        self.assertEqual(M.check(M.MODELS[name][1], d).status, "mismatch")

    def test_r8_first_event_clears_and_idles(self):
        # v14 = 0: both states cleared; n = 1 = aip(5): overlay 46 (aip(6) 0) and Idle(aidel + 1), Normal
        c1 = (1, 0, 0)                                          # v14 = 1 after the count
        d = path("R8", [("StateSet", 0, 0, [U, 90, 0], 1, 0), ("StateSet", 0, 0, [U, 91, 0], 1, 0),
                        ("UnitSetOverlayStat", 0, 0, [U, 46, 0], 1, 0, None, c1), ("Idle", G, U, [16], 0, 0, None, c1)],
                 aip={5: 1}, ad=[15, 0])
        self.ok("R8", d)
        d["aib"][2]["a"][1] = 150
        self.bad("R8", d)

    def test_r16_melee_attack_draws_twice(self):
        mode = 4 if low(100, 2) % 100 < 40 else 5
        d = path("R16", [("SetModeAtUnit", G, U, [mode, T], 1, 2)], melee=1, aip={3: 100, 4: 40})
        self.ok("R16", d)

    def test_r142_a1_cooldown(self):
        # not melee, dist 5 < aip(7) 20, chance(4) 100: v18 0 < T: SetModeAtUnit(4, t), v18 <- T + aip(8)
        d = path("R142", [("SetModeAtUnit", G, U, [4, T], 1, 1)], dist=5, aip={7: 20, 4: 100, 8: 50})
        self.ok("R142", d)

    def test_r17_far_wander_no_draw(self):
        d = path("R17", [("Ovr", U, 0, [75, 0], 1, 0), ("WanderNear", G, U, [T, 5], 1, 0)], dist=11, sk=sk_hex([-1] * 8))
        self.ok("R17", d)

    def test_r18_search_walk(self):
        # not melee, chance(1) 0 fails (one draw); the packmate at 100 > aip(3)^2 = 64: Ovr(0, 75, 0), Walk(unit, 7)
        d = path("R18", [("UnitSearch", G, U, [0, 0x005B0D00, 1], 0, 1, ({"0": [0, 0x7FFFFFFF]}, {"0": [0x7200000, 100]})),
                         ("Ovr", U, 0, [75, 0], 1, 0), ("Walk", G, U, [0x7200000, 7], 1, 0)], aip={1: 0, 3: 8})
        self.ok("R18", d)

    def test_r24_switch_retreat(self):
        # not melee, v14 = 2: Ovr(2, 100, 0), StepAway(t, 10, 1); no draw
        d = path("R24", [("Ovr", U, 2, [100, 0], 1, 0), ("StepAway", G, U, [T, 10, 1], 1, 0)], ctl14=2)
        self.ok("R24", d)

    def test_r25_plain_cast(self):
        # no target: no trigger; v14 = 2, not melee: SetModeAtUnit(7, t) with no draw
        d = path("R25", [("SetModeAtUnit", G, U, [7, 0], 1, 0)], ctl14=2)
        d["aid"]["ctx"][2] = 0
        d["aid"]["t"] = None
        self.ok("R25", d)

    def test_r25_grant(self):
        # four-wisp dance, v14 6, place v1C 1, v18 3, T 134 (134 mod 67 = 0): the trigger's UnitDistSq fails (2000);
        # point t + A[6, 1] = (12 - 10, 22 - 3); PathDist 0; v18 = 3: v14 <- 7, v18 <- 0, Idle(337 - 134), the grant to
        # the player target: UnitIsDead 0, the list allocated (fork), UnitQueueEvent(t, 12, 134 + 1 728 000, 0, 0)
        c0, c1 = (6, 3, 1), (7, 0, 1)
        d = path("R25", [("UnitDistSq", U, T, [], 2000, 0, None, c0), ("PathDist", U, 2, [19], 0, 0, None, c0),
                         ("Idle", G, U, [203], 0, 0, None, c1), ("UnitIsDead", T, 0, [], 0, 0, None, c1),
                         ("QueueEvent", G, T, [12, 134 + 1728000, 0, 0], 1, 0, None, c1)], fr=134)
        ctl = bytearray(0x40)
        for off, v in zip((0x14, 0x18, 0x1C), c0):
            ctl[off:off + 4] = v.to_bytes(4, "little")
        d["aid"]["ctl"] = ctl.hex()
        self.ok("R25", d, forks=1)
        self.assertEqual(M.check(M.m_r25, d, flip="g.dead").status, "mismatch")
        self.assertEqual(M.check(M.m_r25, d, flip="4.T%67!=0").status, "mismatch")

    def test_r25_tables_from_the_spec(self):
        W = M.wisp_tables()
        self.assertEqual(W["A"][(6, 1)], (-10, -3))
        self.assertEqual(W["B"][(12, 4)], (0, 0))
        self.assertEqual(W["A5"][1], (-5, -5))
        self.assertEqual(W["B5"][1], W["A5"][3])
        self.assertEqual((len(W["A"]), len(W["B"])), (28, 28))

    def test_r27_not_melee(self):
        d = path("R27", [("Walk13", G, U, [T, 7], 1, 0)], ctl14=3)
        d["aib"][0]["c"][0] = 0                                 # v14 <- 0 before the walk
        self.ok("R27", d)

    def test_r72_melee_idle(self):
        d = path("R72", [("Idle", G, U, [9], 0, 1)], melee=1, aip={1: 0, 2: 9})
        self.ok("R72", d)

    def test_r74_search_then_hostile_then_idle_or_t56(self):
        # dist 50: not near; no hostile; 50 < aip(8) 60, so no wander test; D100 > 69: Idle(10), else T56(t, 3, 0)
        blk = {"0": [0, 0, 2500, 0x7FFFFFFF, 0x7FFFFFFF]}
        last = ("Idle", G, U, [10], 0, 1) if low(100) % 100 > 69 else ("T56", G, U, [T, 3, 0], 1, 1)
        d = path("R74", [("UnitSearch", G, U, [0, 0x005FAE40, 1], 0, 0, blk), ("FindHostile", G, U, [0, 0], 0, 0), last],
                 dist=50, aip={1: 6, 8: 60})
        self.ok("R74", d)
        d["aib"][0]["b"]["0"][2] = 2401
        self.bad("R74", d)                                      # the search block's r2 word is compared

    def test_r115_death_mode_returns(self):
        d = path("R115", [("UnitGetOwner", G, U, [], 0, 0), ("MonIsDeathMode", 0, 0, [U], 1, 0)])
        self.ok("R115", d)

    def test_r116_no_head_melee(self):
        d = path("R116", [("ParamsHead", U, 0, [], 0, 0), ("Idle", G, U, [7], 0, 1)], melee=1, aip={1: 0, 2: 7})
        self.ok("R116", d)

    def test_r117_timer_dies(self):
        d = path("R117", [("SetModeAtUnit", G, U, [0, T], 1, 0)], ctl14=50)
        self.ok("R117", d)
        d["aid"]["ctl"] = ("00" * 0x14) + M.u32(500).to_bytes(4, "little").hex() + "00" * 0x28
        d["aib"][0]["c"][0] = 500
        self.bad("R117", d)                                     # T 100 < v14 500: the idle, not mode 0

    def test_r119_melee_step(self):
        # t present but the flag fork aside: dist 10 >= aip(4) 5, so step 1 fails with no draw; melee: chance(3) 100,
        # StepAway(t, 5, 1) succeeds
        d = path("R119", [("StepAway", G, U, [T, 5, 1], 1, 1)], melee=1, dist=10, aip={3: 100, 4: 5})
        self.ok("R119", d, forks=1)

    def test_r120_search_count_walk(self):
        # no stored hostile (fork), not melee; the search's count 2 and dist 30 > aip(4) + aip(5) = 24: Walk(t, 0)
        blk = ({"0": [576, 400, 50, 0, 0, 0]}, {"0": [576, 400, 50, 0, 0, 2, 0, 0]})
        d = path("R120", [("UnitSearch", G, U, [0, 0x005E26D0, 1], 0, 0, blk), ("Walk", G, U, [T, 0], 1, 0)],
                 dist=30, aip={4: 17, 5: 7}, sk=sk_hex([-1, -1, 0, -1, -1, -1, -1, -1]))
        self.ok("R120", d, forks=1)

    def test_r122_no_host_idle(self):
        # v14 = -1, not melee, Skill1 < 0: D100 < R3.aip(2), D100 < 33, D100 < 20 drawn as the seed falls
        r3a2 = IMP[3][0][3]
        d1 = low(100, 1) % 100
        if d1 < r3a2 or low(100, 2) % 100 < 33 or low(100, 3) % 100 < 20:
            self.skipTest("the seed takes another arm")
        d = path("R122", [("Idle", G, U, [10], 0, 3)], dist=1, ctl14=-1, sk=sk_hex([-1] * 8))
        self.ok("R122", d)

    def test_r123_null_target(self):
        mode_call = low(100) % 100 < 22
        d = path("R123", [("SetModeAtUnit", G, U, [4, 0], 1, 1)] if mode_call else [("Idle", G, U, [15], 0, 1)],
                 aip={1: 22})
        self.ok("R123", d)

    def test_s16_not_attached(self):
        d = path("S16", [("UnitGetOwner", G, U, [], 0x7200000, 0), ("HasState", 0, 0, [U, 143], 0, 0),
                         ("MonAiInit", G, U, [CTL, 0], 0, 0), ("Idle", G, U, [1], 0, 0)])
        self.ok("S16", d)

    def test_r126_cooldown_idle(self):
        # v1C = 0: no draw; the dead test's room, the fork says alive; v1C <- 1; aip(2) 50 - T 100 + 1 < 0, so on: no
        # target -> Idle(aip(2))
        d = path("R126", [("UnitGetRoom", 0, 0, [U], 0x7300000, 0), ("Idle", G, U, [50], 0, 0)], aip={2: 50})
        d["aid"]["ctx"][2] = 0
        d["aib"][1]["c"][2] = 1
        self.ok("R126", d, forks=1)

    def test_r129_no_target(self):
        d = path("R129", [("Idle", G, U, [20], 0, 0)])
        d["aid"]["ctx"][2] = 0
        self.ok("R129", d)

    def test_r136_taunt_on_the_eleventh(self):
        d = path("R136", [("UseSkill", G, U, [4, 284, T, 0, 0], 1, 0)], ctl14=10, aip={2: 10})
        d["aid"]["t"] = [0, 1, 4, 1, 12, 22, 0]
        d["aib"][0]["c"][0] = 0                                 # v14 <- 0 after the eleventh
        self.ok("R136", d)

    def test_r137_search_impregnate(self):
        d = path("R137", [("UnitSearch", G, U, [0, 0x005EFA50, 1], 0x7200000, 0, {"0": [0, 25]}),
                          ("InMeleeRange", 0, 0, [U, 0x7200000, 0], 1, 0), ("UseSkill", G, U, [8, 300, 0x7200000, 0, 0], 1, 0)])
        d["aib"][0]["b"] = {"0": [0, 25, 0, 0, 0, 0, 0, 0]}
        self.ok("R137", d)

    def test_s5_town_ring_or_idle(self):
        ring = low(100) % 100 < 20
        d = path("S5", [("UnitGetRoom", 0, 0, [U], 0x7300000, 0), ("RoomIsTown", 0, 0, [0x7300000], 1, 0),
                        ("Ring", G, U, [5], 0, 1) if ring else ("Idle", G, U, [10], 0, 1)], st=5)
        self.ok("S5", d)
        self.ok("R60", d)

    def test_s6_mode_not_1(self):
        d = path("S6", [("Idle", G, U, [5], 0, 0)], m=2)
        self.ok("S6", d)

    def test_r41_home_unset(self):
        d = path("R41", [("Idle", G, U, [20], 0, 0)])
        self.ok("R41", d, forks=1)

    def test_r42_vendor(self):
        cmd = low(100) % 100 < 20
        d = path("R42", [("SetMode", G, U, [8, 0, 0], 1, 1)] if cmd else [("Idle", G, U, [30], 0, 1)])
        self.ok("R42", d)

    def test_r58_hostile_attack(self):
        d = path("R58", [("FindHostile", G, U, [0, 0], 0x7200000, 0, {"0": [24]}), ("SetModeAtUnit", G, U, [4, 0x7200000], 1, 0)])
        self.ok("R58", d, forks=2)


class Revision4(unittest.TestCase):
    """The engine additions: a call on another unit's word, the opaque seed and the state selection."""

    def test_edx_override(self):
        q = M.CONV["QueueEvent"][0]
        d = decision([(q, G, T, [12, 5, 0, 0], 1, SEED)])
        self.assertEqual(M.check(lambda r: r.call("q", "QueueEvent", _edx=r.t, kind=12, frame=5, a=0, b=0), d).status, "ok")
        self.assertEqual(M.check(lambda r: r.call("q", "QueueEvent", kind=12, frame=5, a=0, b=0), d).status, "mismatch")

    def test_opaque_resyncs_at_the_next_call(self):
        s2 = ai.step(ai.step(SEED))
        d = decision([(IDLE, G, U, [1], 0, s2, s2)], exit_seed=s2)

        def model(r):
            r.opaque("x")
            r.call("idle", "Idle", n=1)
        self.assertEqual(M.check(model, d).status, "ok")
        self.assertEqual(M.check(lambda r: r.call("idle", "Idle", n=1), d).status, "mismatch")

        def draws(r):
            r.opaque("x")
            r.step()
        self.assertEqual(M.check(draws, decision([], exit_seed=s2)).status, "stop")

    def test_select_by_state(self):
        self.assertTrue(M.SELECT["S5"]({"st": 5}))
        self.assertFalse(M.SELECT["R60"]({"st": 5}))
        self.assertTrue(M.SELECT["R117"]({"st": 0}))
        self.assertFalse(M.SELECT["S15"]({"st": 0}))
        self.assertNotIn("R12", M.SELECT)


def report():
    """`python3 -I tools/test_ai_model_check.py report`: per revision 4 entry, over the recorder's 1500 seeded decisions,
    how many stop, how many the unforked check decides (no unknown branch on the matching path), and the branches run and
    separated."""
    M.IMP_RECS = IMP
    for n in NEW:
        rep = branch_report(n)
        if "bad" in rep:
            print("ENTRY %s BAD %s" % (n, rep["bad"]))
            continue
        left = sorted(rep["seen"] - rep["failed"])
        print("ENTRY %-5s recorded %4d stopped %4d fork-free %4d branches %3d separated %3d exempt %s" % (
            n, rep["decided"], rep["stopped"], rep["free"], len(rep["seen"]), len(rep["failed"]), ",".join(left) or "-"))


if __name__ == "__main__":
    if sys.argv[1:] == ["report"]:
        report()
        sys.exit(0)
    unittest.main()

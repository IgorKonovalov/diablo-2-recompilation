"""No-game tests of tools/ai_model_check.py (plan 0066 batch S1b): the engine on hand-built decisions (an AID line,
its AIB calls and AIR returns, an AIX exit), with the R3 Zombie and R12 Goatman models and two toy models.

    python3 -I tools/test_ai_model_check.py
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


if __name__ == "__main__":
    unittest.main()

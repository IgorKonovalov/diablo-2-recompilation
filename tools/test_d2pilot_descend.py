"""Offline tests of tools/d2pilot.py's warp destinations (descend --descend-to) and the level-copy frontier
(--all-copies): python3 -I tools/test_d2pilot_descend.py (or python3 -I -m unittest discover -s tools -p
test_d2pilot_descend.py).

Lane/rdp (backlog 2026-10-27, architect -> reverser). `descend` took the nearest logged warp of a LvlWarp row, and rows
51 (Spider Forest 76 -> the Arachnid Lair 84 or the Spider Cavern 85) and 61 (Kurast Bazaar 80 -> the Ruined Temple 94
or the Disused Fane 95) serve two levels each, so H6e2's eye4 reached 84 and tome4 95. LogState.warp_dest follows the
WRP line's room to its warp node (room +0x4C, node +0x00 the destination room, drlg/0007) and that room's level.

The synthetic cases need no game data. The kept-log cases replay the H6e2 logs (workspace/logs/h6e2, each checked
against its manifest line first) and are skipped when workspace/ is absent. Stdlib only, no harness, no slot.
"""
import hashlib
import io
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2pilot  # noqa: E402

LOGS = os.path.join(HERE, "..", "workspace", "logs", "h6e2")
MANIFESTS = ("manifest-final.sha256", "manifest-dev-final.sha256")


def state(lines):
    """A LogState fed the given log lines (no file)."""
    st = d2pilot.LogState(os.devnull)
    st.f.close()
    st.f = io.StringIO("\n".join(lines) + "\n")
    st.poll()
    return st


def kept(name):
    """The path of a kept H6e2 log, after its manifest line's sha256 is checked; None without workspace/."""
    path = os.path.join(LOGS, name)
    if not os.path.exists(path):
        return None
    want = None
    for m in MANIFESTS:
        mp = os.path.join(LOGS, m)
        if os.path.exists(mp):
            with open(mp) as fh:
                rows = fh.readlines()
            for line in rows:
                h, _, f = line.strip().partition("  ")
                if f == name:
                    want = h
    assert want is not None, "%s is in no manifest" % name
    with open(path, "rb") as fh:
        got = hashlib.sha256(fh.read()).hexdigest()
    assert got == want, "%s: sha256 %s, manifest %s" % (name, got, want)
    return path


class Replay:
    """Feed a log to a LogState one line at a time; until(pred) stops at the first line for which pred(st) holds."""

    def __init__(self, path):
        self.st = d2pilot.LogState(os.devnull)
        self.st.f.close()
        with open(path, errors="replace") as f:
            self.lines = iter(f.readlines())

    def step(self):
        line = next(self.lines, None)
        if line is None:
            return False
        self.st.f = io.StringIO(line if line.endswith("\n") else line + "\n")
        self.st.poll()
        return True

    def until(self, pred):
        while self.step():
            if pred(self.st):
                return True
        return False

    def end(self):
        while self.step():
            pass


def rl(level, room, x, y, lid=None):
    d = '"level":%d,%s"room":%d,"type":1,"rect":[%d,%d,8,8],"warps":[]' % (
        level, '"lid":%d,' % lid if lid is not None else "", room, x, y)
    return "RL {%s}" % d


def rreseed(room, lid, nodes):
    w = ",".join("[%d,%d,[%d,0,1,0,0,0,0,0]]" % (rec, rec, dst) for rec, dst in nodes)
    return 'RRESEED {"room":%d,"level":%d,"warps":[%s]}' % (room, lid, w)


def wrp(room, lid, x, y, rec, dx=10, dy=10):
    return 'WRP {"room":%d,"lid":%d,"rect":[%d,%d,8,8],"dx":%d,"dy":%d,"rec":%d}' % (room, lid, x, y, dx, dy, rec)


# level pointers 1..3 (76, 84, 85), rooms 100/101 in 76 with a row-51 warp each, 200 in 84, 300 in 85
def two_warps(with_lid):
    lid = (lambda v: v) if with_lid else (lambda v: None)
    return [rl(1, 100, 0, 0, lid(76)), rl(1, 101, 40, 0, lid(76)), rl(2, 200, 100, 0, lid(84)),
            rl(3, 300, 200, 0, lid(85)),
            rreseed(100, 76, [(51, 200)]), wrp(100, 76, 0, 0, 51),
            rreseed(101, 76, [(51, 300)]), wrp(101, 76, 40, 0, 51)]


class SyntheticTest(unittest.TestCase):
    A, B = (10, 10), (210, 10)          # the two warp cells: 5 * tile + offset

    def test_default_takes_every_warp_of_the_row(self):
        st = state(two_warps(True))
        self.assertEqual(sorted(d2pilot.descend_cells(st, 76, {51})), [self.A, self.B])
        self.assertEqual(d2pilot.descend_cells(st, 76, {57}), [])

    def test_destination_from_rl_lid(self):
        st = state(two_warps(True))
        self.assertEqual(st.warp_dest((76, 51) + self.A), 84)
        self.assertEqual(st.warp_dest((76, 51) + self.B), 85)
        self.assertEqual(d2pilot.descend_cells(st, 76, {51}, dest=85), [self.B])
        self.assertEqual(d2pilot.descend_cells(st, 76, {51}, dest=84), [self.A])
        self.assertEqual(d2pilot.descend_cells(st, 76, {51}, dest=90), [])     # both known, neither leads there

    def test_old_logger_unknown_until_visited(self):
        st = state(two_warps(False))
        self.assertIsNone(st.warp_dest((76, 51) + self.A))
        self.assertEqual(sorted(d2pilot.descend_cells(st, 76, {51}, dest=85)), [self.A, self.B])
        # descend() marks a warp that led elsewhere wrong; the other one is left
        self.assertEqual(d2pilot.descend_cells(st, 76, {51}, dest=85, wrong={(76,) + self.A}), [self.B])
        # once a room of 84 is activated, its pointer's level is known and the 84 warp is dropped
        st.f = io.StringIO(rreseed(200, 84, [(52, 100)]) + "\n")
        st.poll()
        self.assertEqual(st.warp_dest((76, 51) + self.A), 84)
        self.assertEqual(d2pilot.descend_cells(st, 76, {51}, dest=85), [self.B])

    def test_any_row_back(self):
        st = state(two_warps(True) + [rreseed(200, 84, [(52, 100)]), wrp(200, 84, 100, 0, 52)])
        self.assertEqual(d2pilot.descend_cells(st, 84, d2pilot.ANY_ROW, dest=76), [(510, 10)])

    def test_two_nodes_of_the_row_to_two_levels(self):
        st = state(two_warps(True) + [rreseed(100, 76, [(51, 200), (51, 300)])])
        self.assertIsNone(st.warp_dest((76, 51) + self.A))

    def test_all_copies_frontier(self):
        lines = [rl(1, 100, 0, 0), rl(1, 101, 8, 0), rl(2, 500, 0, 0), rl(2, 501, 8, 0),
                 rreseed(100, 91, []), rreseed(500, 91, []), rreseed(501, 91, [])]
        st = state(lines)
        self.assertEqual(st.frontier(91), [])                   # the last RRESEED's copy: both rooms activated
        try:
            d2pilot.LogState.all_copies = True
            self.assertEqual([r for r, _ in st.frontier(91)], [101])
        finally:
            d2pilot.LogState.all_copies = False


# Every level change by a logged warp in the H6e2 logs: (log, from, to, LvlWarp row), from the replay below
ARRIVALS = [
    ("dev-quest-items-s1-4912-staff4.log", [(43, 62, 47), (62, 63, 49), (63, 64, 49)]),
    ("dev-quest-items-s1-4912-staff-nm4.log", [(43, 62, 47), (62, 63, 49), (63, 64, 49)]),
    ("dev-quest-items-s1-4914-brain4b.log", [(78, 88, 54), (88, 89, 56), (89, 91, 56)]),
    ("dev-quest-items-s1-4915-eye4.log", [(76, 84, 51)]),
    ("quest-items-s1-4904-radament4.log", [(48, 49, 23)]),
    ("quest-items-s1-4911-cube4.log", [(57, 60, 46)]),
    ("quest-items-s1-4911-cube-held4.log", [(57, 60, 46)]),
    ("quest-items-s1-4913-heart4.log", [(80, 92, 57), (92, 93, 60)]),
    ("quest-items-s1-4913-tome4.log", [(80, 95, 61)]),
    ("quest-items-s1-4914-brain4.log", [(78, 88, 54), (88, 89, 56), (89, 91, 56)]),
    ("quest-items-s1-4916-staff4b.log", [(43, 62, 47), (62, 63, 49), (63, 64, 49)]),
    ("quest-items-s1-4916-staff-nm4b.log", [(43, 62, 47), (62, 63, 49), (63, 64, 49)]),
]


class KeptLogTest(unittest.TestCase):

    def need(self, name):
        p = kept(name)
        if p is None:
            self.skipTest("workspace/logs/h6e2 absent")
        return p

    def pair(self, name, lid0, row, got, other):
        """Up to the first WRP of row on lid0: the destination is not yet known (no RL "lid" in these logs), so
        --descend-to other keeps the warp as a candidate; its node's destination room is already logged (RL), and
        that room's level pointer is the one the arrival's RRESEED names for got. At the end of the log the warp is
        known to lead to got: --descend-to other drops it, --descend-to got keeps it."""
        r = Replay(self.need(name))
        self.assertTrue(r.until(lambda st: any(k[0] == lid0 and k[1] == row for k in st.wrp)))
        st = r.st
        key = [k for k in st.wrp if k[0] == lid0 and k[1] == row][0]
        self.assertIsNone(st.warp_dest(key))
        self.assertEqual(d2pilot.descend_cells(st, lid0, {row}, dest=other), [key[2:]])
        dst = [n[2][0] for n in st.warps[st.wrp_room[key]] if n[0] == row]
        self.assertEqual(len(dst), 1)
        ptr = st.rl[dst[0]][0]
        r.end()
        self.assertEqual(r.st.ptr_lid.get(ptr), got)
        self.assertEqual(r.st.warp_dest(key), got)
        cells = [k[2:] for k in r.st.wrp if k[0] == lid0 and k[1] == row]
        self.assertEqual(d2pilot.descend_cells(r.st, lid0, {row}, dest=other), [])
        self.assertEqual(sorted(d2pilot.descend_cells(r.st, lid0, {row}, dest=got)), sorted(cells))

    def test_eye4_row_51_led_to_84(self):
        self.pair("dev-quest-items-s1-4915-eye4.log", 76, 51, 84, 85)

    def test_tome4_row_61_led_to_95(self):
        self.pair("quest-items-s1-4913-tome4.log", 80, 61, 95, 94)

    def test_every_logged_descent(self):
        """For every level change of the H6e2 logs made next to a logged warp (within 8 sub-tiles of the last
        position), warp_dest of that warp, taken at the end of the log, is the level arrived in: 25 descents."""
        n = 0
        for name, want in ARRIVALS:
            r = Replay(self.need(name))
            got, prev = [], None
            while r.step():
                st = r.st
                if st.pos and prev and st.pos[2] != prev[2]:
                    ks = [k for k in st.wrp if k[0] == prev[2]]
                    if ks:
                        k = min(ks, key=lambda k: math.hypot(k[2] - prev[0], k[3] - prev[1]))
                        if math.hypot(k[2] - prev[0], k[3] - prev[1]) <= 8:
                            got.append((prev[2], st.pos[2], k))
                prev = st.pos
            self.assertEqual([(a, b, k[1]) for a, b, k in got], want, name)
            for a, b, k in got:
                self.assertEqual(r.st.warp_dest(k), b, (name, a, b, k))
                n += 1
        self.assertEqual(n, 25)

    def test_brain_frontier_copies(self):
        """Level 91 (LvlPrest 704): the default frontier (the copy of the last RRESEED) is empty at the end of both
        brain sessions, though the other copy left rooms unactivated, the chest's room (tile offset 0, 32) among them."""
        for name, left in (("quest-items-s1-4914-brain4.log", 11), ("dev-quest-items-s1-4914-brain4b.log", 4)):
            r = Replay(self.need(name))
            r.end()
            st = r.st
            self.assertEqual(len(st.copies[91]), 2, name)
            self.assertEqual(st.frontier(91), [], name)
            try:
                d2pilot.LogState.all_copies = True
                fr = st.frontier(91)
            finally:
                d2pilot.LogState.all_copies = False
            self.assertEqual(len(fr), left, name)
            self.assertIn([2000, 2372, 8, 8], [rect for _, rect in fr], name)


if __name__ == "__main__":
    unittest.main()

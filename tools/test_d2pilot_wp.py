"""No-game test of tools/d2pilot.py's waypoint click (plan 0052 Phase 2, lane/p52d): python3 -I tools/test_d2pilot_wp.py.

A fake pilot (dark share of the list's panel, a click log, the player's position) and a fake clock replay the two
starts the harness met: the screen still black at the first click (the old `menu_open` was true at once and the tab
and row clicks hit the ground), and a lit screen. Nothing is launched.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d2pilot  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakePilot:
    """share(t) gives the dark share at clock time t; a click at the waypoint (the first, or any if `every`) makes the
    list open `walk` seconds later (the walk to the waypoint)."""

    def __init__(self, clock, black_until=0.0, walk=3.7, ignore_first_click=False):
        self.c, self.black_until, self.walk = clock, black_until, walk
        self.clicks, self.opened_at, self.ignore = [], None, ignore_first_click

    def menu_share(self):
        if self.c.now() < self.black_until:
            return 1.0
        if self.opened_at is not None and self.c.now() >= self.opened_at:
            return 0.96
        return 0.14

    def click_at(self, x, y, button=1):
        self.clicks.append((round(self.c.now(), 2), x, y))
        if self.ignore and len(self.clicks) == 1:
            return
        if self.opened_at is None:
            self.opened_at = self.c.now() + self.walk


class FakeState:
    def __init__(self, clock):
        self.c = clock
        self.pos = (5048, 5043, 103, 1)

    def poll(self):
        pass


def run(p, c, **kw):
    return d2pilot.wp_click_until_open(p, FakeState(c), 715, 58, clock=c.now, sleep=c.sleep, **kw)


class WaypointClick(unittest.TestCase):
    def test_lit_start_one_click(self):
        c = Clock()
        p = FakePilot(c)
        r = run(p, c)
        self.assertTrue(r["opened"])
        self.assertEqual(len(p.clicks), 1)
        self.assertGreater(r["t_open"], 3.5)

    def test_black_start_waits_for_the_light_before_the_click(self):
        c = Clock()
        p = FakePilot(c, black_until=6.0)
        r = run(p, c)
        self.assertTrue(r["opened"])
        self.assertEqual(len(p.clicks), 1)
        self.assertGreaterEqual(p.clicks[0][0], 6.0)                  # the click came after the screen lit
        self.assertGreater(r["t_open"], 3.5)                          # and the list was not taken at t = 0
        self.assertAlmostEqual(r["lit_wait"], 6.0, delta=0.3)

    def test_the_old_rule_would_have_taken_black_for_the_list(self):
        c = Clock()
        p = FakePilot(c, black_until=6.0)
        self.assertGreater(p.menu_share(), 0.75)                      # what menu_open() saw at the first click

    def test_a_lost_first_click_is_clicked_again_in_the_same_process(self):
        c = Clock()
        p = FakePilot(c, ignore_first_click=True)
        r = run(p, c)
        self.assertTrue(r["opened"])
        self.assertEqual(len(p.clicks), 2)
        self.assertEqual(r["clicks"], 2)

    def test_a_slow_walk_is_waited_for_not_clicked_again(self):
        c = Clock()
        p = FakePilot(c, walk=11.0)                     # the player keeps walking past the first 8 s
        st = FakeState(c)
        st.poll = lambda: setattr(st, "pos", (5048 - int(c.now()), 5043, 103, 1))    # one step a second
        r = d2pilot.wp_click_until_open(p, st, 715, 58, clock=c.now, sleep=c.sleep)
        self.assertTrue(r["opened"])
        self.assertEqual(len(p.clicks), 1)

    def test_never_opens(self):
        c = Clock()
        p = FakePilot(c, walk=1e9)
        r = run(p, c)
        self.assertFalse(r["opened"])
        self.assertEqual(len(p.clicks), 2)                            # one retry, then it gives up
        self.assertLess(c.now(), 40)

    def test_a_black_screen_that_never_lights_gives_up(self):
        c = Clock()
        p = FakePilot(c, black_until=1e9)
        r = run(p, c)
        self.assertFalse(r["opened"])
        self.assertEqual(len(p.clicks), 0)                            # no click into a black screen


if __name__ == "__main__":
    unittest.main()

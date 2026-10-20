"""Self-test for tools/joiner.py and the PLRS handling of tools/d2pilot.py (plan 0044 Phase 1):
python3 -I tools/test_joiner.py (or python3 -I -m unittest discover -s tools -p test_joiner.py).

Needs neither wine, a display nor workspace/: the logs are written to a scratch directory, no game is launched and no
X display is opened (d2pilot's Pilot is never built).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import joiner  # noqa: E402


def plrs(players, parties=(), t=0.0):
    return "PLRS " + json.dumps({"t": t, "p": players, "pty": list(parties)}, separators=(",", ":"))


def unit(uid, x, y, lid=1, cls=1, tk=0, hl=(), room=0x1000, dead=0, mode=1):
    return {"id": uid, "cls": cls, "mode": mode, "x": x, "y": y, "room": room, "lid": lid, "dead": dead, "tk": tk,
            "hl": [list(h) for h in hl]}


class Plrs(unittest.TestCase):
    def test_parse(self):
        d = joiner.parse_plrs(plrs([unit(1, 10, 20)]))
        self.assertEqual(d["p"][0]["x"], 10)
        self.assertIsNone(joiner.parse_plrs("PLR {\"x\":1}"))
        self.assertIsNone(joiner.parse_plrs("PLRS not json"))
        self.assertIsNone(joiner.parse_plrs('PLRS {"q":1}'))

    def test_roles_follow_first_appearance(self):
        pl = joiner.Players()
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1)])))
        self.assertEqual(pl.resolve("host"), 7)
        self.assertIsNone(pl.resolve("join"))
        pl.feed(joiner.parse_plrs(plrs([unit(3, 5, 5), unit(7, 1, 1)])))   # list order is hash order, not join order
        self.assertEqual(pl.resolve("host"), 7)
        self.assertEqual(pl.resolve("join"), 3)
        self.assertEqual(pl.resolve("0x3"), 3)
        self.assertEqual(pl.get("join")["x"], 5)
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1)])))                  # the joiner left
        self.assertIsNone(pl.get("join"))
        self.assertEqual(pl.resolve("join"), 3)
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1), unit(9, 2, 2)])))   # it rejoined with a new unit id
        self.assertEqual(pl.resolve("join"), 9)
        self.assertEqual(pl.get("join")["x"], 2)

    def test_party(self):
        pl = joiner.Players()
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1), unit(3, 2, 2)])))
        self.assertIsNone(pl.party_of("join"))
        self.assertFalse(pl.same_party("join", "host"))
        self.assertTrue(joiner.party_done(pl, "leave", "join", "host"))
        self.assertFalse(joiner.party_done(pl, "accept", "join", "host"))
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1), unit(3, 2, 2)], [{"id": 0, "m": [7, 3]}])))
        self.assertEqual(pl.party_of("join"), 0)
        self.assertTrue(joiner.party_done(pl, "accept", "join", "host"))
        self.assertFalse(joiner.party_done(pl, "leave", "join", "host"))
        self.assertTrue(joiner.party_done(pl, "invite", "join", "host"))

    def test_hostile_seen_by_tick(self):
        pl = joiner.Players()
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1), unit(3, 2, 2, tk=100)])))
        self.assertFalse(joiner.party_done(pl, "hostile", "join", "host", tk0=100))
        pl.feed(joiner.parse_plrs(plrs([unit(7, 1, 1), unit(3, 2, 2, tk=5100, hl=[(7, 65100)])])))
        self.assertTrue(joiner.party_done(pl, "hostile", "join", "host", tk0=100))
        with self.assertRaises(ValueError):
            joiner.party_done(pl, "dance", "join", "host")

    def test_read_players(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "host.log")
            with open(p, "w") as f:
                f.write("GPTR {\"game\":1}\n" + plrs([unit(9, 1, 1)]) + "\nnoise\n" + plrs([unit(9, 1, 1), unit(4, 3, 3)])
                        + "\n")
            pl = joiner.read_players(p)
            self.assertEqual(pl.order, [9, 4])


class Follow(unittest.TestCase):
    def test_near_far_level(self):
        self.assertIsNone(joiner.follow_step(unit(1, 100, 100), unit(2, 104, 95)))
        self.assertEqual(joiner.follow_step(unit(1, 100, 100), unit(2, 108, 100)), ("move", 8, 0))
        self.assertEqual(joiner.follow_step(unit(1, 100, 100), unit(2, 140, 120)), ("move", 10, 5))
        self.assertEqual(joiner.follow_step(unit(1, 100, 100), unit(2, 60, 100), hop=12), ("move", -12, 0))
        self.assertEqual(joiner.follow_step(unit(1, 0, 0, lid=1), unit(2, 0, 0, lid=2)), ("level", 1, 2))
        # --cross (plan 0044 Phase 2): an outdoor border is crossed like any other move
        self.assertEqual(joiner.follow_step(unit(1, 100, 100, lid=2), unit(2, 140, 100, lid=3), cross=True),
                         ("move", 10, 0))
        self.assertEqual(joiner.follow_step(None, unit(2, 0, 0))[0], "wait")
        self.assertEqual(joiner.follow_step(unit(1, None, None), unit(2, 0, 0))[0], "wait")

    def test_screen(self):
        self.assertEqual(joiner.screen(400, 290, 0, 0), (400, 290))
        self.assertEqual(joiner.screen(400, 290, 10, 0), (560, 370))
        self.assertEqual(joiner.screen(400, 290, 0, 10), (240, 370))
        self.assertEqual(joiner.clamp_click(900, -5), (790, 10))


class Gates(unittest.TestCase):
    def test_waypoint_and_portal(self):
        self.assertFalse(joiner.gate_open("waypoint", 1000 + 9999, 1000))
        self.assertTrue(joiner.gate_open("waypoint", 1000 + 10000, 1000))
        self.assertFalse(joiner.gate_open("portal", 1000 + 4999, 1000))
        self.assertTrue(joiner.gate_open("portal", 1000 + 5000, 1000))
        self.assertTrue(joiner.gate_open("portal", 123456789, 0))           # tick 0 (never written): open once up 5 s

    def test_u32_wrap(self):
        tk = 0xFFFFF000
        self.assertTrue(joiner.gate_open("portal", 0x00000388, tk))
        self.assertFalse(joiner.gate_open("portal", 0x00000387, tk))


class Steps(unittest.TestCase):
    def test_plan_0011_files(self):
        for a in ("invite", "accept", "leave"):
            cmds = joiner.read_steps(joiner.STEPS[a])
            self.assertEqual(cmds[0], ["key", "p"])
            self.assertEqual(cmds[-1], ["key", "p"])
            self.assertTrue(any(c[0] == "click" for c in cmds))
        self.assertIn(["click", "297", "141"], joiner.read_steps(joiner.STEPS["accept"]))
        self.assertIn(["click", "333", "87"], joiner.read_steps(joiner.STEPS["leave"]))

    def test_hostile_file(self):
        cmds = joiner.read_steps(joiner.STEPS["hostile"])
        self.assertEqual([c[0] for c in cmds], ["key", "sleep", "click", "sleep", "shot", "key"])

    def test_type_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "s.steps")
            with open(p, "w") as f:
                f.write("# c\ntype 127.0.0.1  # ip\n\nclick 1 2\n")
            self.assertEqual(joiner.read_steps(p), [["type", "127.0.0.1"], ["click", "1", "2"]])


class Trade(unittest.TestCase):
    def test_plan(self):
        acts = joiner.plan_trade(["request", "sleep:1", "give:inv:0,0>tr:2,1", "ok", "key:Escape", "shot:/x.png"],
                                 lead_xy=(450, 250))
        self.assertEqual(acts[0], ("click", 450, 250, 1))
        self.assertEqual(acts[1], ("sleep", 1.0))
        self.assertEqual(acts[2], ("click", 418 + 14, 316 + 14, 1))
        x0, y0 = joiner.TRADE_UI["grid"][:2]
        self.assertEqual(acts[3], ("click", x0 + 2 * 29 + 14, y0 + 29 + 14, 1))
        self.assertEqual(acts[4], ("click",) + joiner.TRADE_UI["ok"] + (1,))
        self.assertEqual(acts[5:], [("key", "Escape"), ("shot", "/x.png")])

    def test_errors(self):
        with self.assertRaises(ValueError):
            joiner.plan_trade(["request"])
        with self.assertRaises(ValueError):
            joiner.plan_trade(["give:inv:9,0,2,1>tr:0,0"])
        with self.assertRaises(ValueError):
            joiner.plan_trade(["wave"])


class Pilot(unittest.TestCase):
    """d2pilot.py's LogState with --me, and `join where`, on a written log (no display)."""

    def test_logstate_me(self):
        import d2pilot
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "host.log")
            with open(p, "w") as f:
                f.write('PLR {"th":1,"room":1,"lid":1,"x":10,"y":10}\n')
                f.write(plrs([unit(7, 10, 10)]) + "\n")
                f.write('PLR {"th":1,"room":1,"lid":1,"x":50,"y":50}\n')
                f.write(plrs([unit(7, 10, 10), unit(3, 50, 50, lid=2, room=0x2000)]) + "\n")
            old = d2pilot.LogState.me
            try:
                d2pilot.LogState.me = "join"
                st = d2pilot.LogState(p)
                st.poll()
                st.f.close()
                self.assertEqual(st.pos, (50, 50, 2, 0x2000))
                d2pilot.LogState.me = None
                st = d2pilot.LogState(p)
                st.poll()
                st.f.close()
                self.assertEqual(st.pos, (50, 50, 1, 1))                   # without --me: the last PLR, as before
                self.assertEqual(st.players.order, [7, 3])
            finally:
                d2pilot.LogState.me = old

    def test_join_where_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "host.log")
            with open(p, "w") as f:
                f.write(plrs([unit(7, 10, 10)]) + "\n")
                f.write(plrs([unit(7, 10, 10), unit(3, 30, 10)], [{"id": 1, "m": [7, 3]}]) + "\n")
            out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "d2pilot.py"), "join", p, "where",
                                  "--slot", "1", "--done-wait", "1"], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("player 3 join", out.stdout)
            self.assertIn("party 1", out.stdout)
            self.assertIn("('move', -10, 0)", out.stdout)


if __name__ == "__main__":
    unittest.main()

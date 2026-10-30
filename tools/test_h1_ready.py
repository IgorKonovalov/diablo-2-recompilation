"""Self-test for the start wait of tools/h1a_sessions.py and tools/h1c_sessions.py (lane/hx):
python3 -I tools/test_h1_ready.py.

The H1a/H1c steps file stays at the main menu, so the log holds no TBL line until the runner's first load. The
old wait counted three TBL lines and so always ran out its 120 s. The loggers now echo "RDY {...}" once every file
is sourced, before `continue`, and the runner waits for that line. The log prefix below has the shape of a kept
H1a dev log up to the attach (d2run header, gdb noise, the pilot's armed line); nothing is launched.
"""
import os
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import h1a_sessions  # noqa: E402
import h1c_sessions  # noqa: E402

PREFIX = [
    "# d2run seed=27201 gdb=tools/gdb/d2s-h1a.gdb steps=tools/gdb/h1a-menu.steps\n",
    "# installed x.d2s sha256=0000000000000000\n",
    "# game pid 1\n",
    "[New LWP 2 (id 2)]\n",
    "warning: Selected architecture i386:x86-64 is not compatible with reported target architecture i386:x64-32\n",
    "[Switching to thread 1 (LWP 1)]\n",
    "PILOT logger armed\n",
]
RDY = 'RDY {"logger":"d2s-h1a"}\n'
LOAD = ['TBL {"computed":1,"stored":1,"file_size":2,"count":3}\n'] * 3 + ['PLD {"code":0}\n']


def old_ready(log):
    """The wait this lane replaced."""
    return len(h1a_sessions.lines(log, "TBL")) >= 3


class ReadyWait(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.log = os.path.join(self.dir, "s.log")

    def write(self, rows):
        with open(self.log, "w") as f:
            f.writelines(rows)

    def test_old_wait_misses_the_menu(self):
        self.write(PREFIX + [RDY])
        self.assertFalse(old_ready(self.log))         # before the first case: never 3 TBL lines
        self.write(PREFIX + [RDY] + LOAD)
        self.assertTrue(old_ready(self.log))          # only after a load the runner itself starts

    def test_rdy_ends_the_wait_at_once(self):
        self.write(PREFIX + [RDY])
        t0 = time.time()
        self.assertTrue(h1a_sessions.wait_ready(self.log, 120, step=0.01))
        self.assertLess(time.time() - t0, 1)

    def test_rdy_written_later(self):
        self.write(PREFIX)
        n = {"polls": 0}

        def tick():
            n["polls"] += 1
            if n["polls"] == 3:
                with open(self.log, "a") as f:
                    f.write(RDY)
        self.assertTrue(h1a_sessions.wait_ready(self.log, 120, tick=tick, step=0.01))
        self.assertEqual(n["polls"], 3)

    def test_no_rdy_driver_gone(self):
        self.write(PREFIX)
        t0 = time.time()
        self.assertFalse(h1a_sessions.wait_ready(self.log, 120, gone=lambda: True, step=0.01))
        self.assertLess(time.time() - t0, 1)

    def test_no_rdy_timeout(self):
        self.write(PREFIX)
        self.assertFalse(h1a_sessions.wait_ready(self.log, 0.05, step=0.01))

    def test_missing_log(self):
        self.assertFalse(h1a_sessions.wait_ready(os.path.join(self.dir, "none.log"), 0.05, step=0.01))

    def test_h1c_shares_the_wait(self):
        self.assertIs(h1c_sessions.wait_ready, h1a_sessions.wait_ready)

    def test_loggers_echo_rdy_before_continue(self):
        for name in ("d2s-h1a", "d2s-h1c"):
            rows = [ln.strip() for ln in open(os.path.join(HERE, "gdb", name + ".gdb"))
                    if ln.strip() and not ln.startswith("#")]
            self.assertEqual(rows[-1], "continue", name)
            self.assertEqual(rows[-2], 'echo RDY {"logger":"%s"}\\n' % name, name)
            self.assertTrue(all(not r.startswith("source") for r in rows[rows.index(rows[-2]):]), name)
            # the echoed text is the runner's tag plus a space
            self.assertTrue(rows[-2][len("echo "):].startswith(h1a_sessions.READY + " "), name)

    def test_runners_wait_on_rdy(self):
        for mod in ("h1a_sessions.py", "h1c_sessions.py"):
            src = open(os.path.join(HERE, mod)).read()
            self.assertIn("wait_ready(log, 120", src, mod)
            self.assertNotIn('lines(log, "TBL")) >= 3', src, mod)


if __name__ == "__main__":
    unittest.main()

"""Self-test for tools/slots.py and the --slot handling of saves.py, d2run.py, xdrive.py, d2pilot.py and d2hunt.py:
python3 -I tools/test_slots.py (or python3 -I -m unittest discover -s tools -p test_slots.py).

Needs neither wine nor workspace/: every prefix is a stand-in directory tree under a scratch workspace, and the
"is the slot busy" check is replaced by a stub. Nothing is launched and no display is opened.
"""
import contextlib
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import saves  # noqa: E402
import slots  # noqa: E402

USER = "tester"


def fake_prefix(ws, n, saves_files=()):
    """A minimal prefix tree: registry files, a dosdevices symlink, the user's saves directory."""
    p = slots.prefix(n, ws)
    sd = slots.saves_dir(n, ws, USER)
    os.makedirs(sd)
    os.makedirs(os.path.join(p, "dosdevices"))
    os.symlink("../drive_c", os.path.join(p, "dosdevices", "c:"))
    os.makedirs(os.path.join(p, "drive_c", "windows"))
    with open(os.path.join(p, "drive_c", "windows", "win.ini"), "w") as f:
        f.write("[windows]\n")
    for reg in ("system.reg", "user.reg", "userdef.reg"):
        with open(os.path.join(p, reg), "w") as f:
            f.write("WINE REGISTRY Version 2\n")
    for name, data in saves_files:
        with open(os.path.join(sd, name), "wb") as f:
            f.write(data)
    return p


class MappingTest(unittest.TestCase):
    def test_slot_zero_is_the_historical_layout(self):
        ws = "/w"
        self.assertEqual(slots.display(0), ":7")
        self.assertEqual(slots.prefix(0, ws), "/w/wineprefix")
        self.assertEqual(slots.runtime(0, ws), "/w/runtime")
        self.assertEqual(slots.pidfile(0, ws), "/w/runtime/d2run-driver.pid")
        self.assertEqual(slots.suffix(0), "")

    def test_slot_n(self):
        ws = "/w"
        self.assertEqual(slots.display(1), ":8")
        self.assertEqual(slots.display(3), ":10")
        self.assertEqual(slots.prefix(2, ws), "/w/wineprefix-2")
        self.assertEqual(slots.runtime(2, ws), "/w/runtime/slot-2")
        self.assertEqual(slots.pidfile(2, ws), "/w/runtime/d2run-driver-slot2.pid")
        self.assertEqual(slots.suffix(2), "-s2")
        self.assertEqual(slots.saves_dir(1, ws, "u"), "/w/wineprefix-1/drive_c/users/u/Saved Games/Diablo II")

    def test_display_to_slot(self):
        self.assertEqual(slots.slot_of_display(":7"), 0)
        self.assertEqual(slots.slot_of_display(":9"), 2)
        self.assertEqual(slots.slot_of_display(":7.0"), 0)
        self.assertIsNone(slots.slot_of_display(":0"))
        self.assertIsNone(slots.slot_of_display(":%d" % (7 + slots.MAX_SLOT + 1)))

    def test_range(self):
        for bad in (-1, slots.MAX_SLOT + 1, "1"):
            with self.assertRaises(slots.SlotError):
                slots.display(bad)


class ResolveTest(unittest.TestCase):
    ws = "/w"

    def r(self, *a):
        return slots.resolve(*a, ws=self.ws)

    def test_defaults(self):
        self.assertEqual(self.r(None, None, None), (0, ":7", "/w/wineprefix"))
        self.assertEqual(self.r(2, None, None), (2, ":9", "/w/wineprefix-2"))

    def test_display_picks_slot_and_prefix(self):
        self.assertEqual(self.r(None, ":8", None), (1, ":8", "/w/wineprefix-1"))

    def test_agreeing_explicit_values(self):
        self.assertEqual(self.r(1, ":8", "/w/wineprefix-1"), (1, ":8", "/w/wineprefix-1"))
        self.assertEqual(self.r(0, ":7", "/w/wineprefix"), (0, ":7", "/w/wineprefix"))

    def test_conflicts(self):
        for args in ((1, ":7", None), (0, ":8", None), (1, None, "/w/wineprefix"), (0, None, "/w/wineprefix-1"),
                     (None, ":8", "/w/wineprefix"), (None, ":7", "/w/wineprefix-2")):
            with self.assertRaises(slots.SlotError, msg=repr(args)):
                self.r(*args)

    def test_legacy_prefix(self):
        # plan 0011's second client: a prefix outside the slots, kept as given
        self.assertEqual(self.r(None, ":8", "/w/wineprefix2"), (1, ":8", "/w/wineprefix2"))
        with self.assertRaises(slots.SlotError):
            self.r(None, ":20", None)  # outside the slots without a prefix
        self.assertEqual(self.r(None, ":20", "/w/p"), (None, ":20", "/w/p"))

    def test_pick_display(self):
        self.assertEqual(slots.pick_display(None, None), (0, ":7"))
        self.assertEqual(slots.pick_display(2, None), (2, ":9"))
        self.assertEqual(slots.pick_display(None, ":9"), (2, ":9"))
        self.assertEqual(slots.pick_display(None, ":0"), (None, ":0"))
        with self.assertRaises(slots.SlotError):
            slots.pick_display(1, ":7")

    def test_argv_slot(self):
        a = slots.argv_slot
        self.assertEqual(a(["python3", "-I", "tools/d2run.py", "--seed", "1", "--log", "x"], ws=self.ws), 0)
        self.assertEqual(a(["python3", "tools/d2run.py", "--slot", "2"], ws=self.ws), 2)
        self.assertEqual(a(["python3", "tools/d2run.py", "--slot=3"], ws=self.ws), 3)
        self.assertEqual(a(["python3", "tools/d2run.py", "--display", ":8"], ws=self.ws), 1)
        self.assertEqual(a(["d2run.py", "--prefix", "workspace/wineprefix-1", "--display", ":8"], cwd="/", ws="/workspace"), 1)
        self.assertIsNone(a(["d2run.py", "--prefix", "/w/wineprefix2", "--display", ":8"], ws=self.ws))
        self.assertIsNone(a(["d2run.py", "--slot", "1", "--display", ":7"], ws=self.ws))
        self.assertIsNone(a(["d2run.py", "--slot", "x"], ws=self.ws))


class BusyTest(unittest.TestCase):
    def test_busy_by_prefix_and_cmdline(self):
        with tempfile.TemporaryDirectory() as ws:
            fake_prefix(ws, 0)
            fake_prefix(ws, 1)
            p0, p1 = slots.prefix(0, ws), slots.prefix(1, ws)
            ps = [
                (101, 1, "S", ["Z:\\x\\game.exe", "-w"], {"WINEPREFIX": p0, "DISPLAY": ":7"}),
                (102, 1, "t", ["Z:\\x\\game.exe", "-w"], {"WINEPREFIX": p1, "DISPLAY": ":8"}),
                (103, 1, "Z", ["Z:\\x\\game.exe"], {"WINEPREFIX": p1}),  # zombie: ignored
                (201, 1, "S", ["python3", "-I", "tools/d2run.py", "--slot", "1"], {}),
                (202, 1, "S", ["python3", "-I", "tools/d2run.py", "--display", ":20", "--prefix", "/elsewhere"], {}),
                (203, 1, "S", ["python3", "-I", "tools/d2run.py", "--slot", "2"], {}),
            ]
            self.assertEqual(slots.busy(0, ws, ps), [101, 202])
            self.assertEqual(slots.busy(1, ws, ps), [102, 201, 202])
            self.assertEqual(slots.busy(2, ws, ps), [202, 203])


class CreateStopTest(unittest.TestCase):
    def test_create_skips_saves_and_keeps_symlinks(self):
        with tempfile.TemporaryDirectory() as ws:
            fake_prefix(ws, 0, [("a.d2s", b"secret")])
            os.makedirs(os.path.join(slots.prefix(0, ws), "drive_c", "users", USER, "Saved Games", "aside-x"))
            dst = slots.create(1, ws)
            self.assertEqual(dst, slots.prefix(1, ws))
            sg = os.path.join(dst, "drive_c", "users", USER, "Saved Games")
            self.assertEqual(os.listdir(sg), ["Diablo II"])
            self.assertEqual(os.listdir(os.path.join(sg, "Diablo II")), [])
            self.assertEqual(os.readlink(os.path.join(dst, "dosdevices", "c:")), "../drive_c")
            with open(os.path.join(dst, "drive_c", "windows", "win.ini")) as f:
                self.assertEqual(f.read(), "[windows]\n")
            self.assertTrue(os.path.isdir(slots.runtime(1, ws)))
            # the base is untouched
            self.assertEqual(os.listdir(slots.saves_dir(0, ws, USER)), ["a.d2s"])
            with self.assertRaises(slots.SlotError):
                slots.create(1, ws)  # exists
            with self.assertRaises(slots.SlotError):
                slots.create(0, ws)

    def test_stop_targets_only_its_prefix(self):
        with tempfile.TemporaryDirectory() as ws:
            fake_prefix(ws, 0)
            fake_prefix(ws, 2)
            os.makedirs(os.path.join(ws, "runtime"))
            with open(slots.pidfile(2, ws), "w") as f:
                f.write("999999999 game=1\n")  # no such process: not killed, pidfile removed
            calls = []
            with contextlib.redirect_stdout(io.StringIO()):
                slots.stop(2, ws, run=lambda cmd, env, **k: calls.append((cmd, env["WINEPREFIX"])))
            self.assertEqual(calls, [(["wineserver", "-k"], os.path.realpath(slots.prefix(2, ws)))])
            self.assertFalse(os.path.exists(slots.pidfile(2, ws)))
            with self.assertRaises(slots.SlotError):
                slots.stop(3, ws, run=lambda *a, **k: None)  # no prefix


def sha(b):
    return hashlib.sha256(b).hexdigest()


class SavesTest(unittest.TestCase):
    """saves.py on stand-in prefixes: each slot has its own saves directory, asides and manifests."""

    def setUp(self):
        self.ws = tempfile.mkdtemp()
        fake_prefix(self.ws, 0, [("base.d2s", b"slot0"), ("base.key", b"k0")])
        fake_prefix(self.ws, 1, [("one.d2s", b"slot1")])
        self.busy = saves.harness_busy
        saves.harness_busy = lambda: []
        self.user = saves.getpass.getuser
        saves.getpass.getuser = lambda: USER
        self.test_d2s = os.path.join(self.ws, "t.d2s")
        with open(self.test_d2s, "wb") as f:
            f.write(b"test")

    def tearDown(self):
        saves.harness_busy = self.busy
        saves.getpass.getuser = self.user
        saves.configure(0)
        shutil.rmtree(self.ws)

    def run_cmd(self, slot, fn, *a):
        saves.configure(slot, self.ws)
        os.makedirs(saves.RUNTIME, exist_ok=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            fn(*a)
        return out.getvalue()

    def listing(self, slot):
        d = slots.saves_dir(slot, self.ws, USER)
        out = {}
        for n in sorted(os.listdir(d)):
            with open(os.path.join(d, n), "rb") as f:
                out[n] = f.read()
        return out

    def test_configure_slot0_matches_historical_paths(self):
        saves.configure(0)
        root = os.path.dirname(HERE)
        self.assertEqual(saves.RUNTIME, os.path.join(root, "workspace", "runtime"))
        self.assertEqual(saves.SAVES, os.path.join(root, "workspace", "wineprefix", "drive_c", "users", USER,
                                                   "Saved Games", "Diablo II"))

    def test_per_slot_round_trip(self):
        self.run_cmd(1, saves.cmd_aside, "t1")
        self.assertEqual(self.listing(1), {})
        self.assertEqual(self.listing(0), {"base.d2s": b"slot0", "base.key": b"k0"})  # slot 0 untouched
        man = os.path.join(self.ws, "runtime", "slot-1", "saves-aside-t1.sha256")
        with open(man) as f:
            self.assertEqual(f.read(), "%s  one.d2s\n" % sha(b"slot1"))
        self.run_cmd(1, saves.cmd_install, "t1", [self.test_d2s])
        self.assertEqual(self.listing(1), {"t.d2s": b"test"})
        # the same tag is not aside in slot 0
        with self.assertRaises(SystemExit):
            self.run_cmd(0, saves.cmd_install, "t1", [self.test_d2s])
        with self.assertRaises(SystemExit):
            self.run_cmd(0, saves.cmd_restore, "t1")
        out = self.run_cmd(1, saves.cmd_status)
        self.assertIn("aside: saves-aside-t1", out)
        self.assertNotIn("t1", self.run_cmd(0, saves.cmd_status))
        self.run_cmd(1, saves.cmd_restore, "t1")
        self.assertEqual(self.listing(1), {"one.d2s": b"slot1"})
        self.assertFalse(os.path.exists(man))

    def test_reinstall_overwrites_the_rewritten_save(self):
        # run:2026-10-14-props: the game rewrites the installed save on exit; installing again puts it back
        self.run_cmd(1, saves.cmd_aside, "r")
        self.run_cmd(1, saves.cmd_install, "r", [self.test_d2s])
        with open(os.path.join(slots.saves_dir(1, self.ws, USER), "t.d2s"), "wb") as f:
            f.write(b"rewritten by the game")
        self.run_cmd(1, saves.cmd_install, "r", [self.test_d2s])
        self.assertEqual(self.listing(1), {"t.d2s": b"test"})
        self.run_cmd(1, saves.cmd_restore, "r")
        self.assertEqual(self.listing(1), {"one.d2s": b"slot1"})

    def test_install_ignores_only_the_named_pid(self):
        # tools/d2run.py --install runs while d2run itself counts as busy: it passes its own PID
        self.run_cmd(1, saves.cmd_aside, "p")
        saves.harness_busy = lambda: ["4242"]
        with self.assertRaises(SystemExit):
            self.run_cmd(1, saves.cmd_install, "p", [self.test_d2s])
        self.run_cmd(1, saves.cmd_install, "p", [self.test_d2s], (4242,))
        self.assertEqual(self.listing(1), {"t.d2s": b"test"})
        saves.harness_busy = lambda: ["4242", "77"]
        with self.assertRaises(SystemExit):
            self.run_cmd(1, saves.cmd_install, "p", [self.test_d2s], (4242,))
        saves.harness_busy = lambda: []
        self.run_cmd(1, saves.cmd_restore, "p")

    def test_empty_slot_round_trip(self):
        fake_prefix(self.ws, 2)  # a fresh `slots.py create 2`: empty saves directory
        self.assertEqual(self.listing(2), {})
        self.run_cmd(2, saves.cmd_aside, "e")
        base = os.path.join(self.ws, "runtime", "slot-2", "saves-aside-e")
        man = base + ".sha256"
        self.assertEqual(os.listdir(base), [])
        with open(man) as f:
            self.assertEqual(f.read(), "")
        self.assertIn("aside: saves-aside-e", self.run_cmd(2, saves.cmd_status))
        # a second aside under the same tag is still refused
        with self.assertRaises(SystemExit):
            self.run_cmd(2, saves.cmd_aside, "e")
        self.run_cmd(2, saves.cmd_install, "e", [self.test_d2s])
        self.assertEqual(self.listing(2), {"t.d2s": b"test"})
        self.run_cmd(2, saves.cmd_restore, "e")
        self.assertEqual(self.listing(2), {})
        self.assertFalse(os.path.exists(base))
        self.assertFalse(os.path.exists(man))
        self.assertIn("aside: none", self.run_cmd(2, saves.cmd_status))
        # other slots untouched
        self.assertEqual(self.listing(0), {"base.d2s": b"slot0", "base.key": b"k0"})
        self.assertEqual(self.listing(1), {"one.d2s": b"slot1"})

    def test_empty_slot0_still_refuses(self):
        d = slots.saves_dir(0, self.ws, USER)
        for n in os.listdir(d):
            os.remove(os.path.join(d, n))
        with self.assertRaises(SystemExit):
            self.run_cmd(0, saves.cmd_aside, "z")
        self.assertFalse(os.path.exists(os.path.join(self.ws, "runtime", "saves-aside-z")))
        self.assertFalse(os.path.exists(os.path.join(self.ws, "runtime", "saves-aside-z.sha256")))

    def test_slot0_aside_output_unchanged(self):
        out = self.run_cmd(0, saves.cmd_aside, "o")
        base = os.path.join(self.ws, "runtime", "saves-aside-o")
        self.assertEqual(out, "set aside 2 file(s) to %s; saves directory emptied\n" % base)
        with open(base + ".sha256") as f:
            self.assertEqual(f.read(), "%s  base.d2s\n%s  base.key\n" % (sha(b"slot0"), sha(b"k0")))
        self.assertEqual(self.listing(0), {})

    def test_two_slots_same_tag(self):
        self.run_cmd(0, saves.cmd_aside, "x")
        self.run_cmd(1, saves.cmd_aside, "x")
        self.assertTrue(os.path.isdir(os.path.join(self.ws, "runtime", "saves-aside-x")))
        self.assertTrue(os.path.isdir(os.path.join(self.ws, "runtime", "slot-1", "saves-aside-x")))
        self.run_cmd(1, saves.cmd_restore, "x")
        self.run_cmd(0, saves.cmd_restore, "x")
        self.assertEqual(self.listing(0), {"base.d2s": b"slot0", "base.key": b"k0"})
        self.assertEqual(self.listing(1), {"one.d2s": b"slot1"})

    def test_restore_verifies_per_slot(self):
        self.run_cmd(1, saves.cmd_aside, "v")
        with open(os.path.join(self.ws, "runtime", "slot-1", "saves-aside-v", "one.d2s"), "wb") as f:
            f.write(b"tampered")
        with self.assertRaises(SystemExit):
            self.run_cmd(1, saves.cmd_restore, "v")
        self.assertTrue(os.path.isdir(os.path.join(self.ws, "runtime", "slot-1", "saves-aside-v")))

    def test_empty_saves_round_trip(self):
        # a new slot's saves directory is empty: aside records an empty manifest, restore empties it again
        fake_prefix(self.ws, 2, [])
        self.run_cmd(2, saves.cmd_aside, "e")
        self.run_cmd(2, saves.cmd_install, "e", [self.test_d2s])
        self.assertEqual(self.listing(2), {"t.d2s": b"test"})
        self.run_cmd(2, saves.cmd_restore, "e")
        self.assertEqual(self.listing(2), {})
        self.assertFalse(os.path.exists(os.path.join(self.ws, "runtime", "slot-2", "saves-aside-e")))

    def test_busy_refuses(self):
        saves.harness_busy = lambda: ["4242"]
        with self.assertRaises(SystemExit):
            self.run_cmd(1, saves.cmd_aside, "b")
        self.assertEqual(self.listing(1), {"one.d2s": b"slot1"})

    def test_take_slot(self):
        self.assertEqual(saves.take_slot(["status"]), (0, ["status"]))
        self.assertEqual(saves.take_slot(["--slot", "2", "aside", "t"]), (2, ["aside", "t"]))
        self.assertEqual(saves.take_slot(["aside", "t", "--slot=1"]), (1, ["aside", "t"]))
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            saves.take_slot(["--slot", "99", "status"])


class CliConflictTest(unittest.TestCase):
    """The argument conflicts are refused by every tool before it touches wine or a display."""

    def run_tool(self, *argv):
        return subprocess.run([sys.executable, "-I", os.path.join(HERE, argv[0])] + list(argv[1:]),
                              capture_output=True, text=True, timeout=60)

    def test_d2run(self):
        r = self.run_tool("d2run.py", "--seed", "1", "--log", os.devnull, "--slot", "1", "--display", ":7")
        self.assertEqual(r.returncode, 2)
        self.assertIn("contradicts --slot 1", r.stderr)
        r = self.run_tool("d2run.py", "--seed", "1", "--log", os.devnull, "--slot", "0", "--prefix", "/nonexistent")
        self.assertEqual(r.returncode, 2)
        self.assertIn("contradicts --slot 0", r.stderr)
        r = self.run_tool("d2run.py", "--seed", "1", "--log", os.devnull, "--slot", str(slots.MAX_SLOT))
        self.assertEqual(r.returncode, 2)  # its prefix does not exist (never created)
        self.assertIn("slots.py create", r.stderr)

    def test_xdrive(self):
        r = self.run_tool("xdrive.py", "--slot", "2", "--display", ":8", "key", "Return")
        self.assertEqual(r.returncode, 2)
        self.assertIn("contradicts --slot 2", r.stderr)

    def test_d2pilot(self):
        r = self.run_tool("d2pilot.py", "where", os.devnull, "--slot", "1", "--display", ":7")
        self.assertEqual(r.returncode, 2)
        self.assertIn("contradicts --slot 1", r.stderr)

    def test_d2hunt(self):
        r = self.run_tool("d2hunt.py", "--slot", "1", "--display", ":9", "wpmenu")
        self.assertEqual(r.returncode, 2)
        self.assertIn("contradicts --slot 1", r.stderr)

    def test_saves(self):
        r = self.run_tool("saves.py", "--slot", "x", "status")
        self.assertEqual(r.returncode, 1)


class ShotNameTest(unittest.TestCase):
    def test_xdrive_shot_tag(self):
        try:
            import xdrive
        except OSError:
            self.skipTest("no libX11/libXtst")

        class Dpy:
            def __init__(self):
                self.paths = []

            def shot(self, path, *a):
                self.paths.append(path)
        d = Dpy()
        xdrive.do(d, ["shot", "workspace/logs/d2run-last.png"])
        xdrive.do(d, ["shot", "workspace/logs/d2run-last.png"], None, slots.suffix(2))
        xdrive.do(d, ["shot", "x.png"], (10, 20), slots.suffix(1))
        self.assertEqual(d.paths, ["workspace/logs/d2run-last.png", "workspace/logs/d2run-last-s2.png", "x-s1.png"])


class HuntTargetTest(unittest.TestCase):
    def test_run_target(self):
        import d2hunt
        ws = os.path.join(os.path.dirname(HERE), "workspace")
        args, p = d2hunt.run_target(1, ":8", ["--seed", "{n}"])
        self.assertEqual(args, ["--seed", "{n}", "--slot", "1"])
        self.assertEqual(p, slots.prefix(1, ws))
        args, p = d2hunt.run_target(0, ":7", ["--seed", "1"])
        self.assertEqual(p, slots.prefix(0, ws))
        args, p = d2hunt.run_target(1, ":8", ["--display", ":8", "--prefix", "/x/wineprefix2"])
        self.assertEqual(p, "/x/wineprefix2")
        with self.assertRaises(slots.SlotError):
            d2hunt.run_target(0, ":7", ["--slot", "1"])  # d2run on :8, d2hunt on :7


if __name__ == "__main__":
    unittest.main()

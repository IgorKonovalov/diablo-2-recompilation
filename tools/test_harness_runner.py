"""No-game tests of tools/harness_runner.py (plan 0056 Phase 1): python3 -I tools/test_harness_runner.py.

Fake logs (temporary files written by the test), fake processes (objects with poll(), and short `python3 -I -c`
children that write a log and exit) and fake clocks; nothing is launched on a slot, no saves.py or slots.py command
runs (install and stop get a recording `run`).
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_runner as hr  # noqa: E402

HEAD = [
    "# d2run seed=27204 gdb=tools/gdb/d2s-h1a.gdb steps=tools/gdb/h1a-menu.steps slot=1\n",
    "# installed qitsor.d2s sha256=0000000000000000\n",
    "# game pid 1\n",
    "[New LWP 2 (id 2)]\n",
    "PILOT logger armed\n",
]
RDY = 'RDY {"logger":"d2s-h1a"}\n'


class FakeProc:
    """poll() is None for the first `alive` calls, then 0."""

    def __init__(self, alive=10 ** 9, pid=4242):
        self.alive, self.pid, self.calls = alive, pid, 0

    def poll(self):
        self.calls += 1
        return None if self.calls <= self.alive else 0


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.log = os.path.join(self.dir, "s.log")

    def write(self, rows, path=None, mode="w"):
        with open(path or self.log, mode) as f:
            f.writelines(rows)


class ReadyWait(Base):
    def test_ready_at_once(self):
        self.write(HEAD + [RDY])
        t0 = time.time()
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, proc=FakeProc(), step=0.01), hr.READY)
        self.assertLess(time.time() - t0, 1)

    def test_ready_written_later(self):
        self.write(HEAD)
        n = {"polls": 0}

        def tick():
            n["polls"] += 1
            if n["polls"] == 4:
                self.write([RDY], mode="a")
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, proc=FakeProc(), tick=tick, step=0.01), hr.READY)
        self.assertEqual(n["polls"], 4)

    def test_timeout_is_reported(self):
        self.write(HEAD)
        c = Clock()
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, proc=FakeProc(), step=0.5, clock=c, sleep=c.sleep),
                         hr.TIMEOUT)
        self.assertGreaterEqual(c.t - 1000.0, 120)
        self.assertLess(c.t - 1000.0, 121)

    def test_gone_returns_without_the_timeout(self):
        self.write(HEAD)
        c = Clock()
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, proc=FakeProc(alive=3), clock=c, sleep=c.sleep),
                         hr.GONE)
        self.assertLess(c.t - 1000.0, 5)

    def test_gone_callable(self):
        self.write(HEAD)
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, gone=lambda: True, step=0.01), hr.GONE)

    def test_line_written_just_before_the_exit_counts(self):
        self.write(HEAD)
        proc = FakeProc(alive=0)
        # the line lands between the wait's read and its gone() test: gone() writes it, then reports the exit
        state = {"n": 0}

        def gone():
            state["n"] += 1
            self.write([RDY], mode="a")
            return proc.poll() is not None
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, gone=gone, step=0.01), hr.READY)

    def test_unterminated_ready_line_at_the_exit(self):
        self.write(HEAD + ['RDY {"logger":"x"}'])
        self.assertEqual(hr.wait_ready(self.log, "RDY", 120, gone=lambda: True, step=0.01), hr.READY)

    def test_tag_is_the_first_word_not_a_substring(self):
        self.write(HEAD + ["RDYX 1\n", "TBL RDY\n", "# RDY\n"])
        self.assertEqual(hr.wait_ready(self.log, "RDY", 0.05, step=0.01), hr.TIMEOUT)
        self.write(['PLR {"x":1}\n'], mode="a")
        self.assertEqual(hr.wait_ready(self.log, "PLR", 0.05, step=0.01), hr.READY)

    def test_a_ready_line_with_a_space_is_a_prefix(self):
        self.write(HEAD + ['CUBE {"op":1}\n'])
        self.assertEqual(hr.wait_ready(self.log, "CUBE logger armed", 0.05, step=0.01), hr.TIMEOUT)
        self.write(["CUBE logger armed\n"], mode="a")
        self.assertEqual(hr.wait_ready(self.log, "CUBE logger armed", 0.05, step=0.01), hr.READY)

    def test_a_case_line_is_not_the_ready_line(self):
        # review-fixes 16: a line only a case produces (TBL) never ends the start wait
        self.write(HEAD + ['TBL {"count":3}\n'] * 3)
        self.assertEqual(hr.wait_ready(self.log, "RDY", 0.05, step=0.01), hr.TIMEOUT)

    def test_missing_log(self):
        self.assertEqual(hr.wait_ready(os.path.join(self.dir, "none.log"), "RDY", 0.05, step=0.01), hr.TIMEOUT)

    def test_real_child_that_writes_ready(self):
        code = "import sys,time; f=open(sys.argv[1],'a'); f.write('RDY {}\\n'); f.close(); time.sleep(5)"
        p = subprocess.Popen([sys.executable, "-I", "-c", code, self.log], stdin=subprocess.DEVNULL)
        try:
            self.assertEqual(hr.wait_ready(self.log, "RDY", 30, proc=p, step=0.02), hr.READY)
        finally:
            p.kill()
            p.wait()

    def test_real_child_that_exits_without_it(self):
        code = "import sys; f=open(sys.argv[1],'a'); f.write('PILOT logger armed\\n'); f.close()"
        p = subprocess.Popen([sys.executable, "-I", "-c", code, self.log], stdin=subprocess.DEVNULL)
        t0 = time.time()
        self.assertEqual(hr.wait_ready(self.log, "RDY", 60, proc=p, step=0.02), hr.GONE)
        self.assertLess(time.time() - t0, 30)
        p.wait()

    def test_tail_reads_only_what_was_appended(self):
        t = hr.Tail(self.log)
        self.assertEqual(t.poll(), [])
        self.write(["a 1\n", "b 2"])
        self.assertEqual(t.poll(), ["a 1\n"])
        self.write(["\n", "c 3\n"], mode="a")
        self.assertEqual(t.poll(), ["b 2\n", "c 3\n"])
        self.assertEqual(t.poll(), [])

    def test_wait_count(self):
        self.write(HEAD + ['PLD {"code":0}\n'])
        self.assertTrue(hr.wait_count(self.log, "PLD", 1, 0.05, step=0.01))
        self.assertFalse(hr.wait_count(self.log, "PLD", 2, 0.05, step=0.01))
        c = Clock()
        self.assertFalse(hr.wait_count(self.log, "PLD", 2, 120, proc=FakeProc(alive=1), clock=c, sleep=c.sleep))
        self.assertLess(c.t - 1000.0, 5)


class Marks(Base):
    def test_rows_and_line_counts(self):
        stem = self.log[:-4]
        self.write(HEAD)
        hr.mark(stem, "-", "launch", self.log, "pid=1 seed=5", clock=lambda: 1.0)
        self.write([RDY], mode="a")
        hr.mark(stem, "-", "ready", self.log, "ready", clock=lambda: 2.0)
        hr.mark(stem, "a", "start", self.log, clock=lambda: 3.0)
        self.write(["X 1\n", "X 2\n"], mode="a")
        hr.mark(stem, "a", "end", self.log, "pld=0", clock=lambda: 4.5)
        with open(stem + ".marks.tsv") as f:
            self.assertEqual(f.readline(), "case\tevent\ttime\tline\tnote\n")
        rows = hr.read_marks(stem + ".marks.tsv")
        self.assertEqual([(r["case"], r["event"], r["line"]) for r in rows],
                         [("-", "launch", 5), ("-", "ready", 6), ("a", "start", 6), ("a", "end", 8)])
        self.assertEqual(rows[3]["time"], 4.5)
        self.assertEqual(rows[0]["note"], "pid=1 seed=5")

    def test_the_mark_line_is_the_next_line_index(self):
        self.write(HEAD)
        r = hr.mark(self.log[:-4], "a", "start", self.log)
        with open(self.log) as f:
            self.assertEqual(int(r["line"]), len(f.readlines()))

    def test_no_log_yet(self):
        self.assertEqual(hr.mark(self.log[:-4], "-", "launch", self.log)["line"], "0")

    def test_bad_event_and_tab(self):
        with self.assertRaises(hr.HarnessError):
            hr.mark(self.log[:-4], "a", "begin", self.log)
        with self.assertRaises(hr.HarnessError):
            hr.mark(self.log[:-4], "a\tb", "start", self.log)

    def test_note_whitespace_folded(self):
        r = hr.mark(self.log[:-4], "a", "fail", self.log, "two\nlines  here")
        self.assertEqual(r["note"], "two lines here")

    def test_not_a_marks_file(self):
        p = os.path.join(self.dir, "x.marks.tsv")
        self.write(["case\tline\n"], path=p)
        with self.assertRaises(hr.HarnessError):
            hr.read_marks(p)


class Split(Base):
    def build(self):
        """HEAD, RDY, then three cases; the second case's game-start line (GAME) comes two lines after its mark,
        the third case has none; the first case is named again at the end (a repeat)."""
        stem = self.log[:-4]
        self.write(HEAD + [RDY])
        rows = []

        def case(name, body):
            hr.mark(stem, name, "start", self.log)
            self.write(body, mode="a")
            hr.mark(stem, name, "end", self.log)
        case("a", ["GAME 1\n", "PLD 0\n"])
        case("b", ["xd click\n", "noise\n", "GAME 2\n", "PLD 0\n", "WDONE 1\n"])
        case("c", ["PLD 7\n"])
        case("a", ["GAME 3\n", "PLD 0\n"])
        return rows

    def test_split_at_marks(self):
        self.build()
        out = hr.split(self.log)
        self.assertEqual([(p["case"], p["first"], p["end"]) for p in out],
                         [("a", 6, 8), ("b", 8, 13), ("c", 13, 14), ("a", 14, 16)])
        self.assertEqual([os.path.basename(p["path"]) for p in out], ["s-a.log", "s-b.log", "s-c.log", "s-a-2.log"])
        with open(out[1]["path"]) as f:
            body = f.readlines()
        self.assertEqual(body[:6], HEAD + [RDY])
        self.assertEqual(body[6], "# split s.log case=b lines=8-13 at=mark\n")
        self.assertEqual(body[7:], ["xd click\n", "noise\n", "GAME 2\n", "PLD 0\n", "WDONE 1\n"])

    def test_pieces_cover_the_log_once(self):
        self.build()
        with open(self.log) as f:
            src = f.readlines()
        got = []
        for p in hr.split(self.log, head=False):
            with open(p["path"]) as f:
                got += f.readlines()
        self.assertEqual(got, src[6:])

    def test_split_at_game_start(self):
        self.build()
        out = hr.split(self.log, at="GAME", out_dir=os.path.join(self.dir, "cut"))
        self.assertEqual([(p["case"], p["first"], p["end"], p["snapped"]) for p in out],
                         [("a", 6, 10, True), ("b", 10, 13, True), ("c", 13, 14, False), ("a", 14, 16, True)])
        with open(out[1]["path"]) as f:
            body = f.readlines()
        self.assertEqual(body[6], "# split s.log case=b lines=10-13 at=GAME\n")
        self.assertEqual(body[7], "GAME 2\n")
        self.assertEqual(os.path.dirname(out[0]["path"]), os.path.join(self.dir, "cut"))

    def test_a_cut_never_moves_past_the_next_mark(self):
        stem = self.log[:-4]
        self.write(HEAD)
        hr.mark(stem, "a", "start", self.log)
        self.write(["x\n"], mode="a")
        hr.mark(stem, "b", "start", self.log)
        self.write(["GAME 1\n"], mode="a")
        out = hr.split(self.log, at="GAME")
        self.assertEqual([(p["case"], p["first"], p["snapped"]) for p in out], [("a", 5, False), ("b", 6, True)])

    def test_only_start_marks_cut(self):
        stem = self.log[:-4]
        self.write(HEAD)
        hr.mark(stem, "-", "launch", self.log)
        self.write([RDY], mode="a")
        hr.mark(stem, "-", "ready", self.log)
        hr.mark(stem, "a", "start", self.log)
        self.write(["X\n"], mode="a")
        hr.mark(stem, "a", "fail", self.log)
        self.assertEqual([p["case"] for p in hr.split(self.log)], ["a"])

    def test_cli(self):
        self.build()
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(hr.main(["split", self.log, "--at", "GAME", "--out", os.path.join(self.dir, "o")]), 0)
        self.assertIn("(no GAME line: cut at the mark)", buf.getvalue().splitlines()[2])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(hr.main(["marks", self.log]), 0)
        self.assertEqual(len(buf.getvalue().splitlines()), 8)


class Batch(Base):
    def test_status_counts(self):
        st_path = os.path.join(self.dir, "b.status.json")
        tries = {}

        def run(case):
            tries[case] = tries.get(case, 0) + 1
            if case == "boom":
                raise ValueError("no PLD")
            if case == "flaky":
                return tries[case] >= 2
            if case == "bad":
                return False, "driver gone before the first case"
            return True, "2 of 2 loads"
        c = Clock()
        with redirect_stdout(io.StringIO()):
            st = hr.batch(["ok", "flaky", "bad", "boom"], run, st_path, reruns=1, clock=c)
        self.assertEqual((st["kept"], st["rerun"], st["failed"], st["done"]), (1, 1, 2, True))
        self.assertEqual([(r["case"], r["outcome"], r["tries"]) for r in st["cases"]],
                         [("ok", "kept", 1), ("flaky", "rerun", 2), ("bad", "failed", 1), ("boom", "failed", 1)])
        self.assertEqual(st["cases"][3]["note"], "ValueError: no PLD")
        with open(st_path) as f:
            self.assertEqual(json.load(f), st)
        self.assertFalse(os.path.exists(st_path + ".tmp"))

    def test_rerun_budget_is_per_batch(self):
        with redirect_stdout(io.StringIO()):
            st = hr.batch(["a", "b"], lambda c: False, os.path.join(self.dir, "s.json"), reruns=1)
        self.assertEqual([r["tries"] for r in st["cases"]], [2, 1])

    def test_status_written_when_interrupted(self):
        st_path = os.path.join(self.dir, "b.status.json")
        pid_path = os.path.join(self.dir, "b.pid")

        def run(case):
            if case == "stop":
                raise KeyboardInterrupt
            return hr.KEPT
        with redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            hr.batch(["a", "stop", "never"], run, st_path, pidfile=pid_path)
        with open(st_path) as f:
            st = json.load(f)
        self.assertEqual((st["kept"], st["done"], len(st["cases"])), (1, False, 1))
        self.assertIn("STOPPED EARLY", hr.summary(st))
        with open(pid_path) as f:
            self.assertEqual(int(f.read()), os.getpid())

    def test_status_cli(self):
        st_path = os.path.join(self.dir, "b.status.json")
        with redirect_stdout(io.StringIO()):
            hr.batch(["a", "b"], lambda c: c == "a", st_path)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(hr.main(["status", st_path]), 1)
        self.assertTrue(buf.getvalue().startswith("kept 1, rerun 0, failed 1, cases 2"))

    def test_detach(self):
        out = os.path.join(self.dir, "bg.txt")
        pid = hr.detach([sys.executable, "-I", "-c", "import os; print(os.getsid(0) == os.getpid())"], out)
        hr._DETACHED[-1].wait(30)
        self.assertEqual(hr._DETACHED[-1].pid, pid)
        with open(out) as f:
            self.assertEqual(f.read().strip(), "True")


class Steps(Base):
    def rec(self, codes=None):
        calls, codes = [], list(codes or [])

        def run(argv, timeout=None, out=None):
            calls.append(argv[argv.index("--slot") + 2:] if "--slot" in argv else argv[3:])
            return codes.pop(0) if codes else 0
        return calls, run

    def test_install_restores_only_an_existing_aside(self):
        ws = self.dir
        calls, run = self.rec()
        hr.install(1, "p56", ws=ws, run=run)
        self.assertEqual(calls, [["aside", "p56"]])
        os.makedirs(hr.aside_dir(1, "p56", ws))
        calls, run = self.rec()
        hr.install(1, "p56", ["/x/a.d2s"], ws=ws, run=run)
        self.assertEqual(calls, [["restore", "p56"], ["aside", "p56"], ["install", "p56", "/x/a.d2s"]])
        self.assertEqual(hr.aside_dir(1, "p56", ws), os.path.join(ws, "runtime", "slot-1", "saves-aside-p56"))

    def test_install_refusals_raise(self):
        ws = self.dir
        os.makedirs(hr.aside_dir(2, "t", ws))
        for codes, word in (([1], "restore"), ([0, 1], "aside"), ([0, 0, 1], "install")):
            calls, run = self.rec(codes)
            with self.assertRaises(hr.HarnessError) as e:
                hr.install(2, "t", ["/x/a.d2s"], ws=ws, run=run)
            self.assertIn(word, str(e.exception))
            self.assertEqual(len(calls), len(codes))

    def test_stop_waits_for_idle(self):
        calls, run = self.rec()
        seq = [[11, 12], [12], []]
        c = Clock()
        self.assertTrue(hr.stop(1, FakeProc(), run=run, busy=lambda: seq.pop(0), clock=c, sleep=c.sleep))
        self.assertEqual(calls, [["stop", "1"]])
        self.assertEqual(c.t - 1000.0, 1.0)

    def test_stop_reports_a_busy_slot(self):
        calls, run = self.rec()
        c = Clock()
        with redirect_stdout(io.StringIO()) as buf:
            self.assertFalse(hr.stop(1, run=run, busy=lambda: [77], timeout=30, clock=c, sleep=c.sleep))
        self.assertIn("pids 77", buf.getvalue())

    def test_slot_zero_refused(self):
        with self.assertRaises(hr.HarnessError):
            hr.stop(0, run=lambda *a: 0, busy=lambda: [])
        with self.assertRaises(hr.HarnessError):
            hr.launch_argv(0, 1, self.log)

    def test_launch_argv(self):
        a = hr.launch_argv(2, 27204, self.log, gdb="g.gdb", steps="s.steps", after=3000,
                           install=("p56", ["/c/base/qitsor.d2s"]), game_args="-act 2")
        self.assertEqual(a[:2], [sys.executable, "-I"])
        self.assertTrue(a[2].endswith(os.path.join("tools", "d2run.py")))
        s = " ".join(a[3:])
        self.assertEqual(s, "--slot 2 --seed 27204 --log %s --after 3000 --mem-max 4G --gdb g.gdb --steps s.steps "
                            "--game-args=-act 2 --install p56 /c/base/qitsor.d2s" % self.log)

    def test_launch_new_session_and_mark(self):
        seen = {}

        def popen(argv, **kw):
            seen.update(kw)
            return FakeProc(pid=99)
        stem = self.log[:-4]
        with redirect_stdout(io.StringIO()):
            p = hr.launch(1, 5, self.log, gdb="g.gdb", stem=stem, popen=popen)
        self.assertEqual(p.pid, 99)
        self.assertTrue(seen["start_new_session"])
        self.assertIs(seen["stdin"], subprocess.DEVNULL)
        r = hr.read_marks(stem + ".marks.tsv")
        self.assertEqual((r[0]["event"], r[0]["note"]), ("launch", "pid=99 seed=5"))

    def test_new_stem_never_reuses_a_log(self):
        s1 = hr.new_stem(self.dir, "dev-x", 1, 27204, "order")
        self.assertEqual(os.path.basename(s1), "dev-x-s1-27204-order")
        self.write([], path=s1 + ".log")
        s2 = hr.new_stem(self.dir, "dev-x", 1, 27204, "order")
        self.assertEqual(os.path.basename(s2), "dev-x-s1-27204-order-r2")
        self.write([], path=s2 + ".log")
        self.assertTrue(hr.new_stem(self.dir, "dev-x", 1, 27204, "order").endswith("-r3"))


class Example(Base):
    """The worked example, tools/h1a_sessions.py, on the library: its wrapper keeps the bool wait tools/h1c_sessions.py
    imports, and `run` is one hr.batch with one status file."""

    def test_wrapper(self):
        import h1a_sessions
        self.write(HEAD + [RDY])
        self.assertIs(h1a_sessions.wait_ready(self.log, 1, step=0.01), True)
        self.write(HEAD)
        self.assertIs(h1a_sessions.wait_ready(self.log, 120, gone=lambda: True, step=0.01), False)
        self.assertIs(h1a_sessions.lines, hr.lines)

    def test_run_is_one_batch(self):
        import h1a_sessions
        got = []
        old = h1a_sessions.run_session, h1a_sessions.LOGS
        h1a_sessions.LOGS = self.dir

        def fake(name, slot, tag, cases, run, only=None):
            got.append((name, slot, tag, cases, run, only))
            return (True, "1 of 1 loads") if name == "stub7" else (False, "driver gone before the first case")
        h1a_sessions.run_session = fake
        try:
            with redirect_stdout(io.StringIO()) as buf:
                rc = h1a_sessions.main(["run", "--slot", "1", "--tag", "p56", "--cases", "/c", "--run", "dev-x",
                                        "--only", "param,hdrshort", "stub7", "order"])
        finally:
            h1a_sessions.run_session, h1a_sessions.LOGS = old
        self.assertEqual(rc, 1)
        self.assertEqual(got, [("stub7", 1, "p56", "/c", "dev-x", {"param", "hdrshort"}),
                               ("order", 1, "p56", "/c", "dev-x", {"param", "hdrshort"})])
        with open(os.path.join(self.dir, "dev-x-s1.status.json")) as f:
            st = json.load(f)
        self.assertEqual((st["kept"], st["failed"]), (1, 1))
        self.assertIn("BATCH kept 1, rerun 0, failed 1", buf.getvalue())

    def test_session_flow_on_fakes(self):
        """run_session end to end with every harness call faked: no slot, no saves directory, no game. The fake
        launch writes the d2run header and RDY; the fake xdrive answers OK (690, 556) with a PLD line (code 5 after
        the hdrshort swap, 0 otherwise) and Save and Exit (400, 268) with two WDONE lines. Both mark files get the
        cases at the same lines, and the split cuts there."""
        import h1a_sessions as h
        box, calls = {}, []

        def launch(slot, seed, log, **kw):
            box["log"] = log
            self.write(HEAD + [RDY], path=log)
            calls.append(("launch", slot, seed, kw["install"][0], os.path.basename(kw["install"][1][0])))
            return FakeProc()

        def sh(argv, timeout=None, out=None):
            xy = argv[argv.index("click") + 1:] if "click" in argv else None
            if xy == ["690", "556"]:
                code = 5 if calls[-1] == ("copy", "hdrshort") else 0
                self.write(['PLD {"code":%d}\n' % code], path=box["log"], mode="a")
            elif xy == ["400", "268"]:
                self.write(["WDONE {}\n", "WDONE {}\n"], path=box["log"], mode="a")
            return 0

        saved = (h.sh, h.hide_window, h.shutil.copyfile, h.LOGS, hr.launch, hr.install, hr.stop, h.time.sleep)
        h.sh, h.hide_window, h.LOGS = sh, (lambda s: None), self.dir
        h.shutil.copyfile = lambda a, b: calls.append(("copy", os.path.basename(os.path.dirname(a))))
        hr.launch = launch
        hr.install = lambda *a, **k: calls.append(("install",) + a)
        hr.stop = lambda *a, **k: calls.append(("stop", a[0])) or True
        h.time.sleep = lambda s: None
        try:
            with redirect_stdout(io.StringIO()):
                r = h.run_session("order", 1, "p56", "/cases", "dev-x", {"hdrshort", "param"})
        finally:
            h.sh, h.hide_window, h.shutil.copyfile, h.LOGS, hr.launch, hr.install, hr.stop, h.time.sleep = saved
        self.assertEqual(r, (True, "2 of 2 loads"))
        self.assertEqual(calls[:2], [("install", 1, "p56"), ("launch", 1, 27204, "p56", "qitsor.d2s")])
        self.assertEqual([c[1] for c in calls if c[0] == "copy"], ["base", "hdrshort", "base", "param"])
        self.assertEqual(calls[-1], ("stop", 1))
        stem = os.path.join(self.dir, "dev-x-s1-27204-order")
        with open(stem + ".marks.jsonl") as f:
            js = [json.loads(ln) for ln in f]
        rows = hr.read_marks(stem + ".marks.tsv")
        self.assertEqual([(m["case"], m["line"]) for m in js],
                         [(m["case"], m["line"]) for m in rows if m["event"] == "start"])
        self.assertEqual([m["case"] for m in js], ["hdrshort", "param"])
        self.assertEqual([m["note"] for m in rows if m["event"] == "end"], ["pld=5", "pld=0"])
        self.assertEqual([(m["case"], m["event"]) for m in rows][:1], [("-", "ready")])
        self.assertEqual([p["case"] for p in hr.split(stem + ".log", out_dir=os.path.join(self.dir, "cut"))],
                         ["hdrshort", "param"])

    def test_slot_zero_refused(self):
        import h1a_sessions
        with redirect_stdout(io.StringIO()):
            self.assertEqual(h1a_sessions.main(["run", "--slot", "0", "--tag", "t", "--cases", "/c", "--run", "r",
                                                "stub7"]), 2)


if __name__ == "__main__":
    unittest.main()

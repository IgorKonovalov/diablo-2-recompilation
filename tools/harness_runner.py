#!/usr/bin/env python3
"""Shared harness runner library (plan 0056 Phase 1): the steps every tools/*_sessions.py runner repeats.

A runner keeps its own session table and its own command kinds (clicks, pilot calls, line-count waits); the launch
skeleton comes from here:

    stem = new_stem(LOGS, run, slot, seed, name)        # <run>-s<slot>-<seed>-<name>[-rK], never an existing log
    install(slot, tag)                                  # saves.py restore TAG (if aside) + aside TAG, checked
    proc = launch(slot, seed, log, gdb=..., steps=..., after=..., install=(tag, [save]), out=pilot_txt)
    r = wait_ready(log, "RDY", 120, proc=proc, tick=lambda: hide_window(slot))   # READY | TIMEOUT | GONE
    mark(stem, case, "start", log) ... mark(stem, case, "end", log)              # <stem>.marks.tsv
    stop(slot, proc)                                    # slots.py stop N, then wait until slots.busy(N) is empty
    batch(names, run_one, status_path)                  # one status file at the end: kept / failed / rerun, wall

and, offline, split(log, marks) cuts a several-case log into one log per case.

Command line (no game is started by any of these):
    python3 -I tools/harness_runner.py split  LOG [--marks M.tsv] [--at TAG] [--out DIR] [--no-head]
    python3 -I tools/harness_runner.py marks  LOG|M.tsv          # the marks, one line each
    python3 -I tools/harness_runner.py status STATUS.json        # a batch's summary line and its failed cases
    python3 -I tools/harness_runner.py bg OUT -- CMD ...         # start CMD detached (own session, stdio to OUT),
                                                                 # print its pid: wait once with
                                                                 # `tail --pid=PID -f /dev/null`

Rules this library implements are stated in .claude/skills/reverser/references/harness-play.md (§ Before the batch,
§ Running a batch unattended, § Runners and the library); it does not restate them. Stdlib only.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slots  # noqa: E402

PY = [sys.executable, "-I"]
WS = os.path.join(ROOT, "workspace")
MEM_MAX = "4G"            # d2run.py's own default; passed explicitly so a runner's cap is in its command line

READY, TIMEOUT, GONE = "ready", "timeout", "gone"
EVENTS = ("launch", "ready", "start", "end", "fail")
MARK_COLS = ("case", "event", "time", "line", "note")
KEPT, FAILED = "kept", "failed"


class HarnessError(RuntimeError):
    pass


# ---- small shared helpers ------------------------------------------------------------------------------------

def sh(args, timeout=None, out=None):
    """Run a tool to completion (stdin closed, stdout+stderr to `out` or ours); its return code, None on timeout."""
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=out, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def tool(name):
    return os.path.join(HERE, name)


def hide_window(slot):
    """Keep the slot's Xwayland on Hyprland's hidden special workspace d2harness (harness-play.md)."""
    title = "Xwayland on %s" % slots.display(slot)
    try:
        cl = json.loads(subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True,
                                       timeout=10).stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return
    for c in cl:
        if c.get("title") == title and (c.get("workspace") or {}).get("name") != "special:d2harness":
            subprocess.run(["hyprctl", "dispatch", 'hl.dsp.window.move({ workspace = "special:d2harness", '
                            'follow = false, window = "address:%s" })' % c["address"]], capture_output=True,
                           timeout=10)


def tag_of(line):
    """A log line's tag: its first space-separated word ("PLR" of 'PLR {...}', "RDY" of 'RDY {...}')."""
    return line.split(" ", 1)[0].rstrip("\r\n")


def lines(log, tag):
    """Every line of `log` whose tag is `tag` ([] when the log does not exist yet)."""
    try:
        with open(log, errors="replace") as f:
            return [ln for ln in f if tag_of(ln) == tag]
    except OSError:
        return []


def line_count(log):
    """Complete lines in `log` so far (0 when it does not exist): the line index the next line will have."""
    try:
        with open(log, "rb") as f:
            return sum(chunk.count(b"\n") for chunk in iter(lambda: f.read(1 << 20), b""))
    except OSError:
        return 0


def new_stem(logs, run, slot, seed, name):
    """<logs>/<run>-s<slot>-<seed>-<name>, or -r2, -r3 … when that log exists (a rerun never overwrites a log)."""
    os.makedirs(logs, exist_ok=True)
    base = os.path.join(logs, "%s-s%d-%d-%s" % (run, slot, seed, name))
    stem, k = base, 2
    while os.path.exists(stem + ".log"):
        stem = "%s-r%d" % (base, k)
        k += 1
    return stem


class Tail:
    """Reads a growing log incrementally: each poll() reads only what was appended since the last one."""

    def __init__(self, log):
        self.log, self.pos, self.rest = log, 0, ""

    def poll(self):
        """The complete lines appended since the last call."""
        try:
            with open(self.log, errors="replace") as f:
                f.seek(self.pos)
                data = f.read()
                self.pos = f.tell()
        except OSError:
            return []
        data = self.rest + data
        out = data.split("\n")
        self.rest = out.pop()
        return [ln + "\n" for ln in out]


# ---- the launch skeleton ------------------------------------------------------------------------------------

def aside_dir(slot, tag, ws=None):
    return os.path.join(slots.runtime(slot, ws or WS), "saves-aside-" + tag)


def install(slot, tag, saves=(), out=None, ws=None, run=None):
    """harness-play.md's sequence on slot `slot`: `saves.py restore TAG` when TAG is aside there (the slot back to
    what it held), `saves.py aside TAG` (the slot's own characters kept), then `saves.py install TAG SAVES…` when
    saves are given (a runner that installs through launch(install=…) passes none). Each step's return code is
    checked: HarnessError on the first refusal. `run` replaces sh (tests)."""
    run = run or sh
    base = [*PY, tool("saves.py"), "--slot", str(slot)]
    if os.path.exists(aside_dir(slot, tag, ws)) and run(base + ["restore", tag], 60, out) != 0:
        raise HarnessError("saves.py restore %s refused on slot %d" % (tag, slot))
    if run(base + ["aside", tag], 60, out) != 0:
        raise HarnessError("saves.py aside %s refused on slot %d" % (tag, slot))
    if saves and run(base + ["install", tag] + list(saves), 60, out) != 0:
        raise HarnessError("saves.py install %s refused on slot %d" % (tag, slot))


def launch_argv(slot, seed, log, gdb=None, steps=None, after=1800, install=None, game_args="", mem_max=MEM_MAX,
                extra=()):
    """The tools/d2run.py command line of one launch (see launch)."""
    if slots.check(slot) == 0:
        raise HarnessError("slot 0 is the owner's")
    argv = [*PY, tool("d2run.py"), "--slot", str(slot), "--seed", str(seed), "--log", log, "--after", str(after),
            "--mem-max", mem_max]
    if gdb:
        argv += ["--gdb", gdb]
    if steps:
        argv += ["--steps", steps]
    if game_args:
        argv += ["--game-args=" + game_args]
    if install:
        tag, files = install
        argv += ["--install", tag] + list(files)
    return argv + list(extra)


def launch(slot, seed, log, gdb=None, steps=None, after=1800, install=None, game_args="", mem_max=MEM_MAX,
           extra=(), out=None, stem=None, popen=subprocess.Popen):
    """Start tools/d2run.py on `slot` (never 0) in a new session group (so the lane's tool call and a later kill of the
    runner never reach the game), capped at `mem_max` (d2run.py's systemd scope), stdin closed and its output to
    `out`. install=(TAG, [save.d2s…]) is d2run.py's --install (TAG aside on the slot first). Records a `launch` mark
    in <stem>.marks.tsv when `stem` is given. Returns the Popen: d2run.py execs gdb, so proc.poll() is not None once
    gdb, and with it the game, is gone."""
    argv = launch_argv(slot, seed, log, gdb, steps, after, install, game_args, mem_max, extra)
    print("$ " + " ".join(argv), flush=True)
    proc = popen(argv, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                 start_new_session=True)
    if stem:
        mark(stem, "-", "launch", log, "pid=%d seed=%d" % (proc.pid, seed))
    return proc


def wait_ready(log, ready, timeout, proc=None, gone=None, tick=None, step=0.5, clock=time.time, sleep=time.sleep):
    """Wait for the logger's ready line: the first line whose tag is `ready` ("RDY"; a runner that keys on its
    first position line passes "PLR"), or, when `ready` holds a space, the first line that starts with it ("CUBE
    logger armed", a fixed line whose tag other lines share). Returns READY as soon as it is in the log, GONE as soon as the driver has
    exited without it (proc.poll() is not None, or gone() is true; the log is read once more first, so a line written
    just before the exit still counts), TIMEOUT after `timeout` seconds. Never a silent pass. `tick` runs once per
    poll (the runner hides the window there). The log is read incrementally."""
    if gone is None:
        gone = (lambda: proc.poll() is not None) if proc is not None else (lambda: False)
    tail = Tail(log)
    t0 = clock()

    def hit(ln):
        return ln.startswith(ready) if " " in ready else tag_of(ln) == ready

    def seen():
        return any(hit(ln) for ln in tail.poll())

    while True:
        if tick:
            tick()
        if seen():
            return READY
        if gone():
            return READY if seen() or hit(tail.rest) else GONE
        if clock() - t0 >= timeout:
            return TIMEOUT
        sleep(step)


def wait_count(log, tag, n, timeout, proc=None, step=0.5, clock=time.time, sleep=time.sleep):
    """Wait until `log` holds at least n lines tagged `tag`: True, or False on timeout or once the driver is gone."""
    t0 = clock()
    while True:
        if len(lines(log, tag)) >= n:
            return True
        if (proc is not None and proc.poll() is not None) or clock() - t0 >= timeout:
            return len(lines(log, tag)) >= n
        sleep(step)


def stop(slot, proc=None, timeout=30, out=None, run=None, busy=None, clock=time.time, sleep=time.sleep):
    """`slots.py stop N` (the slot's driver from its pidfile, then wineserver -k on its prefix only), then wait until
    slots.busy(N) is empty, the confirmation slots.py status prints. Reaps `proc` when given. True when the slot is
    idle within `timeout` seconds; False (and the busy pids printed) otherwise."""
    if slots.check(slot) == 0:
        raise HarnessError("slot 0 is the owner's")
    run = run or sh
    busy = busy or (lambda: slots.busy(slot, WS))
    run([*PY, tool("slots.py"), "stop", str(slot)], 60, out)
    t0 = clock()
    while True:
        if proc is not None:
            proc.poll()
        left = busy()
        if not left:
            return True
        if clock() - t0 >= timeout:
            print("  slot %d still busy after stop: pids %s" % (slot, " ".join(map(str, left))), flush=True)
            return False
        sleep(0.5)


# ---- case marks and the split ---------------------------------------------------------------------------------

def marks_path(stem):
    return stem + ".marks.tsv"


def mark(stem, case, event, log=None, note="", clock=time.time):
    """Append one row to <stem>.marks.tsv: the case, the event (launch, ready, start, end, fail), the wall time and
    the log's line count at that moment (the index of the next line the log will get), and a free note. The file
    gets its header row when it is new. Returns the row."""
    if event not in EVENTS:
        raise HarnessError("unknown mark event %r (one of %s)" % (event, ", ".join(EVENTS)))
    row = {"case": str(case), "event": event, "time": "%.3f" % clock(),
           "line": str(line_count(log) if log else 0), "note": " ".join(str(note).split())}
    if any("\t" in v for v in row.values()):
        raise HarnessError("a mark field holds a tab")
    path = marks_path(stem)
    new = not os.path.exists(path)
    with open(path, "a") as f:
        if new:
            f.write("\t".join(MARK_COLS) + "\n")
        f.write("\t".join(row[c] for c in MARK_COLS) + "\n")
    return row


def read_marks(path):
    """The rows of a marks file, as dicts with `time` a float and `line` an int."""
    out = []
    with open(path) as f:
        head = f.readline().rstrip("\n").split("\t")
        if tuple(head) != MARK_COLS:
            raise HarnessError("%s: not a marks file (header %r)" % (path, head))
        for ln in f:
            v = ln.rstrip("\n").split("\t")
            if len(v) != len(MARK_COLS):
                raise HarnessError("%s: bad row %r" % (path, ln))
            r = dict(zip(MARK_COLS, v))
            r["time"], r["line"] = float(r["time"]), int(r["line"])
            out.append(r)
    return out


def split(log, marks=None, out_dir=None, at=None, head=True):
    """Cut a several-case log into one log per case: <out_dir>/<log stem>-<case>.log (default: beside the log; a case
    name met twice gets -2, -3 …). A case's piece runs from its `start` mark's line to the next case's cut (or the
    end). With `at`, each cut moves forward to the first line tagged `at` (the game-start line, as the h4b
    -game1/-game2 split was cut) at or after the mark and before the next mark; a case with no such line keeps the
    mark's line and its returned `snapped` is False. With head (the default), every piece starts with the log's lines
    before the first cut (the d2run header, the logger's armed and ready lines), then one `# split` comment naming
    the source lines. Returns [{case, path, first, end, snapped}] (first/end: 0-based source line range, end
    exclusive)."""
    marks = marks or (log[:-4] if log.endswith(".log") else log) + ".marks.tsv"
    rows = [r for r in read_marks(marks) if r["event"] == "start"]
    with open(log, errors="replace") as f:
        src = f.readlines()
    cuts = []
    for k, r in enumerate(rows):
        lo = min(r["line"], len(src))
        hi = min(rows[k + 1]["line"], len(src)) if k + 1 < len(rows) else len(src)
        c, snapped = lo, at is None
        if at is not None:
            for j in range(lo, hi):
                if tag_of(src[j]) == at:
                    c, snapped = j, True
                    break
        cuts.append((r["case"], c, snapped))
    stem = os.path.basename(log[:-4] if log.endswith(".log") else log)
    out_dir = out_dir or os.path.dirname(os.path.abspath(log))
    os.makedirs(out_dir, exist_ok=True)
    prefix = src[:cuts[0][1]] if (head and cuts) else []
    seen, out = {}, []
    for k, (case, first, snapped) in enumerate(cuts):
        end = cuts[k + 1][1] if k + 1 < len(cuts) else len(src)
        seen[case] = seen.get(case, 0) + 1
        name = case if seen[case] == 1 else "%s-%d" % (case, seen[case])
        path = os.path.join(out_dir, "%s-%s.log" % (stem, name))
        with open(path, "w") as f:
            f.writelines(prefix)
            if head:
                f.write("# split %s case=%s lines=%d-%d at=%s\n" % (os.path.basename(log), case, first, end,
                                                                    at if snapped and at else "mark"))
            f.writelines(src[first:end])
        out.append({"case": case, "path": path, "first": first, "end": end, "snapped": snapped})
    return out


# ---- the batch -------------------------------------------------------------------------------------------------

def batch(cases, run_case, status_path, reruns=0, pidfile=None, clock=time.time, label=str):
    """Run `cases` in order through run_case(case) and write one status file at the end (also when the batch is
    interrupted or a case raises). run_case returns True or KEPT for a kept case, False, FAILED or None for a failed
    one, or (outcome, note). A failed case is run again up to `reruns` times in all (each try counted: `tries`; a
    case kept on a later try is `rerun`). Writes this process's pid to `pidfile` first (harness-play.md § Cleanup).
    The status file is JSON: {"kept", "failed", "rerun", "wall", "done", "cases": [{case, outcome, tries, wall,
    note}]}; `done` is false when the batch stopped early. One line per case is printed as it ends."""
    if pidfile:
        with open(pidfile, "w") as f:
            f.write("%d\n" % os.getpid())
    rows, t0, left, done = [], clock(), reruns, False
    try:
        for case in cases:
            tries, c0 = 0, clock()
            while True:
                tries += 1
                try:
                    r = run_case(case)
                except Exception as e:  # noqa: BLE001  (one case's error never loses the batch's status)
                    r = (FAILED, "%s: %s" % (type(e).__name__, e))
                outcome, note = (r if isinstance(r, tuple) else (r, ""))
                outcome = KEPT if outcome is True or outcome == KEPT else FAILED
                if outcome == KEPT or left <= 0:
                    break
                left -= 1
                print("  %s failed (%s); rerun" % (label(case), note), flush=True)
            row = {"case": label(case), "outcome": "rerun" if outcome == KEPT and tries > 1 else outcome,
                   "tries": tries, "wall": round(clock() - c0, 1), "note": note}
            rows.append(row)
            print("BATCH %s %s tries=%d wall=%.0f %s" % (row["case"], row["outcome"], tries, row["wall"], note),
                  flush=True)
        done = True
    finally:
        st = {"kept": sum(r["outcome"] == KEPT for r in rows), "failed": sum(r["outcome"] == FAILED for r in rows),
              "rerun": sum(r["outcome"] == "rerun" for r in rows), "wall": round(clock() - t0, 1), "done": done,
              "cases": rows}
        tmp = status_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(st, f, indent=1)
            f.write("\n")
        os.replace(tmp, status_path)
    return st


def summary(st):
    """One line for a status file (what a lane reads back after its one wait)."""
    return "kept %d, rerun %d, failed %d, cases %d, wall %.0f s%s" % (
        st["kept"], st["rerun"], st["failed"], len(st["cases"]), st["wall"], "" if st["done"] else ", STOPPED EARLY")


def detach(argv, out_path):
    """Start argv in its own session, stdin closed, stdout+stderr appended to out_path; return its pid."""
    out = open(out_path, "a")
    p = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    out.close()
    _DETACHED.append(p)   # kept referenced: a detached child outlives this call by design
    return p.pid


_DETACHED = []


# ---- several cases per process (plan 0056 Phase 2) -----------------------------------------------------------

MENU_STEPS = {"activate": (700, 150), "single": (400, 307), "ok": (690, 556), "normal": (400, 280),
              "nightmare": (400, 315), "hell": (400, 350), "exit": (400, 268)}


def xd(slot, args, out=None, run=None):
    """One tools/xdrive.py call on the slot's game window (window-relative coordinates)."""
    return (run or sh)([*PY, tool("xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + [str(a) for a in args],
                       30, out)


def next_case(slot, log, saves=(), diff=None, tag="PLR", leave=True, menu_wait=8.0, load_timeout=90, out=None,
              run=None, copy=None, clock=time.time, sleep=time.sleep, ws=None, stem=None, case=None):
    """The menu return: Save and Exit the running game (Escape, the menu's Save and Exit line), install the next
    case's `saves` (.d2s paths, copied over the same names in the slot's saves directory: the game is up, so
    saves.py refuses; the slot's aside, taken at the batch start, stays), SINGLE PLAYER, OK (and `diff` = normal |
    nightmare | hell when the character offers the difficulty box), then wait for the next `tag` line (PLR: the
    player's first position mark). `leave=False` skips the exit (the game is already at the menu). Returns
    {"ok", "secs" (Escape to the new tag line), "n0" (tag lines before), "line" (the log's line count at the
    Escape)}: a caller decides what a failure costs (harness-play.md Fresh process). With `stem` and `case`, the
    case's `start` mark is written just before the OK click, when the previous game's lines are all in the log and
    the new game's are not yet: `split(log)` then cuts the games exactly where the games begin; the caller writes the
    `end` mark (and a `fail` mark when ok is False)."""
    run = run or sh
    copy = copy or shutil.copy2
    n0, l0, t0 = len(lines(log, tag)), line_count(log), clock()
    if leave:
        xd(slot, ["key", "Escape"], out, run)
        sleep(1.5)
        xd(slot, ["click", *MENU_STEPS["exit"]], out, run)
    sleep(menu_wait)
    dst = slots.saves_dir(slot, ws or WS)
    for f in saves:
        copy(f, os.path.join(dst, os.path.basename(f)))
    xd(slot, ["click", *MENU_STEPS["activate"]], out, run)
    sleep(1)
    xd(slot, ["click", *MENU_STEPS["single"]], out, run)
    sleep(3)
    if stem and case:
        mark(stem, case, "start", log, "menu return")
    xd(slot, ["click", *MENU_STEPS["ok"]], out, run)
    if diff:
        sleep(2)
        xd(slot, ["click", *MENU_STEPS[diff]], out, run)
    ok = wait_count(log, tag, n0 + 1, load_timeout, None, clock=clock, sleep=sleep)
    return {"ok": bool(ok), "secs": round(clock() - t0, 1), "n0": n0, "line": l0}


# ---- command line --------------------------------------------------------------------------------------------

def main(argv):
    if not argv or argv[0] not in ("split", "marks", "status", "bg"):
        print(__doc__)
        return 2
    cmd, a = argv[0], argv[1:]
    if cmd == "bg":
        if len(a) < 3 or a[1] != "--":
            print(__doc__)
            return 2
        print(detach(a[2:], a[0]))
        return 0
    if cmd == "status":
        with open(a[0]) as f:
            st = json.load(f)
        print(summary(st))
        for r in st["cases"]:
            if r["outcome"] != KEPT:
                print("  %s %s tries=%d %s" % (r["case"], r["outcome"], r["tries"], r["note"]))
        return 0 if st["done"] and not st["failed"] else 1
    if cmd == "marks":
        p = a[0] if a[0].endswith(".tsv") else (a[0][:-4] if a[0].endswith(".log") else a[0]) + ".marks.tsv"
        for r in read_marks(p):
            print("%-12s %-6s %.3f %7d %s" % (r["case"], r["event"], r["time"], r["line"], r["note"]))
        return 0
    opt, pos, k = {"head": True}, [], 0
    while k < len(a):
        if a[k] in ("--marks", "--at", "--out"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        elif a[k] == "--no-head":
            opt["head"] = False
            k += 1
        else:
            pos.append(a[k])
            k += 1
    if len(pos) != 1:
        print(__doc__)
        return 2
    for p in split(pos[0], opt.get("marks"), opt.get("out"), opt.get("at"), opt["head"]):
        print("%s %d-%d %s%s" % (p["case"], p["first"], p["end"], p["path"], "" if p["snapped"] else " (no %s line:"
                                 " cut at the mark)" % opt.get("at")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

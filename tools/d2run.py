#!/usr/bin/env python3
"""Runtime harness: run the pinned game.exe under wine with gdb breakpoints.

    python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/seed-tree.gdb \
        --steps tools/gdb/enter-sp.steps --after 20 --log workspace/logs/run.log

What it does, in order:
  1. Marks itself a child subreaper (PR_SET_CHILD_SUBREAPER). wine's start.exe
     exits after spawning game.exe, so the game is reparented to us. With
     kernel.yama.ptrace_scope = 1, only an ancestor may ptrace it.
  2. Makes sure the harness X display exists (default :7, a rootful Xwayland,
     kept on Hyprland's hidden special workspace `d2harness`), then starts
     `wine game.exe -w -ns -seed N` in workspace/runtime/game on it. Nothing
     ever opens on the user's own display.
  3. Waits for the game process and its "Diablo II" window.
  4. Forks a driver child: after --attach-wait seconds it plays the --steps file
     through tools/xdrive.py (window-relative clicks), waits --after seconds,
     then kills the wine session (wineserver -k).
  5. Replaces itself with `gdb -batch -p <game> -x <script>`. gdb keeps our PID,
     so it is the game's ancestor. Its stdout/stderr go to --log.

Without --gdb, step 5 is a plain wait (useful to record menu coordinates).
"""
import argparse
import ctypes
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "workspace", "runtime", "game")
PREFIX = os.path.join(ROOT, "workspace", "wineprefix")
PR_SET_CHILD_SUBREAPER = 36


def children_named(pid, needle):
    """PIDs whose parent is pid and whose cmdline contains needle."""
    hits = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/stat") as f:
                ppid = int(f.read().rsplit(")", 1)[1].split()[1])
            with open(f"/proc/{d}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("latin1")
        except OSError:
            continue
        if ppid == pid and needle in cmd:
            hits.append(int(d))
    return hits


def ensure_display(display):
    """Start a rootful Xwayland on `display` if none is running, parked off-screen.

    A Hyprland window rule (session-only, re-added every run) sends the
    "Xwayland on :N" window to the special workspace `d2harness`, silently, so
    neither the server nor anything wine opens on it reaches the user's
    active workspace. Without Hyprland the rule step is skipped.
    """
    title = f"^Xwayland on {display}$"
    rule = f'hl.window_rule({{ match = {{ title = "{title}" }}, workspace = "special:d2harness silent" }})'
    subprocess.run(["hyprctl", "eval", rule], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sock = f"/tmp/.X11-unix/X{display.lstrip(':')}"
    if os.path.exists(sock):
        return
    logf = open(os.path.join(ROOT, "workspace", "logs", f"xwayland{display.lstrip(':')}.log"), "w")
    subprocess.Popen(["Xwayland", display, "-geometry", "1024x768", "-decorate"],
                     stdout=logf, stderr=logf, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        if os.path.exists(sock):
            return
        time.sleep(0.1)
    sys.exit(f"Xwayland {display} did not start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--gdb", help="gdb command file (breakpoints + continue)")
    ap.add_argument("--steps", help="xdrive step file played once the debugger is attached")
    ap.add_argument("--after", type=float, default=20, help="seconds to keep running after the steps")
    ap.add_argument("--attach-wait", type=float, default=5, help="seconds between exec(gdb) and the first step")
    ap.add_argument("--log", required=True)
    ap.add_argument("--display", default=":7")
    ap.add_argument("--game-args", default="", help="extra game.exe switches, e.g. '-act 2'")
    ns = ap.parse_args()

    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        sys.exit("prctl(PR_SET_CHILD_SUBREAPER) failed")

    ensure_display(ns.display)
    env = dict(os.environ, WINEPREFIX=PREFIX, DISPLAY=ns.display, WINEDEBUG="-all")
    log = open(ns.log, "w", buffering=1)
    log.write(f"# d2run seed={ns.seed} gdb={ns.gdb} steps={ns.steps} args={ns.game_args!r} "
              f"t={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
    subprocess.run(["wineserver", "-k"], env=env, stderr=subprocess.DEVNULL)
    time.sleep(1)
    wine = subprocess.Popen(["wine", "game.exe", "-w", "-ns", "-seed", str(ns.seed)] + ns.game_args.split(),
                            cwd=GAME_DIR, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    me = os.getpid()
    game = None
    for _ in range(600):
        wine.poll()  # reap start.exe when it exits
        hits = children_named(me, "\\game.exe")
        if hits:
            game = hits[0]
            break
        time.sleep(0.1)
    if not game:
        sys.exit("game.exe never became our child (subreaper not working?)")
    log.write(f"# game pid {game}\n")

    xdrive = [sys.executable, "-I", os.path.join(ROOT, "tools", "xdrive.py"), "--display", ns.display]
    for _ in range(600):  # wait for the window: the menu is up
        if subprocess.run(xdrive + ["--window", "Diablo II", "move", "1", "1"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            break
        time.sleep(0.1)
    time.sleep(3)

    if os.fork() == 0:  # driver
        os.setsid()
        time.sleep(ns.attach_wait if ns.gdb else 0)
        if ns.steps:
            subprocess.run(xdrive + ["--window", "Diablo II", "run", ns.steps])
        time.sleep(ns.after)
        subprocess.run(["wineserver", "-k"], env=env)
        os._exit(0)

    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    if ns.gdb:
        os.execvp("gdb", ["gdb", "-q", "-nx", "-batch", "-p", str(game), "-x", ns.gdb])
    while True:  # no debugger: just reap until the session is gone
        try:
            os.wait()
        except ChildProcessError:
            break


if __name__ == "__main__":
    main()

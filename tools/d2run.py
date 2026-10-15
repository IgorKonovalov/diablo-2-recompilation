#!/usr/bin/env python3
"""Runtime harness: run the pinned game.exe under wine with gdb breakpoints.

    python3 -I tools/d2run.py --seed 12345 --gdb tools/gdb/seed-tree.gdb \
        --steps tools/gdb/enter-sp.steps --after 20 --log workspace/logs/run.log

What it does, in order:
  0. Re-executes itself inside its own transient systemd user scope (`systemd-run --user --scope`), capped at
     --mem-max of RAM (default 4G; a run takes about 0.5 GB) and MEM_SWAP_MAX of swap. Everything the run starts
     (wine, game.exe, gdb, the driver) is in the scope, so a runaway is OOM-killed alone instead of systemd-oomd
     killing the whole editor session it was started from (2026-10-15). systemd-run --scope execs the command, so the
     PID, and with it gdb's ancestry over the game, is kept. A capped run that hits the limit is stopped whole; the
     user journal says `d2run-<pid>.scope: Failed with result 'oom-kill'`. `--mem-max off`, or no user systemd,
     runs uncapped.
  1. Marks itself a child subreaper (PR_SET_CHILD_SUBREAPER). wine's start.exe
     exits after spawning game.exe, so the game is reparented to us. With
     kernel.yama.ptrace_scope = 1, only an ancestor may ptrace it.
  2. Makes sure the harness X display exists (default :7, a rootful Xwayland in a scope of its own capped at
     XWAYLAND_MEM_MAX, kept on Hyprland's hidden special workspace `d2harness`), then starts
     `wine game.exe -w -ns -seed N` in workspace/runtime/game on it. Nothing
     ever opens on the user's own display.
  3. Waits for the game process and its "Diablo II" window.
  4. Forks a driver child: after --attach-wait seconds it plays the --steps file
     through tools/xdrive.py (window-relative clicks), waits --after seconds,
     then kills the wine session (wineserver -k). The driver writes its PID to
     workspace/runtime/d2run-driver.pid; it watches the game during --after and
     exits *without* wineserver -k once the game is gone, so a finished run's
     timer never kills a later run's game. A new d2run.py kills a stale driver
     named in the pidfile before it starts.
  5. Replaces itself with `gdb -batch -p <game> -x <script>`. gdb keeps our PID,
     so it is the game's ancestor. Its stdout/stderr go to --log.

--install TAG FILE.d2s... (needs a slot) first copies the test saves into the slot's saves directory, as
`tools/saves.py --slot N install TAG FILE...` does (TAG must be aside there). The game rewrites the installed
save when a session ends (the act byte of the difficulty played), so a loop of games that must start in the same
town passes --install on every launch. The installed files and their sha256 prefixes go in the log header.

Without --gdb, step 5 is a plain wait (useful to record menu coordinates, or to run the second,
undebugged client of a two-client game).

Slots (tools/slots.py): the game refuses a second copy in one wine session ("Only one copy of Diablo II
may run at a time": a FindWindowA on its window class at 0x004F5610), so each copy runs in its own prefix
and display. `--slot N` sets both: slot 0 is :7 with workspace/wineprefix (the default), slot N is :(7+N)
with workspace/wineprefix-N (make it with `tools/slots.py create N`). An explicit --display or --prefix
that contradicts --slot is an error. Without --slot, --display picks the slot and its prefix; an explicit
--prefix outside the slots (plan 0011's workspace/wineprefix2) is still accepted. Each slot has its own
driver pidfile (d2run-driver.pid for slot 0, d2run-driver-slotN.pid otherwise), so launchers on different
slots do not kill each other's driver; each driver's wineserver -k only reaches its own prefix. The log
header ends with slot=N (slot=- for a display outside the slots).
"""
import argparse
import ctypes
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slots  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_DIR = os.path.join(ROOT, "workspace", "runtime", "game")
PR_SET_CHILD_SUBREAPER = 36
DRIVER_PIDFILE = os.path.join(ROOT, "workspace", "runtime", "d2run-driver.pid")
MEM_MAX = "4G"            # a run (game, wine services, gdb) is about 0.5 GB
MEM_SWAP_MAX = "1G"
XWAYLAND_MEM_MAX = "1G"   # one display is about 0.1 GB
SCOPE_ENV = "D2RUN_IN_SCOPE"


def have_user_systemd():
    return bool(shutil.which("systemd-run")) and os.path.exists(f"/run/user/{os.getuid()}/systemd/private")


def scope_argv(name, mem_max, argv):
    """argv prefixed with systemd-run so it runs in a transient user scope `name` capped at mem_max RAM and
    MEM_SWAP_MAX swap. systemd-run --scope execs argv, so the process keeps systemd-run's PID."""
    return ["systemd-run", "--user", "--scope", "--quiet", "--collect", "--unit", name,
            "-p", f"MemoryMax={mem_max}", "-p", f"MemorySwapMax={MEM_SWAP_MAX}", "--"] + argv


def enter_scope(mem_max):
    """Re-exec this d2run.py in its own capped scope (step 0), unless already in one, uncapped, or without systemd."""
    if os.environ.pop(SCOPE_ENV, None) or mem_max == "off":
        return
    if not have_user_systemd():
        print("d2run: no user systemd, running without a memory cap", file=sys.stderr)
        return
    os.environ[SCOPE_ENV] = "1"
    argv = [sys.executable, "-I", os.path.abspath(__file__)] + sys.argv[1:]
    os.execvp("systemd-run", scope_argv(f"d2run-{os.getpid()}", mem_max, argv))


def pidfile_for(display):
    """One pidfile per display: slot 0 (:7) keeps the historical name, slot N is d2run-driver-slotN.pid, a display
    outside the slots d2run-driver-<display>.pid."""
    n = slots.slot_of_display(display)
    if n is not None:
        return slots.pidfile(n, os.path.join(ROOT, "workspace"))
    return os.path.join(ROOT, "workspace", "runtime", f"d2run-driver-{display.lstrip(':')}.pid")


def alive(pid, needle):
    """True while pid exists, is not a zombie, and its cmdline contains needle."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            state = f.read().rsplit(")", 1)[1].split()[0]
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().replace(b"\0", b" ").decode("latin1")
    except OSError:
        return False
    return state != "Z" and needle in cmd


def kill_stale_driver(pidfile):
    """Kill the driver of an earlier run if it is still waiting to fire wineserver -k."""
    try:
        with open(pidfile) as f:
            pid = int(f.read().split()[0])
    except (OSError, ValueError, IndexError):
        return
    if pid != os.getpid() and alive(pid, "d2run.py"):
        os.kill(pid, 9)
        print(f"d2run: killed stale driver {pid}", file=sys.stderr)
    try:
        os.unlink(pidfile)
    except OSError:
        pass


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


def ensure_display(display, fullscreen=False):
    """Start a rootful Xwayland on `display` if none is running, parked off-screen.

    With `fullscreen` the server covers the whole output and scales the game's
    800x600 mode up to it (xrandr emulation); an already running server keeps
    whatever size it was started with.

    A Hyprland window rule (session-only, re-added every run) sends the
    "Xwayland on :N" window to the special workspace `d2harness`, silently, so
    neither the server nor anything wine opens on it reaches the user's
    active workspace; a second rule floats it at 1030x800. Without Hyprland
    the rule step is skipped.
    """
    title = f"^Xwayland on {display}$"
    rule = f'hl.window_rule({{ match = {{ title = "{title}" }}, workspace = "special:d2harness silent" }})'
    # Tiled, the windows of several slots share the special workspace and shrink (800x515 seen with five
    # slots), so step-file clicks miss; floating at a fixed size keeps every slot's window whole.
    sized = f'hl.window_rule({{ match = {{ title = "{title}" }}, float = true, size = {{ 1030, 800 }} }})'
    for r in (rule, sized):
        subprocess.run(["hyprctl", "eval", r], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sock = f"/tmp/.X11-unix/X{display.lstrip(':')}"
    if os.path.exists(sock):
        return
    logf = open(os.path.join(ROOT, "workspace", "logs", f"xwayland{display.lstrip(':')}.log"), "w")
    size = ["-fullscreen"] if fullscreen else ["-geometry", "1024x768", "-decorate"]
    argv = ["Xwayland", display] + size
    if have_user_systemd():
        argv = scope_argv(f"d2harness-xwayland{display.lstrip(':')}-{os.getpid()}", XWAYLAND_MEM_MAX, argv)
    subprocess.Popen(argv,
                     stdout=logf, stderr=logf, stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(50):
        if os.path.exists(sock):
            return
        time.sleep(0.1)
    sys.exit(f"Xwayland {display} did not start")


def install_saves(ap, ns):
    """--install TAG FILE...: saves.cmd_install on this slot, with this process not counted as busy. Returns
    [(file name, sha256)] of what was installed."""
    if ns.slot is None:
        ap.error("--install needs a harness slot (--slot N, or a slot's display)")
    if len(ns.install) < 2:
        ap.error("--install TAG FILE.d2s...")
    import saves
    saves.configure(ns.slot)
    if not os.path.isdir(saves.SAVES):
        ap.error(f"no saves directory {saves.SAVES}")
    tag, paths = ns.install[0], ns.install[1:]
    saves.cmd_install(tag, paths, ignore=(os.getpid(),))
    return [(os.path.basename(p), saves.sha(p)) for p in paths]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--gdb", help="gdb command file (breakpoints + continue)")
    ap.add_argument("--steps", help="xdrive step file played once the debugger is attached")
    ap.add_argument("--after", type=float, default=20, help="seconds to keep running after the steps")
    ap.add_argument("--attach-wait", type=float, default=5, help="seconds between exec(gdb) and the first step")
    ap.add_argument("--log", required=True)
    ap.add_argument("--slot", type=int, help="harness slot: sets --display and --prefix (tools/slots.py)")
    ap.add_argument("--display", help="X display (default: the slot's; :7 without --slot)")
    ap.add_argument("--prefix",
                    help="wine prefix (default: the slot's, workspace/wineprefix for slot 0; plan 0011's second "
                         "client used workspace/wineprefix2 with --display :8)")
    ap.add_argument("--game-args", default="", help="extra game.exe switches, e.g. '-act 2'")
    ap.add_argument("--sound", action="store_true", help="omit -ns (sound on, for owner-played runs)")
    ap.add_argument("--fullscreen", action="store_true",
                    help="fullscreen Xwayland and no -w, so the game fills the screen (owner-played runs; stop a "
                         "running windowed server on the display first)")
    ap.add_argument("--game-dir", default=GAME_DIR,
                    help="directory to start game.exe in (default workspace/runtime/game; e.g. a copy with loose "
                         "data files for -direct)")
    ap.add_argument("--install", nargs="+", metavar="TAG_OR_FILE",
                    help="TAG FILE.d2s...: install these saves into the slot first (TAG aside, as saves.py install); "
                         "use on every launch of a loop, since the game rewrites the installed save on exit")
    ap.add_argument("--mem-max", default=MEM_MAX,
                    help=f"RAM cap of the run's systemd scope, as systemd's MemoryMax (default {MEM_MAX}; 'off' for none)")
    ns = ap.parse_args()
    try:
        ns.slot, ns.display, ns.prefix = slots.resolve(ns.slot, ns.display, ns.prefix, os.path.join(ROOT, "workspace"))
    except slots.SlotError as e:
        ap.error(str(e))
    if not os.path.isdir(ns.prefix):
        ap.error(f"no prefix {ns.prefix}" + (f" (create the slot: python3 -I tools/slots.py create {ns.slot})"
                                              if ns.slot else ""))
    enter_scope(ns.mem_max)

    pidfile = pidfile_for(ns.display)
    kill_stale_driver(pidfile)
    installed = install_saves(ap, ns) if ns.install else []   # refused while the slot's game still runs
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        sys.exit("prctl(PR_SET_CHILD_SUBREAPER) failed")

    ensure_display(ns.display, ns.fullscreen)
    env = dict(os.environ, WINEPREFIX=os.path.abspath(ns.prefix), DISPLAY=ns.display, WINEDEBUG="-all")
    log = open(ns.log, "w", buffering=1)
    log.write(f"# d2run seed={ns.seed} gdb={ns.gdb} steps={ns.steps} args={ns.game_args!r} dir={ns.game_dir} "
              f"prefix={ns.prefix} display={ns.display} "
              f"t={time.strftime('%Y-%m-%dT%H:%M:%S')} slot={'-' if ns.slot is None else ns.slot}\n")
    for name, digest in installed:
        log.write(f"# installed {name} sha256={digest[:16]}\n")
    subprocess.run(["wineserver", "-k"], env=env, stderr=subprocess.DEVNULL)
    time.sleep(1)
    wine = subprocess.Popen(["wine", "game.exe"] + ([] if ns.fullscreen else ["-w"]) + ([] if ns.sound else ["-ns"]) + ["-seed", str(ns.seed)] + ns.game_args.split(),
                            cwd=ns.game_dir, env=env, stdin=subprocess.DEVNULL,
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
        with open(pidfile, "w") as f:
            f.write(f"{os.getpid()} game={game}\n")
        time.sleep(ns.attach_wait if ns.gdb else 0)
        if ns.steps:
            subprocess.run(xdrive + ["--window", "Diablo II", "run", ns.steps])
        end = time.time() + ns.after
        while time.time() < end and alive(game, "game.exe"):
            time.sleep(0.5)
        if alive(game, "game.exe"):  # only kill the session we started
            subprocess.run(["wineserver", "-k"], env=env)
        try:
            with open(pidfile) as f:
                if f.read().split()[0] == str(os.getpid()):
                    os.unlink(pidfile)
        except (OSError, IndexError):
            pass
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

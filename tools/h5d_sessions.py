#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H5d (collision): one game per session on one slot, logged by
tools/gdb/collision-h5d.gdb (tools/gdb/collision.gdb plus mon-special.py's PLR/MON lines), driven by tools/d2pilot.py
(Teleport on the left button, Nova on the right button, F1 Nova and F2 Energy Shield hotkeys of UniqNova).

Usage:
  python3 -I tools/h5d_sessions.py list
  python3 -I tools/h5d_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the difficulty steps file, the map seed, and the commands run in order, each with a time
limit: `pilot` runs tools/d2pilot.py with the log; `until` repeats a pilot command (a descent) until the player's
level is the one named. The log goes to workspace/logs/h5d/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output
beside it (.pilot.txt). A watchdog thread kills the running pilot command and ends the session when the log has not
grown for QUIET s (after the first 150 s) or gdb reports the game exited; the slot is then stopped (tools/slots.py
stop N) and its saves directory returned to the TAG aside, so every session starts from the save it names. Nothing
here feeds a model: the pilot only decides where to click. (The driver code is tools/h5b_sessions.py's.)
"""
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h5d")
QUIET = 90
GDB = os.path.join(HERE, "gdb", "collision-h5d.gdb")

NOVA = ["--nova", "3", "--drink", "0.5"]


def wp(tab, row):
    return ("pilot", ["wp", "--wp-find", str(tab), str(row)], 90)


def explore(hops, extra=()):
    return ("pilot", ["explore", "--hops", str(hops)] + NOVA + list(extra), 60 + 6 * hops)


def descend(lid, rows, extra=()):
    return ("until", (lid, ["farm", "--sweep", "--descend", rows, "--descend-time", "240", "--time", "5"] + NOVA
                      + list(extra), 300, 4), 0)


TOMBS = "38,39,40,41,42,43,44"
SESSIONS = {
    # collision 24, 45 (228), spawn 41, 42: sarcophagi (228, size 1, MonPreset act 2) in the Tal Rasha tombs, entered
    # from the Canyon of the Magi (46, Position 1: collision 46's LevelPointPick); Lut Gholein first (its
    # non-interactive townsfolk, patterns 3 and 4: collision 21, 30, met in the starting town and Lut Gholein by the
    # first tomb session, whose second waypoint hop from the waypoint it stood on did not open the list; so every
    # session now takes one waypoint hop from the starting town); item marks from the kills (19, 36); the map seed
    # of run:2026-10-16-sweep-mazes s3, whose LvlWarp row 42 led into tomb 70
    "tomb": ("UniqNova", "enter-normal", 1557, [wp(2, 9), explore(40), descend(70, "42"), explore(120)]),
    "tomb2": ("UniqNova", "enter-normal", 1558, [wp(2, 9), explore(40), descend(66, TOMBS), explore(120)]),
    # collision 8 (entry flag 0x80: levels 109, 111 in the kept logs), 45 (528 evilhut, MonPreset act 5), the item and
    # pattern lines: Harrogath, then the Frigid Highlands
    "frigid": ("UniqNova", "enter-normal", 4101, [wp(5, 2), explore(160)]),
    # collision 45 (298 with flag 0: the AI callers of SpawnClassCellTest): vile mothers (vilemother1, pools of levels
    # 104 and 105) from the Pandemonium Fortress into the Outer Steppes
    "steppes": ("UniqNova", "enter-normal", 4102, [explore(200, ["--any-level"])]),
    # collision 1, 9, 11 (TileCollisionUpdate in an active room: the Jail had 13-24 TCU lines a session in H5b)
    "jail": ("UniqNova", "enter-normal", 4103, [wp(1, 7), explore(100), descend(30, "14"), explore(100)]),
    # collision 24 (size 0: baaltaunt 545, MonPreset act 5 and level 123's umon) and 46: the Throne of Destruction
    # from the Worldstone Keep Level 2 waypoint
    "throne": ("UniqNova", "enter-normal", 4104, [wp(5, 9), descend(129, "85,86"), descend(131, "87,88,89"),
                                                 explore(80)]),
    # collision 21, 30 (pattern 4): the Rogue Encampment's cows (179: inTown, size 3), then the Jail by a waypoint hop
    # from the town waypoint the character stands on (wpchain's retries)
    "rogue": ("UniqNova", "enter-normal", 4106, [wp(1, 1), ("pilot", ["wpchain", "--chain", "1,7", "--linger", "2"], 150),
                                                explore(60)]),
    # collision 46 again: the Arcane Sanctuary (74, Position 1)
    "arcane": ("UniqNova", "enter-normal", 4105, [wp(2, 8), explore(100)]),
}


def sh(args, timeout=None, log=None, holder=None):
    print("$ " + " ".join(args), flush=True)
    try:
        p = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        if holder is not None:
            holder["p"] = p
        return p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(10)
        print("  (timeout after %s s)" % timeout, flush=True)
        return None
    finally:
        if holder is not None:
            holder["p"] = None


def hide_window(slot):
    """Keep the slot's Xwayland on Hyprland's hidden special workspace d2harness (harness-play.md)."""
    title = "Xwayland on :%d" % (7 + slot)
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


def last_level(log):
    lid = None
    try:
        for ln in open(log, errors="replace"):
            if ln.startswith("PLR "):
                try:
                    lid = json.loads(ln[4:])["lid"]
                except (ValueError, KeyError):
                    pass
    except OSError:
        pass
    return lid


def watchdog(log, holder, stop):
    """Abort the running pilot command when the log stops growing or the game exits; sets stop['why']."""
    t0 = time.time()
    size, t_size = -1, time.time()
    while not stop.get("done"):
        time.sleep(3)
        if stop.get("done"):
            return   # the session ended during the sleep: its own slot stop kills the game, which is no abort
        now = time.time()
        try:
            n = os.path.getsize(log)
        except OSError:
            n = -1
        if n != size:
            size, t_size = n, now
        why = None
        if now - t_size > QUIET and now - t0 > 150:
            why = "log unchanged for %d s" % (now - t_size)
        else:
            try:
                with open(log, "rb") as fh:
                    fh.seek(max(0, n - 4096))
                    tail = fh.read()
                if b"[Inferior " in tail and b" exited" in tail:
                    why = "the game exited (gdb's Inferior line)"
            except OSError:
                pass
        if why:
            stop["why"] = why
            print("WATCHDOG: %s; aborting the session" % why, flush=True)
            p = holder.get("p")
            if p is not None:
                try:
                    p.kill()
                except OSError:
                    pass
            return


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
    path = os.path.join(saves, save + ".d2s")
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    env = dict(os.environ, MONSPAWN_WATCH="")
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 GDB, "--steps", os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "2400",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=env)
    t0 = time.time()
    while time.time() - t0 < 180:
        time.sleep(3)
        hide_window(slot)
        try:
            if "PLR " in open(log, errors="replace").read():
                break
        except OSError:
            pass
    time.sleep(3)
    hide_window(slot)
    holder, stop = {"p": None}, {}
    th = threading.Thread(target=watchdog, args=(log, holder, stop), daemon=True)
    th.start()
    for kind, args, timeout in cmds:
        if stop.get("why"):
            break
        if kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    ["--shots", shots], timeout, out, holder)
        elif kind == "until":
            lid, pargs, tmo, tries = args
            rc = None
            for t in range(tries):
                if last_level(log) == lid or stop.get("why"):
                    break
                if t % 2 == 1:
                    sh(PY + [os.path.join(HERE, "d2pilot.py"), "explore", log, "--slot", str(slot), "--hops", "12"]
                       + NOVA + ["--shots", shots], 120, out, holder)
                sh(PY + [os.path.join(HERE, "d2pilot.py"), pargs[0], log, "--slot", str(slot)] + pargs[1:] +
                   ["--shots", shots], tmo, out, holder)
            if last_level(log) == lid:
                rc = 0
            else:
                print("  level %s, not %d: the session stops here" % (last_level(log), lid), flush=True)
                break
        print("  -> %s" % rc, flush=True)
    stop["done"] = True
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        drv.kill()
    out.close()
    print("=== %s done%s" % (name, (" (watchdog: %s)" % stop["why"]) if stop.get("why") else ""), flush=True)


def main(argv):
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-8s %-8s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
        return 0
    a = argv[1:]
    opt, names, k = {}, [], 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--saves", "--run"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        else:
            names.append(a[k])
            k += 1
    if not names or any(n not in SESSIONS for n in names) or set(opt) != {"slot", "tag", "saves", "run"}:
        print(__doc__)
        return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], os.path.abspath(opt["saves"]), opt["run"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

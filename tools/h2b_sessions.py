#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H2b (items-chain): one game per session on one slot, logged by
tools/gdb/items-h2b.gdb, driven by tools/d2pilot.py (Sorceress: Teleport on Shift + left, Nova on F1, Energy Shield on
F2).

Usage:
  python3 -I tools/h2b_sessions.py list
  python3 -I tools/h2b_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the steps file, the map seed, and the commands run in order, each with a time limit:
`pilot` runs tools/d2pilot.py with the log; `players` types /players N. The log goes to
workspace/logs/h2b/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is stopped
after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside first, so every session
starts from the save it names. The machinery is tools/h2a_sessions.py's (plan 0038 H2a), with the logger and the
sessions changed. Nothing here feeds a model: the pilot only decides where to click.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h2b")
LOGGER = os.path.join(HERE, "gdb", "items-h2b.gdb")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def classic_sweep(row, players=8, t=420):
    """Classic Normal: the Act I waypoint of the given row (2 Cold Plains, 3 Stony Field, 4 Dark Wood, 5 Black
    Marsh, 7 Jail Level 1, 9 Catacombs Level 2), /players N, a Nova sweep: many weapon and armour drops of the low TCs (throwing weapons, body armour)."""
    return [("players", players, 0),
            ("pilot", ["wpchain", "--chain", "1,%d" % row, "--linger", "2"] + CLASSIC_WP, 120),
            ("pilot", ["farm", "--sweep", "--time", str(t)] + NOVA + CLASSIC_WP, t + 60)]


def eldritch(t=300, players=8):
    """Hell: /players N, Frigid Highlands waypoint (tab 5 row 2), Eldritch the Rectifier's pack, then a sweep. (After
    hell-a died at /players 8: the other Hell sessions use /players 1; Eldritch's TC has NoDrop 0 either way.)"""
    return [("pilot", ["farm", "--wp", "5,2", "--players", str(players), "--time", str(t), "--sweep"] + NOVA, t + 90)]


def cube_plan(plan):
    """The transmutes of a tools/d2pilot.py cube plan (run:2026-10-15-cube's options)."""
    return [("pilot", ["cube", "--plan", os.path.join(HERE, "gdb", plan), "--ins-gap", "1.2", "--pick-wait", "0.5"],
             900)]


# name: (save Name, steps file, map seed, commands)
SESSIONS = {
    # affixes 13, 17, 20, 21, 24; uniques-sets 7, 35; properties 20; the seed lines: classic Normal sweeps
    "classic-a": ("UniqClassic", "enter-normal", 3911, classic_sweep(2)),
    "classic-b": ("UniqClassic", "enter-normal", 3912, classic_sweep(3)),
    "classic-c": ("UniqClassic", "enter-normal", 3913, classic_sweep(4)),
    "classic-d": ("UniqClassic", "enter-normal", 3914, classic_sweep(5)),
    # (added after classic-a and -b: the outdoor levels gave about 70 creations a session) denser levels: the Jail
    # (row 7) and the Catacombs (row 9)
    "classic-jail": ("UniqClassic", "enter-normal", 3915, classic_sweep(7, t=480)),
    "classic-cat": ("UniqClassic", "enter-normal", 3916, classic_sweep(9, t=480)),
    # properties 24, sockets 42 and 44, the H2c carrier check, the seed lines: Hell at MF 472
    "hell-a": ("UniqNova", "uniques-hell", 3921, eldritch()),
    "hell-b": ("UniqNova", "uniques-hell", 3922, eldritch(players=1)),
    "hell-c": ("UniqNova", "uniques-hell", 3923, eldritch(players=1)),
    "hell-d": ("UniqNova", "uniques-hell", 3924, eldritch(players=1)),
    "hell-e": ("UniqNova", "uniques-hell", 3925, eldritch(players=1)),
    "hell-f": ("UniqNova", "uniques-hell", 3926, eldritch(players=1)),
    # affixes 5, 19: row 62 on one rare jewel, 17 times
    "jewel": ("H2bJewel", "cube-enter-normal", 3931, cube_plan("h2bjewel.plan")),
    # affixes 13, 17, 21, 24; uniques-sets 35: row 62 on nine built rare classic throwing weapons (classic game)
    "throw": ("H2bThrow", "h2b-cube-classic", 3941, cube_plan("h2bthrow.plan")),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def hide_window(slot):
    """Keep the slot's Xwayland on Hyprland's hidden special workspace d2harness (harness-play.md)."""
    import json
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
            print("moved %s to special:d2harness" % title, flush=True)


def save_path(saves, run, name):
    save = SESSIONS[name][0]
    if save.startswith("@"):            # the save another session of this run wrote (Save and Exit)
        src = save[1:]
        sname = SESSIONS[src][0]
        return os.path.join(saves, "%s-%s" % (run, src), sname + ".d2s"), sname
    return os.path.join(saves, save + ".d2s"), save


def last_level(log):
    """The level id of the last PLR line of the log (tools/gdb/pilot.py)."""
    import json
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


def run_session(name, slot, tag, saves, run):
    _, steps, seed, cmds = SESSIONS[name]
    path, sname = save_path(saves, run, name)
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):     # a retry on the same map seed
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 LOGGER, "--steps",
                                 os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "1500",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
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
    for kind, args, timeout in cmds:
        if kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    ["--shots", shots], timeout, out)
            if args[0] == "hunt" and rc != 0:
                print("  hunt failed: the session stops here", flush=True)
                break
        elif kind == "until":
            # repeat a pilot command (a descent) until the player's level is the target, at most n times
            lid, pargs, tmo, tries = args
            rc = None
            for t in range(tries):
                if last_level(log) == lid:
                    rc = 0
                    break
                if t % 2 == 1:      # after a failed descent: explore a little (new rooms, new cells), then again
                    sh(PY + [os.path.join(HERE, "d2pilot.py"), "explore", log, "--slot", str(slot), "--hops", "12"]
                       + NOVA + ["--shots", shots], 120, out)
                sh(PY + [os.path.join(HERE, "d2pilot.py"), pargs[0], log, "--slot", str(slot)] + pargs[1:] +
                   ["--shots", shots], tmo, out)
            if last_level(log) == lid:
                rc = 0
            else:
                print("  level %s, not %d: the session stops here" % (last_level(log), lid), flush=True)
                print("  -> stop", flush=True)
                break
        elif kind == "savexit":
            # Escape until the game pauses (the game menu is up: no TICK line for 2 s; an open NPC panel takes the
            # first Escape), then the menu's "Save and Exit Game" line
            rc = 1
            for _ in range(4):
                sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "key", "Escape"],
                   30, out)
                time.sleep(1.5)
                n0 = os.path.getsize(log)
                time.sleep(2.0)
                if os.path.getsize(log) == n0:
                    sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "shot",
                             os.path.join(shots, "savexit-menu.png")], 30, out)
                    sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "click",
                             "400", "268"], 30, out)
                    time.sleep(8)
                    rc = 0
                    break
        elif kind == "players":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), "players", log, str(args), "--slot", str(slot)], 60, out)
        elif kind == "xd":
            for c in args:
                if c.startswith("sleep "):
                    time.sleep(float(c.split()[1]))
                    continue
                sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + c.split(),
                   30, out)
            rc = 0
        elif kind == "keep":
            sd = os.path.join(ROOT, "workspace", "wineprefix-%d" % slot, "drive_c", "users")
            found = None
            for dp, _, fs in os.walk(sd):
                if sname + ".d2s" in fs:
                    found = os.path.join(dp, sname + ".d2s")
            dst = os.path.join(saves, "%s-%s" % (run, name), sname + ".d2s")   # the game wants file = character name
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if found:
                shutil.copyfile(found, dst)
                print("kept %s -> %s" % (found, dst), flush=True)
            else:
                print("keep: no %s.d2s under %s" % (sname, sd), flush=True)
            rc = 0
        print("  -> %s" % rc, flush=True)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-18s %-14s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
        return 0
    a = argv[1:]
    opt = {}
    names = []
    k = 0
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

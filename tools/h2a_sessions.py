#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H2a (items-tc): one game per session on one slot, logged by
tools/gdb/tc-h2a.gdb, driven by tools/d2pilot.py (Sorceress: Teleport on Shift + left, Nova on F1, Energy Shield on
F2; Barbarian: War Cry on F1 and the right button, Find Item on F2, walking).

Usage:
  python3 -I tools/h2a_sessions.py list
  python3 -I tools/h2a_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the steps file, the map seed, and the commands run in order, each with a time limit:
`pilot` runs tools/d2pilot.py with the log; `players` types /players N; `until` repeats a descent until the player's
level is the target; `xd` runs tools/xdrive.py on the slot's game window. The log goes to
workspace/logs/h2a/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is stopped
after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside first, so every session
starts from the save it names. The session machinery is tools/h6d_sessions.py's (plan 0038 H6d), with the logger
changed. Nothing here feeds a model: the pilot only decides where to click.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h2a")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]
# Objects records whose OperateFn is a container (1 casket, 3 urn, 4 chest, 5 barrel): d2pilot.loot_fns on the stock
# objects table (113 records)
LOOT = "1,3,4,5,6,7,9,28,50,51,52,53,79,87,88,89,94,95,139,140,141,144,146,147,148,176,177,181,183,198,208,209,240,241,242,243,246,247,248,283,284,326,329,330,331,332,333,334,335,336,341,360,362,364,365,373,383,384,385,387,388,389,390,391,397,413,416,418,420,424,425,430,431,432,433,443,444,445,448,455,463,467,468,469,470,471,477,485,486,487,500,501,502,504,505,516,517,518,524,525,526,529,530,531,532,533,534,535,540,541,544,545,556"


def cold_plains_gold(extra=()):
    """Cold Plains waypoint (tab 1 row 2), /players 8, a Nova sweep, then the containers (each TCR line ends a click)."""
    return [("players", 8, 0),
            ("pilot", ["wpchain", "--chain", "1,2", "--linger", "2"] + list(extra), 120),
            ("pilot", ["farm", "--sweep", "--time", "240"] + NOVA, 300),
            ("pilot", ["objop", "--obj-cls", LOOT, "--times", "8", "--done", "TCR", "--time", "240"] + NOVA, 270)]


def eldritch():
    """Hell: /players 8, Frigid Highlands waypoint (tab 5 row 2), Eldritch the Rectifier's pack (run:2026-10-14-uniques'
    loop), then a short sweep."""
    return [("pilot", ["farm", "--wp", "5,2", "--players", "8", "--time", "150", "--sweep"] + NOVA, 240)]


def find_item():
    """Barbarian: Cold Plains waypoint, then War Cry at what comes near and Find Item on each corpse, walking."""
    return [("pilot", ["wpchain", "--chain", "1,2", "--linger", "2", "--nova-key", "F1"], 120),
            ("pilot", ["corpse", "--walk", "--time", "420", "--chase", "40", "--radius", "5", "--corpse-r", "7",
                       "--nova-key", "F1", "--find-key", "F2", "--nova-hold", "0.8", "--mana-col", "4", "--drink",
                       "0.5", "--hop", "8", "--wait", "1.0"], 480)]


def countess():
    """Classic: Black Marsh waypoint (tab 1 row 5), the Forgotten Tower (LvlWarp 10), its cellar (12), four Crypt
    Down warps (9) to Tower Cellar Level 5 (25), then a sweep and a hunt for the Countess."""
    down = lambda rec: ["farm", "--sweep", "--descend", str(rec), "--descend-time", "240", "--time", "5"] + NOVA + CLASSIC_WP  # noqa: E731
    out = [("pilot", ["wpchain", "--chain", "1,5", "--linger", "2"] + CLASSIC_WP, 120),
           ("until", (20, down(10), 300, 5), 0),
           ("until", (21, down(12), 300, 5), 0)]
    for lid in (22, 23, 24, 25):
        out.append(("until", (lid, down(9), 300, 5), 0))
    out.append(("pilot", ["farm", "--sweep", "--time", "240", "--chase", "30"] + NOVA + CLASSIC_WP, 300))
    # added after the first session (the sweep ended with the level "explored" and her room never activated): hunt
    # her class (corruptrogue3, 45), heading for the farthest unactivated room until she is created
    out.append(("pilot", ["hunt", "--mon-cls", "45", "--time", "300"] + NOVA + CLASSIC_WP, 340))
    return out


def andariel():
    """Andariel by Nova on map seed 3811, the commands of tools/h6d_sessions.py's andariel("nova") (Catacombs Level 2
    waypoint, two Catacombs Down warps, the hunt with her place on that seed): her TC has a `gld,mul=` entry and
    seven picks (tc 60's mul= half, tc 59 and 71)."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import h6d_sessions
    return [("players", 8, 0)] + h6d_sessions.andariel("nova")


def andariel_any():
    """Andariel on a map seed whose layout is not known: /players 8, the Catacombs Level 2 waypoint, two Catacombs
    Down warps, then the hunt with no --goal (towards the farthest unactivated room until she is created)."""
    down = ["farm", "--sweep", "--descend", "18", "--descend-time", "240", "--time", "5"] + NOVA
    return [("players", 8, 0),
            ("pilot", ["wpchain", "--chain", "1,9", "--linger", "2"], 120),
            ("until", (36, down, 300, 5), 0),
            ("until", (37, down, 300, 5), 0),
            ("pilot", ["hunt", "--mon-cls", "156", "--time", "360"] + NOVA, 400)]


def countess_goal():
    """The classic Countess route of countess(), then a hunt towards her place on map seed 3811 (12517, 11064, seen at
    57 sub-tiles in the second session) with longer hops."""
    return countess()[:-2] + [("pilot", ["hunt", "--mon-cls", "45", "--time", "300", "--goal", "12517,11064",
                                         "--hop", "16"] + NOVA + CLASSIC_WP, 340)]


# name: (save Name, steps file, map seed, commands). Map seed 3811: its Rogue Encampment waypoint is on the screen at
# the start (plan 0038 H6d).
SESSIONS = {
    # tc 1, 11, 22, 47, 59, 60, 71: kills and containers with /players 8 (gold lines, the death-drop lines)
    "gold-normal": ("UniqNova", "enter-normal", 3811, cold_plains_gold()),
    # tc 59, 71; quality 22, 23: Eldritch in Hell at MF 472 (max reached, gold find, the D6 clamp)
    "eldritch-hell": ("UniqNova", "uniques-hell", 3821, eldritch()),
    "eldritch-hell-b": ("UniqNova", "uniques-hell", 3822, eldritch()),
    "eldritch-hell-c": ("UniqNova", "uniques-hell", 3823, eldritch()),
    # tc 45, 70: a TCP/IP game hosted alone, /players 8
    "tcpip": ("UniqNova", "h2a-tcpip-host", 3811, cold_plains_gold()),
    # tc 2, 37: Find Item (noNoDrop 1)
    "find": ("FindBar", "enter-normal", 3811, find_item()),
    # tc 59, 60 (mul=), 71: Andariel, /players 8
    "andy": ("UniqNova", "enter-normal", 3811, andariel()),
    "andy-b": ("UniqNova", "enter-normal", 3812, andariel_any()),
    "andy-c": ("UniqNova", "enter-normal", 3813, andariel_any()),
    # tc 34: the classic Countess (Picks -2, total 1)
    "countess": ("UniqClassic", "enter-normal", 3811, countess()),
    "countess-goal": ("UniqClassic", "enter-normal", 3811, countess_goal()),
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
                                 os.path.join(HERE, "gdb", "tc-h2a.gdb"), "--steps",
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

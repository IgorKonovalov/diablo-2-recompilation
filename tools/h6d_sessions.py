#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6d (quest-b6): one game per session on one slot, logged by
tools/gdb/quests.gdb, driven by tools/d2pilot.py (Teleport on Shift + left, Nova on F1, Energy Shield on F2, Hydra on
F3 where the save has it).

Usage:
  python3 -I tools/h6d_sessions.py list
  python3 -I tools/h6d_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the difficulty steps file, the map seed, and the commands run in order, each with a time
limit: `pilot` runs tools/d2pilot.py with the log; `xd` runs tools/xdrive.py on the slot's game window; `keep` copies
the slot's written save (after a Save and Exit) to <DIR>/<RUN>-<SESSION>-<Name>.d2s. The log goes to
workspace/logs/h6d/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is stopped
after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside first, so every session
starts from the save it names. Nothing here feeds a model: the pilot only decides where to click.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6d")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def andariel(kill, extra=(), wp=()):
    """Catacombs Level 2 waypoint (wpchain: the town waypoint's position from its OBJP line), two `Catacombs Down` warps (LvlWarp 18), then the kill. kill: "nova" (the player
    kills), "merc" (the player stands within 8 sub-tiles and casts nothing), "hydra" (as merc, plus Hydra on F3
    towards her every 3 s). The second descent sweeps for no time, so no Nova reaches her before the hunt."""
    ex = list(extra) + list(wp)
    hunt = ["hunt", "--mon-cls", "156", "--time", "300"] + NOVA + list(extra)
    if kill in ("merc", "hydra"):
        hunt += ["--pet", "8"]
    if kill == "hydra":
        hunt += ["--summon-key", "F3", "--summon-every", "3"]
    return [("pilot", ["wpchain", "--chain", "1,9", "--linger", "2"] + list(wp), 120),
            ("pilot", ["farm", "--sweep", "--descend", "18", "--descend-time", "300", "--time", "10"] + NOVA + ex,
             400),
            ("pilot", ["farm", "--sweep", "--descend", "18", "--descend-time", "300",
                       "--time", "0" if kill != "nova" else "5"] + NOVA + list(extra), 380),
            ("pilot", hunt, 340)]


def town_portal_warriv():
    """After the kill: read the Town Portal scroll (inventory cell 9,3), take the portal (object 59), talk to Warriv,
    then Save and Exit (the menu's first line)."""
    return [("pilot", ["insert", "key:i", "sleep:0.8", "rclick:inv:9,3", "sleep:0.8", "key:i", "sleep:1.5"], 60),
            ("pilot", ["objop", "--obj-cls", "59", "--times", "1", "--no-nova"] + NOVA, 120),
            ("pilot", ["npc", "warriv", "talk"], 180),
            ("xd", ["sleep 2", "key Escape", "sleep 1.5", "shot %s" % os.path.join(LOGS, "savexit-menu.png"),
                    "click 400 268", "sleep 6"], 60),
            ("keep", None, 0)]


# name: (save Name, steps file, map seed, commands)
SESSIONS = {
    # qd 18: the kill, Warriv's report and a written save; then the written save's kill (by the mercenary: tc 26/27)
    "andy-warriv": ("QuestFreshM", "enter-normal", 3811, andariel("nova") + town_portal_warriv()),
    "andy-merc": ("@andy-warriv", "enter-normal", 3812, andariel("merc")),
    "andy-merc-fresh": ("QuestFreshM", "enter-normal", 3813, andariel("merc")),
    # tc 27, qd 11: a summon's kill
    "andy-hydra": ("QuestFreshT", "enter-normal", 3814, andariel("hydra")),
    # qd 22: Andariel's gems in Nightmare, Hell and classic
    "andy-nm": ("QuestFreshT", "enter-nightmare", 3821, andariel("nova")),
    "andy-hell": ("QuestFreshT", "enter-hell", 3822, andariel("nova")),
    "andy-classic": ("QuestFreshCT", "enter-normal", 3823, andariel("nova", wp=CLASSIC_WP)),
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
        return os.path.join(saves, "%s-%s-%s.d2s" % (run, src, sname)), sname
    return os.path.join(saves, save + ".d2s"), save


def run_session(name, slot, tag, saves, run):
    _, steps, seed, cmds = SESSIONS[name]
    path, sname = save_path(saves, run, name)
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 os.path.join(HERE, "gdb", "quests.gdb"), "--steps",
                                 os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "2400",
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
            dst = os.path.join(saves, "%s-%s-%s.d2s" % (run, name, sname))
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

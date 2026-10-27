#!/usr/bin/env python3
"""Session runner for plan 0038 batch H1b (run:2026-10-27-sweep-d2s-play): save writes and reloads under
tools/gdb/d2s-h1b.gdb on one harness slot.

    python3 -I tools/h1b_sessions.py list
    python3 -I tools/h1b_sessions.py run --slot N --tag TAG --saves DIR --run RUN NAME [NAME ...]

Each session: the slot's saves directory restored to TAG's aside and set aside again, the session's save installed
alone (tools/d2run.py --install), the game started with the session's gdb file and steps, then the session's commands
in order:
  ("wait", S)                      sleep S seconds (the game runs, nothing is pressed)
  ("pilot", [cmd, args...], T)     tools/d2pilot.py cmd LOG --slot N args... (timeout T)
  ("xd", [xdrive commands])        tools/xdrive.py on the game window ("sleep S" sleeps)
  ("savexit", None, None)          Escape until the game pauses, then "Save and Exit Game" (400, 268); waits for the
                                   two WDONE lines of the write
  ("keep", SUFFIX, None)           copy the character's .d2s from the slot's saves directory to
                                   DIR/RUN-NAME/SUFFIX/<name>.d2s (the file name must stay the character's name)
  ("reload", STEPS, None)          from the main menu: SINGLE PLAYER, OK, and the difficulty of STEPS (normal |
                                   nightmare | hell | none); waits for the next RHRET line and a PLR line after it
  ("tcpreload", None, None)        the same through OTHER MULTIPLAYER -> TCP/IP GAME -> HOST GAME, Normal
  ("wait", S, None) is also the hold in which the agent acts by hand (the drop session's pickup)
  ("menuexit", None, None)         from the main menu: EXIT DIABLO II (400, 532), then wait for the process to end
The session ends with tools/slots.py stop N. The pilot only decides where to click: nothing it computes feeds a check.
Stdlib only.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h1b")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]
DIFF_Y = {"normal": 280, "nightmare": 315, "hell": 350}


def wp(tab, row):
    return ("pilot", ["wpchain", "--chain", "%d,%d" % (tab, row)], 60)


# name: (save, steps, seed, commands, gdb file, extra environment)
SESSIONS = {
    # header pieces, sections, hotkeys, graphics bytes, merc header write/read, LoadFinish, item stats; the weapon
    # swap (key w) before the first Save and Exit, then a reload of the written save and a second Save and Exit; the
    # autosave control: 75 s in town before the swap
    "rt": ("H1bSor", "enter-normal", 27101,
           [("wait", 75, None), ("xd", ["shot {shots}/town.png", "key w", "sleep 2", "shot {shots}/swapped.png"], None),
            ("savexit", None, None), ("keep", "save1", None), ("reload", "normal", None), ("wait", 10, None),
            ("savexit", None, None), ("keep", "save2", None), ("xd", ["shot {shots}/menu.png"], None)],
           "d2s-h1b.gdb", {}),
    # the dead-mercenary header (tool-built bit 16; hireling id 7, name 20 = the last of its 21 names, experience
    # off a level threshold): load, Save and Exit, reload, Save and Exit
    "dead": ("H1bDead", "enter-normal", 27102,
             [("wait", 10, None), ("savexit", None, None), ("keep", "save1", None), ("reload", "normal", None),
              ("wait", 10, None), ("savexit", None, None), ("keep", "save2", None)],
             "d2s-h1b.gdb", {}),
    # a TCP/IP game hosted by this one client (no joiner): who saves and how (PLRSAVE_Save's branch, the host callback,
    # the autosave tick for 80 s), then Save and Exit and a screenshot of where the game lands
    "tcpip": ("H1bSor", "h1b-tcpip-host", 27103,
              [("wait", 80, None), ("savexit", None, None), ("keep", "save1", None),
               ("xd", ["sleep 3", "shot {shots}/after-exit.png"], None)],
              "d2s-h1b.gdb", {}),
    # the window closed in game (Alt+F4): does sub_0052E9C0_SaveAllOnShutdown find a game left to save?
    "shut": ("H1bSor", "enter-normal", 27104,
             [("wait", 10, None), ("xd", ["keydown Alt_L", "key F4", "keyup Alt_L", "sleep 15"], None),
              ("keep", "save1", None)],
             "d2s-h1b.gdb", {}),
    # Hell River of Flame (waypoint tab 4 row 3 from the Act IV town) with 1 life point, teleporting towards new rooms
    # with no attack (the first try stood at the waypoint and met nothing): the character dies and the
    # Rogue (level 30) is left to the monsters; Save and Exit (its first Escape takes the death screen), a reload
    # in Hell, Save and Exit again: the corpse and the mercenary killed in play
    "hell": ("H1bWeak", "enter-hell", 27105,
             [("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", "4", "3"], 90),
              ("pilot", ["explore", "--hops", "25", "--no-nova", "--dead-below", "0"], 240), ("wait", 30, None),
              ("xd", ["shot {shots}/dead.png"], None), ("savexit", None, None), ("keep", "save1", None),
              ("reload", "hell", None), ("wait", 10, None), ("xd", ["shot {shots}/reload.png"], None),
              ("savexit", None, None), ("keep", "save2", None)],
             "d2s-h1b.gdb", {}),
    # a mercenary hired in play (Kashya, Rogue Encampment: waypoint tab 1 row 1), Save and Exit, reload, Save and Exit
    "hire": ("H1bHire", "enter-normal", 27106,
             [("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", "1", "1"], 90),
              ("pilot", ["npc", "kashya", "hire", "--buy", "1"], 300),
              ("savexit", None, None), ("keep", "save1", None), ("reload", "normal", None), ("wait", 10, None),
              ("savexit", None, None), ("keep", "save2", None)],
             "d2s-h1b-hire.gdb", {}),
    # the two plan 0032 reward recipes (questrewards: Soulstone with stat 356 = 0; questrewardsh: the hammer with
    # 356 = 2), loaded and saved: load, Save and Exit
    # the corpus's one runeword (sample qitbarb of run:2026-10-11-d2s-samples, its lsd with flags bit 26): load, Save
    # and Exit, reload (no difficulty box: progression 0), Save and Exit
    "rw": ("qitbarb", "d2s-io-enter", 27109,
           [("wait", 10, None), ("savexit", None, None), ("keep", "save1", None), ("reload", "none", None),
            ("wait", 10, None), ("savexit", None, None), ("keep", "save2", None)], "d2s-h1b.gdb", {}),
    # item flag bit 13 on drops: Normal City of the Damned (waypoint tab 4 row 2; row 1 is the town), Nova kills while exploring, the
    # watchpoint on the first drop's flags (H1B_WATCH=1); a 240 s hold in which the agent picks one drop up by hand
    # (Alt labels, a click on a label: tools/xdrive.py, recorded in the run record), then Save and Exit
    "drop": ("H1bSor", "enter-normal", 27111,
             [("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", "4", "2"], 90),
              ("pilot", ["explore", "--hops", "15"] + NOVA, 200), ("xd", ["shot {shots}/after-explore.png"], None),
              ("wait", 240, None), ("savexit", None, None), ("keep", "save1", None)],
             "d2s-h1b.gdb", {"H1B_WATCH": "1"}),
    "qr": ("QuestRewards", "enter-normal", 27107,
           [("wait", 10, None), ("savexit", None, None), ("keep", "save1", None)], "d2s-h1b.gdb", {}),
    "qrh": ("QuestRewardsH", "enter-hell", 27108,
            [("wait", 10, None), ("savexit", None, None), ("keep", "save1", None)], "d2s-h1b.gdb", {}),
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


def count(log, tag):
    try:
        return sum(1 for ln in open(log, errors="replace") if ln.startswith(tag + " "))
    except OSError:
        return 0


def wait_count(log, tag, n, secs):
    t0 = time.time()
    while time.time() - t0 < secs:
        if count(log, tag) >= n:
            return True
        time.sleep(1.0)
    return False


def saves_dir(slot):
    return os.path.join(ROOT, "workspace", "wineprefix-%d" % slot, "drive_c", "users")


def find_save(slot, sname):
    for dp, _, fs in os.walk(saves_dir(slot)):
        if sname + ".d2s" in fs:
            return os.path.join(dp, sname + ".d2s")
    return None


def run_session(name, slot, tag, saves, run):
    sname, steps, seed, cmds, gdbf, env = SESSIONS[name]
    path = os.path.join(saves, sname + ".d2s")
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
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 os.path.join(HERE, "gdb", gdbf), "--steps",
                                 os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "2400",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=dict(os.environ, **env))
    t0 = time.time()
    while time.time() - t0 < 180:
        time.sleep(3)
        hide_window(slot)
        if count(log, "PLR"):
            break
    time.sleep(3)
    hide_window(slot)

    def xd(*a):
        return sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + list(a),
                  30, out)

    for kind, args, timeout in cmds:
        rc = 0
        print("--- %s %s" % (kind, args), flush=True)
        if kind == "wait":
            time.sleep(args)
        elif kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    ["--shots", shots], timeout, out)
        elif kind == "xd":
            for c in args:
                if c.startswith("sleep "):
                    time.sleep(float(c.split()[1]))
                    continue
                xd(*c.format(shots=shots).split())
        elif kind == "savexit":
            rc = 1
            n0w = count(log, "WDONE")
            for _ in range(4):
                xd("key", "Escape")
                time.sleep(1.5)
                xd("shot", os.path.join(shots, "savexit-menu-%d.png" % n0w))
                xd("click", "400", "268")
                if wait_count(log, "WDONE", n0w + 2, 30):
                    rc = 0
                    break
            time.sleep(6)
            print("  WDONE lines %d -> %d" % (n0w, count(log, "WDONE")), flush=True)
        elif kind == "keep":
            found = find_save(slot, sname)
            dst = os.path.join(saves, "%s-%s" % (run, name), args, sname + ".d2s")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if found:
                shutil.copyfile(found, dst)
                print("kept %s -> %s" % (found, dst), flush=True)
            else:
                print("keep: no %s.d2s under %s" % (sname, saves_dir(slot)), flush=True)
                rc = 1
        elif kind in ("reload", "tcpreload"):
            n0 = count(log, "RHRET")
            p0 = count(log, "PLR")
            xd("click", "700", "150")
            time.sleep(1)
            if kind == "reload":
                xd("click", "400", "307")
            else:
                xd("click", "400", "417")
                time.sleep(2)
                xd("click", "400", "334")
                time.sleep(3)
                xd("click", "400", "189")
            time.sleep(3)
            xd("click", "690", "556")
            time.sleep(2)
            diff = args if kind == "reload" else "normal"
            if diff in DIFF_Y:
                xd("click", "400", str(DIFF_Y[diff]))
            rc = 0 if wait_count(log, "RHRET", n0 + 1, 60) and wait_count(log, "PLR", p0 + 1, 60) else 1
            time.sleep(3)
        elif kind == "menuexit":
            xd("shot", os.path.join(shots, "mainmenu.png"))
            xd("click", "400", "532")
            time.sleep(10)
        print("  -> %s" % rc, flush=True)
        hide_window(slot)
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
            print("%-10s %-10s %-16s %d %d step(s) %s" % (k, v[0], v[1], v[2], len(v[3]), v[4]))
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
    if int(opt["slot"]) == 0:
        print("slot 0 is the owner's")
        return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], opt["saves"], opt["run"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

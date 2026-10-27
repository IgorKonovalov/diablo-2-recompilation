#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6e1 (quest-npc): one game per session on one slot, logged by
tools/gdb/quest-npc.gdb (tools/gdb/quest-state.gdb's files, uniques.py, affixes.py and tools/gdb/quest-npc.py),
driven by tools/d2pilot.py npc (the service menus, the item box, --try for the refusal cases) and tools/quest_sessions.py
act (talk to an NPC, the town waypoint walk, waypoint travel). The session loop is plan 0038 H6e2's
(tools/h6e2_sessions.py): the logger, the log directory and the sessions differ, and a `qs` command runs
tools/quest_sessions.py act on the live log.

Usage:
  python3 -I tools/h6e1_sessions.py list
  python3 -I tools/h6e1_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build; "@S" the save session S of the same run wrote at Save and Exit, kept by `keep`), the
difficulty steps file, the map seed, and the commands run in order, each with a time limit. The log goes to
workspace/logs/h6e1/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is
stopped after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside first, so every
session starts from the save it names. Nothing here feeds a model: the pilot only decides where to click.
"""
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6e1")
GDB = os.path.join(HERE, "gdb", "quest-npc.gdb")


def qs(*actions, t=300):
    """tools/quest_sessions.py act on the live log (talk:CLS:N, towp2, wp:CHAIN, goto:X:Y)."""
    return ("qs", list(actions), t)


def svc(npc, action, item, tries=(), t=240):
    a = ["npc", npc, action, "--item", item, "--npc-time", "150"]
    if tries:
        a += ["--try", ";".join(tries)]
    return ("pilot", a, t)


def wait(s):
    return ("xd", ["sleep %d" % s], 0)


SAVEX = [("savexit", None, 0), ("keep", None, 0)]
# Harrogath: Anya near the waypoint (5114, 5069) as plan 0042 part 3 walked to her
ANYA_GO = qs("goto:5088:5060", "goto:5096:5108")
ANYA = qs("goto:5088:5060", "goto:5096:5108", "talk:512:2")


def give():
    """Qual-Kehk (515), Malah (513: the scroll), Anya (512) in Harrogath; the Rogue Encampment (Akara 148) and the
    Kurast Docks (Ormus 255, Alkor 254: `xyz` in Normal, Meshif 264: `g34` for the held `j34` in Nightmare) by
    waypoint."""
    return [qs("talk:515:2"), qs("talk:513:3"), ANYA, qs("towp2", "wp:1,1", t=200), qs("talk:148:2", t=400),
            qs("towp2", "wp:3,1", t=300), qs("talk:255:2", t=400), qs("talk:254:2", t=400), qs("talk:264:2", t=400),
            wait(3)]


# the refusal cases, by inventory footprint (recipes tools/d2s_recipes/quest-h6e1-*.json)
A_SOCK_TRY = ["inv:0,2,2,2", "inv:6,0,2,3", "inv:9,0,1,3", "inv:2,2,2,2", "inv:4,2,2,2", "inv:6,3,2,1", "inv:8,0,1,3"]
A_PERS_TRY = ["inv:8,0,1,3", "inv:8,3,1,1", "inv:9,3,1,1", "inv:0,2,2,2"]
I5_TRY = ["inv:2,0,1,1", "inv:3,0,1,2", "inv:4,0,1,2", "inv:5,0,2,3", "inv:7,0,1,3", "inv:8,0,2,2", "inv:0,2,2,2",
          "inv:2,2,2,2", "inv:4,2,1,1", "inv:4,3,1,1", "inv:8,2,1,1", "inv:9,2,1,1"]

# name: (save Name, steps file, map seed, commands)
SESSIONS = {
    "give-n": ("NpcGive", "enter-normal", 4921, give()),
    "give-nm": ("NpcGive", "enter-nightmare", 4922, give()),
    "give-h": ("NpcGive", "enter-hell", 4923, give()),
    "imb5": ("NpcImbFive", "enter-normal", 3811, [svc("charsi", "imbue", "inv:0,0,2,2", I5_TRY, 400), wait(3)]),
    "imb6": ("NpcImbSix", "enter-normal", 3811, [svc("charsi", "imbue", "inv:0,0,1,3", ["inv:1,0,2,2", "inv:3,0,2,2"],
                                                     300), wait(3)]),
    # A: a chain of three games on the save each writes (the personalized and socketed items tried again)
    "svca-n": ("NpcSvcA", "enter-normal", 4931, [svc("larzuk", "socket", "inv:0,0,2,2", A_SOCK_TRY, 400),
                                                  svc("anya", "personalize", "inv:2,0,2,2", A_PERS_TRY)] + SAVEX),
    "svca-nm": ("@svca-n", "enter-nightmare", 4932, [svc("larzuk", "socket", "inv:2,0,2,2", ["inv:0,0,2,2"]),
                                                  svc("anya", "personalize", "inv:4,0,2,2", ["inv:2,0,2,2"])] + SAVEX),
    "svca-h": ("@svca-nm", "enter-hell", 4933, [svc("larzuk", "socket", "inv:4,0,2,2"),
                                                  svc("anya", "personalize", "inv:0,0,2,2")] + SAVEX),
    "svcb-n": ("NpcSvcB", "enter-normal", 4941, [svc("larzuk", "socket", "inv:0,0,2,2"),
                                                  svc("anya", "personalize", "inv:7,0,1,2", ["inv:6,0,1,3"])]),
    "svcb-nm": ("NpcSvcB", "enter-nightmare", 4942, [svc("larzuk", "socket", "inv:2,0,2,2"),
                                                  svc("anya", "personalize", "inv:8,0,1,2")]),
    "svcb-h": ("NpcSvcB", "enter-hell", 4943, [svc("larzuk", "socket", "inv:4,0,2,2"),
                                                  svc("anya", "personalize", "inv:0,0,2,2")]),
    "svcc-n": ("NpcSvcC", "enter-normal", 4951, [svc("larzuk", "socket", "inv:0,0,2,2"),
                                                  svc("anya", "personalize", "inv:2,0,2,2")]),
    "svcc-nm": ("NpcSvcC", "enter-nightmare", 4952, [svc("larzuk", "socket", "inv:2,0,2,2")]),
    "svcc-h": ("NpcSvcC", "enter-hell", 4953, [qs("talk:513:3"), svc("larzuk", "socket", "inv:4,0,1,3")]),
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
                                 GDB, "--steps",
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
        if kind == "qs":
            rc = sh(PY + [os.path.join(HERE, "quest_sessions.py"), "act", "--slot", str(slot), log] + args, timeout,
                    out)
        elif kind == "pilot":
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

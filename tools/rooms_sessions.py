"""Scripted harness sessions for plan 0040 Phase 2 (room lifecycle): one game per session on one slot, logged by
tools/gdb/rooms.gdb, driven by tools/d2pilot.py (Teleport on the left button, Nova on the right).

Usage:
  python3 -I tools/rooms_sessions.py list
  python3 -I tools/rooms_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

A session is waypoint travel (`d2pilot.py farm --wp TAB,ROW --time 1`), then cycles of `explore` (Nova bursts, chest
looting, new rooms) and a return to the arrival point (`explore --to-rect`), so the rooms left behind are released
(120-131 frames out of every near set) and restored on the way back. The last cycle waits WAIT seconds before its
return, so its restores come more than 7500 frames after the saves. The "town" kind lures monsters into a town room
(walking out of the town and back), takes the waypoint away and back, for the SaveMonsters 0 case.
The log goes to workspace/logs/rooms/<RUN>-<SESSION>.log. The slot is stopped after each session (tools/slots.py stop
N) and its saves directory returned to the TAG aside. Nothing here feeds a model.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]

# name: (save, steps, seed, kind, wp "TAB,ROW", cycles, hops per explore, final wait s, extra pilot args)
SESSIONS = {
    "n-cold": ("ObjNova", "enter-normal", 4011, "cycle", "1,2", 4, 45, 0, []),
    "n-catacombs": ("ObjNova", "enter-normal", 4012, "cycle", "1,9", 4, 40, 0, []),
    "n-farooze": ("ObjNova", "enter-normal", 4013, "cycle", "2,5", 4, 45, 0, []),
    "nm-dark": ("ObjNova", "enter-nightmare", 4021, "cycle", "1,4", 4, 45, 0, ["--es", "30"]),
    "nm-spider": ("ObjNova", "enter-nightmare", 4022, "cycle", "3,2", 4, 45, 0, ["--es", "30"]),
    "h-highlands": ("ObjNova", "enter-hell", 4031, "cycle", "5,2", 4, 45, 0, ["--es", "30"]),
    "h-flayer": ("ObjNova", "enter-hell", 4032, "cycle", "3,4", 4, 40, 0, ["--es", "30"]),
    "n-long": ("ObjNova", "enter-normal", 4041, "cycle", "1,3", 2, 50, 330, []),
    "nm-long": ("ObjNova", "enter-nightmare", 4042, "cycle", "2,3", 2, 50, 330, ["--es", "30"]),
    "cls-n-cold": ("ObjClassic", "enter-normal", 4051, "cycle", "1,2", 4, 45, 0, CLASSIC_WP),
    "cls-nm-jail": ("ObjClassic", "enter-nightmare", 4052, "cycle", "1,7", 4, 40, 0, CLASSIC_WP + ["--es", "30"]),
    "smoke": ("ObjNova", "enter-normal", 4001, "cycle", "1,2", 1, 20, 0, []),
    "town-n": ("ObjNova", "enter-normal", 4061, "town", "1,1", 3, 35, 0, []),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def last_plr(log):
    pos = None
    try:
        for line in open(os.path.join(ROOT, log), errors="replace"):
            if line.startswith("PLR "):
                try:
                    d = json.loads(line[4:])
                except ValueError:
                    continue
                pos = (d["x"], d["y"], d.get("lid"))
    except OSError:
        pass
    return pos


def pilot(log, slot, args, timeout, out, shots):
    return sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + list(args[1:]) + ["--shots", shots],
              timeout, out)


def run_session(name, slot, tag, saves, run):
    save, steps, seed, kind, wp, cycles, hops, wait, extra = SESSIONS[name]
    log = os.path.join("workspace", "logs", "rooms", "%s-%s.log" % (run, name))
    out = open(os.path.join(ROOT, "workspace", "logs", "rooms", "%s-%s.pilot.txt" % (run, name)), "a")
    shots = os.path.join("workspace", "logs", "rooms", "%s-%s-shots" % (run, name))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    print("=== %s: %s, %s, seed %d, %s -> %s" % (name, save, steps, seed, kind, log), flush=True)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 "tools/gdb/rooms.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after", "2400",
                                 "--install", tag, os.path.join(saves, save + ".d2s"), "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 150:
        time.sleep(3)
        if last_plr(log):
            break
    time.sleep(3)
    common = ["--nova", "2", "--loot", "18", "--persist", "6"] + extra
    wpargs = []
    for k, a in enumerate(extra):
        if a in ("--wp-tab-x0", "--wp-tab-w"):
            wpargs += [a, extra[k + 1]]
    if kind == "cycle":
        pilot(log, slot, ["farm", "--wp", wp, "--time", "1", "--max-res", "1000"] + wpargs, 90, out, shots)
        start = last_plr(log)
        print("arrival %s" % (start,), flush=True)
        for c in range(cycles):
            pilot(log, slot, ["explore", "--any-level", "--hops", str(hops)] + common, 600, out, shots)
            if c == cycles - 1 and wait:
                print("waiting %d s before the last return" % wait, flush=True)
                time.sleep(wait)
            if start:
                rect = "%d,%d,3,3" % (start[0] // 5 - 1, start[1] // 5 - 1)
                pilot(log, slot, ["explore", "--any-level", "--to-rect", rect, "--hops", "120", "--nova", "1"] + extra,
                      600, out,
                      shots)
            time.sleep(8)
    elif kind == "town":
        # the waypoint to the town (arrival next to its waypoint), walk out until monsters come, walk back to the
        # waypoint with them following, take the waypoint away (the town's rooms are released) and back
        pilot(log, slot, ["farm", "--wp", wp, "--time", "1", "--max-res", "1000"] + wpargs, 90, out, shots)
        start = last_plr(log)
        print("arrival %s" % (start,), flush=True)
        for c in range(cycles):
            pilot(log, slot, ["explore", "--any-level", "--walk", "--hops", str(hops), "--nova", "0"], 400, out, shots)
            time.sleep(4)
            if start:
                rect = "%d,%d,1,1" % (start[0] // 5, start[1] // 5)
                pilot(log, slot, ["explore", "--any-level", "--walk", "--to-rect", rect, "--hops", "80", "--nova",
                                  "0"], 400, out, shots)
            time.sleep(3)
            pilot(log, slot, ["wpchain", "--chain", "1,2", "--linger", "15"] + wpargs, 120, out, shots)
            pilot(log, slot, ["wpchain", "--chain", "1,1", "--linger", "6"] + wpargs, 120, out, shots)
    sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
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
            print("%-14s %-10s %-16s %d %-5s wp %s cycles %d hops %d wait %d %s" % ((k,) + v[:8] + (" ".join(v[8]),)))
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
    for n in names:
        if n not in SESSIONS:
            print("unknown session %s" % n)
            return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], opt["saves"], opt["run"])
    sh(PY + ["tools/saves.py", "--slot", opt["slot"], "restore", opt["tag"]], 60)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

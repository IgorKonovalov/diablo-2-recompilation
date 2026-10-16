"""Scripted harness sessions for plan 0037 Phase 2 (combat formulas): one game per session on one slot, logged by
tools/gdb/combat.gdb, driven by tools/d2pilot.py (Teleport on Shift + left, Attack on the right button for the
melee characters; Nova for the immune-monster session).

Usage:
  python3 -I tools/combat_sessions.py list
  python3 -I tools/combat_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (built from tools/d2s_recipes/<recipe>.json with tools/d2s.py
build into --saves), the difficulty steps file, the map seed, and the tools/d2pilot.py commands run in order (each
with a time limit). The log goes to workspace/logs/combat/<RUN>-<SESSION>.log. The slot is stopped after each session
(tools/slots.py stop N) and its saves directory returned to the TAG aside, so every session starts from the built
save. Nothing here feeds a model.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]

MELEE = ["--melee-button", "3", "--melee-hold", "1.4", "--radius", "9", "--max-res", "1000", "--mana-col", "4",
         "--drink", "0.5", "--give-up", "8"]
SWEEP = ["farm", "--sweep"] + MELEE
NOVA = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def andariel(extra=()):
    return [(SWEEP + ["--wp", "1,9", "--descend", "18", "--time", "20"] + list(extra), 260),
            (SWEEP + ["--descend", "18", "--time", "20"] + list(extra), 220),
            (["hunt", "--mon-cls", "156", "--time", "240"] + MELEE + list(extra), 270)]


SESSIONS = {
    # name: (save, steps, seed, [(pilot args, timeout s)])
    "sor-n-plains": ("CombatSor", "enter-normal", 3711, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-n-andariel": ("CombatSor", "enter-normal", 3712, andariel()),
    "sor-nm-plains": ("CombatSor", "enter-nightmare", 3721, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-nm-andariel": ("CombatSor", "enter-nightmare", 3722, andariel()),
    "sor-h-plains": ("CombatSor", "enter-hell", 3731, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-h-andariel": ("CombatSor", "enter-hell", 3732, andariel()),
    "sor-h-highlands": ("CombatSor", "enter-hell", 3733, [(SWEEP + ["--wp", "5,2", "--time", "260"], 330)]),
    "sor-n-p8": ("CombatSor", "enter-normal", 3741, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "260"], 340)]),
    "sor-n-p2": ("CombatSor", "enter-normal", 3742, [(SWEEP + ["--wp", "1,3", "--players", "2", "--time", "200"], 270)]),
    "nova-h-immune": ("CombatSor", "enter-hell", 3751,
                      [(["farm", "--sweep", "--wp", "5,2", "--time", "200", "--max-res", "1000"] + NOVA, 270)]),
    "cls-nm-plains": ("CombatCls", "enter-nightmare", 3761,
                      [(SWEEP + ["--wp", "1,2", "--time", "240"] + CLASSIC_WP, 310)]),
    "cls-h-plains": ("CombatCls", "enter-hell", 3762, [(SWEEP + ["--wp", "1,2", "--time", "240"] + CLASSIC_WP, 310)]),
    "bar-n-plains": ("CombatBar", "enter-normal", 3771,
                     [(["farm", "--wp", "1,2", "--time", "1"], 60),
                      (["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--hops", "120",
                        "--drink", "0.5"], 300)]),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
    log = os.path.join("workspace", "logs", "combat", "%s-%s.log" % (run, name))
    out = open(os.path.join(ROOT, "workspace", "logs", "combat", "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 "tools/gdb/combat.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after", "1500",
                                 "--install", tag, os.path.join(saves, save + ".d2s"), "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 150:
        time.sleep(3)
        try:
            if "PLR " in open(os.path.join(ROOT, log), errors="replace").read():
                break
        except OSError:
            pass
    time.sleep(3)
    for args, timeout in cmds:
        sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + args[1:] +
           ["--shots", "workspace/logs/combat/%s-%s-shots" % (run, name)], timeout, out)
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
            print("%-16s %-10s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
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

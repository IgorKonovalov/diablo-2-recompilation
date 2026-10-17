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

MELEE = ["--melee-button", "3", "--melee-hold", "2.5", "--radius", "9", "--max-res", "1000", "--mana-col", "4",
         "--drink", "0.5", "--give-up", "8"]
SWEEP = ["farm", "--sweep"] + MELEE
NOVA = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def andariel(extra=(), first=(), guard=False):
    """With guard (resume lane), two more descend steps, each skipped once the player is in level 37."""
    if not guard:
        return [(SWEEP + ["--wp", "1,9", "--descend", "18", "--time", "20"] + list(first) + list(extra), 260),
                (SWEEP + ["--descend", "18", "--time", "20"] + list(extra), 220),
                (["hunt", "--mon-cls", "156", "--time", "240"] + MELEE + list(extra), 270)]
    down = SWEEP + ["--descend", "18", "--time", "20"] + list(extra)
    return [(SWEEP + ["--wp", "1,9", "--descend", "18", "--time", "20"] + list(first) + list(extra), 260, 37),
            (down, 220, 37), (down, 220, 37), (down, 220, 37),
            (["hunt", "--mon-cls", "156", "--time", "300"] + MELEE + list(extra), 330)]


def andariel_nova():
    """Nova clears the way and hits Andariel; the mercenary meleeing her gives the hireling boss percent."""
    return [(["farm", "--sweep", "--wp", "1,9", "--descend", "18", "--descend-time", "300", "--time", "15",
              "--max-res", "1000"] + NOVA, 380),
            (["farm", "--sweep", "--descend", "18", "--descend-time", "300", "--time", "15", "--max-res", "1000"]
             + NOVA, 360),
            (["hunt", "--mon-cls", "156", "--time", "240"] + NOVA, 270)]


def andariel_es():
    """Resume lane: CombatSorH (poison and all resistances raised, a mercenary in unique gear) takes the warps
    without sweeping, so the mercenary reaches Andariel alive, then Nova and the mercenary on her."""
    es = NOVA + ["--merc-drink", "0.5"]
    down = ["farm", "--descend", "18", "--descend-time", "300", "--time", "1", "--max-res", "1000"]
    # a descend step is skipped once the player stands in Catacombs Level 4 (level 37), so a failed first search
    # costs one retry instead of leaving the hunt a level short
    return [(down[:1] + ["--wp", "1,9"] + down[1:] + es, 380, 37), (down + es, 360, 37), (down + es, 360, 37),
            (down + es, 360, 37), (["hunt", "--mon-cls", "156", "--time", "300"] + es, 330)]


SESSIONS = {
    "sor-n-highlands": ("CombatSor", "enter-normal", 3715, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "sor-nm-highlands": ("CombatSor", "enter-nightmare", 3725, [(SWEEP + ["--wp", "5,2", "--players", "4", "--time", "270"], 340)]),
    "sor-h-andariel-nova": ("CombatSor", "enter-hell", 3737, andariel_nova()),
    "sor-h-andariel-nova2": ("CombatSor", "enter-hell", 3738, andariel_nova()),
    "sor-h-andariel-nova3": ("CombatSor", "enter-hell", 3739, andariel_nova()),
    "sor-nm-andariel-nova": ("CombatSor", "enter-nightmare", 3727, andariel_nova()),
    # no mercenary, /players 8: monsters live longer, so more attacks per kill on both sides
    "solo-n-p8": ("CombatSolo", "enter-normal", 3713, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "270"], 340)]),
    "solo-n2-p8": ("CombatSolo", "enter-normal", 3714, [(SWEEP + ["--wp", "1,3", "--players", "8", "--time", "270"], 340)]),
    "solo-nm-p8": ("CombatSolo", "enter-nightmare", 3723, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "270"], 340)]),
    "solo-nm2-p8": ("CombatSolo", "enter-nightmare", 3724, [(SWEEP + ["--wp", "1,3", "--players", "8", "--time", "270"], 340)]),
    "solo-h-p3": ("CombatSolo", "enter-hell", 3734, [(SWEEP + ["--wp", "1,2", "--players", "3", "--time", "270"], 340)]),
    "solo-h2-p3": ("CombatSolo", "enter-hell", 3735, [(SWEEP + ["--wp", "1,3", "--players", "3", "--time", "270"], 340)]),
    "solo-h3": ("CombatSolo", "enter-hell", 3736, [(SWEEP + ["--wp", "1,4", "--time", "270"], 340)]),
    # resume lane (plan 0037 Phase 2 review ruling (c)): CombatOW melees with open wounds 85 % and crushing blow 40 %;
    # /players 8 keeps Andariel and Eldritch alive for many hits
    "ow-n-andariel-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel2-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel3-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel4-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel5-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel6-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel7-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-nm-andariel-p8": ("CombatOW", "enter-nightmare", 3727, andariel(first=["--players", "8"], guard=True)),
    "ow-n-highlands-p8": ("CombatOW", "enter-normal", 3783, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands2-p8": ("CombatOW", "enter-normal", 3785, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands3-p8": ("CombatOW", "enter-normal", 3786, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands4-p8": ("CombatOW", "enter-normal", 3787, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-nm-highlands-p8": ("CombatOW", "enter-nightmare", 3784, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "sorh-h-andariel": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel2": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel3": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel4": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel5": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel6": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel7": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel8": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel9": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel10": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel11": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel12": ("CombatSorH", "enter-hell", 3738, andariel_es()),
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


def level_of(path):
    """The level id of the player's last PLR line in a log (None without one)."""
    lid = None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if line.startswith("PLR "):
                    lid = line.split('"lid":', 1)[1].split(",", 1)[0]
    except OSError:
        return None
    return int(lid) if lid is not None else None


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
    os.makedirs(os.path.join(ROOT, "workspace", "logs", "combat", "%s-%s-shots" % (run, name)), exist_ok=True)
    for step in cmds:
        args, timeout = step[0], step[1]
        if len(step) > 2 and level_of(os.path.join(ROOT, log)) == step[2]:
            continue
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

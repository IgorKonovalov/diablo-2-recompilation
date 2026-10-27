"""Scripted harness sessions for plan 0045 Phase 2 (skills and missiles): one game per session on one slot, logged by
tools/gdb/skills.gdb, driven by tools/d2pilot.py.

Usage:
  python3 -I tools/skills_sessions.py list
  python3 -I tools/skills_sessions.py build --saves DIR          # every recipe below into DIR (tools/d2s.py build)
  python3 -I tools/skills_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS: the save (built from tools/d2s_recipes/<recipe>.json), the difficulty steps
file, the game seed, and the steps run in order: ("pilot", [args], timeout) runs one tools/d2pilot.py command;
("wait", s) lets the game run; ("cast", [key, ...], s) presses each key (an F-key choosing the right skill) and
right-clicks next to the player, s seconds apart. A fifth element, a dict, is put in the logger's environment
(SKILLS_CAP_<KIND>, SKILLS_WIN). The log goes to workspace/logs/skills/<RUN>-<SESSION>.log; the slot is stopped
after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside, so every session starts
from the built save. Nothing here feeds a model: the pilot only decides where to click.

The casting: `explore --melee --melee-button 3 --curse-keys K1,K2,...` presses the next skill hotkey and right-clicks
the nearest live monster (the right skill is cast at it; a self-centred skill such as Nova is cast where the player
stands), Teleport stays on Shift + left for the hops.
"""
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGDIR = os.path.join("workspace", "logs", "skills")
EXCEL = os.path.join("workspace", "merged", "data", "global", "excel")
BASE = os.path.join("workspace", "runtime", "saves-backup", "p0005")

# save name: (recipe, base save)
SAVES = {
    "SkillsSor": ("skills-sor", "smpsor"),
    "SkillsAma": ("skills-ama", "smpama"),
    "SkillsAmaJ": ("skills-amaj", "smpama"),
    "SkillsNec": ("skills-nec", "smpnec"),
    "SkillsDru": ("skills-dru", "smpdru"),
    "SkillsBar": ("skills-bar", "smpbar"),
    "SkillsPal": ("skills-pal", "smppal"),
    "SkillsAss": ("skills-ass", "smpasn"),
}


def cast_explore(keys, hops, radius=12, walk=False, extra=()):
    """explore with the right button cast at the nearest live monster, the hotkeys taken in turn over all clicks."""
    return (["explore"] + (["--walk"] if walk else []) +
            ["--melee", "--melee-button", "3", "--curse-keys", ",".join(keys), "--keys-cycle", "--give-up", "8",
             "--radius", str(radius), "--melee-hold", "0.3", "--drink", "0.4", "--mana-col", "4",
             "--hops", str(hops)] + list(extra))


def wp(w):
    return ("pilot", ["farm", "--wp", w, "--time", "1"], 90)


SOR_KEYS = ["F1", "F2", "F3", "F4", "F5", "F6"]
FIELDS = ("1,2", "1,3", "1,4", "1,5")

SESSIONS = {
    # name: (save, steps, seed, [steps], env)
    "sor-smoke": ("SkillsSor", "enter-normal", 4500,
                  [("pilot", ["farm", "--wp", "1,2", "--time", "1"], 90),
                   ("pilot", cast_explore(SOR_KEYS, 12), 300)], {"SKILLS_WIN": "6"}),
    "sor-smoke2": ("SkillsSor", "enter-normal", 4502,
                   [("pilot", ["farm", "--wp", "1,3", "--time", "1"], 90),
                    ("pilot", cast_explore(SOR_KEYS, 60), 600)], {"SKILLS_WIN": "10"}),
}
# the Sorceress: Nova F1, Frost Nova F2, Static Field F3, Fire Bolt F4, Meteor F5, Blaze F6 in turn; Teleport hops
for k, f in enumerate(FIELDS):
    SESSIONS["sor-%d" % (k + 1)] = ("SkillsSor", "enter-normal", 4521 + k, [wp(f), ("pilot", cast_explore(SOR_KEYS, 50), 700)])
# the Amazon: Multiple Shot F1 and Attack F2 (a bow, arrows); Jab F1, Plague Javelin F2, Throw F3 (Titan's Revenge)
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["ama-%d" % (k + 1)] = ("SkillsAma", "enter-normal", 4531 + k,
                                    [wp(f), ("pilot", cast_explore(["F1", "F2"], 50, walk=True), 700)])
    SESSIONS["amaj-%d" % (k + 1)] = ("SkillsAmaJ", "enter-normal", 4541 + k,
                                     [wp(f), ("pilot", cast_explore(["F1", "F2", "F3"], 50, walk=True), 700)])
# the Necromancer: Poison Nova (F1, the killer) and Raise Skeleton on the corpses (F2); Amplify Damage F3, Bone Armor F4
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["nec-%d" % (k + 1)] = ("SkillsNec", "enter-normal", 4551 + k,
                                    [wp(f), ("pilot", ["corpse", "--walk", "--nova-key", "F1", "--find-key", "F2",
                                                       "--corpse-r", "12", "--corpse-tries", "2", "--corpse-max", "30",
                                                       "--radius", "10", "--time", "240", "--chase", "30"], 300),
                                     ("pilot", cast_explore(["F3", "F4", "F1"], 30, walk=True), 500)])
# the Druid: Firestorm F1, Raven F2
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["dru-%d" % (k + 1)] = ("SkillsDru", "enter-normal", 4561 + k,
                                    [wp(f), ("pilot", cast_explore(["F1", "F2"], 50, walk=True), 700)])
# the Barbarian: Bash F1 (twice), Howl F2
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["bar-%d" % (k + 1)] = ("SkillsBar", "enter-normal", 4571 + k,
                                    [wp(f), ("pilot", cast_explore(["F1", "F1", "F2"], 50, walk=True), 700)])
# the Paladin: Holy Shield (F2, cast beside him), Attack F1 with Holy Shield F2 in turn; then Might (F3) and Holy
# Fire (F4) selected while he walks (the aura's periodic do)
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["pal-%d" % (k + 1)] = ("SkillsPal", "enter-normal", 4581 + k,
                                    [wp(f), ("cast", ["F2"], 1.0),
                                     ("pilot", cast_explore(["F1", "F1", "F1", "F2"], 25, walk=True), 400),
                                     ("keys", ["F3"], 0.5),
                                     ("pilot", ["explore", "--walk", "--hops", "15", "--drink", "0.4", "--mana-col", "4"],
                                      300),
                                     ("keys", ["F4"], 0.5),
                                     ("pilot", ["explore", "--walk", "--hops", "15", "--drink", "0.4", "--mana-col", "4"],
                                      300)])
# the Assassin: Fists of Fire F1 (three charges), Attack F2, Fire Trauma F3
for k, f in enumerate(FIELDS[:2]):
    SESSIONS["ass-%d" % (k + 1)] = ("SkillsAss", "enter-normal", 4591 + k,
                                    [wp(f), ("pilot", cast_explore(["F1", "F1", "F1", "F2", "F3"], 50, walk=True), 700)])


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def build(saves):
    os.makedirs(saves, exist_ok=True)
    for name, (recipe, base) in SAVES.items():
        rc = sh(PY + ["tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/%s.json" % recipe,
                      os.path.join(BASE, base + ".d2s"), os.path.join(saves, name + ".d2s")], 60)
        if rc:
            return rc
    return 0


def run_session(name, slot, tag, saves, run):
    row = SESSIONS[name]
    save, steps, seed, todo = row[:4]
    env = row[4] if len(row) > 4 else {}
    log = os.path.join(LOGDIR, "%s-%s.log" % (run, name))
    os.makedirs(os.path.join(ROOT, LOGDIR), exist_ok=True)
    out = open(os.path.join(ROOT, LOGDIR, "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    for k in [k for k in os.environ if k.startswith("SKILLS_")]:
        del os.environ[k]
    os.environ.update(env)
    drv = None
    for attempt in range(3):
        sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
        sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
        if attempt and os.path.exists(os.path.join(ROOT, log)):
            os.replace(os.path.join(ROOT, log), os.path.join(ROOT, log + ".failed%d" % attempt))
        drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                     "tools/gdb/skills.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after",
                                     "1800", "--install", tag, os.path.join(saves, save + ".d2s"), "--log", log],
                               cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               start_new_session=True)
        t0, ok = time.time(), False
        while time.time() - t0 < 150:
            time.sleep(3)
            try:
                if "PLR " in open(os.path.join(ROOT, log), errors="replace").read():
                    ok = True
                    break
            except OSError:
                pass
        if ok:
            break
        print("  no PLR line after 150 s: relaunch", flush=True)
        sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
        try:
            drv.wait(30)
        except subprocess.TimeoutExpired:
            pass
    # wait until the server frame (the lines' "fr") has passed 75
    t0 = time.time()
    while time.time() - t0 < 300:
        try:
            with open(os.path.join(ROOT, log), "rb") as fh:
                fh.seek(max(0, os.path.getsize(os.path.join(ROOT, log)) - 20000))
                tail = fh.read().decode("latin1")
            frs = [int(x) for x in re.findall(r'"fr":(\d+)', tail)]
            if frs and max(frs) >= 75:
                break
        except OSError:
            pass
        time.sleep(2)
    time.sleep(2)
    shots = os.path.join(LOGDIR, "%s-%s-shots" % (run, name))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    for step in todo:
        if step[0] == "pilot":
            args, timeout = step[1], step[2]
            sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + args[1:] + ["--shots", shots],
               timeout, out)
        elif step[0] == "wait":
            time.sleep(step[1])
        elif step[0] == "keys":
            for k in step[1]:
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", k], 30)
                time.sleep(step[2])
        elif step[0] == "cast":
            for k in step[1]:
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", k], 30)
                time.sleep(0.4)
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "--window", "Diablo II", "rclick", "430", "270"], 30)
                time.sleep(step[2])
    sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
    if drv is not None:
        try:
            drv.wait(30)
        except subprocess.TimeoutExpired:
            pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run", "build"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-16s %-10s %-16s %d %r" % (k, v[0], v[1], v[2], v[3]))
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
    if argv[0] == "build":
        return build(opt["saves"])
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

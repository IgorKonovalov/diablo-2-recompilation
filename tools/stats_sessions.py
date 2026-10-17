"""Scripted harness sessions for plan 0041 Phase 2 (stats and states): one game per session on one slot, logged by
tools/gdb/stats.gdb, driven by tools/d2pilot.py (inventory clicks through its `cube --plan` tokens, the weapon swap
key, and for the field sessions `farm`/`explore`).

Usage:
  python3 -I tools/stats_sessions.py list
  python3 -I tools/stats_sessions.py plan SESSION              # print the plan tokens of a session
  python3 -I tools/stats_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (built from tools/d2s_recipes/<recipe>.json with tools/d2s.py
build into --saves), the difficulty steps file, the game seed, and the steps run in order: ("plan", cycles) plays the
equip cycle of the character (written to workspace/logs/stats/<RUN>-<SESSION>.plan) that many times; ("pilot",
[args], timeout) runs one tools/d2pilot.py command; ("wait", s) only lets the game run (the periodic requirement
refresh of an item with `rep-dur` keeps the set code busy). The log goes to workspace/logs/stats/<RUN>-<SESSION>.log;
the slot is stopped after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside, so
every session starts from the built save. Nothing here feeds a model.

The StatsBar cycle (tools/d2s_recipes/statsbar.json; inventory cells as the recipe places them):
  * every equipped slot picked up and put back (an unequip and an equip each: the item's list unlinked and linked,
    its set rebuilt);
  * the weapon swap (W) twice: the dual-wield pair Headstriker + Bing Sz Wang (item_req_percent) in and out;
  * swaps with inventory items: Angelic Mantle (ac%, op 13; Angelical Raiment with the two Angelic Halo rings, a
    duplicate member) and the Paradox breast plate (ac%/lvl, op 5) for the torso (the Soul Cage, whose strength
    requirement fails, comes out to the inventory and back); Sandstorm Trek (stam/lvl, op 2 on maxstamina next to
    Increased Stamina's op 1) and the ethereal War Boots (reqstr 125 - 10) for the boots; Bul-Kathos' ring (hp/lvl,
    op 2) and the unidentified Nagelring for the rings; Highlord's Wrath (+1 skills: passive refresh) for the amulet;
  * the charms Annihilus (all stats) and the Fanatic grand charm (+1 Combat Masteries: Increased Stamina's level)
    picked up and put back;
  * the requirement chain: the belt and gloves (IK Detail +25 and Forge +20 strength) to the inventory (free cells of
    the removed 2 x 3 column), Annihilus picked up and put back (its +20 strength gone while it is on the cursor) and
    the boots slot toggled, the ethereal boots in at that strength and the same again, then the belt and gloves
    back.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGDIR = os.path.join("workspace", "logs", "stats")


S = "settle:0.6,12000"    # after every click: until the log grows by < 12 kB in 0.6 s (the logger holds the game)


def toggle(slot):
    return ["click:eq:%s" % slot, S, "click:eq:%s" % slot, S]


def swap(cell, slot):
    """An inventory item to an equipped slot and the equipped item to the inventory item's footprint."""
    return ["click:inv:%s" % cell, S, "click:eq:%s" % slot, S, "click:inv:%s" % cell, S]


def pickput(cell):
    return ["click:inv:%s" % cell, S, "click:inv:%s" % cell, S]


def statsbar_cycle():
    """StatsBar: the torso holds the Soul Cage, whose strength requirement fails (the game will not equip it again,
    so the cycle never touches that slot)."""
    t = []
    for slot in ("head", "glov", "belt", "feet", "rarm", "larm", "neck", "rrin", "lrin"):
        t += toggle(slot)
    t += ["key:w", S, "key:w", S]
    t += swap("6,0,2,2", "feet") + swap("6,0,2,2", "feet")        # Sandstorm Trek
    t += swap("6,2,2,2", "feet") + swap("6,2,2,2", "feet")        # ethereal War Boots
    t += swap("9,1", "rrin") + swap("9,1", "rrin")                # Bul-Kathos' Wedding Band
    t += swap("9,2", "neck") + swap("9,2", "neck")                # Highlord's Wrath
    t += pickput("9,0") + pickput("8,0,1,3")                      # Annihilus, the Fanatic grand charm
    # the requirement chain: belt and gloves off, Annihilus out and back, the boots slot and the ethereal boots
    t += ["click:eq:belt", S, "click:inv:0,0,2,1", S]
    t += ["click:eq:glov", S, "click:inv:0,1,2,2", S]
    t += pickput("9,0") + toggle("feet")                          # IK Pillar (reqstr 125) at the lower strength
    t += swap("6,2,2,2", "feet")                                  # the ethereal boots in (125 - 10)
    t += pickput("9,0") + toggle("feet")
    t += swap("6,2,2,2", "feet")                                  # the Pillar back
    t += ["click:inv:0,1,2,2", S, "click:eq:glov", S]
    t += ["click:inv:0,0,2,1", S, "click:eq:belt", S]
    return t


def statsbarb_cycle():
    """StatsBarB: Angelic Mantle on the torso swapped with the Paradox breast plate (ac%/lvl, op 5), Ironpelt
    (ac/lvl, op 4) and Duriel's Shell (ac/lvl, hp/lvl); a second Angelic Halo swapped into the right ring (the other
    ring slot holds the unidentified Nagelring); the set and weapon toggles as for StatsBar."""
    t = []
    for slot in ("head", "glov", "belt", "feet", "rarm", "larm", "neck", "tors"):
        t += toggle(slot)
    t += ["key:w", S, "key:w", S]
    for cell in ("0,0,2,3", "2,0,2,3", "4,0,2,3"):
        t += swap(cell, "tors") + swap(cell, "tors")
    t += swap("6,0", "rrin") + swap("6,0", "rrin")
    t += swap("9,2", "neck") + swap("9,2", "neck")
    t += pickput("9,0")
    return t


PLANS = {"statsbar": statsbar_cycle, "statsbarb": statsbarb_cycle}

SESSIONS = {
    # name: (save, steps, seed, [steps])
    "bar-smoke": ("StatsBar", "enter-normal", 4110, [("plan", "statsbar", 1), ("wait", 5)]),
    "barb-smoke": ("StatsBarB", "enter-normal", 4120, [("plan", "statsbarb", 1), ("wait", 5)]),
    "pal-smoke": ("StatsPal", "enter-normal", 4130,
                  [("pilot", ["farm", "--wp", "5,4", "--time", "1"], 90),
                   ("pilot", ["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--hops", "40",
                              "--drink", "0.5"], 300)]),
    "bar-town1": ("StatsBar", "enter-normal", 4111, [("plan", "statsbar", 6), ("wait", 20)]),
    "bar-town2": ("StatsBar", "enter-normal", 4112, [("plan", "statsbar", 6), ("wait", 20)]),
    "bar-town3": ("StatsBar", "enter-nightmare", 4113, [("plan", "statsbar", 6), ("wait", 20)]),
    "bar-town4": ("StatsBar", "enter-hell", 4114, [("plan", "statsbar", 6), ("wait", 20)]),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def plan_tokens(name, cycles):
    t = ["key:i", "settle:1"]
    for _ in range(cycles):
        t += PLANS[name]()
    t += ["key:i", "sleep:0.5"]
    return t


def run_session(name, slot, tag, saves, run):
    save, steps, seed, todo = SESSIONS[name]
    log = os.path.join(LOGDIR, "%s-%s.log" % (run, name))
    os.makedirs(os.path.join(ROOT, LOGDIR), exist_ok=True)
    out = open(os.path.join(ROOT, LOGDIR, "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    for attempt in range(3):
        sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
        sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
        if attempt:
            os.replace(os.path.join(ROOT, log), os.path.join(ROOT, log + ".failed%d" % attempt))
        drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                     "tools/gdb/stats.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after",
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
        # the steps missed the menu (seen with two slots starting together): stop and start again
        print("  no PLR line after 150 s: relaunch", flush=True)
        sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
        try:
            drv.wait(30)
        except subprocess.TimeoutExpired:
            pass
    time.sleep(15)            # the PLR line comes while the loading screen is still up
    shots = os.path.join(LOGDIR, "%s-%s-shots" % (run, name))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    for step in todo:
        if step[0] == "plan":
            pf = os.path.join(LOGDIR, "%s-%s.plan" % (run, name))
            toks = plan_tokens(step[1], step[2])
            if os.environ.get("STATS_SHOTS"):          # a screenshot after every click (debugging a cycle)
                k, with_shots = 0, []
                for tok in toks:
                    with_shots.append(tok)
                    if tok.startswith("settle"):
                        k += 1
                        with_shots.append("shot:%s/c%04d.png" % (shots, k))
                toks = with_shots
            with open(os.path.join(ROOT, pf), "w") as fh:
                fh.write("# tools/stats_sessions.py %s, %d cycle(s)\n" % (step[1], step[2]))
                fh.write("\n".join(toks) + "\n")
            sh(PY + ["tools/d2pilot.py", "cube", log, "--slot", str(slot), "--plan", pf,
                     "shot:%s/end.png" % shots], 1800, out)
        elif step[0] == "pilot":
            args, timeout = step[1], step[2]
            sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + args[1:] + ["--shots", shots],
               timeout, out)
        elif step[0] == "wait":
            time.sleep(step[1])
    sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run", "plan"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-16s %-10s %-16s %d %r" % (k, v[0], v[1], v[2], v[3]))
        return 0
    if argv[0] == "plan":
        for st in SESSIONS[argv[1]][3]:
            if st[0] == "plan":
                print("\n".join(plan_tokens(st[1], st[2])))
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

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

The cycles (tools/d2s_recipes/statsbar.json, statsbarb.json): every click that must change the stat lists is a
`clickv`/`keyv` token (tools/d2pilot.py cube: repeated until a ULK/LNK/UOE line follows), and every equipped slot is
picked up and put back rather than swapped with an inventory item (a swap the game refuses, or a lost click, leaves an
item on the cursor and shifts every later click). See statsbar_cycle and statsbarb_cycle.
"""
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGDIR = os.path.join("workspace", "logs", "stats")


S = "settle:0.6,12000"    # after every click: until the log grows by < 12 kB in 0.6 s (the logger holds the game)


def toggle(slot):
    return ["clickv:eq:%s" % slot, S, "clickv:eq:%s" % slot, S]


def swap(cell, slot):
    """An inventory item to an equipped slot and the equipped item to the inventory item's footprint."""
    return ["click:inv:%s" % cell, S, "clickv:eq:%s" % slot, S, "click:inv:%s" % cell, S]


def pickput(cell):
    """A charm picked up (its list unlinked) and put back (linked)."""
    return ["clickv:inv:%s" % cell, S, "clickv:inv:%s" % cell, S]


def chain():
    """The requirement chain: the belt and the gloves (IK Detail +25 and Forge +20 strength) to empty inventory
    cells, Annihilus (+20 strength while it is on the cursor) picked up and put back, the boots slot toggled at the
    lower strength, then the gloves and the belt back."""
    t = ["clickv:eq:belt", S, "click:inv:0,0,2,1", S]
    t += ["clickv:eq:glov", S, "click:inv:0,1,2,2", S]
    t += pickput("9,0") + toggle("feet")
    t += ["click:inv:0,1,2,2", S, "clickv:eq:glov", S]
    t += ["click:inv:0,0,2,1", S, "clickv:eq:belt", S]
    return t


def statsbar_cycle():
    """StatsBar: every slot picked up and put back except the torso (the Soul Cage, whose strength requirement fails:
    the game would not take it back), the weapon swap twice (the dual-wield pair), the two charms, the chain."""
    t = []
    for slot in ("head", "glov", "belt", "feet", "rarm", "larm", "neck", "rrin", "lrin"):
        t += toggle(slot)
    t += ["keyv:w", S, "keyv:w", S]
    t += pickput("9,0") + pickput("8,0,1,3")
    t += chain()
    return t


def statsbarb_cycle():
    """StatsBarB: the same on the second character (Paradox breast plate, Sandstorm Trek, Highlord's Wrath,
    Bul-Kathos' ring, the unidentified Nagelring, Messerschmidt's Reaver on the switch); the torso is toggled too."""
    t = []
    for slot in ("head", "glov", "belt", "feet", "rarm", "larm", "neck", "rrin", "lrin", "tors"):
        t += toggle(slot)
    t += ["keyv:w", S, "keyv:w", S]
    t += pickput("9,0") + pickput("8,0,1,3")
    t += chain()
    return t


def statsbarc_cycle():
    """StatsBarC (the op coverage character): the weapon swap ten times (Headstriker and Bing Sz Wang against
    Messerschmidt's Reaver: op 4, 5 and 13 on the item lists at every link), the torso (Ironpelt: ac/lvl op 4 and ac%
    op 13) four times, Annihilus four times (strength, energy, vitality: op 1, 2, 8, 9 and The Stone of Jordan's
    mana% op 11 on the player's list), the grand charm twice."""
    t = []
    for _ in range(5):
        t += ["keyv:w", S, "keyv:w", S]
    for _ in range(2):
        t += toggle("tors")
    for _ in range(4):
        t += pickput("9,0")
    t += pickput("8,0,1,3")
    return t


def statsnec_cycle():
    """StatsNec: the full Trang-Oul's Avatar (its full block sets the property `state` = monsterset, stat 98: the
    stat callback's group exclusion, stats/0002 § 2); each piece picked up and put back (full -> 4 of 5 -> full)."""
    t = []
    for slot in ("head", "tors", "larm", "glov", "belt", "rarm"):
        t += toggle(slot)
    return t


PLANS = {"statsbar": statsbar_cycle, "statsbarb": statsbarb_cycle, "statsbarc": statsbarc_cycle,
         "statsnec": statsnec_cycle}

# objects.txt rows with OperateFn 2 (shrines) or 22 (wells): the classes objop may operate
SHRINES_WELLS = ("2,77,81,83,84,85,86,93,96,97,109,111,113,115,116,118,120,123,124,130,132,133,134,135,136,137,138,"
                 "150,151,164,165,166,167,168,170,172,173,184,190,191,197,199,200,201,202,206,226,231,232,236,249,260,"
                 "262,263,264,265,275,276,277,278,279,280,281,282,299,300,301,302,303,319,320,322,325,343,344,361,415,"
                 "416,422,423,424,427,428,429,465,466,473,480,484,485,489,492,493,494,496,498,499,500,504,510,513,514,"
                 "520,521,522,523")
PAL_WALK = ["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--drink", "0.5",
            "--mana-col", "0"]
POTIONS = ("keys", ["2", "3", "4"], 3.0)      # one antidote, one thawing, one stamina potion (belt columns 2..4)


def pal_field(wp, hops=60):
    """The Paladin in the field: waypoint, explore (monsters curse, chill and poison him; Prayer and Sanctuary run;
    the kills level him up), potions, the shrines and wells the explore activated, explore again, potions."""
    return [("pilot", ["farm", "--wp", wp, "--time", "1", "--mana-col", "0"], 90),
            ("pilot", PAL_WALK + ["--hops", str(hops)], 600), POTIONS,
            ("pilot", ["objop", "--walk", "--no-nova", "--obj-cls", SHRINES_WELLS, "--times", "4", "--time", "150",
                       "--done", "SHR1", "--obj-near", "3"], 200), POTIONS,
            ("pilot", PAL_WALK + ["--hops", str(hops)], 600), POTIONS,
            ("pilot", ["objop", "--walk", "--no-nova", "--obj-cls", SHRINES_WELLS, "--times", "4", "--time", "150",
                       "--done", "WEL1", "--obj-near", "3"], 200), POTIONS]


SESSIONS = {
    # name: (save, steps, seed, [steps])
    "bar-smoke": ("StatsBar", "enter-normal", 4110, [("plan", "statsbar", 1), ("wait", 5)]),
    "barb-smoke": ("StatsBarB", "enter-normal", 4120, [("plan", "statsbarb", 1), ("wait", 5)]),
    "pal-smoke": ("StatsPal", "enter-normal", 4130,
                  [("pilot", ["farm", "--wp", "5,4", "--time", "1"], 90),
                   ("pilot", ["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--hops", "40",
                              "--drink", "0.5"], 300)]),
    "pal-crystal1": ("StatsPal", "enter-normal", 4141, pal_field("5,4")),
    "pal-crystal2": ("StatsPal", "enter-normal", 4142, pal_field("5,4")),
    "pal-glacial": ("StatsPal", "enter-normal", 4143, pal_field("5,6")),
    "pal-tundra": ("StatsPal", "enter-normal", 4144, pal_field("5,7")),
    "pal-spider": ("StatsPal", "enter-normal", 4145, pal_field("3,2")),
    "pal-oasis": ("StatsPal", "enter-normal", 4146, pal_field("2,5")),
    "palb-crystal": ("StatsPalB", "enter-normal", 4161, pal_field("5,4", 40)),
    "palb-spider": ("StatsPalB", "enter-normal", 4162, pal_field("3,2", 40)),
    "barb-town1": ("StatsBarB", "enter-normal", 4121, [("plan", "statsbarb", 3), ("wait", 20)]),
    "barb-town2": ("StatsBarB", "enter-nightmare", 4122, [("plan", "statsbarb", 3), ("wait", 20)]),
    "barc-town1": ("StatsBarC", "enter-normal", 4131, [("plan", "statsbarc", 4), ("wait", 10)]),
    "nec-town1": ("StatsNec", "enter-normal", 4151, [("plan", "statsnec", 4), ("wait", 10)]),
    "bar-town1": ("StatsBar", "enter-normal", 4111, [("plan", "statsbar", 3), ("wait", 20)]),
    "bar-town2": ("StatsBar", "enter-normal", 4112, [("plan", "statsbar", 3), ("wait", 20)]),
    "bar-town3": ("StatsBar", "enter-nightmare", 4113, [("plan", "statsbar", 3), ("wait", 20)]),
    "bar-town4": ("StatsBar", "enter-hell", 4114, [("plan", "statsbar", 3), ("wait", 20)]),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def plan_tokens(name, cycles):
    t = ["inv:open", "settle:1"]
    for _ in range(cycles):
        t += PLANS[name]()
    t += ["inv:closed", "sleep:0.5"]
    return t


def run_session(name, slot, tag, saves, run):
    save, steps, seed, todo = SESSIONS[name]
    log = os.path.join(LOGDIR, "%s-%s.log" % (run, name))
    os.makedirs(os.path.join(ROOT, LOGDIR), exist_ok=True)
    out = open(os.path.join(ROOT, LOGDIR, "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    if save.startswith("StatsPal"):                 # field sessions: every tick logged, the objects for objop
        os.environ["STATS_TICKS"] = os.environ.get("STATS_TICKS", "6000")
        os.environ["STATS_OBJS"] = "1"
    for attempt in range(3):
        sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
        sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
        if attempt and os.path.exists(os.path.join(ROOT, log)):
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
    # the PLR line comes while the loading screen is still up (the logger's load-time work holds the game): wait
    # until the server frame (every line's "fr") has passed 75, three seconds in the game
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
        elif step[0] == "keys":
            for k in step[1]:
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", k], 30)
                time.sleep(step[2])
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

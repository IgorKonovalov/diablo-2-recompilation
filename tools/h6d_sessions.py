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
the slot's written save (after a Save and Exit) to <DIR>/<RUN>-<SESSION>/<Name>.d2s. The log goes to
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


def andariel(kill, extra=(), wp=()):  # noqa: C901
    """Catacombs Level 2 waypoint (wpchain: the town waypoint's position from its OBJP line), two `Catacombs Down` warps (LvlWarp 18), then the kill. kill: "nova" (the player
    kills), "merc" (the player stands within 8 sub-tiles and casts nothing), "hydra" (as merc, plus Hydra on F3
    towards her every 3 s). On map seed 3811 she stands near (22546, 9546) (the first session), the hunt's --goal.
    The second descent sweeps for no time, so no Nova reaches her before the hunt."""
    ex = list(extra) + list(wp)
    hunt = ["hunt", "--mon-cls", "156", "--time", "300", "--goal", "22546,9546"] + NOVA + list(extra)
    if kill in ("merc", "hydra"):
        hunt += ["--pet", "8"]
    if kill == "hydra":
        hunt += ["--summon-key", "F3", "--summon-every", "3"]
    return [("pilot", ["wpchain", "--chain", "1,9", "--linger", "2"] + list(wp), 120),
            ("until", (36, ["farm", "--sweep", "--descend", "18", "--descend-time", "240", "--time", "5"] + NOVA + ex,
                       300, 5), 0),
            ("until", (37, ["farm", "--sweep", "--descend", "18", "--descend-time", "240",
                            "--time", "0" if kill != "nova" else "5"] + NOVA + ex, 300, 5), 0),
            ("pilot", hunt, 340)]


def town_portal_warriv():
    """After the kill: read the Town Portal scroll (inventory cell 9,3), take the portal (object 59; the click ends at
    the town's first room activation, RRESEED), walk two steps (so a PLR line gives the town), talk to Warriv, then
    Save and Exit (the menu's first line). Seed 3811 was the first try: the kill, then the portal clicked twice."""
    return [("pilot", ["insert", "key:i", "sleep:0.8", "rclick:inv:9,3", "sleep:0.8", "key:i", "sleep:1.5"], 60),
            ("pilot", ["objop", "--obj-cls", "59", "--times", "1", "--no-nova", "--done", "RRESEED"] + NOVA, 120),
            ("xd", ["sleep 2", "click 470 340", "sleep 1.5", "click 330 330", "sleep 1.5"], 30),
            ("pilot", ["npc", "warriv", "talk"], 180),
            ("savexit", None, 0),
            ("keep", None, 0)]


def hellforge():
    """River of Flame waypoint (tab 4 row 3), to the forge (Hellforge 376, LvlPrest 853/854), clear Hephasto's pack,
    then four single clicks on the forge (the soulstone, three hammer strikes; each FOP line ends a click), with time
    for the forge's mode change after the soulstone, then 30 s for the gem waves and the rune."""
    op = ["objop", "--obj-cls", "376", "--times", "1", "--done", "FOP"] + NOVA
    return [("pilot", ["wpchain", "--chain", "4,3", "--linger", "2"], 120),
            ("pilot", ["objop", "--obj-cls", "376", "--to-pdef", "853,854", "--approach", "--obj-near", "12", "--time",
                       "420", "--no-nova", "--hop", "14"] + NOVA, 450),
            ("pilot", ["farm", "--sweep", "--time", "30"] + NOVA, 90),
            ("pilot", op, 90), ("xd", ["sleep 5"], 0),
            ("pilot", op, 90), ("xd", ["sleep 1.5"], 0),
            ("pilot", op, 90), ("xd", ["sleep 1.5"], 0),
            ("pilot", op, 90), ("xd", ["sleep 30"], 0)]


def diablo():
    """River of Flame waypoint (tab 4 row 3); into the Chaos Sanctuary (level 108) by blind hops towards its Entry
    preset (LvlPrest 857: the Sanctuary is built with the River, objop --pdef-any); to each wing (858-861, explore
    --to-pdef, Nova on the way) so the seals' rooms populate; each of the five seals (objects 392-396) operated once
    (OOP line); a sweep for the seal bosses; then Diablo (243)."""
    out = [("pilot", ["wpchain", "--chain", "4,3", "--linger", "2"], 120),
           ("until", (108, ["objop", "--obj-cls", "9999", "--to-pdef", "857", "--pdef-any", "--time", "90"] + NOVA,
                      120, 4), 0)]
    for wing in (858, 859, 860, 861):
        out.append(("pilot", ["explore", "--to-pdef", str(wing), "--hops", "60"] + NOVA, 240))
    for c in (392, 393, 394, 395, 396):
        out.append(("pilot", ["objop", "--obj-cls", str(c), "--times", "1", "--done", "OOP", "--time", "180"] + NOVA,
                    200))
        out.append(("pilot", ["farm", "--sweep", "--time", "15"] + NOVA, 60))
    out.append(("pilot", ["hunt", "--mon-cls", "243", "--time", "420"] + NOVA, 450))
    return out


def baal():
    """Worldstone Keep Level 2 waypoint (tab 5 row 9); two `Baal Temple Down` warps (LvlWarp 87/88) to the Throne of
    Destruction (131); a long Nova sweep through the five waves; the Worldstone Chamber portal (object 563); Baal
    (544)."""
    down = ["farm", "--sweep", "--descend", "87,88", "--descend-time", "240", "--time", "5"] + NOVA
    return [("pilot", ["wpchain", "--chain", "5,9", "--linger", "2"], 120),
            ("until", (130, down, 300, 5), 0),
            ("until", (131, down, 300, 5), 0),
            ("pilot", ["farm", "--sweep", "--time", "420", "--chase", "30"] + NOVA, 460),
            ("until", (132, ["objop", "--obj-cls", "563", "--times", "1", "--done", "RRESEED", "--time", "120"]
                       + NOVA, 150, 3), 0),
            ("pilot", ["hunt", "--mon-cls", "544", "--time", "420"] + NOVA, 450)]


# name: (save Name, steps file, map seed, commands). The Act I sessions share map seed 3811, whose Rogue Encampment
# waypoint is on the screen at the start (3815's was not: the wpchain clicks fell off the window).
SESSIONS = {
    # qd 18: the kill, Warriv's report and a written save; then the written save's kill (by the mercenary: tc 26/27)
    "andy-warriv": ("QuestFreshM", "enter-normal", 3811, andariel("merc") + town_portal_warriv()),
    "andy-reported": ("@andy-warriv", "enter-normal", 3811, andariel("hydra")),
    "andy-merc-fresh": ("QuestFreshM", "enter-normal", 3811, andariel("merc")),
    # tc 27, qd 11: a summon's kill
    "andy-hydra": ("QuestFreshT", "enter-normal", 3811, andariel("hydra")),
    # qd 22: Andariel's gems in Nightmare, Hell and classic
    "andy-nm": ("QuestFreshT", "enter-nightmare", 3811, andariel("nova")),
    "andy-hell": ("QuestFreshT", "enter-hell", 3811, andariel("nova")),
    "andy-classic": ("QuestFreshCT", "enter-normal", 3811, andariel("nova", wp=CLASSIC_WP)),
    # qd 25: the Nightmare forge with a stat-356-1 hammer (356 = the difficulty)
    "forge-nm": ("QuestSvcOne", "enter-nightmare", 3811, hellforge()),
    # qd 13, 16, 27: Diablo and Baal, fresh (word clear) and done (bit 0)
    "diablo-fresh": ("QuestFreshT", "enter-normal", 3811, diablo()),
    "diablo-done": ("QuestAllDone", "enter-normal", 3811, diablo()),
    "baal-fresh": ("QuestBaalF", "enter-normal", 3811, baal()),
    "baal-done": ("QuestAllDone", "enter-normal", 3811, baal()),
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

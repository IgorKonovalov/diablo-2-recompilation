#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H4a (monsters-a): one game per session on one slot, logged by
tools/gdb/mon-h4a.gdb (tools/gdb/mon-stats.gdb plus tools/gdb/mon-h4a.py), driven by tools/d2pilot.py (Teleport on
Shift + left, Nova on F1, Energy Shield on F2: tools/d2s_recipes/uniqnova.json). MONSPAWN_WATCH and H4B_WATCH are
empty in every session (no debug register armed).

Usage:
  python3 -I tools/h4a_sessions.py list
  python3 -I tools/h4a_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s), the difficulty steps file, the map seed, and
the commands run in order, each with a time limit: `pilot` runs tools/d2pilot.py with the log; `until` repeats a pilot
command until the player's level is the target; `xd` runs tools/xdrive.py on the slot's game window. The log goes to
workspace/logs/h4a/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is stopped
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
LOGS = os.path.join(ROOT, "workspace", "logs", "h4a")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def wp(tab, row):
    """The waypoint from the Act IV town start (the save's last town), at its screen position there (as H4b; the
    object lines held no waypoint at the start in the first try)."""
    return ("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", str(tab), str(row)], 90)


def hunt(cls, t=300, extra=()):
    return ("pilot", ["hunt", "--mon-cls", str(cls), "--time", str(t)] + NOVA + list(extra), t + 40)


def explore(hops, extra=()):
    return ("pilot", ["explore", "--hops", str(hops), "--persist", "10"] + NOVA + list(extra), 60 + 4 * hops)


def sweep(t):
    return ("pilot", ["farm", "--sweep", "--time", str(t)] + NOVA, t + 60)


def descend(lid, rows):
    return ("until", (lid, ["farm", "--sweep", "--descend", rows, "--descend-time", "240", "--time", "5"] + NOVA,
                      300, 5), 0)


def chaos():
    """River of Flame waypoint (tab 4 row 3); into the Chaos Sanctuary (level 108) by blind hops towards its Entry
    preset (LvlPrest 857, objop --pdef-any; plan 0038 H6d's route); to each wing (858-861) so the seals' rooms
    populate; each of the five seals (objects 392-396) operated once (OOP line) with a sweep for the seal bosses
    (Infector of Souls, Lord De Seis, Grand Vizier: records 36-38); an explore of the rooms not yet activated; then
    Diablo (243)."""
    out = [wp(4, 3),
           ("until", (108, ["objop", "--obj-cls", "9999", "--to-pdef", "857", "--pdef-any", "--time", "90"] + NOVA,
                      120, 4), 0)]
    seals = "392,393,394,395,396"
    for wing in (858, 859, 860, 861):
        out.append(("pilot", ["explore", "--to-pdef", str(wing), "--hops", "60", "--persist", "10"] + NOVA, 240))
        # every seal seen so far (OBJS lines, --obj-mem: also those of rooms no longer active), each clicked once
        out.append(("pilot", ["objop", "--obj-cls", seals, "--obj-mem", "--times", "2", "--done", "OOX", "--time",
                              "150", "--obj-near", "6"] + NOVA, 170))
        out.append(sweep(20))
    out.append(("pilot", ["objop", "--obj-cls", seals, "--obj-mem", "--times", "5", "--done", "OOX", "--time",
                          "240", "--obj-near", "6"] + NOVA, 260))
    out.append(sweep(30))
    # the gate's closed state: rooms of 108 that first activate after the seal bosses died (GQ eax 1, quest 23 +0x13)
    out.append(explore(80))
    out.append(hunt(243, 360))
    return out


def chaos6(near="4", t=150):
    """chaos5's route with the seal search per wing: chaos5 stopped at each wing's edge (explore --to-pdef), where only
    the two seals of 859 were logged, and its later objops went back to those two (operated, no OOX). Here each wing in
    turn is an objop that heads for the preset's centre until a seal is listed (--to-pdef), never re-targets a seal
    already operated (--skip-operated), and is followed by a sweep for the seal boss."""
    out = [wp(4, 3),
           ("until", (108, ["objop", "--obj-cls", "9999", "--to-pdef", "857", "--pdef-any", "--time", "90"] + NOVA,
                      120, 4), 0)]
    seals = "392,393,394,395,396"
    for wing in (859, 858, 860, 861):
        out.append(("pilot", ["objop", "--obj-cls", seals, "--to-pdef", str(wing), "--pdef-any", "--skip-operated",
                              "--times", "2", "--done", "OOX", "--time", str(t), "--obj-near", near] + NOVA, t + 20))
        out.append(sweep(25))
    out.append(sweep(30))
    out.append(explore(80))
    out.append(hunt(243, 360))
    return out


# name: (save Name, steps file, map seed, commands). All start in the Act IV town (the save's last town).
SESSIONS = {
    # special 35, 68 (Blood Raven's name, mod 12), the stats 7/18/21 MonEquip creation again; Act I wanderer rider
    "raven": ("UniqNova", "enter-nightmare", 4901,
              [wp(1, 2), ("pilot", ["explore", "--hops", "300", "--to-pdef", "108", "--pdef-any", "--persist", "25"] + NOVA, 400),
               hunt(267, 240), sweep(30)]),
    # raven again on plan 0048's raven-xn2 map seed (its explore reached the Burial Grounds), with --persist
    "raven2": ("UniqNova", "enter-nightmare", 4807,
               [wp(1, 2), ("pilot", ["explore", "--hops", "300", "--to-pdef", "108", "--pdef-any", "--persist", "25"]
                           + NOVA, 400), hunt(267, 240), sweep(30)]),
    # special 34 (Treehead WoodFist, brute2 24, its mod list); Act I rider
    "tree": ("UniqNova", "enter-nightmare", 4902, [wp(1, 4), hunt(24, 420), sweep(30)]),
    # special 69 (Andariel, 156: the fixed-name branch); Act I rider
    "andy": ("UniqNova", "enter-nightmare", 4903, [wp(1, 9), descend(36, "18"), descend(37, "18"), hunt(156, 300)]),
    # special 54 (Radament, tail 10): Sewers Level 2 waypoint, the Sewer Down warp (LvlWarp 23) to level 49
    "radament": ("UniqNova", "enter-nightmare", 4904, [wp(2, 2), descend(49, "23"), hunt(229, 420), sweep(30)]),
    # special 55 (the council, tails 26, 27, 29): Travincal
    "council": ("UniqNova", "enter-nightmare", 4905, [wp(3, 8), explore(220)]),
    # special 30, 50, 51 (Bremm Sparkfist, Mod1 30) and 69 (Mephisto, 242): Durance of Hate 2 -> 3 (LvlWarp 67/68)
    "durance": ("UniqNova", "enter-nightmare", 4906, [wp(3, 9), descend(102, "67,68"), explore(120),
                                                     hunt(242, 300)]),
    # special 9, 10, 25, 31, 38, 50, 56 (the seal bosses), spawn 11 (the gate, GQ), 69 (Diablo, 243)
    "chaos": ("UniqNova", "enter-nightmare", 4907, chaos()),
    # chaos again with the object lines (the first try had none, so objop found no seal)
    "chaos2": ("UniqNova", "enter-nightmare", 4907, chaos(), "mon-h4a-obj.gdb"),
    # chaos2 again with OBJS lines (mon-h4a.py), which objop needs to find an object's position
    "chaos3": ("UniqNova", "enter-nightmare", 4907, chaos(), "mon-h4a-obj.gdb"),
    # chaos3 with the seals by memory after each wing (objop on one class found no seal whose room was inactive)
    "chaos4": ("UniqNova", "enter-nightmare", 4907, chaos(), "mon-h4a-obj.gdb"),
    # chaos4 with --obj-near 6 (chaos4 stood 4.2 sub-tiles from a seal with no hop left and no click)
    "chaos5": ("UniqNova", "enter-nightmare", 4907, chaos(), "mon-h4a-obj.gdb"),
    # chaos5 with the per-wing seal search (chaos6 above)
    "chaos6": ("UniqNova", "enter-nightmare", 4907, chaos6(), "mon-h4a-obj.gdb"),
    # chaos6 with --obj-near 6 and 300 s per wing (chaos6 stood 4.2 sub-tiles from seal 392 with no hop left, and
    # spent its first wing's 150 s getting there)
    "chaos7": ("UniqNova", "enter-nightmare", 4907, chaos6("6", 300), "mon-h4a-obj.gdb"),
    # special 58 (Siege Boss, tail 42): Harrogath to the Bloody Foothills (110)
    "foothills": ("UniqNova", "enter-nightmare", 4908, [wp(5, 1), explore(200, ["--any-level"])]),
    # special 58 again: plan 0048's xm5 map seed, where Shenk (Siege Boss, record 42) stood near (3906, 5114) in the
    # Bloody Foothills next to the Frigid Highlands waypoint (tab 5 row 2); the hunt heads there first
    "shenk": ("UniqNova", "enter-nightmare", 4815, [wp(5, 2), hunt(479, 300, ["--goal", "3906,5114"]), sweep(30)]),
    # special 60 (Nihlathak, tail 60): Halls of Pain waypoint (tab 5 row 6; the first try took row 5, the Glacial Trail), the Temple Down warp (LvlWarp 80) to level 124
    "nihl": ("UniqNova", "enter-nightmare", 4909, [wp(5, 5), descend(124, "80"), hunt(526, 420)]),
    "nihl2": ("UniqNova", "enter-nightmare", 4910, [wp(5, 6), descend(124, "80"), hunt(526, 420)]),
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
    _, steps, seed, cmds = SESSIONS[name][:4]
    gdbf = SESSIONS[name][4] if len(SESSIONS[name]) > 4 else "mon-h4a.gdb"
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
                                 os.path.join(HERE, "gdb", gdbf), "--steps",
                                 os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "2400",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=dict(os.environ, MONSPAWN_WATCH="", H4B_WATCH=""))
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

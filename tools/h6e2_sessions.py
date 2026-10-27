#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6e2 (quest-items): one game per session on one slot, logged by
tools/gdb/quest-items.gdb (tools/gdb/quests.gdb's lines plus tools/gdb/quest-items.py), driven by tools/d2pilot.py
(Teleport on Shift + left, Nova on F1, Energy Shield on F2). Built on tools/h6d_sessions.py (the same session loop;
the logger, the log directory and the sessions differ).

Usage:
  python3 -I tools/h6e2_sessions.py list
  python3 -I tools/h6e2_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the difficulty steps file, the map seed, and the commands run in order, each with a time
limit: `pilot` runs tools/d2pilot.py with the log; `until` repeats a pilot command until the player's level is the
target; `xd` runs tools/xdrive.py on the slot's game window. The log goes to
workspace/logs/h6e2/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt). The slot is
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
LOGS = os.path.join(ROOT, "workspace", "logs", "h6e2")
GDB = os.path.join(HERE, "gdb", "quest-items.gdb")

NOVA = ["--nova-key", "F1", "--es-key", "F2", "--es", "25", "--radius", "9", "--mana-col", "4", "--drink", "0.5",
        "--nova-hold", "1.6", "--max-res", "1000"]


def wpc(chain):
    """Waypoint travel from the Rogue Encampment start (map seed 3811: its waypoint is on the screen)."""
    return ("pilot", ["wpchain", "--chain", chain, "--linger", "2"], 45)   # wpchain's settle loop waits for a quiet log, which this logger never gives (checkpoint 1: 120 s)


def wp4(tab, row):
    """The waypoint from the Act IV town start (the a4/ saves: header act bytes 131, recipes quest-h6e2-*-a4.json), at
    its fixed screen position there (H4a's wp): the Pandemonium Fortress does not depend on the map seed, so the
    Act II and III sessions can take any map seed (checkpoint 1: the Sewers stairs of map seed 3811 had no path)."""
    return ("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", str(tab), str(row)], 90)


def a4(cmds):
    """A session's commands with its first waypoint hop (wpc) replaced by wp4 from the Act IV town."""
    first = cmds[0]
    assert first[0] == "pilot" and first[1][0] == "wpchain"
    tab, row = first[1][2].split(",")
    return [wp4(int(tab), int(row))] + cmds[1:]


def a4x(cmds):
    """a4, and before every objop with --to-pdef an explore --to-pdef (--pdef-any) to the preset room, with --pdef-any
    on the objop too (staff4b: objop alone stood still at the arrival point in staff4 and staff-nm4)."""
    out = []
    for c in a4(cmds):
        if c[0] == "pilot" and c[1][0] == "objop" and "--to-pdef" in c[1]:
            pdef = c[1][c[1].index("--to-pdef") + 1]
            out.append(("pilot", ["explore", "--to-pdef", pdef, "--pdef-any", "--hops", "80", "--persist", "10"]
                        + NOVA, 400))
            c = (c[0], c[1] + ["--pdef-any"], c[2])
        out.append(c)
    return out


def descend(lid, rows):
    return ("until", (lid, ["farm", "--sweep", "--descend", rows, "--descend-time", "240", "--time", "5"] + NOVA,
                      300, 5), 0)


def descend_to(lid, rows):
    """descend with --descend-to lid (lane/rdp): only a warp of the rows that leads to lid is taken (rows 51 and 61
    serve two levels each; eye4 reached 84, tome4 95). descend() is left as it was for the kept sessions."""
    return ("until", (lid, ["farm", "--sweep", "--descend", rows, "--descend-to", str(lid), "--descend-time", "240",
                            "--time", "5"] + NOVA, 300, 5), 0)


def objop(cls, pdef=None, done="OCD", t=420, extra=(), near="4"):
    a = ["objop", "--obj-cls", str(cls), "--times", "1", "--done", done, "--time", str(t), "--obj-near", near]
    if pdef:
        a += ["--to-pdef", pdef]
    return ("pilot", a + NOVA + list(extra), t + 30)


def hunt(cls, t=300):
    return ("pilot", ["hunt", "--mon-cls", str(cls), "--time", str(t)] + NOVA, t + 40)


def sweep(t):
    return ("pilot", ["farm", "--sweep", "--time", str(t)] + NOVA, t + 60)


def wait(s):
    return ("xd", ["sleep %d" % s], 0)


def radament():
    """Sewers Level 2 waypoint (2,2), Sewer Down (LvlWarp 23) to level 49, Radament (MonStats 229: `ass`), then the
    scroll chest (object 355, in Radament's lair, LvlPrest 341-344: `tr1` and E1)."""
    return [wpc("2,2"), descend(49, "23"), hunt(229, 420), objop(355, "341,342,343,344"), wait(5)]


def cube():
    """Halls of the Dead Level 2 waypoint (2,4), Tomb Down (46) to level 60, the cube chest (354, LvlPrest 456-459)."""
    return [wpc("2,4"), descend(60, "46"), objop(354, "456,457,458,459"), wait(5)]


def staff():
    """Far Oasis waypoint (2,5), Desert to Lair (47) and Lair Down (49) twice to level 64, the staff chest (356,
    LvlPrest 509)."""
    return [wpc("2,5"), descend(62, "47"), descend(63, "49"), descend(64, "49"), objop(356, "509"), wait(5)]


def staff_any():
    """staff with --pdef-any: in staff4 (map seed 4912) the room of LvlPrest 509 was logged (RL) but objop stood still
    for 420 s at the arrival point (the room was found offline: objop's hops did not move the player). Here explore
    --to-pdef (the frontier path) goes there first, and a new map seed."""
    return [wpc("2,5"), descend(62, "47"), descend(63, "49"), descend(64, "49"),
            ("pilot", ["explore", "--to-pdef", "509", "--pdef-any", "--hops", "80", "--persist", "10"] + NOVA, 400),
            objop(356, "509", extra=["--pdef-any"]), wait(5)]


def heart():
    """Kurast Bazaar waypoint (3,6), Kurast to Sewer (57) to level 92, the sewer lever (367, LvlPrest 739-742: object
    event 7), Sewer Down (60) to level 93, the heart chest (405, LvlPrest 747)."""
    return [wpc("3,6"), descend(92, "57"), objop(367, "739,740,741,742", done="QOW", t=300), wait(8),
            descend(93, "60"), objop(405, "747"), wait(5)]


def brain():
    """Flayer Jungle waypoint (3,4), Jungle to Dungeon (54), Dungeon Down (56) twice to level 91, the brain chest (406,
    LvlPrest 704)."""
    return [wpc("3,4"), descend(88, "54"), descend(89, "56"), descend(91, "56"), objop(406, "704"), wait(5)]


def brain_mem():
    """brain4 again (map seed 4914), with an explore of level 91 before the objop and the chest found by memory
    (--obj-mem): in brain4 the player stood at the centre of LvlPrest 704 (a whole-level preset, 40 x 40 tiles) for
    420 s with no class-406 object in any OBJS line, which lists only the objects near the player. (lane/rdp: that
    last clause is wrong; OBJS filters neither class nor distance and follows the activated rooms, items/0010 § The
    brain chest in level 91. The recipe is kept as run.)"""
    return [wp4(3, 4), descend(88, "54"), descend(89, "56"), descend(91, "56"),
            ("pilot", ["explore", "--hops", "120", "--persist", "10"] + NOVA, 600),
            objop(406, extra=["--obj-mem"]), wait(5)]   # no --to-pdef: objop takes that branch before --obj-mem


def eye():
    """Spider Forest waypoint (3,2), Jungle to Spider (51: the Arachnid Lair 84 or the Spider Cavern 85), the eye chest
    (407, LvlPrest 663) when the warp led to 85."""
    return [wpc("3,2"), descend(85, "51"), objop(407, "663"), wait(5)]


def tome():
    """Kurast Bazaar waypoint (3,6), Kurast to Temple (61: the Ruined Temple 94 or the Disused Fane 95), the Lam Esen
    tome (193, LvlPrest 748)."""
    return [wpc("3,6"), descend(94, "61"), objop(193, "748", done="QOW"), wait(5)]


def eye_to():
    """eye with --descend-to 85 (lane/rdp): the Spider Cavern, not the Arachnid Lair."""
    return [wpc("3,2"), descend_to(85, "51"), objop(407, "663"), wait(5)]


def tome_to():
    """tome with --descend-to 94 (lane/rdp): the Ruined Temple, not the Disused Fane."""
    return [wpc("3,6"), descend_to(94, "61"), objop(193, "748", done="QOW"), wait(5)]


def brain_copies():
    """brain4b with explore --all-copies (lane/rdp, items/0010 § H6e2 brain chest): on map seed 4914 level 91's DS1 is
    DungRm2B, whose class-406 chest stands in the room at tile offset (0, 32) (sub-tile 14, 179 of the level); that
    room was never activated in the copy whose rooms held the listed objects, while the default frontier (the copy of
    the last RRESEED) read 0. --all-copies keeps exploring until every copy's rooms are activated."""
    return [wp4(3, 4), descend(88, "54"), descend(89, "56"), descend(91, "56"),
            ("pilot", ["explore", "--all-copies", "--hops", "160", "--persist", "10"] + NOVA, 600),
            objop(406, extra=["--obj-mem"]), wait(5)]


def inifuss():
    """Dark Wood waypoint (1,4), the Inifuss tree (30, LvlPrest 161), operated twice (the second: the refusal)."""
    return [wpc("1,4"), objop(30, "161", done="QOW"), wait(4), objop(30, done="QOW", t=60), wait(4)]


def inifuss6():
    """inifuss with --obj-near 6: the first try stood 4.1 sub-tiles from the tree with no hop left and no click."""
    return [wpc("1,4"), objop(30, "161", done="QOW", near="6"), wait(4), objop(30, done="QOW", t=60, near="6"),
            wait(4)]


def tristram():
    """Stony Field waypoint (1,3), the cairn stones (17, LvlPrest 160; quest word 4 done, so the stones open the
    portal), the Tristram portal (60), Wirt's body (268, LvlPrest 300: `leg`, then the gold piles by object event 7),
    a second click on the body, 40 s for the piles."""
    return [wpc("1,3"), ("pilot", ["objop", "--obj-cls", "17", "--to-pdef", "160", "--approach", "--time", "300",
                                   "--obj-near", "8"] + NOVA, 330),
            ("until", (38, ["objop", "--obj-cls", "60", "--times", "1", "--done", "OOP", "--time", "90",
                            "--obj-near", "4"] + NOVA, 120, 3), 0),
            objop(268, "300", done="QOW"), wait(25), objop(268, done="QOW", t=60), wait(20)]


def gate_load():
    """Load only, 20 s in town: the load-time item checks of the held quest items."""
    return [wait(20)]


# name: (save Name, steps file, map seed, commands). Map seed 3811: the Rogue Encampment waypoint is on the screen at
# the start (plan 0038 H6d).
SESSIONS = {
    "gate-done": ("QuestGateD", "enter-normal", 3811, gate_load()),
    "gate-fresh": ("QuestGateF", "enter-normal", 3811, gate_load()),
    "radament": ("QuestFreshT", "enter-normal", 3811, radament()),
    "cube": ("QuestFreshT", "enter-normal", 3811, cube()),
    "cube-held": ("QuestBoxH", "enter-normal", 3811, cube()),
    "staff": ("QuestFreshT", "enter-normal", 3811, staff()),
    "staff-nm": ("QuestMsfN", "enter-nightmare", 3811, staff()),
    "heart": ("QuestFreshT", "enter-normal", 3811, heart()),
    "brain": ("QuestFreshT", "enter-normal", 3811, brain()),
    "eye": ("QuestFreshT", "enter-normal", 3811, eye()),
    "tome": ("QuestFreshT", "enter-normal", 3811, tome()),
    "inifuss": ("QuestFreshT", "enter-normal", 3811, inifuss()),
    "inifuss6": ("QuestFreshT", "enter-normal", 3811, inifuss6()),
    "tristram": ("QuestAllDone", "enter-normal", 3811, tristram()),
    # resume (2026-10-27): the Act II and III sessions from the Act IV town (a4/ saves) on other map seeds; radament
    # on H4a's 4904
    "radament4": ("a4/QuestFreshT", "enter-normal", 4904, a4(radament())),
    "cube4": ("a4/QuestFreshT", "enter-normal", 4911, a4(cube())),
    "cube-held4": ("a4/QuestBoxH", "enter-normal", 4911, a4(cube())),
    "staff4": ("a4/QuestFreshT", "enter-normal", 4912, a4(staff())),
    "staff-nm4": ("a4/QuestMsfN", "enter-nightmare", 4912, a4(staff())),
    "staff4b": ("a4/QuestFreshT", "enter-normal", 4916, a4(staff_any())),
    "staff-nm4b": ("a4/QuestMsfN", "enter-nightmare", 4916, a4(staff_any())),
    "heart4": ("a4/QuestFreshT", "enter-normal", 4913, a4x(heart())),
    "brain4": ("a4/QuestFreshT", "enter-normal", 4914, a4x(brain())),
    "brain4b": ("a4/QuestFreshT", "enter-normal", 4914, brain_mem()),
    "eye4": ("a4/QuestFreshT", "enter-normal", 4915, a4x(eye())),
    "tome4": ("a4/QuestFreshT", "enter-normal", 4913, a4x(tome())),
    # lane/rdp (not run): the reruns of the three failed routes with the pilot fixes
    "eye4c": ("a4/QuestFreshT", "enter-normal", 4915, a4x(eye_to())),
    "tome4c": ("a4/QuestFreshT", "enter-normal", 4913, a4x(tome_to())),
    "brain4c": ("a4/QuestFreshT", "enter-normal", 4914, brain_copies()),
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

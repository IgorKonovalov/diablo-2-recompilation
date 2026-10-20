#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H5b (objects): one game per session on one slot, logged by
tools/gdb/objects-h5b.gdb (tools/gdb/objects.gdb plus vendors.py's object lines), driven by tools/d2pilot.py
(Teleport on the left button, Nova on F1 or the right button, Energy Shield on F2 where the save has it).

Usage:
  python3 -I tools/h5b_sessions.py list
  python3 -I tools/h5b_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from tools/d2s_recipes/<recipe>.json
with tools/d2s.py build), the difficulty steps file, the map seed, and the commands run in order, each with a time
limit: `pilot` runs tools/d2pilot.py with the log; `until` repeats a pilot command (a descent) until the player's
level is the one named. The log goes to workspace/logs/h5b/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output
beside it (.pilot.txt). A watchdog thread kills the running pilot command and ends the session when the log has not
grown for QUIET s (after the first 150 s) or gdb reports the game exited; the slot is then stopped (tools/slots.py
stop N) and its saves directory returned to the TAG aside, so every session starts from the save it names. Nothing
here feeds a model: the pilot only decides where to click.
"""
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h5b")
QUIET = 90
GDB = os.path.join(HERE, "gdb", "objects-h5b.gdb")

NOVA = ["--nova", "3", "--drink", "0.5"]
LOOT = ["--loot", "30", "--loot-max", "8", "--loot-trap", "5,7,8", "--persist", "8"]


def wp(tab, row):
    return ("pilot", ["wp", "--wp-find", str(tab), str(row)], 90)


def explore(hops, fns="1,3,4,5", extra=()):
    return ("pilot", ["explore", "--hops", str(hops)] + NOVA + LOOT + ["--loot-fns", fns] + list(extra), 60 + 6 * hops)


def shelves(n):
    return ("pilot", ["objop", "--obj-cls", "179,180", "--obj-mem", "--times", str(n), "--done", "OO0", "--time",
                      "180"], 210)


def traps(types="5,7,8", n=3):
    return ("pilot", ["objop", "--trap-types", types, "--times", str(n), "--done", "OO0", "--time", "150"], 180)


def descend(lid, rows, extra=()):
    return ("until", (lid, ["farm", "--sweep", "--descend", rows, "--descend-time", "240", "--time", "5"] + NOVA
                      + list(extra), 300, 4), 0)


SESSIONS = {
    # objects 13, 51, 42 (caskets): the Catacombs casket group (ObjGroup 16, members 79/53/1) on Catacombs Level 2
    "cata": ("ObjNova", "enter-normal", 3901, [wp(1, 9), explore(160)]),
    # objects 41, 42, 49: bookshelves 179/180 (OperateFn 26) in the Jail and the Barracks
    "jail": ("ObjNova", "enter-normal", 3902, [wp(1, 7), explore(120, "1,3,4,5,26"), descend(30, "14"),
                                              explore(120, "1,3,4,5,26"), descend(31, "14"),
                                              explore(120, "1,3,4,5,26")]),
    # bookshelves again, each level's explore followed by objop on the bookshelves the OBJS lines list
    "jail2": ("ObjNova", "enter-normal", 3912, [wp(1, 7), explore(80, "1,3,4,5,26"),
                                               ("pilot", ["objop", "--obj-cls", "179,180", "--times", "3", "--done",
                                                          "OO0", "--time", "150"], 180),
                                               descend(28, "13"), explore(100, "1,3,4,5,26"),
                                               ("pilot", ["objop", "--obj-cls", "179,180", "--times", "4", "--done",
                                                          "OO0", "--time", "200"], 230)]),
    # bookshelves a third time: objop with --obj-mem (an OBJS line lists only the objects near the player, so jail2's
    # objop after the explore found none) after each of Jail 1, 2 and 3
    "jail3": ("ObjNova", "enter-normal", 3914, [wp(1, 7), explore(80, "1,3,4,5,26"), shelves(3),
                                               descend(30, "14"), explore(100, "1,3,4,5,26"), shelves(3),
                                               descend(31, "14"), explore(100, "1,3,4,5,26"), shelves(3)]),
    # the cave session again on its map seed: its objop ran before the chest's room was active (no OBJS line with 397),
    # so explore Level 2 first and then go to the chest from the OBJS lines (--obj-mem)
    "cave2": ("ObjNova", "enter-normal", 3913, [wp(1, 2), descend(9, "0,1,2,3"), explore(40), descend(13, "5"),
                                               explore(40),
                                               ("pilot", ["objop", "--obj-cls", "397", "--obj-mem", "--times", "1",
                                                          "--done", "OO0", "--time", "180"], 210)]),
    # objects 26, 39: the sparkly chest 397 (InitFn 57; OperateFn 4's class-397 table) of Cave Level 2's treasure
    # room (LvlPrest 104), through the Cold Plains waypoint and Cave Level 1
    "cave": ("ObjNova", "enter-normal", 3913, [wp(1, 2), descend(9, "0,1,2,3"), explore(40), descend(13, "5"),
                                              ("pilot", ["objop", "--obj-cls", "397", "--to-pdef", "104", "--times",
                                                         "1", "--done", "OO0", "--time", "240"], 270),
                                              explore(60)]),
    # the casket group again, Catacombs Levels 3 and 4 after Level 2
    "cata2": ("ObjNova", "enter-normal", 3911, [wp(1, 9), explore(120), descend(36, "18"), explore(120),
                                               descend(37, "18"), explore(120)]),
    # objects 41, 42: trapped souls 380 (OperateFn 48) in the City of the Damned; fissure 399 if its Mesa room comes
    "cotd": ("ObjNova", "enter-normal", 3903, [wp(4, 2), explore(160, "1,3,4,5,48")]),
    # trapped souls again: cotd's explore operated 1 of 8, so objop on 380/381 from the OBJS lines after the explore
    "cotd2": ("ObjNova", "enter-normal", 3916, [wp(4, 2), explore(120, "1,3,4,5,48"),
                                               ("pilot", ["objop", "--obj-cls", "380,381", "--obj-mem", "--times",
                                                          "8", "--done", "OO0", "--time", "300"], 330)]),
    # objects 6, 35: the Arcane Sanctuary's teleport pads (OperateFn 27) and the Summoner's room (582)
    "arcane": ("ObjNova", "enter-normal", 3904, [wp(2, 8),
                                                ("pilot", ["objop", "--obj-cls", "192,304,305,306", "--times", "4",
                                                           "--done", "RRESEED", "--time", "300"], 330),
                                                explore(120)]),
    # objects 3, 15, 16, 17, 50: Flayer Dungeon (shrine group 66 on slot 0 at ObjPrb 80, members Parm0 3 only, so
    # no health shrine and the due rule's forced conversion once 75 % of the rooms are gated; small levels for caps)
    "flayer": ("ObjNova", "enter-normal", 3905, [wp(3, 4), descend(88, "54"), explore(140),
                                                descend(89, "56"), explore(100)]),
    # the Swampy Pit (levels 86, 87: the same slot-0 group 66 at ObjPrb 80 and slot-2 group 62 as 88, 89); flayer's
    # first descend took row 53 into 86 (LvlWarp 53 is 78 -> 86, 54 is 78 -> 88), so it is a target of its own
    "flayer2": ("ObjNova", "enter-normal", 3917, [wp(3, 4), descend(86, "53"), explore(140),
                                                 descend(87, "56"), explore(100)]),
    # the flayer session again, with a new map seed, after its descend was fixed
    "flayer3": ("ObjNova", "enter-normal", 3918, [wp(3, 4), descend(88, "54"), explore(140),
                                                 descend(89, "56"), explore(100)]),
    # sparkly chest a third time (cave2's objop gave no status lines; objop now prints one every 20 s)
    "cave3": ("ObjNova", "enter-normal", 3913, [wp(1, 2), descend(9, "0,1,2,3"), explore(40), descend(13, "5"),
                                               explore(40),
                                               ("pilot", ["objop", "--obj-cls", "397", "--obj-mem", "--times", "1",
                                                          "--done", "OO0", "--time", "180"], 210)]),
    # objects 4, 40, 45, 46, 52: trapped containers of types 5, 7 (OBJTRAP_ObjectCreate) and 8 (OBJTRAP_MonsterSpawn,
    # levels < 75 only) in the Catacombs; after each level's explore, objop on the ones the OUX lines list
    "traps1": ("ObjNova", "enter-normal", 3921, [wp(1, 9), explore(120), traps(), descend(36, "18"), explore(120),
                                                traps(), descend(37, "18"), explore(120), traps()]),
    "traps2": ("ObjNova", "enter-normal", 3922, [wp(1, 9), explore(120), traps(), descend(36, "18"), explore(120),
                                                traps(), descend(37, "18"), explore(120), traps()]),
    # objects 41, 42: evil urns 466 (ObjGroup 107, slot 0 of levels 113-119 at ObjPrb 25): Crystalline Passage (113)
    # straight from the waypoint (harro's second waypoint trip failed after its NPC walks), then objop on 466
    "ice": ("ObjNova", "enter-normal", 3923, [wp(5, 4), explore(160, "1,3,4,5,68"),
                                             ("pilot", ["objop", "--obj-cls", "466", "--obj-mem", "--times", "3",
                                                        "--done", "OO0", "--time", "200"], 230)]),
    # collision 39, objects 23, 27: Harrogath (class 523, size 0 with HasCollision; InitFn 66, 68) then the ice caves
    "harro": ("ObjNova", "enter-normal", 3906, [wp(5, 1), ("pilot", ["npc", "larzuk", "trade", "--stay"], 150),
                                               ("pilot", ["npc", "anya", "trade", "--stay"], 150),
                                               ("pilot", ["npc", "malah", "trade", "--stay"], 150),
                                               wp(5, 4), explore(140, "1,3,4,5,68")]),
    # objects 27, 36, 38: Tower Cellar Level 5 (level 25: DS1 580 makes class 371, InitFn 47, trap 3)
    "tower": ("ObjNova", "enter-normal", 3907, [wp(1, 5), descend(20, "10"), descend(21, "12"), descend(22, "9"),
                                               descend(23, "9"), descend(24, "9"), descend(25, "9"),
                                               explore(80, "1,3,4,5")]),
}


def sh(args, timeout=None, log=None, holder=None):
    print("$ " + " ".join(args), flush=True)
    try:
        p = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        if holder is not None:
            holder["p"] = p
        return p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(10)
        print("  (timeout after %s s)" % timeout, flush=True)
        return None
    finally:
        if holder is not None:
            holder["p"] = None


def hide_window(slot):
    """Keep the slot's Xwayland on Hyprland's hidden special workspace d2harness (harness-play.md)."""
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


def last_level(log):
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


def watchdog(log, holder, stop):
    """Abort the running pilot command when the log stops growing or the game exits; sets stop['why']."""
    t0 = time.time()
    size, t_size = -1, time.time()
    while not stop.get("done"):
        time.sleep(3)
        if stop.get("done"):
            return   # the session ended during the sleep: its own slot stop kills the game, which is no abort
        now = time.time()
        try:
            n = os.path.getsize(log)
        except OSError:
            n = -1
        if n != size:
            size, t_size = n, now
        why = None
        if now - t_size > QUIET and now - t0 > 150:
            why = "log unchanged for %d s" % (now - t_size)
        else:
            try:
                with open(log, "rb") as fh:
                    fh.seek(max(0, n - 4096))
                    tail = fh.read()
                if b"[Inferior " in tail and b" exited" in tail:
                    why = "the game exited (gdb's Inferior line)"
            except OSError:
                pass
        if why:
            stop["why"] = why
            print("WATCHDOG: %s; aborting the session" % why, flush=True)
            p = holder.get("p")
            if p is not None:
                try:
                    p.kill()
                except OSError:
                    pass
            return


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
    path = os.path.join(saves, save + ".d2s")
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    env = dict(os.environ, MONSPAWN_WATCH="")
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 GDB, "--steps", os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "2400",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=env)
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
    holder, stop = {"p": None}, {}
    th = threading.Thread(target=watchdog, args=(log, holder, stop), daemon=True)
    th.start()
    for kind, args, timeout in cmds:
        if stop.get("why"):
            break
        if kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    ["--shots", shots], timeout, out, holder)
        elif kind == "until":
            lid, pargs, tmo, tries = args
            rc = None
            for t in range(tries):
                if last_level(log) == lid or stop.get("why"):
                    break
                if t % 2 == 1:
                    sh(PY + [os.path.join(HERE, "d2pilot.py"), "explore", log, "--slot", str(slot), "--hops", "12"]
                       + NOVA + ["--shots", shots], 120, out, holder)
                sh(PY + [os.path.join(HERE, "d2pilot.py"), pargs[0], log, "--slot", str(slot)] + pargs[1:] +
                   ["--shots", shots], tmo, out, holder)
            if last_level(log) == lid:
                rc = 0
            else:
                print("  level %s, not %d: the session stops here" % (last_level(log), lid), flush=True)
                break
        print("  -> %s" % rc, flush=True)
    stop["done"] = True
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        drv.kill()
    out.close()
    print("=== %s done%s" % (name, (" (watchdog: %s)" % stop["why"]) if stop.get("why") else ""), flush=True)


def main(argv):
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-8s %-8s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
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
    if not names or any(n not in SESSIONS for n in names) or set(opt) != {"slot", "tag", "saves", "run"}:
        print(__doc__)
        return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], os.path.abspath(opt["saves"]), opt["run"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

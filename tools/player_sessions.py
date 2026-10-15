#!/usr/bin/env python3
"""Session driver for plan 0034 Phase 2 (run:2026-10-16-player): one harness game per save or per batch of new
characters, on one slot, with the slot's saves set aside first and restored after.

    python3 -I tools/player_sessions.py load    --slot N --tag TAG --out DIR SAVE.d2s ...
    python3 -I tools/player_sessions.py newchar --slot N --tag TAG --out DIR --seed S SPEC ...
    python3 -I tools/player_sessions.py levelup --slot N --tag TAG --out DIR --seed S [--diff hell] [--melee] SAVE

load     for every save: restore and re-aside TAG (one character in the directory), launch tools/d2run.py with
         tools/gdb/d2s-io.gdb and tools/gdb/levelup-load.steps (enter the game, Save and Exit), then copy the written
         .d2s to DIR/written/<name>.d2s; the log is DIR/logs/load-<name>.log.
newchar  one game process: for every SPEC (class[:x|c][:h], e.g. ama:x, pal:c:h) create a character through the
         menu (tools/gdb/newchar.steps, written per character), enter the game in Normal, Save and Exit; logged with
         tools/gdb/player.gdb into DIR/logs/newchar-<seed>.log; the written saves are copied to DIR/written/.
         Character names: Nc<Cls><letter><x|c|h>, lower case (the menu's text field takes what xdrive types).

levelup  one game with tools/gdb/player.gdb: enter Normal or Hell, explore out of town with tools/d2pilot.py
         (Nova; --melee: walk and left-click monsters) until a PLAYER_LevelUp return (LUX) is logged, Save and Exit;
         log DIR/logs/lv-<name>-<seed>.log, the pilot's output next to it (.pilot), the written save in DIR/written/.

Every launch ends with tools/slots.py stop N; TAG is restored at the end (the directory is left as before).
Stdlib only.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
# hero-select screen, 800x600 window-relative (measured from screenshots, run:2026-10-16-player)
CLASS_XY = {"ama": (100, 310), "asn": (200, 310), "nec": (300, 300), "bar": (400, 300), "pal": (520, 300),
            "sor": (620, 320), "dru": (720, 310)}
TAG3 = {"ama": "Ama", "sor": "Sor", "nec": "Nec", "pal": "Pal", "bar": "Bar", "dru": "Dru", "asn": "Asn"}


def saves_dir(slot):
    pre = "wineprefix" if slot == 0 else "wineprefix-%d" % slot
    return os.path.join(ROOT, "workspace", pre, "drive_c", "users", os.environ.get("USER", "igor"),
                        "Saved Games", "Diablo II")


def run(cmd, **kw):
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, **kw)


def tool(*a):
    return run(PY + [os.path.join(HERE, a[0])] + list(a[1:]))


def fresh(slot, tag):
    tool("saves.py", "--slot", str(slot), "restore", tag)
    tool("saves.py", "--slot", str(slot), "aside", tag)


def cmd_load(ns):
    os.makedirs(os.path.join(ns.out, "logs"), exist_ok=True)
    os.makedirs(os.path.join(ns.out, "written"), exist_ok=True)
    for k, path in enumerate(ns.saves):
        name = os.path.splitext(os.path.basename(path))[0]
        fresh(ns.slot, ns.tag)
        log = os.path.join(ns.out, "logs", "load-%s.log" % name)
        run(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(ns.slot), "--seed", str(ns.seed + k), "--gdb",
                  "tools/gdb/d2s-io.gdb", "--steps", "tools/gdb/levelup-load.steps", "--after", "3", "--install",
                  ns.tag, path, "--log", log], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, timeout=240)
        tool("slots.py", "stop", str(ns.slot))
        src = os.path.join(saves_dir(ns.slot), name + ".d2s")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ns.out, "written", name + ".d2s"))
            print("written %s" % name, flush=True)
        else:
            print("MISSING written save %s" % name, flush=True)
    fresh(ns.slot, ns.tag)
    tool("saves.py", "--slot", str(ns.slot), "restore", ns.tag)
    return 0


def newchar_steps(specs, names, path, shots):
    """The steps of one process: per character, (Create New on the character screen once one exists), class,
    checkboxes, name, OK, wait in town, Save and Exit."""
    out = ["# written by tools/player_sessions.py newchar (plan 0034 Phase 2); 800x600, window-relative",
           "click 700 150   # empty background: the first click only activates the window", "sleep 1"]
    for k, (sp, nm) in enumerate(zip(specs, names)):
        cls, game, hc = sp
        out += ["click 400 307   # SINGLE PLAYER", "sleep 3"]
        if k:
            out += ["click 115 500   # CREATE NEW CHARACTER", "sleep 3"]
        x, y = CLASS_XY[cls]
        out += ["click %d %d   # the class" % (x, y), "sleep 3"]
        if game == "c":
            out += ["click 326 533   # clear EXPANSION CHARACTER", "sleep 1"]
        if hc:
            out += ["click 326 553   # HARDCORE", "sleep 1"]
        out += ["type %s" % nm, "sleep 1", "shot %s/nc-%s-form.png" % (shots, nm), "click 690 556   # OK"]
        if hc:
            out += ["sleep 2", "click 468 322   # OK in the hardcore warning box"]
        out += ["sleep 14", "shot %s/nc-%s-town.png" % (shots, nm),
                "key Escape", "sleep 1", "click 400 262   # SAVE AND EXIT GAME", "sleep 7"]
    out.append("shot %s/nc-end.png" % shots)
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")


def parse_spec(s):
    p = s.split(":")
    cls = p[0]
    if cls not in CLASS_XY:
        raise SystemExit("unknown class %s" % cls)
    game = p[1] if len(p) > 1 else "x"
    hc = len(p) > 2 and p[2] == "h"
    return cls, game, hc


def cmd_newchar(ns):
    specs = [parse_spec(s) for s in ns.specs]
    os.makedirs(os.path.join(ns.out, "logs"), exist_ok=True)
    os.makedirs(os.path.join(ns.out, "written"), exist_ok=True)
    shots = os.path.join(ns.out, "shots")
    os.makedirs(shots, exist_ok=True)
    names = []
    for k, (cls, game, hc) in enumerate(specs):
        names.append(("nc%s%s%s%s" % (TAG3[cls], chr(ord("a") + (ns.first + k) % 26),
                                       chr(ord("a") + (ns.first + k) // 26), "h" if hc else game)).lower())
    steps = os.path.join(ns.out, "logs", "newchar-%d.steps" % ns.seed)
    newchar_steps(specs, names, steps, os.path.relpath(shots, ROOT))
    fresh(ns.slot, ns.tag)
    log = os.path.join(ns.out, "logs", "newchar-%d.log" % ns.seed)
    args = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(ns.slot), "--seed", str(ns.seed), "--gdb",
                 "tools/gdb/player.gdb", "--steps", steps, "--after", "3", "--log", log]
    if ns.game_args:
        args.append("--game-args=" + ns.game_args)
    run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
        timeout=120 + 60 * len(specs))
    tool("slots.py", "stop", str(ns.slot))
    for nm in names:
        src = os.path.join(saves_dir(ns.slot), nm + ".d2s")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(ns.out, "written", nm + ".d2s"))
            print("written %s" % nm, flush=True)
        else:
            print("MISSING written save %s" % nm, flush=True)
    tool("saves.py", "--slot", str(ns.slot), "restore", ns.tag)
    return 0


def cmd_levelup(ns):
    """One game: install the save, enter Normal or Hell (tools/gdb/enter-<diff>.steps), then tools/d2pilot.py explore
    (Nova, or --melee with walking) out of town until the log has ns.ups level-ups (LUX lines) or ns.time runs out;
    then Save and Exit, and the slot is stopped."""
    os.makedirs(os.path.join(ns.out, "logs"), exist_ok=True)
    os.makedirs(os.path.join(ns.out, "written"), exist_ok=True)
    name = os.path.splitext(os.path.basename(ns.save))[0]
    fresh(ns.slot, ns.tag)
    log = os.path.join(ns.out, "logs", "lv-%s-%d.log" % (name, ns.seed))
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(ns.slot), "--seed", str(ns.seed),
                                 "--gdb", "tools/gdb/player.gdb", "--steps", "tools/gdb/enter-%s.steps" % ns.diff,
                                 "--after", str(int(ns.time) + 120), "--install", ns.tag, ns.save, "--log", log],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 120:
        time.sleep(3)
        if os.path.exists(log) and "PLR " in open(log, errors="replace").read():
            break
    time.sleep(3)
    pil = PY + [os.path.join(HERE, "d2pilot.py"), "explore", log, "--slot", str(ns.slot), "--any-level",
                "--hops", "400", "--persist", "20"]
    if ns.melee:
        pil += ["--walk", "--melee", "--radius", "14", "--give-up", "40", "--burst", "6", "--cast-wait", "0.5"]
    else:
        pil += ["--nova-key", "F1", "--es-key", "F2", "--es", "40"]
    pl = subprocess.Popen(pil, cwd=ROOT, stdout=open(log + ".pilot", "w"), stderr=subprocess.STDOUT,
                          stdin=subprocess.DEVNULL, start_new_session=True)
    ups = 0
    while time.time() - t0 < ns.time:
        time.sleep(3)
        ups = open(log, errors="replace").read().count("\nLUX ")
        if ups >= ns.ups or pl.poll() is not None:
            break
    if pl.poll() is None:
        pl.terminate()
        pl.wait(10)
    print("%s: %d level-up(s) in %.0f s" % (name, ups, time.time() - t0), flush=True)
    for a in (["key", "Escape"], ["click", "400", "262"]):
        run(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(ns.slot), "--window", "Diablo II"] + a)
        time.sleep(1.5)
    time.sleep(6)
    tool("slots.py", "stop", str(ns.slot))
    drv.wait(30)
    src = os.path.join(saves_dir(ns.slot), name + ".d2s")
    if os.path.exists(src):
        shutil.copy(src, os.path.join(ns.out, "written", "%s-%d.d2s" % (name, ns.seed)))
    tool("saves.py", "--slot", str(ns.slot), "restore", ns.tag)
    return 0 if ups else 1


def main(argv):
    ap = argparse.ArgumentParser(prog="player_sessions.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("load")
    a.add_argument("saves", nargs="+")
    b = sub.add_parser("newchar")
    b.add_argument("specs", nargs="+")
    b.add_argument("--first", type=int, default=0, help="index of the first name letter")
    b.add_argument("--game-args", default="")
    c = sub.add_parser("levelup")
    c.add_argument("save")
    c.add_argument("--diff", choices=("normal", "hell"), default="normal")
    c.add_argument("--melee", action="store_true")
    c.add_argument("--time", type=float, default=300)
    c.add_argument("--ups", type=int, default=1)
    for p in (a, b, c):
        p.add_argument("--slot", type=int, required=True)
        p.add_argument("--tag", required=True)
        p.add_argument("--out", required=True)
        p.add_argument("--seed", type=int, default=34100)
    ns = ap.parse_args(argv[1:])
    if ns.slot not in (3, 4):
        print("plan 0034 Phase 2 holds slots 3 and 4 only")
        return 2
    return {"load": cmd_load, "newchar": cmd_newchar, "levelup": cmd_levelup}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

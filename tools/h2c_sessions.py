#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H2c (forced): one game per session on one slot, logged by
tools/gdb/items-h2c.gdb, on a forced game copy (a loose treasureclassex.bin under -direct, ADR-0013), driven by
tools/d2pilot.py (Sorceress: Teleport on Shift + left, Nova on F1, Energy Shield on F2).

Usage:
  python3 -I tools/h2c_sessions.py list
  python3 -I tools/h2c_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, the H2b saves), the steps file, the map seed,
the forced game copy (workspace/runtime/<copy>, started with --game-args=-direct) and the commands run in order, each
with a time limit (`pilot` runs tools/d2pilot.py with the log; `players` types /players N). The log goes to
workspace/logs/h2c/<RUN>-s<slot>-<seed>-<SESSION>.log, the pilot's output beside it (.pilot.txt); a retry on the same
map seed gets -r2, -r3. The slot's saves directory is returned to the TAG aside before each session and the slot is
stopped after it (tools/slots.py stop N). The machinery is tools/h2b_sessions.py's, with the logger, the game copy
and the sessions changed. Nothing here feeds a model: the pilot only decides where to click.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import h2b_sessions as hb  # noqa: E402

ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h2c")
LOGGER = os.path.join(HERE, "gdb", "items-h2c.gdb")
RUNTIME = os.path.join(ROOT, "workspace", "runtime")
NOVA = hb.NOVA


def hephasto(t=360, players=1):
    """Hell: River of Flame waypoint (tab 4 row 5), hunt Hephasto the Armorer (MonStats row 409, ilvl 88 in Hell:
    the only stock-droppable func-24 carrier, Tomb Reaver, has lvl 86), then a sweep."""
    return [("pilot", ["farm", "--wp", "4,5", "--players", str(players), "--time", str(t), "--sweep",
                       "--boss-cls", "409"] + NOVA, t + 90)]


THROW = "game-forced-h2c-throw"
TCN = "game-forced-h2c-tcn"
# name: (save Name, steps file, map seed, game copy, commands)
SESSIONS = {
    # tc 10, 55, 56: classic Normal sweeps; Act 1 Junk names three classic throwables only
    "throw-a": ("UniqClassic", "enter-normal", 4011, THROW, hb.classic_sweep(2, t=300)),
    "throw-b": ("UniqClassic", "enter-normal", 4012, THROW, hb.classic_sweep(3, t=300)),
    "throw-c": ("UniqClassic", "enter-normal", 4013, THROW, hb.classic_sweep(4, t=300)),
    # properties 12 (func 12), 14 (func 23): Eldritch (Act 5 (H) Super A / Ax name Ormus' Robes and Ethereal Edge)
    "tcn-a": ("UniqNova", "uniques-hell", 4021, TCN, hb.eldritch(t=150, players=1)),
    "tcn-b": ("UniqNova", "uniques-hell", 4022, TCN, hb.eldritch(t=150, players=1)),
    "tcn-c": ("UniqNova", "uniques-hell", 4023, TCN, hb.eldritch(t=150, players=1)),
    # properties 15 (func 24), with 12 and 14: Hephasto (Haphesto (H) names Tomb Reaver, Shadowkiller, Ghostflame,
    # Ormus' Robes)
    "heph-a": ("UniqNova", "uniques-hell", 4031, TCN, hephasto()),
    "heph-b": ("UniqNova", "uniques-hell", 4032, TCN, hephasto()),
    "heph-c": ("UniqNova", "uniques-hell", 4033, TCN, hephasto()),
    "heph-d": ("UniqNova", "uniques-hell", 4034, TCN, hephasto()),
}


def run_session(name, slot, tag, saves, run):
    save, steps, seed, copy, cmds = SESSIONS[name]
    path = os.path.join(saves, save + ".d2s")
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
    gdir = os.path.join(RUNTIME, copy)
    print("=== %s: %s, %s, seed %d, %s -> %s" % (name, path, steps, seed, copy, log), flush=True)
    hb.sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    hb.sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 LOGGER, "--steps", os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "1500",
                                 "--game-dir", gdir, "--game-args=-direct",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 180:
        time.sleep(3)
        hb.hide_window(slot)
        try:
            if "PLR " in open(log, errors="replace").read():
                break
        except OSError:
            pass
    time.sleep(3)
    hb.hide_window(slot)
    for kind, args, timeout in cmds:
        if kind == "pilot":
            rc = hb.sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                       ["--shots", shots], timeout, out)
        elif kind == "players":
            rc = hb.sh(PY + [os.path.join(HERE, "d2pilot.py"), "players", log, str(args), "--slot", str(slot)], 60,
                       out)
        print("  -> %s" % rc, flush=True)
    hb.sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
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
            print("%-10s %-12s %-14s %d %-22s %d step(s)" % (k, v[0], v[1], v[2], v[3], len(v[4])))
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

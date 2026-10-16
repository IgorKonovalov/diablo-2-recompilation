#!/usr/bin/env python3
"""Session driver for plan 0033 Phase 2 (run:2026-10-16-hirelings): hire-list tours, hire sessions, mercenary save
loads and a mercenary-kill session on one harness slot, logged with tools/gdb/hirelings.gdb.

    python3 -I tools/hireling_sessions.py saves --out DIR                      # classic act variants of the merc set
    python3 -I tools/hireling_sessions.py tour  --slot N --tag TAG --seed S --diff D --log LOG SAVE.d2s \\
        [--npcs qual-kehk,asheara,kashya,greiz] [--buy NPC:K] [--reopen]
    python3 -I tools/hireling_sessions.py load  --slot N --tag TAG --seed S --diff D --log LOG SAVE.d2s [--stay S]
    python3 -I tools/hireling_sessions.py kill  --slot N --tag TAG --seed S --log LOG SAVE.d2s [--time S]

saves: tools/merc_saves.py builds its 21 saves on the recipes' Act IV start (difficulty bytes 131); MERC_Create of a
classic game makes the mercenary only in its own act, so `saves` also writes the 9 classic saves with the act of the
mercenary (bytes 0x80 | act - 1: Rogue Act I, Desert Act II, Iron Wolf Act III) as Merc<cls><n|m|h>ca.
tour: one game (d2run.py --install, the save alone in the slot's directory); from the Act IV start, the town waypoint
and a hop to each seller's town (wpchain, capped with timeout), the seller's hire list opened (d2pilot.py npc ... hire;
HIRE_BuildStock runs at the first click on the NPC) and closed. --buy NPC:K hires the top row K times at that NPC
(the 10th hire of a list empties it, so the table is rebuilt); --reopen opens that list once more after.
load: one game per save, the mercenary header read at the load; the session ends once the logger has MSX (or after
--stay seconds). kill: Normal, the Cold Plains waypoint, the character stands while the mercenary fights (the
pilot's explore --walk with no attack skill on the right button: Telekinesis), until an MFK line of a mercenary or
--time; with --shots, a screenshot of the mercenary's inventory first.
Every session ends with tools/slots.py stop N, and the slot's directory is restored to TAG's aside. Stdlib only.
"""
import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
STEPS = {"normal": "tools/gdb/enter-normal.steps", "nightmare": "tools/gdb/enter-nightmare.steps",
         "hell": "tools/gdb/enter-hell.steps"}
TOWN_WP = {"kashya": "1,1", "greiz": "2,1", "asheara": "3,1", "qual-kehk": "5,1"}
TOWNS = {1: 1, 40: 2, 75: 3, 103: 4, 109: 5}


def run(cmd, timeout=None):
    print("+ " + " ".join(cmd), flush=True)
    try:
        return subprocess.run(cmd, cwd=ROOT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("  (timed out after %s s)" % timeout, flush=True)
        return 124


def tool(args, timeout=None):
    return run(PY + [os.path.join(HERE, args[0])] + list(args[1:]), timeout=timeout)


def launch(ns, steps, after):
    tool(["saves.py", "--slot", str(ns.slot), "restore", ns.tag])
    tool(["saves.py", "--slot", str(ns.slot), "aside", ns.tag])
    out = open(ns.log + ".d2run.out", "w")
    cmd = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(ns.slot), "--seed", str(ns.seed), "--gdb",
                "tools/gdb/hirelings.gdb", "--steps", steps, "--after", str(after), "--install", ns.tag, ns.save,
                "--log", ns.log]
    print("+ " + " ".join(cmd), flush=True)
    subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     start_new_session=True)


def lines(log, tag):
    out = []
    try:
        with open(log, errors="replace") as fh:
            for ln in fh:
                if ln.startswith(tag + " "):
                    try:
                        out.append(json.loads(ln[len(tag) + 1:]))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def wait_for(log, tag, secs, pred=None):
    t0 = time.time()
    while time.time() - t0 < secs:
        if any(pred is None or pred(d) for d in lines(log, tag)):
            return True
        time.sleep(1.0)
    return False


def level(log):
    p = lines(log, "PLR")
    return p[-1]["lid"] if p else None


def stop(ns):
    tool(["slots.py", "stop", str(ns.slot)])
    time.sleep(2)
    tool(["saves.py", "--slot", str(ns.slot), "restore", ns.tag])


def pilot(ns, *a, timeout=None):
    return tool(["d2pilot.py", "--slot", str(ns.slot)] + list(a), timeout=timeout)


def go_town(ns, npc):
    """Waypoint hop from the current town to the NPC's town (no hop when already there)."""
    want = int(TOWN_WP[npc].split(",")[0])
    for _ in range(3):
        if TOWNS.get(level(ns.log)) == want:
            return True
        pilot(ns, "npc", ns.log, "waypoint", "walk", timeout=90)
        pilot(ns, "wpchain", ns.log, "--chain", TOWN_WP[npc], timeout=20)
        time.sleep(2)
    return TOWNS.get(level(ns.log)) == want


def cmd_tour(ns):
    launch(ns, STEPS[ns.diff], 3000)
    try:
        if not wait_for(ns.log, "PLR", 120):
            print("tour: no PLR line; giving up")
            return 1
        time.sleep(3)
        buy = dict(b.split(":") for b in ns.buy.split(",")) if ns.buy else {}
        for npc in ns.npcs.split(","):
            if not go_town(ns, npc):
                print("tour: did not reach the town of %s" % npc)
                continue
            shots = ["--shots", ns.shots] if ns.shots else []
            if npc in buy:
                pilot(ns, "npc", ns.log, npc, "hire", "--repeat", buy[npc], "--buy", "1", *shots, timeout=900)
                if ns.reopen:
                    pilot(ns, "npc", ns.log, npc, "hire", *shots, timeout=240)
            else:
                pilot(ns, "npc", ns.log, npc, "hire", *shots, timeout=240)
        return 0
    finally:
        stop(ns)


def cmd_load(ns):
    launch(ns, STEPS[ns.diff], 120)
    try:
        ok = wait_for(ns.log, "PLR", 120)
        if ok:
            wait_for(ns.log, "MSX", ns.stay)
            time.sleep(3)
        print("load: %s MRH %d MCX %s MSX %d" % (os.path.basename(ns.save), len(lines(ns.log, "MRH")),
                                                [d.get("merc") is not None for d in lines(ns.log, "MCX")],
                                                len(lines(ns.log, "MSX"))))
        return 0 if ok else 1
    finally:
        stop(ns)


def cmd_kill(ns):
    launch(ns, STEPS["normal"], 3000)
    try:
        if not wait_for(ns.log, "PLR", 120):
            return 1
        time.sleep(3)
        if ns.shots:            # the mercenary's inventory (its equipped items), then closed
            xd = ["xdrive.py", "--slot", str(ns.slot), "--window", "Diablo II"]
            tool(xd + ["key", "o"])
            time.sleep(1.0)
            tool(xd + ["shot", os.path.join(ns.shots, "merc-inventory.png")])
            tool(xd + ["key", "o"])
            time.sleep(0.5)
        pilot(ns, "npc", ns.log, "waypoint", "walk", timeout=90)
        pilot(ns, "wpchain", ns.log, "--chain", ns.wp, timeout=30)
        t0 = time.time()

        def merc_kill(d):
            k = d.get("killer") or {}
            return k.get("type") == 1 and k.get("cls") in (271, 338, 359, 561)
        while time.time() - t0 < ns.time:
            if wait_for(ns.log, "MFK", 2, merc_kill) and sum(map(merc_kill, lines(ns.log, "MFK"))) >= ns.kills:
                break
            pilot(ns, "explore", ns.log, "--hops", "3", "--nova", "0", "--walk", timeout=60)
            time.sleep(6)
        n = sum(map(merc_kill, lines(ns.log, "MFK")))
        print("kill: %d mercenary kills" % n)
        return 0 if n else 1
    finally:
        stop(ns)


def cmd_saves(ns):
    sys.path.insert(0, HERE)
    import d2s
    import hashlib
    import merc_saves
    excel = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
    t = d2s.Tables(excel)
    with open(os.path.join(HERE, "d2s_recipes", merc_saves.RECIPES["classic"])) as fh:
        base_rc = json.load(fh)
    acts = {"271": 0, "338": 1, "359": 2}
    for name, merc in merc_saves.plan(t, "classic"):
        cls = name[4:7]
        b = 0x80 | acts[cls]
        rc = dict(base_rc, name=name + "a", merc=merc, difficulty=[b, b, b])
        d = os.path.join(ns.out, name + "a")
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, name + "a.d2s")
        with contextlib.redirect_stdout(io.StringIO()):
            d2s.build(excel, rc, merc_saves.BASES["classic"], dst)
        with open(dst, "rb") as fh:
            print("%-14s act %d  %s" % (name + "a", acts[cls] + 1, hashlib.sha256(fh.read()).hexdigest()))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("tour", "load", "kill", "saves"))
    ap.add_argument("save", nargs="?")
    ap.add_argument("--slot", type=int, default=1)
    ap.add_argument("--tag", default="h33p2")
    ap.add_argument("--seed", type=int, default=3300)
    ap.add_argument("--diff", default="normal", choices=sorted(STEPS))
    ap.add_argument("--log")
    ap.add_argument("--out")
    ap.add_argument("--npcs", default="qual-kehk,asheara,kashya,greiz")
    ap.add_argument("--buy", default="")
    ap.add_argument("--reopen", action="store_true")
    ap.add_argument("--shots", default="")
    ap.add_argument("--stay", type=float, default=40)
    ap.add_argument("--time", type=float, default=240)
    ap.add_argument("--kills", type=int, default=3)
    ap.add_argument("--wp", default="1,2")
    ns = ap.parse_args(argv)
    if ns.cmd != "saves" and (not ns.save or not ns.log):
        ap.error("SAVE and --log are required")
    if ns.save:
        ns.save = os.path.abspath(ns.save)
    return {"tour": cmd_tour, "load": cmd_load, "kill": cmd_kill, "saves": cmd_saves}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

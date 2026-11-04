"""Scripted harness sessions for plan 0060 Phase 2 (item use and inventory), on the runner library
(tools/harness_runner.py): one fresh game process per session (harness-play.md § Fresh process, rule 1), logged by
tools/gdb/inventory.gdb, checked by tools/inventory_check.py against tools/item_inventory.py's predictions.

Usage:
  python3 -I tools/inventory_sessions.py list
  python3 -I tools/inventory_sessions.py build                       # InvSor.d2s from tools/d2s_recipes/inv-sor.json
  python3 -I tools/inventory_sessions.py run --slot N --tag TAG --run RUN [--dev] SESSION [SESSION ...]

The character is InvSor (CombatSor with a belt of hp1 hp1 mp1 rvs and 12 1x1 potions in the inventory, an Act IV town
start, normal). A SESSION is a list of steps (below); a step is a tuple whose first item names the kind:
  ("wait", s)  ("keys", [key..], gap)  ("click", x, y, s)  ("rclick", x, y, s)  ("shot", name)
  ("arm", "18 page=4")      a forced request edit (tools/gdb/inventory.py): the next request of that opcode is edited once
  ("pilot", [args..], timeout)   a tools/d2pilot.py command on the session's log
  ("drop", cell, gx, gy)    inventory cell (c, r) picked up, then clicked on the ground at screen (gx, gy)
Screen coordinates are the 800x600 game frame (xdrive --window "Diablo II"); the inventory grid is at (418 + 29c, 316 + 29r).
Nothing here feeds a model: the steps only decide where to click.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import harness_runner as hr  # noqa: E402

LOGS = os.path.join(ROOT, "workspace", "logs", "inventory")
EXCEL = os.path.join("workspace", "merged", "data", "global", "excel")
BASE = os.path.join("workspace", "samples", "d2s-owner", "smpsor-l50.d2s")
SAVES = os.path.join(ROOT, "workspace", "samples", "inventory2")
GDB = "tools/gdb/inventory.gdb"
STEPS = "tools/gdb/enter-normal.steps"
CHAR = "InvSor2"
INV0 = (418, 316)
CELL = 29
NOVA = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6",
        "--wp-x", "715", "--wp-y", "58", "--max-res", "1000"]


def drop_run(n, first=0, gx=250, gy=420, gap=1.2):
    """n drops, each of the inventory cell `first + k` (row 0 then row 1), onto the ground at (gx, gy)."""
    out = [("keys", ["i"], 0.8)]
    for k in range(n):
        c = (first + k) % 10
        r = (first + k) // 10
        out += [("click", INV0[0] + CELL * c + 14, INV0[1] + CELL * r + 14, 0.5), ("click", gx, gy, gap)]
    return out + [("keys", ["i"], 0.5)]


def icell(k):
    """Screen centre of inventory cell k (row-major, 10 wide)."""
    return INV0[0] + CELL * (k % 10) + 14, INV0[1] + CELL * (k // 10) + 14


NOVA_CITY = [("400" if a == "715" else "245" if a == "58" else a) for a in NOVA]     # the City's waypoint is under the character


def last_pos(log):
    """The last PLR line's (level, x, y) of a log, or None."""
    pos = None
    try:
        for line in open(log, errors="replace").read().splitlines()[-4000:]:
            if line.startswith("PLR "):
                d = json.loads(line[4:])
                pos = (d["lid"], d["x"], d["y"])
    except (OSError, ValueError):
        pass
    return pos


def first_pos_off_town(log, town=103):
    """(x, y) of the first PLR line whose level is not the town: the waypoint the pilot arrived at."""
    for line in open(log, errors="replace").read().splitlines():
        if line.startswith("PLR "):
            d = json.loads(line[4:])
            if d["lid"] != town:
                return d["x"], d["y"]
    return 0, 0


def goto(log, xd, out, tx, ty, centre=(200, 265), tries=14):
    """Walk to (tx, ty) by clicks with the inventory open: each click goes toward the target along the isometric axes
    (a sub-tile is 16 px across and 8 px down per axis step), at most 130 px from the character, who stays at `centre`.
    Nothing here feeds a model."""
    for _ in range(tries):
        p = last_pos(log)
        if p is None:
            return
        dx, dy = tx - p[1], ty - p[2]
        if abs(dx) <= 2 and abs(dy) <= 2:
            return
        sx, sy = 16 * (dx - dy), 8 * (dx + dy)
        m = max(abs(sx), abs(sy) * 2, 1)
        f = min(1.0, 130.0 / m)
        hr.sh(xd + ["click", str(int(centre[0] + sx * f)), str(int(centre[1] + sy * f))], 30, out)
        time.sleep(2.0)


def drop_cells(cells, gx=250, gy=420, gap=1.0):
    """Each inventory cell picked up and clicked on the ground at (gx, gy) (the inventory is open)."""
    return [x for k in cells for x in (("click",) + icell(k) + (0.5,), ("click", gx, gy, gap))]


def use_run(cells, gap):
    """Right-click use of inventory cells, `gap` seconds apart (the request 0x20)."""
    out = []
    for k in cells:
        x, y = icell(k)
        out.append(("rclick", x, y, gap))
    return out


SESSIONS = {
    # development: the town, the inventory open, screenshots
    "smoke": [("wait", 4), ("shot", "town"), ("keys", ["i"], 1.0), ("shot", "inv"), ("keys", ["i"], 0.5),
              ("wait", 2)],
    # plan 0060 Phase 2 run 2: the potion doubling and its two draws (items/0012 cases 1 to 5). The inventory is open;
    # hp1 cells 0..7, mp1 cells 8..11 by right click (0x20), the belt's four columns by the keys 1..4 (0x26). Pairs
    # 1.2 s apart (the second use finds the first one's list: the blend, case 4), singles 14 s apart (the list ended).
    "pot": ([("keys", ["i"], 1.0)]
            + use_run([0, 1], 1.2) + [("wait", 14)] + use_run([2], 14) + use_run([3], 14)
            + use_run([4, 5], 1.2) + [("wait", 14)] + use_run([6], 14) + use_run([7], 14)
            + use_run([8, 9], 1.2) + [("wait", 14)] + use_run([10], 14) + use_run([11], 14)
            + [("keys", ["1"], 14), ("keys", ["2"], 14), ("keys", ["3"], 14), ("keys", ["4"], 14),
               ("keys", ["1", "2"], 1.2), ("wait", 6), ("shot", "end")]),
    # the drops: 28 items (every quality 1..8, gems, runes, potions) in place at the start, then the 12 potions at the wall
    # (WALLWALK), then the City of the Damned and back (the room's release and restore), then 760 s in the town
    # development: walk down-left to the parapet, screenshots, then six potions dropped there
    "walltest": ([("keys", ["i"], 1.0), ("click", 150, 330, 3.0), ("shot", "w1"), ("click", 110, 372, 3.0), ("shot", "w2"),
                  ("click", 70, 410, 3.0), ("shot", "w3")] + [x for k in range(0, 6) for x in
                                                          (("click",) + icell(k) + (0.5,), ("click", 250, 420, 1.0))]
                 + [("shot", "w4")]),
    "drops2": ([("keys", ["i"], 1.0), ("shot", "inv0"), ("click", 150, 330, 3.0), ("click", 110, 372, 3.0),
                ("click", 70, 410, 3.0), ("shot", "wall")] + drop_cells(range(0, 12))
               + [("goto", 5048, 5043), ("shot", "back")]
               + drop_cells(range(12, 36)) + [("shot", "after24"), ("keys", ["i"], 0.8),
                ("pilot", ["farm", "--wp", "4,2", "--time", "4"] + NOVA, 200), ("wait", 3), ("mark_pos", "city"), ("shot", "city"),
                ("keys", ["i"], 1.0)] + drop_cells(range(36, 40)) + [("keys", ["i"], 0.8), ("wait", 3),
                ("pilot", ["hop", "30", "0"], 60), ("pilot", ["hop", "30", "0"], 60), ("pilot", ["hop", "30", "0"], 60),
                ("shot", "away"), ("wait", 20),
                ("pilot", ["hop", "-30", "0"], 60), ("pilot", ["hop", "-30", "0"], 60), ("pilot", ["hop", "-30", "0"], 60),
                ("keys", ["i"], 0.8), ("goto", "city"), ("keys", ["i"], 0.8), ("wait", 8), ("shot", "back2"),
                ("pilot", ["farm", "--wp", "4,1", "--time", "4"] + NOVA_CITY, 200), ("wait", 8), ("shot", "town2"),
                ("wait", 380), ("shot", "mid"), ("wait", 380), ("shot", "end")]),
}


# development copy of drops2 with the two long waits cut to 20 s
SESSIONS["drops2short"] = [("wait", 20) if (st[0] == "wait" and st[1] in (380, 700)) else st for st in SESSIONS["drops2"]]


def cmd_build():
    os.makedirs(SAVES, exist_ok=True)
    return subprocess.run([*hr.PY, "tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/inv-sor2.json", BASE,
                           os.path.join(SAVES, CHAR + ".d2s")], cwd=ROOT).returncode


def run(slot, tag, run_id, names, dev=False, seed0=6001):
    os.makedirs(LOGS, exist_ok=True)
    runname = ("dev-" if dev else "") + run_id
    out = open(os.path.join(LOGS, "%s-s%d.pilot.txt" % (runname, slot)), "a")
    shots = os.path.join("workspace", "logs", "inventory", "%s-s%d-shots" % (runname, slot))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    xd = [*hr.PY, os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
    py = [*hr.PY, os.path.join(HERE, "d2pilot.py")]
    arm = os.path.join(ROOT, "workspace", "runtime", "inv-arm-slot%d" % slot)
    status = os.path.join(LOGS, "%s-s%d.status.json" % (runname, slot))
    os.environ["INV_SLOT"] = str(slot)
    os.environ["INV_RUNTIME"] = os.path.join(ROOT, "workspace", "runtime")
    launches = [0]
    marks = {}

    def run_case(name):
        seed = seed0 + launches[0]
        launches[0] += 1
        stem = hr.new_stem(LOGS, runname, slot, seed, name)
        log = stem + ".log"
        hr.stop(slot, None, out=out)
        hr.install(slot, tag, out=out)
        drv = hr.launch(slot, seed, log, gdb=GDB, steps=STEPS, after=3000, install=(tag, [os.path.join(SAVES, CHAR + ".d2s")]),
                        out=out, stem=stem)
        hr.mark(stem, name, "start", log, "launch seed=%d" % seed)
        r = hr.wait_ready(log, "INVRDY", 180, proc=drv, tick=lambda: hr.hide_window(slot))
        ok = r == hr.READY and hr.wait_count(log, "PLR", 1, 180, drv)
        hr.mark(stem, name, "ready" if ok else "fail", log, r)
        try:
            if not ok:
                return ("failed", "no PLR (%s)" % r)
            time.sleep(3)
            for step in SESSIONS[name]:
                k = step[0]
                if k == "wait":
                    time.sleep(step[1])
                elif k == "keys":
                    for key in step[1]:
                        hr.sh(xd + ["key", key], 30, out)
                        time.sleep(step[2])
                elif k in ("click", "rclick"):
                    hr.sh(xd + [k, str(step[1]), str(step[2])], 30, out)
                    time.sleep(step[3])
                elif k == "shot":
                    hr.sh(xd + ["shot", os.path.join(shots, "%s-%s.png" % (name, step[1]))], 30, out)
                elif k == "mark_pos":
                    marks[step[1]] = first_pos_off_town(log)
                elif k == "goto":
                    tx, ty = marks[step[1]] if isinstance(step[1], str) else (step[1], step[2])
                    goto(log, xd, out, tx, ty)
                elif k == "arm":
                    with open(arm, "w") as f:
                        f.write(step[1] + "\n")
                elif k == "pilot":
                    hr.sh(py + [step[1][0], log, "--slot", str(slot)] + step[1][1:] + ["--shots", shots], step[2], out)
            hr.mark(stem, name, "end", log, "steps done")
            return ("kept", "log %s" % os.path.basename(log))
        finally:
            hr.stop(slot, drv, out=out)
            if os.path.exists(arm):
                os.remove(arm)

    try:
        st = hr.batch(names, run_case, status, reruns=0)
    finally:
        out.close()
    print(hr.summary(st))
    return 0 if st["done"] and not st["failed"] else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "build", "run"])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--slot", type=int)
    ap.add_argument("--tag")
    ap.add_argument("--run")
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for n, s in SESSIONS.items():
            print(n, len(s), "steps")
        return 0
    if a.cmd == "build":
        return cmd_build()
    if a.slot != 2:
        print("this lane runs on slot 2 only")
        return 2
    return run(a.slot, a.tag, a.run, a.names, dev=a.dev)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

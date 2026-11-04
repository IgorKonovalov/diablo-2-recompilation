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
SAVES = os.path.join(ROOT, "workspace", "samples", "inventory")
GDB = "tools/gdb/inventory.gdb"
STEPS = "tools/gdb/enter-normal.steps"
CHAR = "InvSor"
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


SESSIONS = {
    # development: the town, the inventory open, screenshots
    "smoke": [("wait", 4), ("shot", "town"), ("keys", ["i"], 1.0), ("shot", "inv"), ("keys", ["i"], 0.5),
              ("wait", 2)],
    # items/0014 cases 1, 2, 10: player drops in place (the town start), ring by ring
    "drops1": drop_run(12),
    # the kept session: the two forced requests in the town (0x18 to page 4 with no stash open, 0x23 to box 12 of a
    # 12-box belt), six player drops in place, then Act IV's City of the Damned: kills (monster and chest drops), four
    # player drops, and 760 s standing in the active room (the sweep's frames 1500 apart: cases 7 and 8)
    "armtest": [("keys", ["i"], 1.0),
                ("click", 418 + 29 * 7 + 14, 316 + 14, 0.6), ("arm", "18 page=4"),
                ("click", 418 + 29 * 5 + 14, 316 + 29 * 3 + 14, 1.5), ("shot", "page4"),
                ("keys", ["i"], 0.8),
                ("click", 435, 577, 0.8), ("arm", "23 box=12"), ("click", 435, 512, 1.5), ("shot", "belt23"), ("wait", 2)],
    "main": ([("keys", ["i"], 1.0),
              ("click", 418 + 29 * 7 + 14, 316 + 14, 0.6), ("arm", "18 page=4"),
              ("click", 418 + 29 * 5 + 14, 316 + 29 * 3 + 14, 1.5), ("shot", "page4"),
              ("keys", ["i"], 0.8),
              ("click", 435, 577, 0.8), ("arm", "23 box=12"), ("click", 435, 512, 1.5), ("shot", "belt23")]
             + drop_run(6) +
             [("pilot", (["farm", "--sweep", "--wp", "4,2", "--time", "110"] + NOVA), 300)]
             + drop_run(4, first=10) +
             [("wait", 400), ("shot", "mid"), ("wait", 380), ("shot", "end")]),
}


def cmd_build():
    os.makedirs(SAVES, exist_ok=True)
    return subprocess.run([*hr.PY, "tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/inv-sor.json", BASE,
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

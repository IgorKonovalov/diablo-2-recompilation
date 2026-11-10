"""Scripted harness sessions for plan 0054 Phase 2 (path search, per-event reproduction), on the runner library
(tools/harness_runner.py): fresh game processes on one slot (every case starts a new process: the plan's rule for a
seed-dependent case, and a PathPlan log has process state in it), logged by tools/gdb/path.gdb, driven by
tools/d2pilot.py, checked by tools/path.py.

Usage:
  python3 -I tools/path_sessions.py list
  python3 -I tools/path_sessions.py build --saves DIR            # the characters (tools/ai_sessions.py, tools/skills_sessions.py)
  python3 -I tools/path_sessions.py run --slot N --tag TAG --saves DIR --run RUN [--dev] [--status F] CASE [CASE ...]
  python3 -I tools/path_sessions.py split LOG

A CASE is one row of CASES below: the difficulty, the save (one file of DIR), the steps that stage it, in order:
("pilot", [d2pilot args], timeout[, level]) runs one tools/d2pilot.py command (skipped when the player already stands in
`level`), ("cast", [keys], s) presses each key and right-clicks next to the player, ("keys", [keys], s), ("rclick", x, y, s),
("wait", s). The log of a case is workspace/logs/path/<RUN>-s<N>-<seed>-<CASE>.log with its `.marks.tsv`; a case whose
character never left the starting level (the waypoint did not take) or whose pilot timed out is marked `fail` and is
a development log, not kept (harness-play.md § Fresh process, rule 5). Nothing here feeds a model: the pilot only decides
where to click.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ai_sessions as AS  # noqa: E402
import harness_runner as hr  # noqa: E402
import skills_sessions as SS  # noqa: E402

LOGS = os.path.join(ROOT, "workspace", "logs", "path")
GDB = "tools/gdb/path.gdb"
STEPS = AS.STEPS
CAST = SS.cast_explore


def wp(w, extra=()):
    return ("pilot", ["farm", "--wp", w, "--time", "1"] + list(extra), 90)


def nova_stage(w, secs=130):
    return ("pilot", ["farm", "--sweep", "--wp", w, "--time", str(secs), "--nova-key", "F1", "--radius", "9", "--mana-col", "4",
                      "--drink", "0.5", "--nova-hold", "1.6", "--max-res", "1000"], secs + 150)


# case: (difficulty, save, [steps], what)
RING = [(400, 150), (560, 220), (620, 300), (560, 400), (400, 450), (240, 400), (180, 300), (240, 220)]   # screen points around the character
BAR_KEYS = ["F1", "F2", "F3", "F4", "F5"]       # PathBar: Whirlwind, Leap, Leap Attack, Attack, Bash
PAL_KEYS = ["F1", "F2", "F3", "F4"]             # PathPal: Blessed Hammer, Attack, Charge, Holy Shield
RECIPES = {"PathBar": ("path-bar", "smpbar"), "PathPal": ("path-pal", "smppal")}
CASES = {
    "dev-smoke": ("normal", "SkillsSor", [wp("1,3"), ("pilot", CAST(SS.SOR_KEYS, 10), 300)],
                  "development: Stony Field, the Sorceress casting"),
    "dev-bar": ("normal", "PathBar", [wp("1,3"), ("pilot", CAST(BAR_KEYS, 30, walk=True), 500)], "development: Barbarian, Crushflange"),
    "dev-pal": ("normal", "PathPal", [wp("1,3"), ("pilot", CAST(PAL_KEYS, 30, walk=True), 500)], "development: Paladin, Blessed Hammer"),
    "dev-dru": ("normal", "SkillsDru", [wp("1,3"), ("pilot", CAST(["F1", "F2"], 30, walk=True), 500)], "development: Druid, Firestorm"),
    "dev-town4": ("normal", "CombatSor", [("pilot", ["explore", "--walk", "--hops", "40", "--drink", "0.5", "--mana-col", "4"] + AS.WP, 400)],
                  "development: the Pandemonium Fortress on foot"),
    "dev-a1jail": ("normal", "CombatSor", [("pilot", AS.stage("1,7", 130)[0][0], 280)], "development: Jail 1 (maze), Nova"),
    "dev-a2halls": ("normal", "CombatSor", [("pilot", AS.stage("2,4", 130)[0][0], 280)], "development: Halls of the Dead 2 (maze), Nova"),
    "dev-a3flayer": ("normal", "CombatSor", [("pilot", AS.stage("3,4", 130)[0][0], 280)], "development: Flayer Jungle, Nova"),
    "dev-a5glacial": ("normal", "CombatSor", [("pilot", AS.stage("5,5", 130)[0][0], 280)], "development: Glacial Trail, Nova"),
    "dev-necro": ("normal", "AiNec", AS.CASES["a1-necro"][1], "development: the Necromancer's golem and skeletons (pets: type 1)"),
    "dev-pal-probe": ("normal", "PathPal", [wp("1,3"), ("pilot", CAST(PAL_KEYS, 30, walk=True), 500)], "development: Paladin, Blessed Hammer (the spiral's products, SPX, rev 5)"),
    "dev-dru-chain": ("normal", "SkillsDru", [wp("1,3"), ("pilot", CAST(["F1", "F2"], 30, walk=True), 500)], "development: Druid, seed watchpoints",
                      {"PATH_CHAIN": "40"}),
    "dev-dru-chain2": ("normal", "SkillsDru", [wp("1,3"), ("pilot", CAST(["F1", "F2"], 10, walk=True), 200)], "development: Druid, seed watchpoints, short",
                       {"PATH_CHAIN": "40"}),
    "dev-town-bar": ("normal", "PathBar", [("clicks", 80, 1.2)], "development: the Rogue Encampment on foot, left clicks"),
    "dev-town": ("normal", "SkillsSor", [("pilot", ["explore", "--walk", "--hops", "40", "--drink", "0.4", "--mana-col", "4"], 400)],
                 "development: the Rogue Encampment on foot"),
}
# the kept cases (run:<date>-path): a town, outdoor and maze levels in Acts 1, 2, 3, 4 and 5, one fresh process each
CASES.update({
    "k-town-bar": ("normal", "PathBar", [("clicks", 100, 1.2)], "Rogue Encampment on foot (Act 1 town): player walks, town monsters"),
    "k-bar-stony": ("normal", "PathBar", [wp("1,3"), ("pilot", CAST(BAR_KEYS, 40, walk=True), 600)], "Stony Field (Act 1 outdoor), Barbarian: whirlwind, leap, knockback"),
    "k-bar-jail": ("normal", "PathBar", [wp("1,7"), ("pilot", CAST(BAR_KEYS, 40, walk=True), 600)], "Jail Level 1 (Act 1 maze), Barbarian"),
    "k-bar-halls": ("normal", "PathBar", [wp("2,4"), ("pilot", CAST(BAR_KEYS, 40, walk=True), 600)], "Halls of the Dead 2 (Act 2 maze), Barbarian"),
    "k-pal-stony": ("normal", "PathPal", [wp("1,3"), ("pilot", CAST(PAL_KEYS, 40, walk=True), 600)], "Stony Field, Paladin: Blessed Hammer (the 2026-11-04 run wrote a probe here; removed in logger rev 5)"),
    "k-pal-jail": ("normal", "PathPal", [wp("1,7"), ("pilot", CAST(PAL_KEYS, 40, walk=True), 600)], "Jail Level 1, Paladin: Blessed Hammer (the 2026-11-04 run wrote a probe here; removed in logger rev 5)"),
    "k-dru-stony": ("normal", "SkillsDru", [wp("1,3"), ("pilot", CAST(["F1", "F2"], 40, walk=True), 600)], "Stony Field, Druid: Firestorm, seed watchpoints",
                    {"PATH_CHAIN": "60"}),
    "k-dru-oasis": ("normal", "SkillsDru", [wp("2,5"), ("pilot", CAST(["F1", "F2"], 40, walk=True), 600)], "Far Oasis (Act 2 outdoor), Druid: Firestorm",
                    {"PATH_CHAIN": "60"}),
    "k-sor-jail": ("normal", "CombatSor", [("pilot", AS.stage("1,7", 130)[0][0], 280)], "Jail Level 1, Sorceress Nova and the mercenary"),
    "k-sor-oasis": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 130)[0][0], 280)], "Far Oasis, Nova: Scarab (type 2 tests)"),
    "k-sor-flayer": ("normal", "CombatSor", [("pilot", AS.stage("3,4", 130)[0][0], 280)], "Flayer Jungle (Act 3 outdoor), Nova"),
    "k-sor-river": ("normal", "CombatSor", [("pilot", AS.stage("4,3", 130)[0][0], 280)], "River of Flame (Act 4), Nova"),
    "k-sor-glacial": ("normal", "CombatSor", [("pilot", AS.stage("5,5", 130)[0][0], 280)], "Glacial Trail (Act 5 outdoor), Nova"),
    "k-necro": ("normal", "AiNec", AS.CASES["a1-necro"][1], "Jail Level 1, Necromancer with golem and skeletons (pets: type 1)"),
})
# the second kept batch: the types the first batch left short (2: Scarab and the River of Flame; 14: Blessed Hammer without the probe)
CASES.update({
    "k-sor-oasis-2": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 260)[0][0], 410)], "Far Oasis, Nova, longer: Scarab (type 2 tests)"),
    "k-sor-oasis-3": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 260)[0][0], 410)], "Far Oasis again, Nova, longer"),
    "k-sor-river-2": ("normal", "CombatSor", [("pilot", AS.stage("4,3", 300)[0][0], 450)], "River of Flame, Nova, longer (AI row 73)"),
    "k-pal-stony-2": ("normal", "PathPal", [wp("1,3"), ("pilot", CAST(PAL_KEYS, 40, walk=True), 600)], "Stony Field, Paladin: Blessed Hammer, natural inputs"),
    "k-pal-jail-2": ("normal", "PathPal", [wp("1,7"), ("pilot", CAST(PAL_KEYS, 40, walk=True), 600)], "Jail Level 1, Paladin: Blessed Hammer, natural inputs"),
    "k-pal-stony-3": ("normal", "PathPal", [wp("1,3"), ("pilot", CAST(PAL_KEYS, 40, walk=True), 600)], "Stony Field, Paladin, natural inputs again"),
})
# the third batch (logger rev 4): the ground items in the unit list and the watchpoint control; the same characters and stages
CASES.update({
    "k4-bar-stony": ("normal", "PathBar", [wp("1,3"), ("pilot", CAST(BAR_KEYS, 40, walk=True), 600)], "Stony Field, Barbarian, items in the unit list",
                     {"PATH_ITEMS": "1", "PATH_CHAIN_CTL": "40"}),
    "k4-sor-oasis": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 130)[0][0], 280)], "Far Oasis, Nova, items in the unit list",
                     {"PATH_ITEMS": "1", "PATH_CHAIN_CTL": "40"}),
    "k4-dru-stony": ("normal", "SkillsDru", [wp("1,3"), ("pilot", CAST(["F1", "F2"], 40, walk=True), 600)], "Stony Field, Druid: seed watchpoints and their control",
                     {"PATH_ITEMS": "1", "PATH_CHAIN": "60", "PATH_CHAIN_CTL": "40"}),
})

# the fourth batch (logger rev 5, run:<date>-path-2, plan 0054 Phase 2, the hold-out of path/0005): the same characters, the stages longer and
# more of them, and the waypoint hops of the W1 floor (act changes and arrivals inside an act, the player standing still after each)
def hops(chain, first_from_town=True, linger=3):
    """One pilot step per waypoint hop; the first from the Act IV town start uses the town waypoint's click (AS.WP)."""
    out = []
    for i, h in enumerate(chain):
        tab, row = h
        if i == 0 and first_from_town:
            out.append(("wp", str(tab), str(row)))
        else:
            out.append(("pilot", ["wpchain", "--chain", "%d,%d" % (tab, row), "--linger", str(linger)], 240))
    return out


BAR_LONG = CAST(BAR_KEYS, 70, walk=True)
PAL_LONG = CAST(PAL_KEYS, 70, walk=True)
CASES.update({
    "k5-bar-stony": ("normal", "PathBar", [wp("1,3"), ("pilot", BAR_LONG, 700)], "Stony Field, Barbarian: Whirlwind, Leap, Leap Attack (COR, L1)"),
    "k5-bar-stony-2": ("normal", "PathBar", [wp("1,3"), ("pilot", BAR_LONG, 700)], "Stony Field again, Barbarian, another seed"),
    "k5-bar-jail": ("normal", "PathBar", [wp("1,7"), ("pilot", BAR_LONG, 700)], "Jail Level 1 (maze), Barbarian"),
    "k5-bar-halls": ("normal", "PathBar", [wp("2,4"), ("pilot", BAR_LONG, 700)], "Halls of the Dead 2 (maze), Barbarian"),
    "k5-bar-cotd": ("normal", "PathBar", [wp("4,2"), ("pilot", BAR_LONG, 700)], "City of the Damned (Act 4 outdoor), Barbarian: trapped souls (deadCol 1)"),
    "k5-pal-stony": ("normal", "PathPal", [wp("1,3"), ("pilot", PAL_LONG, 700)], "Stony Field, Paladin: Blessed Hammer, natural (SPX)"),
    "k5-pal-stony-2": ("normal", "PathPal", [wp("1,3"), ("pilot", PAL_LONG, 700)], "Stony Field, Paladin, another seed"),
    "k5-pal-jail": ("normal", "PathPal", [wp("1,7"), ("pilot", PAL_LONG, 700)], "Jail Level 1, Paladin"),
    "k5-pal-jail-2": ("normal", "PathPal", [wp("1,7"), ("pilot", PAL_LONG, 700)], "Jail Level 1, Paladin, another seed"),
    "k5-pal-halls": ("normal", "PathPal", [wp("2,4"), ("pilot", PAL_LONG, 700)], "Halls of the Dead 2, Paladin"),
    "k5-sor-oasis": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 260)[0][0], 410)], "Far Oasis, Nova: Scarab (class 225), seed watchpoints",
                     {"PATH_CHAIN": "200"}),
    "k5-sor-oasis-2": ("normal", "CombatSor", [("pilot", AS.stage("2,5", 260)[0][0], 410)], "Far Oasis again, Nova, seed watchpoints", {"PATH_CHAIN": "200"}),
    "k5-sor-flayer": ("normal", "CombatSor", [("pilot", AS.stage("3,4", 200)[0][0], 350)], "Flayer Jungle, Nova, seed watchpoints", {"PATH_CHAIN": "200"}),
    "k5-sor-cotd": ("normal", "CombatSor", [("pilot", AS.stage("4,2", 260)[0][0], 410)], "City of the Damned, Nova: trapped souls", {"PATH_CHAIN": "200"}),
    "k5-sor-jail": ("normal", "CombatSor", [("pilot", AS.stage("1,7", 200)[0][0], 350)], "Jail Level 1, Nova and the mercenary (type 1 sites)"),
    "k5-necro": ("normal", "AiNec", AS.CASES["a1-necro"][1], "Jail Level 1, Necromancer with golem and skeletons (type 1)"),
    "k5-bar-river": ("normal", "PathBar", [wp("4,3"), ("pilot", BAR_LONG, 700)], "River of Flame (Act 4, in-act arrival), Barbarian"),
    "k5-bar-river-2": ("normal", "PathBar", [wp("4,3"), ("pilot", BAR_LONG, 700)], "River of Flame again, Barbarian"),
    "k5-bar-cotd-2": ("normal", "PathBar", [wp("4,2"), ("pilot", BAR_LONG, 700)], "City of the Damned again, Barbarian"),
    "k5-pal-cotd": ("normal", "PathPal", [wp("4,2"), ("pilot", PAL_LONG, 700)], "City of the Damned, Paladin: Blessed Hammer"),
    "k5-pal-cotd-2": ("normal", "PathPal", [wp("4,2"), ("pilot", PAL_LONG, 700)], "City of the Damned again, Paladin"),
    "k5-pal-river": ("normal", "PathPal", [wp("4,3"), ("pilot", PAL_LONG, 700)], "River of Flame, Paladin: Blessed Hammer"),
    "k5-sor-river": ("normal", "CombatSor", [("pilot", AS.stage("4,3", 260)[0][0], 410)], "River of Flame, Nova", {"PATH_CHAIN": "200"}),
    "k5-sor-river-2": ("normal", "CombatSor", [("pilot", AS.stage("4,3", 260)[0][0], 410)], "River of Flame again, Nova", {"PATH_CHAIN": "200"}),
    "k5-sor-glacial": ("normal", "CombatSor", [("pilot", AS.stage("5,5", 200)[0][0], 350)], "Glacial Trail, Nova", {"PATH_CHAIN": "200"}),
    "k5-hop-act": ("normal", "PathBar", hops([(1, 3), (4, 1)] * 6), "W1: Act IV town and Stony Field, 12 act changes, the player standing after each"),
    "k5-hop-in": ("normal", "PathBar", hops([(4, 3), (4, 1)] * 7), "W1: Act IV town and the River of Flame, 14 arrivals inside an act"),
    "k5-town": ("normal", "PathBar", [("clicks", 100, 1.2)], "Act IV town on foot (town monsters)"),
    "k5-town-a1": ("normal", "PathBar", hops([(1, 1)]) + [("clicks", 100, 1.2)], "Rogue Encampment on foot after a waypoint arrival (town monsters, the town-follow geometry)"),
})
CAP_SECS = 40 * 60


def cmd_list():
    for k, (diff, save, steps, what, *env) in CASES.items():
        print("%-18s %-10s %-11s %d step(s)  %s" % (k, diff, save, len(steps), what))
    return 0


def n_lines(path, tag):
    n = 0
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if line.startswith(tag + " "):
                    n += 1
    except OSError:
        pass
    return n


def run(slot, tag, saves, run_id, names, dev=False, status=None, seed0=5401, reruns=1):
    os.makedirs(LOGS, exist_ok=True)
    saves = os.path.abspath(saves)
    runname = ("dev-" if dev else "") + run_id
    out = open(os.path.join(LOGS, "%s-s%d.pilot.txt" % (runname, slot)), "a")
    shots = os.path.join("workspace", "logs", "path", "%s-s%d-shots" % (runname, slot))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    py = [*hr.PY, os.path.join(HERE, "d2pilot.py")]
    xd = [*hr.PY, os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
    info = {"cases": {}, "waypoint_retries": 0}
    seeds = [seed0]

    def run_case(case):
        diff, savename, steps, what = CASES[case][:4]
        for k in [k for k in os.environ if k.startswith("PATH_")]:
            del os.environ[k]
        os.environ.update(CASES[case][4] if len(CASES[case]) > 4 else {})
        seed = seeds[0]
        seeds[0] += 1
        stem = hr.new_stem(LOGS, runname, slot, seed, case)
        log = stem + ".log"
        t_case = time.time()
        hr.install(slot, tag, out=out)
        drv = hr.launch(slot, seed, log, gdb=GDB, steps=STEPS[diff], after=3000,
                        install=(tag, [os.path.join(saves, savename + ".d2s")]), out=out, stem=stem)
        hr.mark(stem, case, "start", log, "launch seed=%d %s %s" % (seed, diff, savename))
        try:
            r = hr.wait_ready(log, "PATH logger armed", 180, proc=drv, tick=lambda: hr.hide_window(slot))
            ok = r == hr.READY and hr.wait_count(log, "PLR", 1, 180, drv)
            hr.mark(stem, case, "ready" if ok else "fail", log, r)
            if not ok:
                return ("failed", "no PLR (%s)" % r)
            time.sleep(4)
            lid_start = AS.level_of(log)
            dead = False
            for step in steps:
                if isinstance(step[0], list):            # tools/ai_sessions.py's (args, timeout[, level])
                    step = ("pilot", step[0], step[1]) + tuple(step[2:])
                if step[0] == "wp":                      # ("wp", tab, row): town waypoint travel with the Act IV town's waypoint click
                    step = ("pilot", ["wp", step[1], step[2]] + AS.WP, 120)
                if step[0] == "wait":
                    time.sleep(step[1])
                    continue
                if step[0] == "keys":
                    for key in step[1]:
                        hr.sh(xd + ["key", key], 30, out)
                        time.sleep(step[2])
                    continue
                if step[0] == "clicks":                  # ("clicks", n, s): n left clicks on a ring of points around the character
                    for i in range(step[1]):
                        x, y = RING[i % len(RING)]
                        hr.sh(xd + ["click", str(x), str(y)], 30, out)
                        time.sleep(step[2])
                    continue
                if step[0] == "rclick":
                    hr.sh(xd + ["rclick", str(step[1]), str(step[2])], 30, out)
                    time.sleep(step[3])
                    continue
                if step[0] == "cast":
                    for key in step[1]:
                        hr.sh(xd + ["key", key], 30, out)
                        time.sleep(0.4)
                        hr.sh(xd + ["rclick", "430", "270"], 30, out)
                        time.sleep(step[2])
                    continue
                args, timeout = step[1], step[2]
                if len(step) > 3 and AS.level_of(log) == step[3]:
                    continue
                lid0 = AS.level_of(log)
                for attempt in range(3):          # a waypoint click that does not open the list is tried again
                    rc = hr.sh(py + [args[0], log, "--slot", str(slot)] + args[1:] + ["--shots", shots], timeout, out)
                    if rc is None:
                        dead = True
                        break
                    if "--wp" not in args or AS.level_of(log) != lid0:
                        break
                    info["waypoint_retries"] += 1
                    time.sleep(3)
                if dead:
                    break
            plns = n_lines(log, "PLN")
            hr.mark(stem, case, "end", log, "plans=%d" % plns)
            info["cases"][case] = {"stem": os.path.basename(stem), "plans": plns, "wall": round(time.time() - t_case, 1)}
            if dead:
                return ("failed", "pilot timeout")
            if AS.level_of(log) == lid_start and any(s[0] == "pilot" and "--wp" in s[1] for s in steps):
                return ("failed", "stayed in level %s" % lid_start)
            return ("kept", "plans=%d wall=%.0f s" % (plns, time.time() - t_case))
        finally:
            hr.stop(slot, drv, out=out)

    status = status or os.path.join(LOGS, "%s-s%d.status.json" % (runname, slot))
    try:
        st = hr.batch(names, run_case, status, reruns=reruns, stage=hr.NO_SHARING)
    finally:
        out.close()
    with open(status + ".info.json", "w") as f:
        json.dump(info, f, indent=1)
    print(hr.summary(st))
    return 0 if st["done"] and not st["failed"] else 1


def build_path(saves):
    for name, (recipe, base) in RECIPES.items():
        rc = hr.sh([*hr.PY, os.path.join(HERE, "d2s.py"), "build", AS.EXCEL, os.path.join(HERE, "d2s_recipes", recipe + ".json"),
                    os.path.join(ROOT, "workspace", "runtime", "saves-backup", "p0005", base + ".d2s"), os.path.join(saves, name + ".d2s")], 120)
        if rc:
            return 1
    return 0


def main(argv):
    if not argv or argv[0] not in ("list", "build", "run", "split"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        return cmd_list()
    ap = argparse.ArgumentParser()
    if argv[0] == "split":
        ap.add_argument("log")
        a = ap.parse_args(argv[1:])
        for r in hr.split(a.log):
            print("%-14s %s lines %d-%d" % (r["case"], r["path"], r["first"], r["end"]))
        return 0
    ap.add_argument("--saves", required=True)
    if argv[0] == "build":
        a = ap.parse_args(argv[1:])
        return AS.cmd_build(a.saves) or SS.build(a.saves) or build_path(a.saves)
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--status")
    ap.add_argument("--seed", type=int, default=5401)
    ap.add_argument("--reruns", type=int, default=1)
    ap.add_argument("cases", nargs="+")
    a = ap.parse_args(argv[1:])
    for c in a.cases:
        if c not in CASES:
            print("unknown case %s" % c)
            return 2
    return run(a.slot, a.tag, a.saves, a.run, a.cases, a.dev, a.status, a.seed, a.reruns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

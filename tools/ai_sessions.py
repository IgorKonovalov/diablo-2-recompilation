"""Scripted harness sessions for plan 0052 Phase 2 (monster AI, per-event reproduction), on the runner library
(tools/harness_runner.py; plan 0056 Phase 3's pilot): game processes on one slot, each holding several cases (one
stage of the game, one save, one difficulty), logged by tools/gdb/ai.gdb, driven by tools/d2pilot.py, checked by
tools/ai.py.

Usage:
  python3 -I tools/ai_sessions.py list
  python3 -I tools/ai_sessions.py build --saves DIR                    # CombatSor.d2s from tools/d2s_recipes/combatsor.json
  python3 -I tools/ai_sessions.py run --slot N --tag TAG --saves DIR --run RUN [--dev] [--status F] CASE [CASE ...]
  python3 -I tools/ai_sessions.py split LOG                            # the per-case logs of a launch log

The character is CombatSor (clvl 85 Sorceress, Teleport and Nova, an Act V Barbarian mercenary, every waypoint and
quest open; tools/combat_sessions.py's character, `1d9de374…`): the monsters of the stage think and act on it, and the
mercenary's own AI (row 61) is logged beside theirs. A CASE is one row of CASES below: the difficulty and the
tools/d2pilot.py commands that stage it (a waypoint, then `farm --sweep` with Nova). `run` takes the cases in order:
the first case of a launch starts the game (tools/d2run.py with the difficulty's steps file), each further case is a
menu return (harness_runner.next_case: Save and Exit, the save copied over, SINGLE PLAYER, OK, the difficulty box).
A new launch (after `slots.py stop`) starts when the launch holds 8 cases or has run 40 minutes (harness-play.md
§ Fresh process, the cap), when a case is marked FRESH, or after a case that failed. The log of a launch is
workspace/logs/ai/<RUN>-s<N>-<seed>-<LAUNCH>.log with its `.marks.tsv`; `split` cuts the per-case logs. Nothing here
feeds a model: the pilot only decides where to click.
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

LOGS = os.path.join(ROOT, "workspace", "logs", "ai")
EXCEL = os.path.join("workspace", "merged", "data", "global", "excel")
BASE = os.path.join("workspace", "samples", "d2s-owner", "smpsor-l50.d2s")
BASE_NEC = os.path.join("workspace", "samples", "d2s", "smpnec.d2s")
BASE_BAR = os.path.join("workspace", "samples", "d2s", "smpbar.d2s")
GDB = "tools/gdb/ai-g4.gdb"
CAP_GAMES, CAP_SECS = 8, 40 * 60

# the character starts in the Act IV town (Pandemonium Fortress), whose waypoint is at (715, 58) on the screen
WP = ["--wp-x", "715", "--wp-y", "58"]
NOVA0 = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6"] + WP
NOVA = NOVA0 + ["--max-res", "1000"]
STEPS = {"normal": "tools/gdb/enter-normal.steps", "nightmare": "tools/gdb/enter-nightmare.steps",
         "hell": "tools/gdb/enter-hell.steps"}


def stage(wp, secs=130, more=(), players=0):
    """Waypoint TAB,ROW, then Nova sweep for `secs` seconds of the kill loop. `players` N types /players N once the
    game takes keys (d2pilot farm --players; a process holds it across games, so run such a case fresh)."""
    return [(["farm", "--sweep", "--wp", wp, "--time", str(secs)] + NOVA + list(more) +
             (["--players", str(players)] if players else []), secs + 150)]


def catacombs(secs=60, hold=False, players=0):
    """Catacombs Level 2 waypoint, descents to Level 4 (Level 3 holds Vampires; a descent is skipped once the player
    stands in level 37), then Andariel (Level 4): the combat sessions' route (tools/combat_sessions.py andariel with
    guard). With `hold` the Nova radius is 1, so that she is not killed at once and thinks for a while."""
    down = ["farm", "--sweep", "--descend", "18", "--descend-time", "300", "--time", "15", "--max-res", "1000"] + NOVA0
    first = ["farm", "--sweep", "--wp", "1,9", "--descend", "18", "--descend-time", "300", "--time", "15",
             "--max-res", "1000"] + NOVA0 + (["--players", str(players)] if players else [])
    return [(first, 380, 37), (down, 360, 37), (down, 360, 37), (down, 360, 37),
            (["hunt", "--mon-cls", "156", "--time", str(secs * 4)] + NOVA0 + (["--radius", "1"] if hold else []),
             secs * 4 + 40)]


def countess(secs=60):
    """Black Marsh waypoint (tab 1 row 5), the Forgotten Tower (LvlWarp 10, level 20), its cellar (12, level 21), four
    Crypt Down warps (9) to Tower Cellar Level 5 (level 25), then a hunt for the Countess (class 45) with the Nova
    radius at 1 so that she is not killed at once and thinks for a while (the route of tools/h2a_sessions.py's
    countess(), on the Act IV start). A descent is skipped once the player stands in its level or a deeper one."""
    def down(rec, more=()):
        return ["farm", "--sweep", "--descend", str(rec), "--descend-time", "240", "--time", "5"] + NOVA0 + list(more)
    return [(["farm", "--sweep", "--wp", "1,5", "--descend", "10", "--descend-time", "240", "--time", "5"] + NOVA0,
             400, (20, 21, 22, 23, 24, 25)),
            (down(12), 340, (21, 22, 23, 24, 25)),
            (down(9), 340, (22, 23, 24, 25)),
            (down(9), 340, (23, 24, 25)),
            (down(9), 340, (24, 25)),
            (down(9), 340, (25,)),
            (["hunt", "--mon-cls", "45", "--time", str(secs * 5)] + NOVA0 + ["--radius", "1"], secs * 5 + 40)]


def skipped(level, skip):
    """A step's third element: a level id, or a tuple of them; the step is skipped when the player stands in one."""
    if skip is None or level is None:
        return False
    return level == skip if isinstance(skip, int) else level in skip


def launch_seed(case, seed0, launches, pinned=None):
    """The map seed of a launch. A case in PINNED keeps its seed on every launch, a rerun included (a route of fixed
    positions holds on that seed only); any other case takes seed0 plus the launch number."""
    pinned = PINNED if pinned is None else pinned
    name = case[6:] if case.startswith("fresh:") else case
    return pinned[name] if name in pinned else seed0 + launches


# case: (difficulty, [pilot steps (args, timeout[, level])], what the stage holds [MonStats AI rows, Levels mon cols])
CASES = {
    "a1-jail": ("normal", stage("1,7"), "Jail Level 1: Fallen 6, SkeletonBow 37, SkeletonMage 64, Wraith 9"),
    "a1-stony": ("normal", stage("1,3"), "Stony Field: CorruptArcher 35, Skeleton 2"),
    "a1-darkwood": ("normal", stage("1,4"), "Dark Wood: Fallen 6, SkeletonBow 37"),
    "a1-marsh": ("normal", stage("1,5"), "Black Marsh: CorruptArcher 35, FallenShaman 13, Skeleton 2"),
    "a1-cloister": ("normal", stage("1,8"), "Inner Cloister: CorruptArcher 35, Fallen 6, SkeletonMage 64"),
    "a1-catacombs": ("normal", catacombs(), "Catacombs 2-4: FallenShaman 13, Vampire 28, Andariel 34"),
    "a2-halls": ("normal", stage("2,4"), "Halls of the Dead 2: BatDemon 29, GreaterMummy 22, Mummy 21"),
    "a2-oasis": ("normal", stage("2,5"), "Far Oasis: Scarab 20"),
    "a2-arcane": ("normal", stage("2,8"), "Arcane Sanctuary: Vampire 28, Wraith 9"),
    "a3-flayer": ("normal", stage("3,4"), "Flayer Jungle: Fetish 30"),
    "a3-travincal": ("normal", stage("3,8"), "Travincal: Vampire 28"),
    "a3-durance": ("normal", stage("3,9"), "Durance of Hate 2: Fetish 30, Mummy 21, Vampire 28"),
    "a4-cotd": ("normal", stage("4,2"), "City of the Damned: BatDemon 29, Megademon 89"),
    "a5-crystal": ("normal", stage("5,4"), "Crystalline Passage: BloodLord 125"),
    "a5-glacial": ("normal", stage("5,5"), "Glacial Trail: BloodLord 125"),
    # rev 3 batch (plan 0052 Phase 2, second launch group)
    "a2-oasis-3": ("normal", stage("2,5"), "Far Oasis again, for the Scarab sites the rev 2 logger window missed"),
    "a2-halls-long": ("normal", stage("2,4", 260), "Halls of the Dead 2, longer: GreaterMummy 22, Mummy 21, BatDemon 29"),
    "a1-cloister-2": ("normal", stage("1,8", 200), "Inner Cloister again: SkeletonMage 64, CorruptArcher 35"),
    "a4-river": ("normal", stage("4,3"), "River of Flame: Megademon 89"),
    "a5-pain": ("normal", stage("5,6"), "Halls of Pain: BloodLord 125"),
    "a1-andariel": ("normal", catacombs(120, hold=True), "Catacombs to Andariel; she is kept alive: Andariel 34"),
    # third group: the tier AIs still short after the first two (Andariel, SkeletonMage, Megademon)
    "a1-jail-2": ("normal", stage("1,7", 200), "Jail Level 1 again, longer: SkeletonMage 64, SkeletonBow 37, Wraith 9"),
    "a2-palace": ("normal", stage("2,7", 200), "Palace Cellar Level 1: SkeletonMage 64, SkeletonBow 37"),
    "a4-cotd-long": ("normal", stage("4,2", 300), "City of the Damned, longer: Megademon 89, BatDemon 29"),
    "a4-river-long": ("normal", stage("4,3", 300), "River of Flame, longer: Megademon 89"),
    "a1-andariel-2": ("normal", catacombs(120, hold=True), "Catacombs to Andariel with the level guards: Andariel 34"),
    # /players 8: Andariel has 4.5 times the life, so the mercenary needs longer and she thinks for longer (a process
    # holds /players across games: run it as a fresh case)
    "a3-flayer-p8": ("normal", stage("3,4", 240, players=8), "Flayer Jungle at /players 8: Fetish 30 (chained pairs)"),
    "a1-andariel-p8": ("normal", catacombs(120, hold=True, players=8), "Catacombs to Andariel at /players 8: Andariel 34"),
    "a1-countess": ("normal", countess(), "Tower Cellar Level 5: The Countess (row 10; state 13)"),
    "wp-probe": ("normal", stage("1,7", 10), "Jail Level 1, ten seconds: the waypoint click's launch-by-launch failure rate (plan 0052 lane/p52d)"),
    "nm-a2-halls": ("nightmare", stage("2,4"), "Halls of the Dead 2, Nightmare"),
    "h-a4-cotd": ("hell", stage("4,2"), "City of the Damned, Hell"),
    # the Necromancer (tools/d2s_recipes/ai-nec.json, built on samples/d2s/smpnec.d2s): a golem and skeletons fight
    # beside her (the summons' AI, row 67). Steps: ("wp", TAB, ROW), ("keys", [key..], s), ("rclick", x, y, s),
    # ("wait", s), then d2pilot commands as above.
    "a1-necro": ("normal", [("wp", "1", "7"), ("keys", ["F2"], 0.6), ("rclick", 440, 330, 1.0), ("keys", ["F2"], 0.6),
                            ("rclick", 360, 330, 1.0),
                            (["explore", "--walk", "--hops", "60", "--hop", "8", "--nova-key", "F1", "--radius", "9",
                              "--mana-col", "4", "--drink", "0.5", "--give-up", "8"] + WP, 330),
                            ("keys", ["F3"], 0.6), ("rclick", 440, 330, 1.0)],
                 "Jail Level 1 with Clay Golem and Raise Skeleton: NecroPet 67", "AiNec"),
}


def melee(wp, secs, keys=None, button=3, save="AiNecC", what=""):
    """A melee character (tools/d2pilot.py explore --melee) in a stage: with `keys`, the curse hotkeys are pressed in
    turn before each right-button click on a monster (--keys-cycle); without, the left-button Attack."""
    args = ["explore", "--walk", "--hops", str(secs // 3), "--hop", "8", "--radius", "9", "--mana-col", "4",
            "--drink", "0.5", "--give-up", "8", "--melee"] + WP
    if keys:
        args += ["--melee-button", str(button), "--curse-keys", keys, "--keys-cycle"]
    return [("wp", wp[0], wp[1]), ("wait", 4), (args, secs + 120)]


# plan 0052 Phase 2, second run (lane/p52b): the state control (a curse or a taunt cast on monsters: AiCtl.state 10, 11,
# 12 observed live) and a melee character in the tier stages (monsters at distance 0-2 and adjacent targets)
CASES.update({
    "s-necro-curse": ("normal", melee("1,7".split(","), 240, "F1,F2", 3), "Jail Level 1: Dim Vision and Terror cast on monsters", "AiNecC"),
    "s-barb-howl": ("normal", melee("1,7".split(","), 200, "F1,F2", 3), "Jail Level 1: Howl and Taunt", "AiBar"),
    "s-barb-halls": ("normal", melee("2,4".split(","), 240), "Halls of the Dead 2, a melee Barbarian", "AiBar"),
    "s-barb-flayer": ("normal", melee("3,4".split(","), 240), "Flayer Jungle, a melee Barbarian: Fetish 30", "AiBar"),
    "s-barb-oasis": ("normal", melee("2,5".split(","), 240), "Far Oasis, a melee Barbarian: Scarab 20", "AiBar"),
})


def duriel(secs=420):
    """Plan 0052 Phase 1b P1b-1: Duriel's lair on map seed 3364 (run with --seed 3364), where Tal Rasha's real tomb is
    level 72 (a Canyon of the Magi waypoint arrival at (12678, 5178), the tomb's warp near (12794, 5033), the orifice at
    (22858, 14043), the portal at (22845, 14046): positions of the plan 0032 session 3364 log). The Horadric Staff is
    at inventory cell 0,0 of AiDur; the hunt keeps the Nova radius at 1 so that Duriel is not killed at once and thinks
    for a while beside the player (the mercenary fights him)."""
    hold = ["--radius", "1"]
    return [("wp", "2", "9"), ("wait", 4),
            (["objop", "--obj-cls", "9999", "--goal", "12794,5033", "--time", "120", "--no-nova", "--hop", "14",
              "--stop-on-level"] + NOVA0, 150, 72),
            (["insert", "key:i", "sleep:1.0", "click:inv:0,0", "sleep:0.6", "key:i", "sleep:1.0"], 60),
            (["objop", "--obj-cls", "152", "--times", "1", "--no-nova", "--goal", "22858,14043", "--hop", "14",
              "--time", "150"] + NOVA0, 180),
            (["objop", "--obj-cls", "100", "--times", "1", "--no-nova", "--goal", "22845,14046", "--hop", "14",
              "--time", "120"] + NOVA0, 150),
            (["hunt", "--mon-cls", "211", "--time", str(secs)] + NOVA0 + hold, secs + 60)]


CASES["a2-halls-p12"] = ("normal", stage("2,4", 420), "Halls of the Dead 2, long: GreaterMummy 22, Mummy 21 (P1b-2 with AI_P1B2=1)")
CASES["d-duriel"] = ("normal", duriel(), "Duriel's lair at /players 1, Normal: row 44, the melee decision (map seed 3364)", "AiDur")
CHAR = "CombatSor"
# cases whose route holds on one map seed only: the launch seed is this one every time, a rerun included
PINNED = {"d-duriel": 3364}


def case_of(name):
    c = CASES[name]
    return c[0], c[1], c[2], (c[3] if len(c) > 3 else CHAR)


def cmd_list():
    for k in CASES:
        diff, steps, what, save = case_of(k)
        print("%-14s %-10s %-9s %d step(s)  %s" % (k, diff, save, len(steps), what))
    return 0


def cmd_build(saves):
    os.makedirs(saves, exist_ok=True)
    rc = subprocess.run([*hr.PY, "tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/combatsor.json", BASE,
                         os.path.join(saves, CHAR + ".d2s")], cwd=ROOT).returncode
    rc = rc or subprocess.run([*hr.PY, "tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/ai-dur.json", BASE,
                               os.path.join(saves, "AiDur.d2s")], cwd=ROOT).returncode
    for rec, base, name in (("ai-nec", BASE_NEC, "AiNec"), ("ai-nec-curse", BASE_NEC, "AiNecC"),
                            ("ai-barb", BASE_BAR, "AiBar")):
        rc = rc or subprocess.run([*hr.PY, "tools/d2s.py", "build", EXCEL, "tools/d2s_recipes/%s.json" % rec, base,
                                   os.path.join(saves, name + ".d2s")], cwd=ROOT).returncode
    return rc


class Proc:
    """The launch a batch is in: the stem and log, the driver, how many games it holds, when it began."""

    def __init__(self):
        self.drv = self.stem = self.log = None
        self.games = 0
        self.t0 = 0.0
        self.dead = False
        self.launches = 0
        self.save = None
        self.switch_ok = False    # the last case was kept and passed stage_reached: next_case may switch


def run(slot, tag, saves, run_id, names, dev=False, status=None, seed0=5201, reruns=1, gdb=GDB):
    os.makedirs(LOGS, exist_ok=True)
    saves = os.path.abspath(saves)
    runname = ("dev-" if dev else "") + run_id
    out_path = os.path.join(LOGS, "%s-s%d.pilot.txt" % (runname, slot))
    out = open(out_path, "a")
    shots = os.path.join("workspace", "logs", "ai", "%s-s%d-shots" % (runname, slot))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    pr = Proc()
    retries = [0]
    starts = {}                               # case -> the level it began in (stage_reached reads it)
    info = {"launches": [], "cases": {}, "waypoint_retries": 0}
    py = [*hr.PY, os.path.join(HERE, "d2pilot.py")]

    def close(why):
        if pr.drv is None:
            return
        hr.mark(pr.stem, "-", "end", pr.log, why)
        hr.stop(slot, pr.drv, out=out)
        pr.drv = None

    def launch(case, diff, save):
        seed = launch_seed(case, seed0, pr.launches)
        pr.launches += 1
        pr.stem = hr.new_stem(LOGS, runname, slot, seed, "L%d" % pr.launches)
        pr.log = pr.stem + ".log"
        hr.install(slot, tag, out=out)
        pr.drv = hr.launch(slot, seed, pr.log, gdb=gdb, steps=STEPS[diff], after=3000, install=(tag, [save]), out=out,
                           stem=pr.stem)
        hr.mark(pr.stem, case, "start", pr.log, "launch seed=%d %s" % (seed, diff))
        r = hr.wait_ready(pr.log, "AI logger armed", 180, proc=pr.drv, tick=lambda: hr.hide_window(slot))
        ok = r == hr.READY and hr.wait_count(pr.log, "PLR", 1, 180, pr.drv)
        pr.games, pr.t0, pr.dead = 1, time.time(), not ok
        info["launches"].append({"stem": os.path.basename(pr.stem), "seed": seed, "first": case, "ready": r})
        return bool(ok)

    def run_case(case):
        name = case[6:] if case.startswith("fresh:") else case
        diff, steps, what, savename = case_of(name)
        save = os.path.join(saves, savename + ".d2s")
        t_case = time.time()
        fresh = case.startswith("fresh:")
        # a case with another character than the process holds starts a new process (one character per saves directory);
        # so does any case after one that was not kept with its stage checked (a raise inside run_case leaves pr.dead
        # unset, and hr.next_case would refuse every later case of the batch)
        prev_ok, pr.switch_ok = pr.switch_ok, False
        need_new = (pr.drv is None or pr.dead or not prev_ok or fresh or pr.games >= CAP_GAMES or time.time() - pr.t0 >= CAP_SECS
                    or pr.save != savename)
        if need_new:
            close("new launch for %s" % case)
            ok = launch(case, diff, save)
            pr.save = savename
            note = "launch"
        else:
            res = hr.next_case(slot, pr.log, [save], diff=diff, out=out, stem=pr.stem, case=case)
            ok = res["ok"]
            pr.games += 1
            note = "switch %.1f s" % res["secs"]
            if not ok:
                pr.dead = True
        hr.mark(pr.stem, case, "ready" if ok else "fail", pr.log, note)
        if not ok:
            return ("failed", "no PLR (%s)" % note)
        n_before = sum(1 for ln in open(pr.log, errors="replace") if ln.startswith("AID "))
        lid_start = starts[case] = level_of(pr.log)
        xd = [*hr.PY, os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
        for step in steps:
            if step[0] == "wait":                       # ("wait", seconds)
                time.sleep(step[1])
                continue
            if step[0] == "keys":                       # ("keys", [key, ...], seconds between)
                for key in step[1]:
                    hr.sh(xd + ["key", key], 30, out)
                    time.sleep(step[2])
                continue
            if step[0] == "rclick":                     # ("rclick", x, y, seconds after)
                hr.sh(xd + ["rclick", str(step[1]), str(step[2])], 30, out)
                time.sleep(step[3])
                continue
            if step[0] == "wp":                         # ("wp", tab, row): town waypoint travel
                step = (["wp", step[1], step[2]] + WP, 120)
            if len(step) > 2 and skipped(level_of(pr.log), step[2]):
                continue
            args, timeout = step[0], step[1]
            lid0, pos0 = level_of(pr.log), plr_pos(pr.log)
            for attempt in range(3):         # a waypoint click that does not open the list is tried again
                a = list(args)
                if attempt and pos0 and plr_pos(pr.log):
                    # the walk toward the waypoint stopped short: the waypoint is where it was on the screen, moved by
                    # what the player has walked (a sub-tile (dx, dy) moves it by (16 (dx - dy), 8 (dx + dy)); the
                    # click's y is in the 571-row screenshot of the 600-row frame)
                    dx, dy = plr_pos(pr.log)[0] - pos0[0], plr_pos(pr.log)[1] - pos0[1]
                    i = a.index("--wp-x")
                    a[i + 1] = str(int(a[i + 1]) - 16 * (dx - dy))
                    a[a.index("--wp-y") + 1] = str(int(round(int(a[a.index("--wp-y") + 1]) - 8 * (dx + dy) * 571 / 600)))
                rc = hr.sh(py + [a[0], pr.log, "--slot", str(slot)] + a[1:] + ["--shots", shots], timeout, out)
                if rc is None:
                    pr.dead = True
                    break
                if "--wp" not in args or level_of(pr.log) != lid0:
                    break
                retries[0] += 1
                hr.sh([*hr.PY, os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "shot",
                       os.path.join(shots, "wpfail-%s-%d-%d.png" % (case, retries[0], attempt))], 30, out)
                time.sleep(3)
        n_after = sum(1 for ln in open(pr.log, errors="replace") if ln.startswith("AID "))
        hr.mark(pr.stem, case, "end", pr.log, "decisions=%d" % (n_after - n_before))
        info["cases"][case] = {"launch": os.path.basename(pr.stem), "decisions": n_after - n_before,
                               "wall": round(time.time() - t_case, 1)}
        if pr.dead:
            return ("failed", "pilot timeout")
        return ("kept", "decisions=%d wall=%.0f s" % (n_after - n_before, time.time() - t_case))

    def stage_reached(case):
        """The case gate (hr.batch stage=): a case that stayed in town is a failure, and its process takes no
        further case."""
        r = left_start(pr.log, starts.get(case))
        if not r[0]:
            pr.dead = True
        pr.switch_ok = r[0]
        return r

    status = status or os.path.join(LOGS, "%s-s%d.status.json" % (runname, slot))
    try:
        st = hr.batch(names, run_case, status, reruns=reruns, stage=stage_reached)
    finally:
        close("batch end")
        out.close()
    info["waypoint_retries"] = retries[0]
    with open(status + ".launches.json", "w") as f:
        json.dump(info, f, indent=1)
    print(hr.summary(st))
    return 0 if st["done"] and not st["failed"] else 1


def left_start(log, lid_start):
    """The stage check (plan 0056 Phase 4): (True, "") when the player's last PLR level differs from the level the
    case began in (the waypoint took the character out of town), else (False, "stayed in level N")."""
    lid = level_of(log)
    if lid == lid_start:
        return False, "stayed in level %s" % lid
    return True, ""


def level_of(path):
    """The level id of the player's last PLR line in a log (None without one)."""
    lid = None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if line.startswith("PLR "):
                    lid = line.split('"lid":', 1)[1].split(",", 1)[0]
    except OSError:
        return None
    return int(lid) if lid is not None else None


def plr_pos(path):
    """The player's last PLR position (x, y) in a log, None without one."""
    r = None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if line.startswith("PLR "):
                    r = line
    except OSError:
        return None
    if r is None:
        return None
    d = json.loads(r[4:])
    return d["x"], d["y"]


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
        return cmd_build(a.saves)
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--status")
    ap.add_argument("--seed", type=int, default=5201)
    ap.add_argument("--reruns", type=int, default=1)
    ap.add_argument("--gdb", default=GDB, help="the logger script (tools/gdb/ai-skills.gdb: the AI and the skills loggers)")
    ap.add_argument("--fresh", action="store_true", help="every case in its own game process (plan 0056 Phase 4: the default for kept runs)")
    ap.add_argument("cases", nargs="+")
    a = ap.parse_args(argv[1:])
    if a.fresh:
        a.cases = [c if c.startswith("fresh:") else "fresh:" + c for c in a.cases]
    for c in a.cases:
        if (c[6:] if c.startswith("fresh:") else c) not in CASES:
            print("unknown case %s" % c)
            return 2
    return run(a.slot, a.tag, a.saves, a.run, a.cases, a.dev, a.status, a.seed, a.reruns, a.gdb)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

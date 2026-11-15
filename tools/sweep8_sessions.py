"""Single-client sessions of plan 0065 (harness sweep 8) Phase 1, on the runner library (tools/harness_runner.py).

Usage:
  python3 -I tools/sweep8_sessions.py list
  python3 -I tools/sweep8_sessions.py build                 # every recipe of RECIPES into workspace/samples/sweep8/
  python3 -I tools/sweep8_sessions.py check                 # build into a temporary directory and test each recipe's state
  python3 -I tools/sweep8_sessions.py run --slot N --tag TAG --run RUN [--dev] SESSION [SESSION ...]

Every session starts a fresh game process (harness-play.md § Fresh process, rule 1; no sharing opt-in: each case has
its own character and its own logger, and C2, P12 and the exp-state kills depend on the map seed), one launch per
session, `hr.batch(..., stage=hr.NO_SHARING)`. A SESSION names a row of SESSIONS: the recipe, the logger, the steps file
entering the game, the seed, the logger's ready line, the steps, and the logger environment. A step is a tuple whose
first item names the kind:
  ("wait", s)  ("keys", [key..], gap)  ("shiftkey", key, gap)  ("click", x, y, s)  ("rclick", x, y, s)  ("shot", name)
  ("pilot", [args..], timeout)   a tools/d2pilot.py command on the session's log
  ("p12go", hops)                P12: the bit-0-only cell pick of tools/sweep8_check.py pick on this session's own log
                                 (nearest to the player), then tools/d2pilot.py hop towards its stand cell
  ("nova", n)                    n Nova bursts where the player stands (F1, Shift + right button held 1.6 s)
Screen coordinates are the 800x600 game frame (xdrive --window "Diablo II"); the inventory grid is at (418 + 29c,
316 + 29r). Nothing here feeds a model: the steps only decide where to click. The H3 portrait point MERC_PORTRAIT is a
measured input of the development session (plan 0065 log, Phase 0 staging table): until measured it is a guess.

Read-only loggers only (ADR-0003): tools/gdb/inventory.py (sourced by sweep8-use.gdb) has an armed request edit that
fires when its arm file exists; this runner points INV_RUNTIME at a directory of its own that holds no arm file and
refuses to start if one is there.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import harness_runner as hr  # noqa: E402

LOGS = os.path.join(ROOT, "workspace", "logs", "sweep8")
EXCEL = os.path.join("workspace", "merged", "data", "global", "excel")
SAVES = os.path.join(ROOT, "workspace", "samples", "sweep8")
NOARM = os.path.join(ROOT, "workspace", "runtime", "sweep8-noarm")
RECIPES = os.path.join(HERE, "d2s_recipes")
BASE_X = os.path.join("workspace", "samples", "d2s-owner", "smpsor-l50.d2s")
BASE_PAL = os.path.join("workspace", "samples", "d2s", "smppal.d2s")
# recipe -> (base save, character name)
RECIPE_SET = {
    "sw8-nova": (BASE_X, "SweepNova"),
    "sw8-h2": (BASE_X, "SweepPot"),
    "sw8-h3": (BASE_X, "SweepMerc"),
    "sw8-b8room": (BASE_X, "SweepBeltRoom"),
    "sw8-b8full": (BASE_X, "SweepBeltFull"),
    "sw8-xs": (BASE_PAL, "SweepConv"),
}
INV0, CELL = (418, 316), 29
MERC_PORTRAIT = (38, 40)       # the hireling's portrait frame (15..62, 18..62 in the 800x600 frame): measured in the dev session (screenshot, run:2026-11-15-sweep8-single)


def icell(k):
    """Screen centre of inventory cell k (row-major, 10 wide)."""
    return INV0[0] + CELL * (k % 10) + 14, INV0[1] + CELL * (k // 10) + 14


def use_run(cells, gap):
    """Right-click use of inventory cells, `gap` seconds apart (the request 0x20)."""
    return [("rclick",) + icell(k) + (gap,) for k in cells]


def explore(hops, extra=()):
    return ["explore", "--hops", str(hops), "--drink", "0.4", "--mana-col", "4"] + list(extra)


def cast_explore(keys, hops, radius=12, walk=False):
    """tools/skills_sessions.py's cast_explore: the right button cast at the nearest live monster, the hotkeys in turn."""
    return (["explore"] + (["--walk"] if walk else []) +
            ["--melee", "--melee-button", "3", "--curse-keys", ",".join(keys), "--keys-cycle", "--give-up", "8",
             "--radius", str(radius), "--melee-hold", "0.3", "--drink", "0.4", "--mana-col", "4", "--hops", str(hops)])


# --dead-below 0: the pilot never stops on an empty-looking orb (the b8 characters stand at 5 of 60 life)
LEAVE_TOWN = ("pilot", ["explore", "--any-level", "--walk", "--hops", "12", "--drink", "0", "--dead-below", "0"], 300)
H3_GIVE = [step for k in range(5) for step in (("click",) + icell(k) + (0.6,),
                                                ("click", MERC_PORTRAIT[0], MERC_PORTRAIT[1], 1.5),
                                                ("click",) + icell(k) + (0.8,))]

# name: (recipe, gdb, steps file, seed, ready line, [steps], env)
SESSIONS = {
    # C2 (skills/0002 § 12; backlog 2026-10-27 plan-0045-c2): quill rats (quillrat1, MissA2 spike1) shoot at the player
    # in the Blood Moor; seed 3 Normal held two quillrat1 creations in level 2 (p44h-mstat-1-host.log, PC lines
    # 7039 and 7471). No casting: the pilot only hops, so the rats live to shoot. skills.gdb is the rev 5 logger.
    "c2": ("sw8-nova", "tools/gdb/skills.gdb", "tools/gdb/enter-normal.steps", 3, "SKILLS logger armed",
           [LEAVE_TOWN, ("pilot", explore(60, ["--nova", "0"]), 900), ("shot", "end")], {"SKILLS_WIN": "10"}),
    # P12 (backlog 2026-11-04 0054-p12; skills/missiles D3): Nova (pSrvDoFunc 1, CollideType 3) cast beside a
    # bit-0-only cell of the Blood Moor, then Nova bursts over the level for more crossings and the free-cell control
    "p12": ("sw8-nova", "tools/gdb/p12.gdb", "tools/gdb/enter-normal.steps", 3, "P12 logger armed",
            [LEAVE_TOWN, ("p12go", 12), ("nova", 6), ("shot", "pick"),
             ("pilot", cast_explore(["F1"], 25), 600), ("shot", "end")], {"P12_CLS": "90"}),
    # H2 (items/0017 H2, items/use F1f): four pairs of different tiers 1.2 s apart, life and mana far below their
    # maxima; then 150 s of mana regeneration and two mp3 for the free at the maximum (UFM)
    "h2": ("sw8-h2", "tools/gdb/sweep8-use.gdb", "tools/gdb/enter-normal.steps", 6501, "USE8 logger armed",
           [("keys", ["i"], 1.0)] + use_run([0, 1], 1.2) + [("wait", 14)] + use_run([2, 3], 1.2) + [("wait", 14)]
           + use_run([4, 5], 1.2) + [("wait", 14)] + use_run([6, 7], 1.2) + [("wait", 150), ("shot", "mana")]
           + use_run([8], 2.0) + use_run([9], 8.0) + [("shot", "end")], {}),
    # H3 (items/0017 H3, items/use D3, D5): Shift + belt key (request 0x26 with the flag) for hp1, then wms (fallen
    # to box 1), rvs, yps and mp1 twice; then each of the five page-0 cells put on the cursor and clicked on the
    # hireling's portrait (request 0x61), then back to its cell
    "h3": ("sw8-h3", "tools/gdb/sweep8-use.gdb", "tools/gdb/enter-normal.steps", 6502, "USE8 logger armed",
           [("wait", 4), ("shot", "town"), ("shiftkey", "2", 2.0), ("shiftkey", "2", 2.0), ("shiftkey", "3", 2.0),
            ("shiftkey", "4", 2.0), ("shiftkey", "1", 2.0), ("shiftkey", "1", 2.0), ("shot", "belt"),
            ("keys", ["i"], 1.0)] + H3_GIVE + [("shot", "end")], {}),
    # B8 (items/0017 B8, items/inventory F6): a death with a 16-box belt full, page 0 empty / page 0 full
    "b8room": ("sw8-b8room", "tools/gdb/sweep8-use.gdb", "tools/gdb/enter-normal.steps", 3, "USE8 logger armed",
               [LEAVE_TOWN,
                ("pilot", ["explore", "--hops", "40", "--drink", "0", "--nova", "0", "--dead-below", "0"], 600),
                ("wait", 6), ("shot", "dead")], {}),
    "b8full": ("sw8-b8full", "tools/gdb/sweep8-use.gdb", "tools/gdb/enter-normal.steps", 3, "USE8 logger armed",
               [LEAVE_TOWN,
                ("pilot", ["explore", "--hops", "40", "--drink", "0", "--nova", "0", "--dead-below", "0"], 600),
                ("wait", 6), ("shot", "dead")], {}),
    # exp-state kills (player/0002 § 4; backlog 2026-11-04 a68-review): Conversion (F1) cast at the nearest live
    # monster while the Paladin walks the Blood Moor; the converted monster kills and is killed
    "xs": ("sw8-xs", "tools/gdb/sweep8-xs.gdb", "tools/gdb/enter-normal.steps", 3, "PLAYER logger armed",
           [LEAVE_TOWN, ("pilot", cast_explore(["F1"], 40, walk=True), 900), ("shot", "end")], {}),
}


def build_one(name, out_path):
    base, _cname = RECIPE_SET[name]
    import d2s
    with contextlib.redirect_stdout(io.StringIO()):
        d2s.build(os.path.join(ROOT, EXCEL), os.path.join(RECIPES, name + ".json"), os.path.join(ROOT, base), out_path)
    with open(out_path, "rb") as fh:
        return fh.read()


def cmd_build():
    os.makedirs(SAVES, exist_ok=True)
    for n, (base, cname) in RECIPE_SET.items():
        b = build_one(n, os.path.join(SAVES, cname + ".d2s"))
        print("%-12s %-14s %-14s %s" % (n, cname, os.path.basename(base), hashlib.sha256(b).hexdigest()))
    return 0


def conditions():
    """recipe -> [(label, predicate(f))]: the state each case needs, written apart from the recipes."""
    import mp_saves as ms

    def items(f, **kw):
        return [i for i in f["items"]["items"] if all(i.get(k) == v for k, v in kw.items())]

    def code(i):
        return i["code"].strip()

    def belt_boxes(f):
        return {i["x"]: code(i) for i in items(f, location=2)}

    lvl = lambda f: f["header"]["level"]  # noqa: E731
    return {
        "sw8-nova": [("Act I Normal start", lambda f: list(f["header"]["difficulty"]) == [128] * 3),
                     ("Nova (skills.txt Id 48) on the right button", lambda f: f["header"]["mouse"][1] == 48),
                     ("a belt with a mana column", lambda f: belt_boxes(f).get(3) == "mp5")],
        "sw8-h2": [("life below a fifth of its maximum", lambda f: ms.stat(f, 6) * 5 < ms.stat(f, 7)),
                   ("mana below a fifth of its maximum", lambda f: ms.stat(f, 8) * 5 < ms.stat(f, 9)),
                   ("page 0: hp1 hp4 hp5 hp2 mp1 mp4 mp5 mp2 mp3 mp3 in cells 0..9",
                    lambda f: ms.page0(f) == sorted(zip(["hp1", "hp4", "hp5", "hp2", "mp1", "mp4", "mp5", "mp2", "mp3", "mp3"],
                                                        range(10), [0] * 10)))],
        "sw8-h3": [("a living hireling", lambda f: f["header"]["merc_seed"] != 0 and not f["header"].get("merc_dead")),
                   ("belt boxes 0..3 and 5: mp1 hp1 rvs yps wms",
                    lambda f: belt_boxes(f) == {0: "mp1", 1: "hp1", 2: "rvs", 3: "yps", 5: "wms"}),
                   ("page 0 cells 0..4: mp1 hp1 rvs yps wms",
                    lambda f: ms.page0(f) == sorted(zip(["mp1", "hp1", "rvs", "yps", "wms"], range(5), [0] * 5))),
                   ("expansion", lambda f: bool(f["header"]["status"] & 0x20))],
        "sw8-b8room": [("hbl worn, all 16 boxes filled", lambda f: sorted(belt_boxes(f)) == list(range(16))),
                       ("page 0 empty", lambda f: ms.page0(f) == []),
                       ("life 5 of 60", lambda f: ms.stat(f, 6) >> 8 == 5 and ms.stat(f, 7) >> 8 == 60)],
        "sw8-b8full": [("hbl worn, all 16 boxes filled", lambda f: sorted(belt_boxes(f)) == list(range(16))),
                       ("page 0 full: 40 1x1 items", lambda f: len(ms.page0(f)) == 40),
                       ("life 5 of 60", lambda f: ms.stat(f, 6) >> 8 == 5 and ms.stat(f, 7) >> 8 == 60)],
        "sw8-xs": [("Paladin", lambda f: f["header"]["cls"] == 3),
                   ("Conversion (skills.txt Id 116) on the right button", lambda f: f["header"]["mouse"][1] == 116),
                   ("level >= 24 (Conversion's reqlevel)", lambda f: lvl(f) >= 24)],
    }


def cmd_check():
    import d2s
    t = d2s.Tables(os.path.join(ROOT, EXCEL))
    tmp = tempfile.mkdtemp(prefix="sweep8-")
    bad = 0
    try:
        cond = conditions()
        for n in RECIPE_SET:
            f = d2s.parse(build_one(n, os.path.join(tmp, n + ".d2s")), t.isc, t.kinds)
            errs = [lab for lab, p in cond[n] if not p(f)]
            bad += bool(errs)
            print("%-12s %-14s %s" % (n, f["header"]["name"], "ok" if not errs else "FAIL " + "; ".join(errs)))
    finally:
        shutil.rmtree(tmp)
    print("SURVEY sweep8_sessions recipes=%d bad=%d sessions=%d" % (len(RECIPE_SET), bad, len(SESSIONS)))
    return 1 if bad else 0


def run(slot, tag, run_id, names, dev=False):
    if os.path.isdir(NOARM) and os.listdir(NOARM):
        print("refusing: %s is not empty (inventory.py's arm file must not exist)" % NOARM)
        return 2
    os.makedirs(NOARM, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    runname = ("dev-" if dev else "") + run_id
    out = open(os.path.join(LOGS, "%s-s%d.pilot.txt" % (runname, slot)), "a")
    shots = os.path.join("workspace", "logs", "sweep8", "%s-s%d-shots" % (runname, slot))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    xd = [*hr.PY, os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
    py = [*hr.PY, os.path.join(HERE, "d2pilot.py")]
    status = os.path.join(LOGS, "%s-s%d.status.json" % (runname, slot))

    def run_case(name):
        recipe, gdb, steps, seed, ready, todo, env = SESSIONS[name]
        os.environ.update({"INV_SLOT": str(slot), "INV_RUNTIME": NOARM}, **env)
        stem = hr.new_stem(LOGS, runname, slot, seed, name)
        log = stem + ".log"
        save = os.path.join(SAVES, RECIPE_SET[recipe][1] + ".d2s")
        hr.stop(slot, None, out=out)
        hr.install(slot, tag, out=out)
        drv = hr.launch(slot, seed, log, gdb=gdb, steps=steps, after=3000, install=(tag, [save]), out=out, stem=stem)
        hr.mark(stem, name, "start", log, "launch seed=%d recipe=%s" % (seed, recipe))
        r = hr.wait_ready(log, ready, 180, proc=drv, tick=lambda: hr.hide_window(slot))
        ok = r == hr.READY and hr.wait_count(log, "PLR", 1, 180, drv)
        hr.mark(stem, name, "ready" if ok else "fail", log, r)
        try:
            if not ok:
                return ("failed", "no PLR (%s)" % r)
            time.sleep(3)
            for step in todo:
                k = step[0]
                if k == "wait":
                    time.sleep(step[1])
                elif k == "keys":
                    for key in step[1]:
                        hr.sh(xd + ["key", key], 30, out)
                        time.sleep(step[2])
                elif k == "shiftkey":
                    hr.sh(xd + ["keydown", "Shift_L"], 30, out)
                    time.sleep(0.05)
                    hr.sh(xd + ["key", step[1]], 30, out)
                    time.sleep(0.05)
                    hr.sh(xd + ["keyup", "Shift_L"], 30, out)
                    time.sleep(step[2])
                elif k in ("click", "rclick"):
                    hr.sh(xd + [k, str(step[1]), str(step[2])], 30, out)
                    time.sleep(step[3])
                elif k == "shot":
                    hr.sh(xd + ["shot", os.path.join(shots, "%s-%s.png" % (name, step[1]))], 30, out)
                elif k == "pilot":
                    hr.sh(py + [step[1][0], log, "--slot", str(slot)] + step[1][1:] + ["--shots", shots], step[2], out)
                elif k == "p12go":
                    import sweep8_check
                    pk = sweep8_check.pick(log, near_player=True)
                    with open(stem + ".pick.json", "w") as pf:      # a case mark has a fixed event set
                        pf.write(json.dumps(pk) + "\n")
                    if pk:
                        for _ in range(step[1]):
                            p = sweep8_check.last_pos(log)
                            dx, dy = pk["stand"][0] - p[0], pk["stand"][1] - p[1]
                            if max(abs(dx), abs(dy)) <= 1:
                                break
                            f = min(1.0, 10.0 / max(abs(dx), abs(dy)))
                            hr.sh(py + ["hop", log, str(int(round(dx * f))), str(int(round(dy * f))), "--slot", str(slot)],
                                  60, out)
                            time.sleep(0.8)
                elif k == "nova":
                    for _ in range(step[1]):
                        hr.sh(xd + ["key", "F1"], 30, out)
                        hr.sh(xd + ["keydown", "Shift_L"], 30, out)
                        hr.sh(xd + ["rhold", "400", "290", "1.6"], 30, out)   # d2pilot.py's --cx/--cy
                        hr.sh(xd + ["keyup", "Shift_L"], 30, out)
                        time.sleep(0.4)
            hr.mark(stem, name, "end", log, "steps done")
            return ("kept", "log %s" % os.path.basename(log))
        finally:
            hr.stop(slot, drv, out=out)

    try:
        st = hr.batch(names, run_case, status, reruns=0, stage=hr.NO_SHARING)
    finally:
        out.close()
    print(hr.summary(st))
    return 0 if st["done"] and not st["failed"] else 1


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "build", "check", "run"])
    ap.add_argument("names", nargs="*")
    ap.add_argument("--slot", type=int)
    ap.add_argument("--tag")
    ap.add_argument("--run")
    ap.add_argument("--dev", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for n, s in SESSIONS.items():
            print("%-8s recipe %-11s logger %-26s seed %5d steps %d" % (n, s[0], s[1], s[3], len(s[5])))
        return 0
    if a.cmd == "build":
        return cmd_build()
    if a.cmd == "check":
        return cmd_check()
    if not a.slot or not a.tag or not a.run or not a.names or any(n not in SESSIONS for n in a.names):
        ap.error("run needs --slot N (not 0), --tag, --run and known SESSION names")
    return run(a.slot, a.tag, a.run, a.names, dev=a.dev)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

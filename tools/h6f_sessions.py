#!/usr/bin/env python3
"""Plan 0038 batch H6f (hirelings, run:2026-10-27-sweep-hirelings): recipes, predictions and sessions on one harness
slot, logged with tools/gdb/h6f.gdb (tools/gdb/hirelings.gdb's loggers plus tools/gdb/h6f.py).

    python3 -I tools/h6f_sessions.py write                  # tools/d2s_recipes/h6f-*.json and the built saves
    python3 -I tools/h6f_sessions.py plan                   # the seeded predictions the sessions are chosen by
    python3 -I tools/h6f_sessions.py run SESSION --slot N --tag TAG --seed S --log LOG [--shots DIR]

Recipes (ADR-0003 tool-built inputs on stock tables; each built from an existing recipe, the changes named in RECIPES;
built states the game's own play does not make are marked "test state" there and in the run record). Saves go to
workspace/logs/h6f/saves/<Name>/<Name>.d2s, one character per directory.

Sessions (one game each; every one ends with tools/slots.py stop N and tools/saves.py restore TAG):
  ash     Act IV start, the town waypoint to Act III; Asheara's trade first (NPC_OpenStore), then her hire list and
          eight top-row hires (the seed lists name 1057 eighth: the client's 1057 -> 11021 string, list and merc init)
  floor   Act I start at clvl 3, quest word 2 bit 0 clear: Kashya's list (the level floor) and a refused hire
  free    Act I start at clvl 3, word 2 bit 1 set (the reward pending), no mercenary: Kashya's quest gift, then a hire
  lvlup   Act I start at clvl 7 one point below level 8, word 2 bit 0 clear: Kashya's menu (no hire line below 8);
          Cold Plains, Nova until a kill levels the player; back, a hire at level 8
  lvl30   Act I start at clvl 30 one point below level 31: Kashya's list drawn at 30, Cold Plains kills, back, a hire
          at 31 (the entry drawn at 30, rolled at 31)
  qk      Act IV start, word 36 bit 0 clear, 100 gold and a stash sized by `plan`: Qual-Kehk's refused hire, then two
          Asheara hires (the first takes the rest from the stash, the second is refused for gold)
  cl1/cl2/cl3  classic, the start act 1/2/3: the seller's list and a hire (Kashya, Greiz, Asheara)
  cl2w    classic, the Act I start, the waypoint to Act II (the classic 4-tab menu), then Greiz's list and a hire
          (cl2 started in Lut Gholein, where the pilot found neither Greiz nor the waypoint)
  mact    MercNova (a loaded Rogue): Kashya's list, then the waypoint to Act II and a Greiz hire, then back to Act I
  dead    a dead mercenary loaded (Act IV start), then Kashya's resurrect line (Qual-Kehk's was run:2026-10-17-economy's)
  hexp    Hell, a level-10 Rogue one point below level 11 with a clvl 80 Nova build: Cold Plains kills
  qkh     H6fAsh (every quest done): one Qual-Kehk hire (the word-36 read that passes)
  hx3, hx85  as hexp with a Rogue at L 3 (the cap binds) and at L 85 (above its clvl 80 owner)
  n99     Normal: a mercenary past level 99's experience and a name id past its row's range (test state), the
          Cold Plains waypoint, the mercenary fights
Stdlib only.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import hireling_sessions as hs  # noqa: E402

PY = [sys.executable, "-I"]
EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
SAVES = os.path.join(ROOT, "workspace", "logs", "h6f", "saves")
EXP_BASE = os.path.join(ROOT, "workspace", "samples", "d2s-owner", "smpsor-l50.d2s")
CLS_BASE = os.path.join(ROOT, "workspace", "runtime", "monspawn-chars", "cls", "smpsor.d2s")
GDB = "tools/gdb/h6f.gdb"

LOW = {"level": 3, "experience": 2000, "gold": 20000, "goldbank": 0}
# name: (base recipe, base save, changes, note)
RECIPES = {
    "H6fAsh": ("vendornova.json", EXP_BASE, {}, "VendorNova as it is"),
    "H6fFloor": ("vendornova.json", EXP_BASE, {"stats": LOW, "difficulty": [128, 128, 128],
                                              "quest_bits": {"normal": {"2": {"clear": [0, 1, 13]}}}},
                 "clvl 3 with every quest but Act I word 2 done (test state: a clvl 3 with the later quests)"),
    "H6fFree": ("vendornova.json", EXP_BASE, {"stats": LOW, "difficulty": [128, 128, 128],
                                             "quest_bits": {"normal": {"2": {"set": [1], "clear": [0, 13]}}}},
                "clvl 3, word 2 bit 1 set and bit 0 clear (the reward pending; test state as H6fFloor)"),
    "H6fLvl": ("vendornova.json", EXP_BASE, {"stats": {"level": 7, "experience": 32885, "gold": 70000, "goldbank": 0},
                                            "difficulty": [128, 128, 128],
                                            "skills": {"Nova": 1, "Teleport": 1, "Telekinesis": 1},
                                            "mouse": {"left": "Teleport", "right": "Nova"},
                                            "quest_bits": {"normal": {"2": {"clear": [0, 1, 13]}}}},
               "clvl 7 one point below level 8 (32 886), word 2 open; Nova at clvl 7 (test state)"),
    "H6fL30": ("vendornova.json", EXP_BASE, {"stats": {"experience": 5493362}, "difficulty": [128, 128, 128],
                                            "skills": {"Nova": 1, "Teleport": 1, "Telekinesis": 1},
                                            "mouse": {"left": "Teleport", "right": "Nova"}},
               "VendorNova one point below level 31's threshold (5 493 363), Act I start, Nova at level 1"),
    "H6fQk": ("vendornova.json", EXP_BASE, {"stats": {"gold": 100}, "quest_bits": {"normal": {"36": {"clear": [0]}}}},
              "word 36 bit 0 clear, 100 gold; the stash from `plan` (goldbank)"),
    "H6fCl1": ("mercclassic.json", CLS_BASE, {"difficulty": [128, 128, 128], "merc": None}, "classic, Act I, no merc"),
    "H6fCl2": ("mercclassic.json", CLS_BASE, {"difficulty": [129, 129, 129], "merc": None}, "classic, Act II, no merc"),
    "H6fCl3": ("mercclassic.json", CLS_BASE, {"difficulty": [130, 130, 130], "merc": None}, "classic, Act III, no merc"),
    "H6fMact": ("mercnova.json", EXP_BASE, {}, "MercNova as it is (Rogue Id 0, name 3, 2 790 000)"),
    "H6fDead": ("mercnova.json", EXP_BASE, {"merc": {"id": 0, "seed": 12345, "name": 3, "exp": 2790000, "dead": True}},
                "MercNova with the dead bit (no items: a dead mercenary's list is empty here)"),
    "H6fHexp": ("uniqnova.json", EXP_BASE, {"merc": {"id": 0, "seed": 24680, "name": 5, "exp": 145199, "dead": False}},
                "UniqNova (clvl 80) with a Rogue at L 10, one point below ExpForLevel(11, 100) = 145 200"),
    "H6fHx3": ("uniqnova.json", EXP_BASE, {"merc": {"id": 0, "seed": 24681, "name": 6, "exp": 7999, "dead": False}},
               "UniqNova with a Rogue at L 3, one point below ExpForLevel(4, 100) = 8 000 (the cap is 68 there)"),
    "H6fHx85": ("uniqnova.json", EXP_BASE, {"merc": {"id": 0, "seed": 24682, "name": 7, "exp": 62200000,
                                                     "dead": False}},
                "UniqNova (clvl 80) with a Rogue at L 85, above its owner (ExpForLevel(85, 100) = 62 135 000)"),
    "H6fN99": ("mercnova.json", EXP_BASE, {"merc": {"id": 0, "seed": 13579, "name": 50, "exp": 150000000,
                                                    "dead": False, "name_unchecked": True}},
               "MercNova's Rogue with experience 150 000 000 (> ExpForLevel(100, 100) = 101 000 000) and name id 50 "
               "(the row's range is 0..40; test state, name_unchecked)"),
}
SESSION_SAVE = {"ash": "H6fAsh", "floor": "H6fFloor", "free": "H6fFree", "lvlup": "H6fLvl", "lvl30": "H6fL30", "qk": "H6fQk",
                "cl1": "H6fCl1", "cl2": "H6fCl2", "cl3": "H6fCl3", "mact": "H6fMact", "dead": "H6fDead",
                "hexp": "H6fHexp", "n99": "H6fN99", "qkh": "H6fAsh", "hx3": "H6fHx3", "hx85": "H6fHx85", "cl2w": "H6fCl1"}
QK_SEED = 6631


def recipe(name):
    base_rc, base, ch, _ = RECIPES[name]
    with open(os.path.join(HERE, "d2s_recipes", base_rc)) as fh:
        rc = json.load(fh)
    rc["name"] = name
    for k, v in ch.items():
        if k == "stats":
            rc["stats"] = dict(rc["stats"], **v)
        elif v is None:
            rc.pop(k, None)
        else:
            rc[k] = v
    if name == "H6fQk":
        rc["stats"]["goldbank"] = plan_qk()["bank"]
    return rc, base


def cmd_write(ns):
    sys.path.insert(0, HERE)
    import d2s
    for name in RECIPES:
        rc, base = recipe(name)
        path = os.path.join(HERE, "d2s_recipes", "h6f-%s.json" % name[3:].lower())
        with open(path, "w") as fh:
            json.dump(rc, fh, indent=2)
            fh.write("\n")
        d = os.path.join(SAVES, name)
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, name + ".d2s")
        with contextlib.redirect_stdout(io.StringIO()):
            d2s.build(EXCEL, rc, base, dst)
        with open(dst, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        with open(path, "rb") as fh:
            rsha = hashlib.sha256(fh.read()).hexdigest()
        print("%-9s recipe %s %s  save %s" % (name, os.path.relpath(path, ROOT), rsha[:8], sha))
    return 0


def npc_seed(t, n):
    import hirelings as h
    s = h.Seed(n)
    s.step()
    s.step()
    return h.Seed(s.step())


def plan_qk(seed=QK_SEED):
    """Qual-Kehk's build, then Asheara's (clvl 30, Normal, expansion): the first two listed names' prices; the
    stash that pays the first with 100 gold and leaves the second short."""
    import hirelings as h
    t = h.Tables(EXCEL)
    S = npc_seed(t, seed)
    h.build_stock(t, S, 515, 1)
    tab, _ = h.build_stock(t, S, 252, 1)
    listed = [e for e in tab if e[3]]
    pr = []
    for e in listed[:2]:
        _, o = h.roll_entry(t, 1, 30, e[1], t.get_act(1, e[0]), 0)
        pr.append(o[5])
    bank = pr[0] - 100 + 10
    return {"seed": seed, "names": [e[0] for e in listed[:2]], "prices": pr, "bank": bank}


def cmd_plan(ns):
    import hirelings as h
    t = h.Tables(EXCEL)
    S = npc_seed(t, 6602)
    tab, _ = h.build_stock(t, S, 252, 1)
    listed = [e[0] for e in tab if e[3]]
    print("ash 6602: Asheara's first build lists %s; 1057 is row %d" % (listed, listed.index(1057) + 1))
    q = plan_qk()
    print("qk %d: Asheara after Qual-Kehk lists first %s, prices %s at clvl 30; gold 100, stash %d "
          "(first: 100 + %d; second short by %d)" % (q["seed"], q["names"], q["prices"], q["bank"],
                                                     q["prices"][0] - 100, q["prices"][1] - 10))
    for n, e in ((10, 100), (11, 100), (99, 100), (100, 100)):
        print("ExpForLevel(%d, %d) = %d" % (n, e, h.exp_for_level(n, e)))
    print("n99: load level %d (cap 99)" % h.load_level(t, 1, 0, 150000000))
    print("hexp: load level %d" % h.load_level(t, 1, 0, 145199))
    return 0


def launch(ns, steps, after):
    hs.tool(["saves.py", "--slot", str(ns.slot), "restore", ns.tag])
    hs.tool(["saves.py", "--slot", str(ns.slot), "aside", ns.tag])
    out = open(ns.log + ".d2run.out", "w")
    cmd = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(ns.slot), "--seed", str(ns.seed), "--gdb", GDB,
                "--steps", steps, "--after", str(after), "--install", ns.tag, ns.save, "--log", ns.log]
    print("+ " + " ".join(cmd), flush=True)
    subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     start_new_session=True)


def npc(ns, who, action, *extra, timeout=300):
    shots = ["--shots", ns.shots] if ns.shots else []
    return hs.pilot(ns, "npc", ns.log, who, action, *extra, *shots, timeout=timeout)


def town(ns, who):
    ok = hs.go_town(ns, who)
    if not ok:
        print("h6f: did not reach the town of %s" % who)
    return ok


def to_wp(ns, chain):
    hs.pilot(ns, "npc", ns.log, "waypoint", "walk", timeout=90)
    hs.pilot(ns, "wpchain", ns.log, "--chain", chain, timeout=30)
    time.sleep(2)


def explore(ns, secs, *extra):
    t0 = time.time()
    while time.time() - t0 < secs:
        hs.pilot(ns, "explore", ns.log, "--hops", "6", "--nova", "2", *extra, timeout=120)


def s_ash(ns):
    if town(ns, "asheara"):
        npc(ns, "asheara", "trade")
        npc(ns, "asheara", "hire", "--repeat", "8", "--buy", "1", timeout=1200)


def s_floor(ns):
    npc(ns, "kashya", "hire", "--buy", "1")


def s_free(ns):
    npc(ns, "kashya", "hire")
    time.sleep(2)
    npc(ns, "kashya", "hire", "--buy", "1")


def s_lvlup(ns):
    npc(ns, "kashya", "hire", "--buy", "1")
    to_wp(ns, "1,2")
    explore(ns, 90)
    to_wp(ns, "1,1")
    npc(ns, "kashya", "hire", "--buy", "1")


def s_lvl30(ns):
    npc(ns, "kashya", "hire")
    to_wp(ns, "1,2")
    explore(ns, 60)
    to_wp(ns, "1,1")
    npc(ns, "kashya", "hire", "--buy", "1")


def s_qk(ns):
    if town(ns, "qual-kehk"):
        npc(ns, "qual-kehk", "hire", "--buy", "1")
    if town(ns, "asheara"):
        npc(ns, "asheara", "hire", "--repeat", "2", "--buy", "1", timeout=600)


def s_cl2w(ns):
    hs.pilot(ns, "npc", ns.log, "waypoint", "walk", timeout=90)
    hs.pilot(ns, "wpchain", ns.log, "--chain", "2,1", "--wp-tab-x0", "120", "--wp-tab-w", "78", timeout=30)
    time.sleep(2)
    if hs.TOWNS.get(hs.level(ns.log)) == 2:
        npc(ns, "greiz", "hire", "--buy", "1")
    else:
        print("h6f: not in Lut Gholein")


def s_qkh(ns):
    if town(ns, "qual-kehk"):
        npc(ns, "qual-kehk", "hire", "--buy", "1")


def s_classic(who):
    def f(ns):
        if who == "greiz":      # Greiz's usual place is an offset from the town waypoint: walk there first
            hs.pilot(ns, "npc", ns.log, "waypoint", "walk", timeout=90)
        npc(ns, who, "hire", "--buy", "1")
    return f


def s_mact(ns):
    if town(ns, "kashya"):
        npc(ns, "kashya", "hire")
    if town(ns, "greiz"):
        npc(ns, "greiz", "hire", "--buy", "1")
    town(ns, "kashya")
    time.sleep(5)


def s_dead(ns):
    if town(ns, "kashya"):
        npc(ns, "kashyares", "resurrect")
        time.sleep(3)


def s_hexp(ns):
    to_wp(ns, "1,2")
    explore(ns, ns.time, "--es", "30")


def s_n99(ns):
    to_wp(ns, "1,2")
    t0 = time.time()
    while time.time() - t0 < ns.time:
        if len(hs.lines(ns.log, "AX0")) >= 3:
            break
        hs.pilot(ns, "explore", ns.log, "--hops", "3", "--nova", "0", "--walk", timeout=60)
        time.sleep(6)


SESSIONS = {"ash": s_ash, "floor": s_floor, "free": s_free, "lvlup": s_lvlup, "lvl30": s_lvl30, "qk": s_qk,
            "cl1": s_classic("kashya"), "cl2": s_classic("greiz"), "cl3": s_classic("asheara"), "mact": s_mact,
            "dead": s_dead, "hexp": s_hexp, "n99": s_n99, "qkh": s_qkh, "hx3": s_hexp, "hx85": s_hexp, "cl2w": s_cl2w}


def cmd_run(ns):
    ns.save = os.path.join(SAVES, SESSION_SAVE[ns.session], SESSION_SAVE[ns.session] + ".d2s")
    steps = hs.STEPS["hell" if ns.session in ("hexp", "hx3", "hx85") else "normal"]
    launch(ns, steps, 3000)
    try:
        if not hs.wait_for(ns.log, "PLR", 150):
            print("h6f: no PLR line; giving up")
            return 1
        time.sleep(4)
        SESSIONS[ns.session](ns)
        time.sleep(2)
        return 0
    finally:
        hs.stop(ns)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("write", "plan", "run"))
    ap.add_argument("session", nargs="?", choices=sorted(SESSIONS))
    ap.add_argument("--slot", type=int, default=2)
    ap.add_argument("--tag", default="h6f")
    ap.add_argument("--seed", type=int, default=6600)
    ap.add_argument("--log")
    ap.add_argument("--shots", default="")
    ap.add_argument("--time", type=float, default=150)
    ns = ap.parse_args(argv)
    if ns.cmd == "run" and (not ns.session or not ns.log):
        ap.error("run needs SESSION and --log")
    return {"write": cmd_write, "plan": cmd_plan, "run": cmd_run}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6b (sockets): one game per session on one slot, logged by
tools/gdb/h6b.gdb (pilot.py, vendors.py, quests.py, the plan 0029 sockets.py, and h6b.py), driven by
tools/d2pilot.py insert (inventory clicks), tools/d2pilot.py npc (Anya's personalize, Malah's trade window) and
tools/economy_sessions.py act (a sale in the open trade window). The session loop is plan 0038 H6e1's
(tools/h6e1_sessions.py).

Usage:
  python3 -I tools/h6b_sessions.py write [--excel DIR]   # tools/d2s_recipes/sock-h6b-<name>.json and
                                                        # tools/gdb/sock-h6b-<name>.plan (tools/socket_sessions.py's
                                                        # layout)
  python3 -I tools/h6b_sessions.py list
  python3 -I tools/h6b_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

A SESSION row names its save (<DIR>/<Name>.d2s, built with tools/d2s.py build from its recipe; a path starting
"workspace/" is used as it is: the game-written sample), the steps file, the map seed and the commands. Logs go to
workspace/logs/h6b/<RUN>-s<slot>-<seed>-<SESSION>.log with the pilot's output beside it (.pilot.txt). The slot is
stopped after each session (tools/slots.py stop N) and its saves directory returned to the TAG aside first. Nothing
here feeds a model: the pilot only decides where to click.
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

import props  # noqa: E402
import socket_sessions as SS  # noqa: E402

PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6b")
GDB = os.path.join(HERE, "gdb", "h6b.gdb")
J, runes, gems = SS.J, SS.runes, SS.gems

# ------------------------------------------------------------------------------------------------ the characters
# name: (recipe base, jobs, tries, extra) as tools/socket_sessions.py's layout takes them; "base" is the recipe the
# character comes from ("socketnova": the level-80 Sorceress; "low": the level-1 Barbarian of the qitbarb sample,
# keep_items [], so the sample's own items and the Steel sword are not in it)
LAYOUTS = {
    # sock 21 (no level test for the child), sock 38 (funcs 17 with par 0, 20, 24), sock 18 (stat 252), sock 16
    # (x, y), sock 17 (the cursor clear), sock 29 (equipped parents: the link branch)
    "low": ("low", [J("qui", runes("Mal Tir"), "tors"),                 # Prudence: rep-dur (stat 252)
                    J("lbw", runes("Ohm Jah Lem Eld"), "rarm"),         # Faith: reanimate (func 24)
                    J("aar", runes("El Sol Dol Lo")),                   # Fortitude: hp/lvl 8-12 (func 17, par 0)
                    J("lsd", runes("Amn Lem Ko")),                      # Lawbringer: dmg-cold 130-180 (func 17)
                    J("lsd", runes("Shael Pul Mal Lum"))], (), None),   # Oath: indestruct (func 20)
    # the non-server rows of sock 38: Eternity (indestruct, func 20) and Leaf (ac/lvl, func 17 with par 0, min = max)
    # (the four rows of "low" other than Prudence are server rows: inserted, no runeword in a non-ladder game)
    "low2": ("low", [J("crs", runes("Amn Ber Ist Sol Sur")),           # Eternity
                     J("sst", runes("Tir Ral"))], (), None),            # Leaf
    # the client's refusals (sock 9-13) and the S2c piece of sock 14 (an unidentified socketed parent identified)
    "refuse": ("socketnova", [
        J("skp", [{"code": "gcy"}], identified=False, suffix=SS.SFX_HELM, sockets=2),   # refused, then identified
        J("rin", [], forced_sockets=True, sockets=1, loose=False),     # built state: bit 11 on a ring
        J("lgl", [], forced_sockets=True, sockets=1, loose=False),     # built state: bit 11 on gloves (hasinv 0)
        J("cap", [], dur=0, broken=True, sockets=1),                   # built state: broken (bit 8)
        J("ghm", [{"code": "gpv"}], "head"),                           # an equipped parent
        J("uit", [{"code": "gpb"}], "larm")],
        [("gfv", "rin"), ("gfv", "lgl"), ("gfv", "cap")],
        {"stock": [{"code": "isc"}, {"code": "gcy"}],
         "tokens": ["rclick:{0}", "click:{skp}", "sleep:1", "shot:workspace/logs/h6b/refuse-identified.png",
                    "{1}>{skp}"]}),
}

# the Act V characters (written directly: they are not insert layouts)
SVC_ITEMS = [
    {"code": "cap", "sockets": 1, "filled": [{"code": "gsv"}], "store": "inventory", "x": 0, "y": 0},   # sold
    {"code": "cap", "sockets": 2, "filled": [{"code": "gsy"}, {"code": "r01"}], "store": "inventory", "x": 2,
     "y": 0},                                                                                           # personalized
    {"code": "skp", "sockets": 2, "filled": [{"code": "jew", "suffix": 260}], "store": "inventory", "x": 4, "y": 0},
]


def low_recipe():
    """The qitbarb sample's level-1 Barbarian (its stats as the sample holds them), without its items."""
    return {"game": "expansion", "class": "Barbarian", "keep_items": [],
            "stats": {"strength": 30, "energy": 10, "dexterity": 20, "vitality": 25, "hitpoints": 55, "maxhp": 55,
                      "mana": 10, "maxmana": 10, "stamina": 92, "maxstamina": 92, "level": 1}}


def svc_recipe():
    """The level-80 Sorceress of tools/d2s_recipes/quest-h6e1-svca.json (plan 0038 H6e1), Act V start, with Anya's
    reward bit (word 38 bit 1) as that recipe sets it, and three socketed items holding children."""
    with open(os.path.join(SS.RECIPES, "quest-h6e1-svca.json")) as f:
        r = json.load(f)
    r["items"] = [i for i in r["items"] if "equip" in i] + SVC_ITEMS
    r["name"] = "SockSvc"
    r["seed"] = 381160001
    return r


def cmd_write(ns):
    T = props.Tables(ns.excel)
    for i, (name, (base, jobs, tries, extra)) in enumerate(LAYOUTS.items()):
        items, plan = SS.layout(T, "h6b-" + name, jobs, tries, extra)
        # the layout writes the job keys it knows; the H6b test-state keys go on the base items as the jobs say
        for j in jobs:
            for it in items:
                if it.get("code") == j["base"] and "sockets" in it:
                    for k in ("forced_sockets", "dur", "broken"):
                        if k in j:
                            it[k] = j[k]
        r = SS.base_recipe() if base == "socketnova" else low_recipe()
        r["name"] = "SockH" + name[0].upper() + name[1:]
        r["seed"] = 381150001 + i
        r["items"] = items
        with open(os.path.join(SS.RECIPES, "sock-h6b-%s.json" % name), "w") as f:
            json.dump(r, f, indent=1)
            f.write("\n")
        plan = [t.replace("workspace/logs/sock-", "workspace/logs/h6b/sock-") for t in plan]
        with open(os.path.join(SS.PLANS, "sock-h6b-%s.plan" % name), "w") as f:
            f.write("# tools/d2pilot.py insert tokens for tools/d2s_recipes/sock-h6b-%s.json (tools/h6b_sessions.py)\n"
                    % name)
            f.write("\n".join(plan) + "\n")
        print("%-8s %-12s %2d items, %2d inserts" % (name, r["name"], len(items), sum(">" in t for t in plan)))
    r = svc_recipe()
    with open(os.path.join(SS.RECIPES, "sock-h6b-svc.json"), "w") as f:
        json.dump(r, f, indent=1)
        f.write("\n")
    print("svc      %-12s %2d items" % (r["name"], len(r["items"])))
    return 0


# ------------------------------------------------------------------------------------------------ the sessions

def plan(name):
    with open(os.path.join(SS.PLANS, "sock-h6b-%s.plan" % name)) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


def ins(tokens, t=400):
    return ("pilot", ["insert"] + list(tokens), t)


def svc(npc, action, item, t=300):
    return ("pilot", ["npc", npc, action, "--item", item, "--npc-time", "150"], t)


def trade(npc, tokens, t=300):
    return ("trade", [npc] + list(tokens), t)


def wait(s):
    return ("xd", ["sleep %d" % s], 0)


STEEL = "workspace/samples/d2s/qitbarb.d2s"
# name: (save, steps file, map seed, commands)
SESSIONS = {
    # the game-written Steel sword loaded (sock 35, 46, 17), then the sample's jewel tried on it (the client's copy)
    "steel": (STEEL, "sock-enter", 6101, [wait(4), ins(["key:i", "inv:7,3>inv:0,0,2,3",
                                                        "shot:workspace/logs/h6b/steel-end.png"]), wait(2)]),
    "low": ("SockHLow", "sock-enter", 6102, [wait(3), ("plan", "low", 600), wait(3)]),
    "low2": ("SockHLow2", "sock-enter", 6105, [wait(3), ("plan", "low2", 400), wait(3)]),
    "refuse": ("SockHRefuse", "sock-enter", 6103, [wait(3), ("plan", "refuse", 600), wait(3)]),
    # Act V: the gem-holding cap sold to Malah (NPC_SellItem's copy), the cap holding a gem and a rune personalized
    "svc": ("SockSvc", "enter-normal", 6104, [trade("malah", ["sell:0,0", "sleep:2"]),
                                              svc("anya", "personalize", "inv:2,0,2,2"), wait(3)]),
}


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


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


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
    path = os.path.join(ROOT, save) if save.startswith("workspace/") else os.path.join(saves, save + ".d2s")
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
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 GDB, "--steps", os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "1800",
                                 "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
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
    for kind, args, timeout in cmds:
        rc = None
        if kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    (["--shots", shots] if args[0] == "npc" else []), timeout, out)
        elif kind == "plan":
            # the plan's own shot tokens name workspace/logs/h6b/...; the pilot writes them on slot N with -sN
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), "insert", log, "--slot", str(slot)] + plan(args), timeout,
                    out)
        elif kind == "trade":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), "npc", log, args[0], "trade", "--stay", "--slot",
                          str(slot), "--shots", shots, "--npc-time", "150"], timeout, out)
            if rc == 0:
                rc = sh(PY + [os.path.join(HERE, "economy_sessions.py"), "--slot", str(slot), "act"] + args[1:],
                        120, out)
                sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "shot",
                         os.path.join(shots, "trade-end.png")], 30, out)
                sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "key",
                         "Escape"], 30, out)
                time.sleep(1.5)
        elif kind == "xd":
            for c in args:
                if c.startswith("sleep "):
                    time.sleep(float(c.split()[1]))
                    continue
                sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + c.split(),
                   30, out)
            rc = 0
        print("  -> %s" % rc, flush=True)
    sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "shot",
             os.path.join(shots, "end.png")], 30, out)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if argv and argv[0] == "write":
        ap = argparse.ArgumentParser()
        ap.add_argument("cmd")
        ap.add_argument("--excel", default=props.EXCEL)
        return cmd_write(ap.parse_args(argv))
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-8s %-36s %-12s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
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

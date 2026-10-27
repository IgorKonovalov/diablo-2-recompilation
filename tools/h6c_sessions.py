#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6c (vendors): one game per session on one slot, logged by
tools/gdb/h6c.gdb (pilot.py, uniques.py, affixes.py, vendors.py and h6c.py), driven by tools/d2pilot.py npc (the
trade, gamble and hire windows), tools/economy_sessions.py act (purchases and sales in an open window), d2pilot.py
farm, explore and wpchain. The session loop is plan 0038 H6b's (tools/h6b_sessions.py).

Usage:
  python3 -I tools/h6c_sessions.py write              # tools/d2s_recipes/vend-h6c-<name>.json
  python3 -I tools/h6c_sessions.py list
  python3 -I tools/h6c_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

A SESSION row names its save (<DIR>/<Name>.d2s, built with tools/d2s.py build from its recipe), the steps file, the
map seed and the commands. Logs go to workspace/logs/h6c/<RUN>-s<slot>-<seed>-<SESSION>.log with the pilot's output
beside it (.pilot.txt). The slot is stopped after each session (tools/slots.py stop N) and its saves directory returned
to the TAG aside first.

Window tokens (inside a trade or gamble window opened with d2pilot.py npc --stay), resolved from the log at the moment
they run and handed to economy_sessions.py act:
  BUY:<what>   a purchase in the open trade window: the item of the NPC's stock (the last INVB or INVT line of its
               class) chosen by <what>: a code (e.g. tsc), "nonperm" (the first item whose code is not one of the
               record's permanent codes, BS0 "perm") or "any"; right-clicked at its page's tab and its cell
  GBUY         a purchase in the open gamble window: the first item of the last INVG line, right-clicked at its cell
The other tokens are economy_sessions.py's (sell:c,r, key:, sleep:, shot:). Nothing here feeds a model: the pilot only
decides where to click.
"""
import argparse
import json
import os
import struct
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6c")
GDB = os.path.join(HERE, "gdb", "h6c.gdb")
RECIPES = os.path.join(HERE, "d2s_recipes")

# ------------------------------------------------------------------------------------------------ the characters
UNIQ = "uniqnova.json"          # the reference Nova build (harness-play.md): stats, skills, hotkeys, belt


def uniq_base():
    """uniqnova.json without its inventory (the charms): its equipped items stay (the belt for belt_fill)."""
    with open(os.path.join(RECIPES, UNIQ)) as f:
        r = json.load(f)
    r["items"] = [i for i in r["items"] if "equip" in i]
    return r


def inv(code, x, y):
    return {"code": code, "store": "inventory", "x": x, "y": y}


def recipe_low():
    """A level-1 Sorceress in the Act I town (every difficulty open, every quest done, as the vendor saves), 10 000 gold
    (the level-1 cap) and 2 000 000 in the stash; to sell: a Super Healing Potion, a Scroll of Town Portal, a cap."""
    r = uniq_base()
    r.update(name="VendH6cLow", seed=382010001, difficulty=[128, 128, 128], keep_items=[])
    r["stats"].update(level=1, experience=0, gold=10000, goldbank=2000000)
    r["items"] = [inv("hp5", 0, 0), inv("tsc", 1, 0), inv("cap", 2, 0)]
    r.pop("belt_fill", None)
    r.pop("hotkeys", None)
    return r


def recipe_lvl():
    """The Nova build at level 30 in the Act IV town (the -a4 start: the Pandemonium Fortress's waypoint at a fixed
    screen position), one experience point short of experience.txt's row 31 (6 397 855), for a level-up between two
    trade opens (run:2026-10-27-sweep-vendors: the first kill's experience took it to level 32)."""
    r = uniq_base()
    r.update(name="VendH6cLvl", seed=382010002, difficulty=[131, 131, 131], keep_items=[])
    r["stats"].update(level=30, experience=6397854, gold=300000, goldbank=2000000)
    return r


def recipe_h99(act):
    """The Nova build at level 99 (experience.txt row 99) in the town of act <act> (1-based), every difficulty open;
    to sell: a Super Healing Potion and a cap."""
    r = uniq_base()
    r.update(name="VendH6cH99" + "abcde"[act - 1], seed=382010010 + act, difficulty=[127 + act] * 3, keep_items=[])
    r["stats"].update(level=99, experience=3837739017, gold=990000, goldbank=2500000)
    r["items"] += [inv("hp5", 0, 0), inv("cap", 1, 0)]
    return r


def recipe_n19():
    """The Nova build at level 19 (experience.txt row 19) in the Act IV town: a Nightmare stock level of 24, the
    highest with normal copies (Fara's 53 entries), for a build past 32 failed creations."""
    r = uniq_base()
    r.update(name="VendH6cN19", seed=382010006, difficulty=[131, 131, 131], keep_items=[])
    r["stats"].update(level=19, experience=537513, gold=190000, goldbank=2000000)
    return r


RECIPE_FNS = {"low": recipe_low, "lvl": recipe_lvl, "h99e": lambda: recipe_h99(5), "n19": recipe_n19}


def cmd_write(ns):
    for name, fn in RECIPE_FNS.items():
        r = fn()
        with open(os.path.join(RECIPES, "vend-h6c-%s.json" % name), "w") as f:
            json.dump(r, f, indent=1)
            f.write("\n")
        print("%-5s %-12s level %d, %d items" % (name, r["name"], r["stats"]["level"], len(r["items"])))
    return 0


# ------------------------------------------------------------------------------------------------ log reading

def log_lines(log, tags):
    out = []
    try:
        for line in open(log, errors="replace"):
            t, _, rest = line.partition(" ")
            if t in tags and rest.startswith("{"):
                try:
                    out.append((t, json.loads(rest)))
                except ValueError:
                    pass
    except OSError:
        pass
    return out


_CODES = None


def code_of(idx):
    global _CODES
    if _CODES is None:
        import vendors
        T = vendors.Tables(vendors.EXCEL)
        _CODES = {i: T.code(i).decode("latin-1").strip() for i in range(len(T.items))}
    return _CODES.get(idx, "?")


def store_xy(c, r):
    return 110 + 29 * c, 138 + 29 * r


def resolve(log, cls, tok):
    """A BUY or GBUY token as economy_sessions.py act tokens (or None)."""
    if tok == "GBUY":
        g = [d for t, d in log_lines(log, ("INVG",)) if d["cls"] == cls]
        if not g or not g[-1]["items"]:
            return None
        it = g[-1]["items"][-1]
        x, y = store_xy(it[3], it[4])
        print("  GBUY: item id %s %s at (%s, %s)" % (it[0], code_of(it[1]), it[3], it[4]), flush=True)
        return ["rclick:%d,%d" % (x + 8, y + 8)]
    what = tok.split(":", 1)[1]
    ev = [(t, d) for t, d in log_lines(log, ("INVB", "INVT", "BS0")) if d.get("cls") == cls]
    perm = []
    items = None
    for t, d in ev:
        if t == "BS0":
            perm = [struct.pack("<I", c).decode("latin-1").strip() for c in d["perm"]]
        elif d.get("gamble", 0) == 0:
            items = d["items"]
    if not items:
        return None
    for it in items:
        c = code_of(it[1])
        if what == "any" or c == what or (what == "nonperm" and c not in perm):
            print("  BUY %s: item id %s %s page %s at (%s, %s)" % (what, it[0], c, it[2], it[3], it[4]), flush=True)
            return ["buy:%d:%d,%d" % (it[2] + 1, it[3], it[4])]
    return None


# ------------------------------------------------------------------------------------------------ the sessions
CLS = {"akara": 148, "gheed": 147, "charsi": 154, "drognan": 177, "larzuk": 511, "anya": 512, "malah": 513,
       "asheara": 252, "halbu": 257, "jamella": 405}


def npc(name, action, extra=(), t=240):
    return ("pilot", ["npc", name, action, "--npc-time", "150"] + list(extra), t)


def win(name, action, tokens, t=300):
    return ("win", [name, action] + list(tokens), t)


def wait(s):
    return ("xd", ["sleep %d" % s], 0)


def wp4(tab, row):
    """The waypoint from the Act IV town start at its fixed screen position (plan 0038 H4a, H6e2's wp4)."""
    return ("pilot", ["wp", "--wp-x", "715", "--wp-y", "58", str(tab), str(row)], 90)


SESSIONS = {
    # Normal, level 1, Act I: Gheed's gamble window (every lvl clamped to 5), a sale in it (the gamble view), a gamble
    # purchase, a second window; Akara: sales of a Super Healing Potion (copied) and a Scroll of Town Portal
    # (permanent), purchases of a Scroll of Town Portal (permanent) and a non-permanent item; Charsi: a purchase, the
    # window again (built, not stale); then a walk out of the Rogue Encampment
    "low": ("VendH6cLow", "enter-normal", 6201, [
        wait(3),
        win("gheed", "gamble", ["sell:2,0", "sleep:1.5", "GBUY", "sleep:1.5"]),
        npc("gheed", "gamble"),
        win("akara", "trade", ["sell:0,0", "sleep:1.5", "sell:1,0", "sleep:1.5", "BUY:tsc", "sleep:1.5",
                               "BUY:nonperm", "sleep:1.5"]),
        win("charsi", "trade", ["BUY:nonperm", "sleep:1.5"]),
        npc("charsi", "trade"),
        ("walkout", [], 240),
        wait(3)]),
    # Normal, level 30, from the Act IV town to Lut Gholein: Drognan's trade window twice, the Frigid Highlands (an
    # act change) and Eldritch's pack for a level-up, back to Lut Gholein, Drognan's window again; then his trade
    # window, Escape, the game menu's Save and Exit (PlayerInteractEnd at the player's removal)
    "lvl": ("VendH6cLvl", "enter-normal", 6202, [
        wait(3),
        wp4(2, 1),
        npc("drognan", "trade"),
        npc("drognan", "trade"),
        ("pilot", ["npc", "waypoint", "walk"], 60),
        ("pilot", ["wpchain", "--chain", "5,2", "--linger", "3"], 60),
        ("pilot", ["farm", "--players", "1", "--time", "75", "--sweep", "--nova-key", "F1", "--es-key", "F2", "--es",
                   "20", "--mana-col", "4", "--mana-drink", "0.3"], 200),
        ("back", [], 300),
        ("pilot", ["wpchain", "--chain", "2,1", "--linger", "3"], 60),
        npc("drognan", "trade"),
        ("saveexit", ["drognan"], 120),
        wait(3)]),
    # Hell, level 99, Act V: Larzuk, Anya and Malah's stock at ilvl 104; sales to Malah of a Super Healing Potion
    # (permanent outside Normal) and a cap; Anya's gamble window (lvl clamped to 99), a gamble purchase, a second
    # window; then the Act III town: Asheara's hire list first, then her trade window
    "h99e": ("VendH6cH99e", "enter-hell", 6203, [
        wait(3),
        npc("larzuk", "trade"),
        win("anya", "trade", []),
        win("malah", "trade", ["sell:0,0", "sleep:1.5", "sell:1,0", "sleep:1.5", "BUY:nonperm", "sleep:1.5"]),
        win("anya", "gamble", ["GBUY", "sleep:1.5"]),
        npc("anya", "gamble"),
        ("pilot", ["npc", "waypoint", "walk"], 60),
        ("pilot", ["wpchain", "--chain", "3,1", "--linger", "4"], 60),
        npc("asheara", "hire"),
        npc("asheara", "trade"),
        wait(3)]),
    # Hell, level 99, Act V: Larzuk's stock at ilvl 104 rebuilt again and again (his trade window, the Frigid
    # Highlands waypoint and back: an in-act leave resets the act's stores), for a build past 32 failed creations
    "larz": ("VendH6cH99e", "enter-hell", 6205, [wait(3)] + [
        c for _ in range(8) for c in (npc("larzuk", "trade"), ("pilot", ["npc", "waypoint", "walk"], 60),
                                      ("pilot", ["wpchain", "--chain", "5,2", "--linger", "2"], 60),
                                      ("pilot", ["wpchain", "--chain", "5,1", "--linger", "2"], 60))] + [wait(3)]),
    # Hell, level 99, Act V, towns only: Larzuk's stock at ilvl 104 rebuilt again and again by the stale path (his
    # trade window; Anya's gamble window six times and a pause, so that more than 240 000 ms pass; the Act IV town and
    # back: the act change marks the store stale and the next trade open resets and rebuilds it)
    "larz2": ("VendH6cH99e", "enter-hell", 6207, [wait(3)] + [
        c for _ in range(6) for c in (npc("larzuk", "trade"), npc("anya", "gamble", ["--repeat", "6"], 400),
                                      wait(150), ("pilot", ["npc", "waypoint", "walk"], 60),
                                      ("pilot", ["wpchain", "--chain", "4,1", "--linger", "2"], 60),
                                      ("pilot", ["wpchain", "--chain", "5,1", "--linger", "2"], 60))] + [wait(3)]),
    # Nightmare, level 19, from the Act IV town to Lut Gholein: Fara's stock at ilvl 24 rebuilt again and again (her
    # trade window, the Sewers Level 2 waypoint and back: an in-act leave resets the act's stores)
    "fara": ("VendH6cN19", "enter-nightmare", 6206, [wait(3), wp4(2, 1)] + [
        c for _ in range(6) for c in (npc("fara", "trade"), ("pilot", ["npc", "waypoint", "walk"], 60),
                                      ("pilot", ["wpchain", "--chain", "2,2", "--linger", "2"], 60),
                                      ("pilot", ["wpchain", "--chain", "2,1", "--linger", "2"], 60))] + [wait(3)]),
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


def tags_count(log, tag):
    return len(log_lines(log, (tag,)))


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
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
    xd = PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
    pilot = PY + [os.path.join(HERE, "d2pilot.py")]
    for kind, args, timeout in cmds:
        rc = None
        if kind == "pilot":
            rc = sh(pilot + [args[0], log, "--slot", str(slot)] + args[1:] + ["--shots", shots], timeout, out)
        elif kind == "win":
            who, action, toks = args[0], args[1], args[2:]
            rc = sh(pilot + ["npc", log, who, action, "--stay", "--slot", str(slot), "--shots", shots,
                             "--npc-time", "150"], timeout, out)
            if rc == 0:
                time.sleep(1.0)
                sh(xd + ["shot", os.path.join(shots, "%s-%s-open.png" % (who, action))], 30, out)
                for tok in toks:
                    if tok == "GBUY" or tok.startswith("BUY:"):
                        rt = resolve(log, CLS[who], tok)
                        if not rt:
                            print("  %s: nothing to buy" % tok, flush=True)
                            continue
                    else:
                        rt = [tok]
                    sh(PY + [os.path.join(HERE, "economy_sessions.py"), "--slot", str(slot), "act"] + rt, 120, out)
                sh(xd + ["shot", os.path.join(shots, "%s-%s-end.png" % (who, action))], 30, out)
                sh(xd + ["key", "Escape"], 30, out)
                time.sleep(1.5)
        elif kind == "walkout":
            # walk on to the nearest unactivated room (any level) a few hops at a time until a TLL line comes
            n0 = tags_count(log, "TLL")
            for _ in range(8):
                sh(pilot + ["explore", log, "--slot", str(slot), "--any-level", "--walk", "--hops", "6", "--nova",
                            "0", "--shots", shots], 120, out)
                if tags_count(log, "TLL") > n0:
                    break
            rc = 0 if tags_count(log, "TLL") > n0 else 1
        elif kind == "back":
            # back to the arrival point of the last level change (the waypoint), then wpchain takes it
            arr = None
            lid = None
            for t, d in log_lines(log, ("PLR",)):
                if d.get("lid") != lid:
                    lid, arr = d.get("lid"), (d["x"], d["y"])
            if arr:
                rect = "%d,%d,1,1" % (arr[0] // 5, arr[1] // 5)
                rc = sh(pilot + ["explore", log, "--slot", str(slot), "--any-level", "--to-rect", rect, "--hops",
                                 "60", "--nova", "1", "--shots", shots], timeout, out)
        elif kind == "saveexit":
            # the NPC's menu, Escape, then the game menu's Save and Exit (tooling.md: Escape, click 400 262)
            sh(pilot + ["npc", log, args[0], "trade", "--stay", "--slot", str(slot), "--shots", shots,
                        "--npc-time", "150"], 200, out)
            time.sleep(1.0)
            sh(xd + ["shot", os.path.join(shots, "saveexit-0.png")], 30, out)
            sh(xd + ["key", "Escape"], 30, out)
            time.sleep(1.0)
            sh(xd + ["key", "Escape"], 30, out)
            time.sleep(1.0)
            sh(xd + ["shot", os.path.join(shots, "saveexit-1.png")], 30, out)
            sh(xd + ["click", "400", "262"], 30, out)
            time.sleep(6)
            sh(xd + ["shot", os.path.join(shots, "saveexit-2.png")], 30, out)
            rc = 0
        elif kind == "xd":
            for c in args:
                if c.startswith("sleep "):
                    time.sleep(float(c.split()[1]))
                    continue
                sh(xd + c.split(), 30, out)
            rc = 0
        print("  -> %s" % rc, flush=True)
    sh(xd + ["shot", os.path.join(shots, "end.png")], 30, out)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if argv and argv[0] == "write":
        return cmd_write(None)
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-6s %-14s %-12s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
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

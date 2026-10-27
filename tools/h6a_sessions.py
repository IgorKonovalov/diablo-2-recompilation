#!/usr/bin/env python3
"""Plan 0038 batch H6a (cube): the session layouts, their recipes and transmute plans, and the session loop.

    python3 -I tools/h6a_sessions.py write [NAME ...]      # tools/d2s_recipes/cube-h6a-<name>.json and
                                                          # tools/gdb/cube-h6a-<name>.plan (every session, or the named)
    python3 -I tools/h6a_sessions.py list
    python3 -I tools/h6a_sessions.py run --slot N --tag TAG --saves DIR --run RUN NAME [NAME ...]

The layouts are plan 0030 Phase 2's (tools/cube_sessions.py: the items packed around the cube at inventory (8, 2), one
step = the step's items moved into the cube, Transmute, then out / back / keep / leave / gone), with two additions:
  - a step's "ins": items (runes) put into input 1's sockets in the inventory before the step (tools/d2pilot.py cube
    `mv:` onto the parent: the game's insert path, which forms a runeword when the runes spell one);
  - a session's "act4": the header's Normal act byte 131 (0x80 | 3, the Act IV start of plan 0038 H6e2's -a4
    recipes) instead of 128, so the game starts in the Pandemonium Fortress (level 103).
`run` plays one game per session on one slot: saves.py restore and aside TAG, tools/d2run.py --install TAG
<DIR>/<Name>.d2s with tools/gdb/cube.gdb (logger r4) and the session's entry steps, tools/d2pilot.py cube --plan,
then tools/slots.py stop N. A session marked "crash" (its last transmute is expected to fault the game) runs in its
own game directory (--game-dir, a symlink copy of workspace/runtime/game inside the slot's prefix), so a crash folder
never lands in the shared one. The log goes to workspace/logs/h6a/<RUN>-s<slot>-<seed>-<name>.log, the pilot's output
beside it (.pilot.txt). Nothing here feeds a model: the plan only decides where to click; tools/cube.py and
tools/sweep_h6a.py decide from the log what happened. Stdlib only.
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import cube_sessions as cs  # noqa: E402

PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6a")
GDB = os.path.join(HERE, "gdb", "cube.gdb")
S, MAG, RARE, R, step = cs.S, cs.MAG, cs.RARE, cs.R, cs.step
JEW = cs.JEW
SESSIONS = {}


def session(name, steps, game="expansion", level=80, diff=0, quest_bits=None, extra=None, note="", act4=False,
            crash=False, seed=None):
    SESSIONS[name] = dict(name=name, steps=steps, game=game, level=level, diff=diff, quest_bits=quest_bits or [],
                          extra=extra or {}, note=note, act4=act4, crash=crash, seed=seed)


def ins(st, items):
    st["ins"] = items
    return st


UCODE = {"Gull": "dgr", "Wizardspike": "7dg", "Spineripper": "9dg", "Greyform": "qui"}
_item_code = cs.item_code


def item_code(it):
    """cube_sessions.item_code with this batch's uniques."""
    return UCODE[it["unique"]] if it.get("unique") in UCODE else _item_code(it)


cs.item_code = item_code


def U(name, **kw):
    d = {"unique": name}
    d.update(kw)
    return d


POLE = [S("kri"), S("gpw"), S("sst"), S("lbl")]          # row 19: an item of type pole (the random-of-type output)
LEG_TOME = [S("leg"), S("tbk", tome=0, quantity=20)]


def define():
    if SESSIONS:
        return SESSIONS
    # upgrades: row 131 (`weap,exc,uni` -> `useitem,mod,eli`) fed a normal-, an elite- and an exceptional-tier unique
    # dagger; row 135 on an exceptional rare; row 129 on an ethereal unique; then row 19
    session("upgu", [
        step([U("Gull", ilvl=40), R(17), R(21), S("gpg")], then="back", note="row 131 on a normal-tier unique: exc refuses"),
        step([U("Wizardspike", ilvl=80), R(17), R(21), S("gpg")], then="back",
             note="row 131 on an elite-tier unique: exc refuses"),
        step([U("Spineripper", ilvl=60), R(17), R(21), S("gpg")], note="row 131 elite unique upgrade (eli)"),
        step([RARE("9dg", ilvl=60), R(19), R(22), S("gpb")], note="row 135 elite rare upgrade (eli)"),
        step([U("Gull", ilvl=40, ethereal=True), R(8), R(12), S("gpg")], note="row 129 on an ethereal unique (exc)"),
        step(list(POLE), then="leave", note="row 19 savage polearm (random item of a type)"),
    ], note="upgrade rows with exceptional and elite tiers, an ethereal upgrade")
    # crafted `upg` inputs of a higher tier; a socketed unique upgrade with its gem
    session("upgc", [
        step([MAG("xmg", ilvl=60), dict(JEW), R(9), S("gpb")], note="row 66 on exceptional gloves (upg)"),
        step([MAG("umg", ilvl=70), dict(JEW), R(9), S("gpb")], note="row 66 on elite gloves (upg)"),
        step([U("Greyform", ilvl=30, sockets=1, filled=[S("gsv")]), R(7), R(13), S("gpw")],
             note="row 130 on a socketed unique with a gem (mod exc)"),
    ], note="upg tiers, a socketed copy")
    # repair, recharge, qty, noe, unsocket, a runeword stripped
    session("repair", [
        step([S("ssd", ilvl=20, dur=5), R(9)], note="row 137 on a damaged short sword (rep)"),
        step([S("ssd", ilvl=20, dur=0, broken=True), R(9)], note="row 137 on a broken short sword (rep)"),
        step([S("wnd", ilvl=20, item_props=[[204, 101 << 6 | 3, 27 << 8 | 5]]), R(9), S("gcv")],
             note="row 139 on a wand with 5 of 27 charges (rep, rch)"),
        step([S("tkf", ilvl=20, quantity=20), R(9)], note="row 137 on throwing knives, 20 of 160 (rep, qty=255)"),
        step([S("ssd", ilvl=20, ethereal=True), R(9)], then="back", note="row 137 on an ethereal sword: noe refuses"),
        step([S("ssd", ilvl=20, sockets=2, filled=[S("gsv"), S("gsb")]), R(15), S("tsc")],
             note="row 141 on a sword with two gems (uns)"),
        ins(step([S("ssd", ilvl=20, sockets=2), R(15), S("tsc")], note="row 141 on Steel (uns strips the runeword)"),
            [R(3), R(1)]),
    ], note="rep, rch, qty, noe, uns")
    # the quest outputs: Khalim's Will (qf2) and the Horadric Staff (hst, 1 x 4: left in the cube)
    session("quest", [
        step([S("qf1"), S("qhr", quest_diff=0), S("qey", quest_diff=0), S("qbr", quest_diff=0)], out="qf2",
             note="row 1 Khalim's Will"),
        step([S("msf"), S("vip", quest_diff=0)], then="leave", note="row 0 Horadric Staff"),
    ], quest_bits=[["normal", 10, 11, 0]], note="the quest hooks")
    # the cow portal outside level 1 (the Act IV start), row 17 on a magic tower shield, then row 19
    session("cowa4", [
        step(list(LEG_TOME), then="back", note="row 2 in the Pandemonium Fortress: refused (level)"),
        step([MAG("tow", 382, ilvl=30), S("skc"), S("skf"), S("spc")], note="row 17 on a magic tower shield (suf=162)"),
        step(list(POLE), then="leave", note="row 19 savage polearm"),
    ], act4=True, extra={"quests": "all"}, quest_bits=[["normal", 4, 10, 0]], note="cow portal outside level 1")
    # classic: the word 26 test, with word 40 bit 0 clear in both
    session("cowcl0", [
        step(list(LEG_TOME), then="back", note="row 2 in classic, word 26 bit 0 clear: refused"),
        step(list(POLE), then="leave", note="row 19 savage polearm (classic: version < 100 only)"),
    ], game="classic", level=50, extra={"quests": "all"},
        quest_bits=[["normal", 4, 10, 0], ["normal", 26, 0, 0], ["normal", 40, 0, 0]], note="classic cow refused")
    session("cowcl1", [
        step(list(LEG_TOME), then="gone", note="row 2 in classic, word 26 bit 0 set, word 40 bit 0 clear: opens"),
    ], game="classic", level=50, extra={"quests": "all"},
        quest_bits=[["normal", 4, 10, 0], ["normal", 26, 0, 1], ["normal", 40, 0, 0]], note="classic cow opens")
    # crafting at output ilvl 1 (clvl 1, input ilvl 1): the one-group suffix sides of lbt (row 83) and sst (row 72);
    # a second suffix pick of 0 faults the game, so the session ends at that transmute (own game directory)
    lb = lambda: step([MAG("lbt", ilvl=1), dict(JEW), R(10), S("gpv")], note="row 83 crafted boots at ilvl 1")
    ss = lambda: step([MAG("sst", ilvl=1), dict(JEW), R(3), S("gpb")], note="row 72 crafted short staff at ilvl 1")
    session("craftlow", [lb(), ss(), lb(), ss(), lb()], level=1, crash=True, note="crafted pick of 0")
    return SESSIONS


# ---------------------------------------------------------------- layout and plan (cube_sessions.layout + "ins")

def layout(sess):
    inv = cs.Grid(cs.INV_W, cs.INV_H)
    inv.put(cs.CUBE_AT[0], cs.CUBE_AT[1], 2, 2)
    items = [dict(code="box", store="inventory", x=cs.CUBE_AT[0], y=cs.CUBE_AT[1])]
    placed, placed_ins = [], []
    for st in sess["steps"]:
        row, extra = [], []
        for group, out in ((st["items"], row), (st.get("ins", []), extra)):
            for it in group:
                w, h = cs.size(cs.item_code(it))
                at = inv.place(w, h)
                if at is None:
                    raise SystemExit("%s: the inventory is full at step %r" % (sess["name"], st["note"]))
                e = copy.deepcopy(it)
                e.update(store="inventory", x=at[0], y=at[1])
                items.append(e)
                out.append((it, (at[0], at[1], w, h)))
        placed.append(row)
        placed_ins.append(extra)
    toks = ["key:i", "rclick:inv:%d,%d,2,2" % cs.CUBE_AT, "sleep:1",
            "shot:workspace/logs/h6a/cube-h6a-%s-open.png" % sess["name"]]
    cube = cs.Grid(cs.CUBE_W, cs.CUBE_H)
    in_cube = []
    for k, (st, row, extra) in enumerate(zip(sess["steps"], placed, placed_ins)):
        toks.append("# step %d: %s" % (k + 1, st["note"]))
        px, py, pw, ph = row[0][1]
        for it, (x, y, w, h) in extra:
            toks.append("mv:inv:%d,%d,%d,%d>inv:%d,%d,%d,%d" % (x, y, w, h, px, py, pw, ph))
            toks.append("sleep:1.5")
        if extra:
            toks.append("shot:workspace/logs/h6a/cube-h6a-%s-ins%d.png" % (sess["name"], k + 1))
        for it, (x, y, w, h) in row:
            at = cube.place(w, h)
            if at is None:
                raise SystemExit("%s: the cube is full at step %r" % (sess["name"], st["note"]))
            toks.append("mv:inv:%d,%d,%d,%d>cube:%d,%d,%d,%d" % (x, y, w, h, at[0], at[1], w, h))
            in_cube.append((it, (at[0], at[1], w, h), (x, y, w, h)))
        toks.append("tm")
        toks.append("shot:workspace/logs/h6a/cube-h6a-%s-tm%d.png" % (sess["name"], k + 1))
        if st["then"] == "out":
            x, y, w, h = in_cube[0][2]
            ow, oh = cs.size(st["out"]) if st.get("out") else (w, h)
            if ow > w or oh > h:
                raise SystemExit("%s: output %dx%d does not fit input 1's %dx%d at step %r" % (
                    sess["name"], ow, oh, w, h, st["note"]))
            toks.append("out:inv:%d,%d,%d,%d" % (x, y, ow, oh))
            cube, in_cube = cs.Grid(cs.CUBE_W, cs.CUBE_H), []
        elif st["then"] in ("leave", "gone"):
            cube, in_cube = cs.Grid(cs.CUBE_W, cs.CUBE_H), []
        elif st["then"] == "back":
            for it, (cx, cy, w, h), (x, y, _, _) in in_cube:
                toks.append("mv:cube:%d,%d,%d,%d>inv:%d,%d,%d,%d" % (cx, cy, w, h, x, y, w, h))
            cube, in_cube = cs.Grid(cs.CUBE_W, cs.CUBE_H), []
    toks.append("shot:workspace/logs/h6a/cube-h6a-%s-end.png" % sess["name"])
    return items, toks


def recipe(sess, items):
    s2 = dict(sess, name="h6a-" + sess["name"])
    r = cs.recipe(s2, items)
    if sess["act4"]:
        r["difficulty"] = [131, 0, 0]
    return r


def rp_path(name):
    return os.path.join(cs.RECIPES, "cube-h6a-%s.json" % name)


def plan_path(name):
    return os.path.join(cs.PLANS, "cube-h6a-%s.plan" % name)


def cmd_write(names):
    define()
    for name in names or sorted(SESSIONS):
        s = SESSIONS[name]
        items, toks = layout(s)
        with open(rp_path(name), "w") as f:
            json.dump(recipe(s, items), f, indent=2)
            f.write("\n")
        with open(plan_path(name), "w") as f:
            f.write("# tools/d2pilot.py cube --plan for tools/d2s_recipes/cube-h6a-%s.json (tools/h6a_sessions.py)\n"
                    % name)
            for t in toks:
                f.write(t + "\n")
        print("%s: %d steps, %d items -> %s, %s" % (name, len(s["steps"]), len(items), os.path.relpath(rp_path(name)),
                                                      os.path.relpath(plan_path(name))))
    return 0


def cmd_list():
    define()
    for name, s in SESSIONS.items():
        print("%-9s %-9s diff %d level %2d%s%s  %d steps  %s" % (name, s["game"], s["diff"], s["level"],
                                                               " act4" if s["act4"] else "",
                                                               " crash" if s["crash"] else "", len(s["steps"]),
                                                               s["note"]))
        for st in s["steps"]:
            print("    %-5s %s" % (st["then"], st["note"]))
    return 0


# ---------------------------------------------------------------- the session loop

SEEDS = {"upgu": 6101, "upgc": 6102, "repair": 6103, "quest": 6104, "cowa4": 6105, "cowcl0": 6106, "cowcl1": 6107,
         "craftlow": 6108}


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


def game_copy(slot):
    """A symlink copy of workspace/runtime/game inside the slot's prefix (the crash session's --game-dir)."""
    src = os.path.join(ROOT, "workspace", "runtime", "game")
    dst = os.path.join(ROOT, "workspace", "wineprefix-%d" % slot, "drive_c", "h6a-game")
    os.makedirs(dst, exist_ok=True)
    for n in os.listdir(src):
        if n in ("BlizzardError", "BnetLog.txt", "default.key"):
            continue
        p = os.path.join(dst, n)
        if not os.path.lexists(p):
            os.symlink(os.path.realpath(os.path.join(src, n)), p)
    return dst


def run_session(name, slot, tag, saves, run):
    s = SESSIONS[name]
    seed = SEEDS[name]
    rname = cs.recipe(dict(s, name="h6a-" + name), [])["name"]
    path = os.path.join(saves, rname + ".d2s")
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, seed %d -> %s" % (name, path, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    argv = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb", GDB, "--steps",
                 os.path.join(HERE, "gdb", "cube-enter-normal.steps"), "--after", "1200", "--install", tag, path,
                 "--log", log]
    if s["crash"]:
        argv += ["--game-dir", game_copy(slot)]
    drv = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0, armed = time.time(), None
    while time.time() - t0 < 150:
        time.sleep(2)
        hide_window(slot)
        try:
            if "CUBE logger armed" in open(log, errors="replace").read():
                armed = time.time()
                break
        except OSError:
            pass
    if armed is None:
        print("  no logger after 150 s: the session stops here", flush=True)
    else:
        time.sleep(34)          # attach-wait 5 s + the entry steps (about 18 s) + the game's entry
        hide_window(slot)
        sh(PY + [os.path.join(HERE, "d2pilot.py"), "cube", log, "--slot", str(slot), "--plan", plan_path(name),
                 "--ins-gap", "1.2", "--pick-wait", "0.5"], 600, out)
        time.sleep(3)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    out.close()
    if s["crash"]:
        be = os.path.join(game_copy(slot), "BlizzardError")
        if os.path.isdir(be):
            dst = os.path.join(LOGS, "dev", stem + "-BlizzardError")
            shutil.move(be, dst)
            print("moved %s -> %s" % (be, dst), flush=True)


def main(argv):
    if not argv or argv[0] not in ("list", "run", "write"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        return cmd_list()
    if argv[0] == "write":
        return cmd_write(argv[1:])
    define()
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

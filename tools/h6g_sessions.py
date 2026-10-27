#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H6g (player; run:2026-10-27-sweep-player): one game per session on
one slot, logged by tools/gdb/h6g.gdb (tools/gdb/player.gdb's files and tools/gdb/h6g.py), driven by tools/xdrive.py
(the character screen's attribute buttons, the skill tree, Shift + click to the belt), tools/d2pilot.py explore (Nova
kills out of town) and the death steps below. The session loop is plan 0038 H6e1's (tools/h6e1_sessions.py).

Usage:
  python3 -I tools/h6g_sessions.py recipes             # (re)write tools/d2s_recipes/player-h6g-*.json
  python3 -I tools/h6g_sessions.py list
  python3 -I tools/h6g_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s, built from
tools/d2s_recipes/player-h6g-<recipe>.json with tools/d2s.py build; None for the new-character session, which starts
from an empty saves directory), the steps file, the map seed and the commands run in order. The log goes to
workspace/logs/h6g/<RUN>-s<slot>-<seed>-<SESSION>.log, the driver's and pilot's output beside it (.pilot.txt), the
screenshots to <stem>-shots/. The slot is stopped after each session (tools/slots.py stop N) and its saves directory
returned to the TAG aside first, so every session starts from the save it names. Nothing here feeds a model: the pilot
only decides where to click.
"""
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
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h6g")
GDB = os.path.join(HERE, "gdb", "h6g.gdb")
GDB_QUEST = os.path.join(HERE, "gdb", "h6g-quest.gdb")
RECIPES = os.path.join(HERE, "d2s_recipes")

# Sorceress experience thresholds T(L) (experience.txt, the Sorceress column; T(L) is the experience that reaches
# level L + 1): the recipes' experience values below are written from them
T = {29: 4663553, 39: 17270791, 49: 47116709, 79: 681027665, 80: 742730244, 97: 3229426756, 98: 3520485254}

NOVA_SKILLS = {"Lightning": 20, "Chain Lightning": 20, "Lightning Mastery": 20, "Charged Bolt": 1, "Static Field": 1,
               "Telekinesis": 20, "Nova": 20, "Teleport": 1, "Thunder Storm": 1, "Energy Shield": 20, "Warmth": 20,
               "Fire Wall": 20, "Fire Bolt": 1, "Inferno": 1, "Blaze": 1}
NOVA_MOUSE = {"left": "Teleport", "right": "Nova", "swap_left": "Teleport", "swap_right": "Nova"}
NOVA_GEAR = [{"unique": "Griffon's Eye", "equip": "head", "roll": "max"},
             {"unique": "Skin of the Vipermagi", "equip": "tors"},
             {"unique": "Chance Guards", "equip": "glov", "roll": "max"},
             {"unique": "Goldwrap", "equip": "belt", "roll": "max"},
             {"unique": "Wartraveler", "equip": "feet", "roll": "max"},
             {"unique": "Mara's Kaleidoscope", "equip": "neck"},
             {"unique": "Nagelring", "equip": "rrin", "roll": "max"},
             {"unique": "Nagelring", "equip": "lrin", "roll": "max"},
             {"unique": "Eschuta's temper", "equip": "rarm"},
             {"unique": "Lidless Wall", "equip": "larm"}]


def stats(level, exp, life, mana=8000, s=(88, 1000, 25, 1000), extra=None):
    d = {"strength": s[0], "energy": s[1], "dexterity": s[2], "vitality": s[3], "hitpoints": life, "maxhp": life,
         "mana": mana, "maxmana": mana, "stamina": 275, "maxstamina": 275, "level": level, "experience": exp}
    d.update(extra or {})
    return d


def nova(name, seed, level, exp, life=8000, gear=True, items=(), diff=128):
    r = {"game": "expansion", "class": "Sorceress", "seed": seed, "name": name, "progression": 15,
         "difficulty": [diff, diff, diff], "waypoints": {"normal": "all", "nightmare": "all", "hell": "all"},
         "stats": stats(level, exp, life), "skills": dict(NOVA_SKILLS), "mouse": dict(NOVA_MOUSE),
         "items": (list(NOVA_GEAR) if gear else []) + list(items), "quests": "all",
         "hotkeys": ["Nova", "Energy Shield"]}
    if gear:
        r["belt_fill"] = ["rvl", "rvl", "rvl", "mp5"]
    return r


def recipes():
    """The batch's recipes (a test state each, ADR-0013 Neutral: a built save on stock tables)."""
    town = {"game": "expansion", "class": "Sorceress", "seed": 6701, "name": "H6gTown", "progression": 15,
            "difficulty": [128, 128, 128], "waypoints": {"normal": "all"},
            "stats": stats(30, T[29] + 1000, 100, 100, (35, 35, 25, 30), {"statpts": 4, "newskills": 4}),
            # Ice Bolt absent (two points: the append, then the raise), Frozen Armor at 19 (one point: the raise to
            # the maximum), Frost Nova at 20 (a click at the maximum)
            "skills": {"Frozen Armor": 19, "Frost Nova": 20},
            "items": [{"code": "vbl", "equip": "belt"},
                      {"code": "hp1", "belt_slot": 0},
                      {"code": "hp1", "store": "inventory", "x": 0, "y": 0},
                      {"code": "hp1", "store": "inventory", "x": 1, "y": 0},
                      {"code": "mp1", "store": "inventory", "x": 2, "y": 0},
                      {"code": "hp1", "store": "inventory", "x": 3, "y": 0}]}
    out = {
        "town": town,
        # level 98 two points below the level-99 threshold: the first Hell Blood Moor kill adds about 5
        "cap98": nova("H6gCap", 6702, 98, T[98] - 2),
        # level 80 with Annihilus (item_addexperience at its max, 10) in the inventory
        "xp85": nova("H6gXp", 6703, 80, T[79] + 1000,
                     items=[{"unique": "Annihilus", "store": "inventory", "x": 0, "y": 0, "roll": "max"}]),
        # deaths: no gear, 1 point of life (Normal: DeathExpPenalty 0; Hell: 10, mid-level)
        "deathn": nova("H6gDn", 6704, 30, T[29] + 500000, life=1, gear=False),
        "deathh": nova("H6gDh", 6705, 50, 50000000, life=1, gear=False),
        # Nightmare, 1000 above the level start (the clamp: 5 % of the span is 98 223), 60 life to come back to the
        # corpse
        "deathnm": nova("H6gDnm", 6706, 40, T[39] + 1000, life=60, gear=False),
    }
    # the Ancients (quest 35, word 39): QuestSummit's quest state (plan 0042, tools/d2s_recipes/quest-w39summit.json:
    # every quest done but words 39 and 40, Act V start) on the Nova build, 1000 below level 81: the grant fills the
    # level, PLAYER_LevelUp, then the rest
    anc = nova("H6gAnc", 6707, 80, T[80] - 1000, diff=132)
    anc["quest_bits"] = {d: {"39": {"clear": [0]}, "40": {"clear": [0]}} for d in ("normal", "nightmare", "hell")}
    out["anc"] = anc
    for k, r in out.items():
        with open(os.path.join(RECIPES, "player-h6g-%s.json" % k), "w") as fh:
            json.dump(r, fh, indent=2)
            fh.write("\n")
        print("wrote player-h6g-%s.json" % k)
    return 0


def pilot(*a, t=300):
    return ("pilot", list(a), t)


def xd(*cmds):
    return ("xd", list(cmds), 0)


def until(tag, n, t):
    """wait until the log holds n lines of TAG (or t seconds)"""
    return ("until", [tag, n], t)


NOVA = ["--nova-key", "F1"]
KILLS = ["explore", "--any-level", "--hops", "400", "--persist", "20"] + NOVA
# the character screen (c) with unspent points: the four + buttons, 800x600 window-relative (measured from
# run:2026-10-27-sweep-player's calibration screenshot, h6g-cal)
STAT_XY = {"str": (220, 152), "dex": (220, 213), "vit": (220, 300), "energy": (220, 362)}
# the skill tree (t): skill at (440 + 68 (col - 1), 97 + 69 (row - 1)); page tabs at x 675, y 430 / 325 / 215 for
# pages 1 / 2 / 3 (plan 0035, tooling.md); Ice Bolt and Frozen Armor are page 3, row 1, columns 2 and 3; Frost Nova
# page 3, row 2, column 1
SKILL_TAB3 = (675, 215)
ICE_BOLT, FROZEN_ARMOR, FROST_NOVA = (508, 97), (576, 97), (440, 166)


def inv(c, r):
    return 418 + 29 * c + 14, 316 + 29 * r + 14


def town_cmds():
    c = ["sleep 1", "key c", "sleep 1.5", "shot {shots}/char-open.png"]
    for k in ("str", "dex", "vit", "energy"):
        c += ["click %d %d" % STAT_XY[k], "sleep 1.2"]
    c += ["shot {shots}/char-after.png", "key c", "sleep 1", "key t", "sleep 1.5", "click %d %d" % SKILL_TAB3,
          "sleep 1", "shot {shots}/tree-open.png"]
    for xy in (ICE_BOLT, ICE_BOLT, FROZEN_ARMOR, FROST_NOVA):
        c += ["click %d %d" % xy, "sleep 1.5"]
    c += ["shot {shots}/tree-after.png", "key t", "sleep 1", "key i", "sleep 1.5", "shot {shots}/inv-open.png"]
    for cell in ((0, 0), (1, 0), (2, 0), (3, 0)):
        x, y = inv(*cell)
        c += ["keydown Shift_L", "sleep 0.2", "click %d %d" % (x, y), "sleep 0.2", "keyup Shift_L", "sleep 1.5"]
    c += ["shot {shots}/inv-after.png", "key i", "sleep 1"]
    return [xd(*c)]


def death_cmds(pickup):
    """explore out of town until the player's death (DG0), let the death mode end (CC0), then Escape to come back to
    town; with pickup, walk back to the corpse (CC0's position) and click it."""
    # no Nova: the monsters reach the low-life character
    c = [("death", ["--nova", "0"], 400),
         xd("sleep 6", "shot {shots}/dead.png", "key Escape", "sleep 6", "shot {shots}/town.png")]
    if pickup:
        c.append(("corpse", [], 240))
    return c


# name: (save Name or None, steps file, map seed, commands)
SESSIONS = {
    "cal": ("H6gTown", "enter-normal", 6710, [xd("sleep 1", "key c", "sleep 1.5", "shot {shots}/char.png", "key c",
                                                 "sleep 1", "key t", "sleep 1.5", "click %d %d" % SKILL_TAB3,
                                                 "sleep 1", "shot {shots}/tree.png", "key t", "sleep 1", "key i",
                                                 "sleep 1.5", "shot {shots}/inv.png")]),
    "town": ("H6gTown", "enter-normal", 6711, town_cmds()),
    "newchar": (None, None, 6712, [("newchar", ["sor:x", "bar:c"], 300)]),
    "cap98": ("H6gCap", "enter-hell", 6713, [pilot(*KILLS, t=420), until("XA0", 6, 360)]),
    "xp85": ("H6gXp", "enter-hell", 6714, [pilot(*KILLS, t=420), until("XA0", 6, 360)]),
    "deathn": ("H6gDn", "enter-normal", 6715, death_cmds(False)),
    "deathh": ("H6gDh", "enter-hell", 6716, death_cmds(False)),
    "deathnm": ("H6gDnm", "enter-nightmare", 6717, death_cmds(True)),
    # Act V start; the route of plan 0042's x-summit sessions (tools/quest_sessions.py), the altar (object 546), then
    # the three Ancients (540-542)
    "anc": ("H6gAnc", "enter-normal", 4314,
            [("qs", ["towp2", "wp:5,8", "explore:40", "warp:76:150", "clickwarp:76:1", "objop:546:1"], 600),
             pilot("farm", "--boss-cls", "540,541,542", "--time", "300", "--nova-key", "F1", "--es-key", "F2",
                   "--es", "20", "--sweep", t=360),
             until("EG0", 1, 30)]),
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
            print("moved %s to special:d2harness" % title, flush=True)


def count(log, tag):
    try:
        return open(log, errors="replace").read().count("\n%s " % tag)
    except OSError:
        return 0


def last_line(log, tag):
    v = None
    try:
        for ln in open(log, errors="replace"):
            if ln.startswith(tag + " "):
                try:
                    v = json.loads(ln[len(tag) + 1:])
                except ValueError:
                    pass
    except OSError:
        pass
    return v


def xdrive(slot, cmds, out, shots):
    path = os.path.join(shots, "xd-%d.txt" % int(time.time() * 1000))
    with open(path, "w") as fh:
        fh.write("\n".join(c.replace("{shots}", os.path.relpath(shots, ROOT)) for c in cmds) + "\n")
    return sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II", "run", path], 300,
              out)


TOWNS = (1, 40, 75, 103, 109)


def pilot_obj(slot):
    import d2pilot
    import slots

    class A:
        pass
    a = A()
    a.slot, a.display = slots.pick_display(slot, None)
    a.cx, a.cy, a.view_h = 400, 290, 571
    return d2pilot.Pilot(a)


def do_death(slot, log, args, timeout, out, shots):
    """Until the gate line DG0 is logged: with a live monster within 40 sub-tiles, Teleport next to the nearest and
    stand (no Nova); else a few exploration hops (tools/d2pilot.py explore --nova 0 --hops 4). Then wait for the
    corpse (CC0)."""
    import d2pilot
    n0 = count(log, "DG0")
    p = pilot_obj(slot)
    st = d2pilot.LogState(log)
    t0 = time.time()
    while time.time() - t0 < timeout and count(log, "DG0") == n0:
        st.poll()
        if not st.pos:
            time.sleep(0.5)
            continue
        px, py = st.pos[0], st.pos[1]
        near = [m for m in st.mon if d2pilot.live(m) and m["cls"] not in d2pilot.HIRE_CLS]
        near = [(((m["x"] - px) ** 2 + (m["y"] - py) ** 2) ** 0.5, m) for m in near]
        near = [x for x in near if x[0] <= 40]
        if near and st.pos[2] not in TOWNS:
            d, m = min(near, key=lambda x: x[0])
            if d > 3:
                k = min(1.0, 10.0 / d)
                p.teleport(int((m["x"] - px) * k), int((m["y"] - py) * k))
                time.sleep(0.6)
            else:
                time.sleep(1.0)
            continue
        sh(PY + [os.path.join(HERE, "d2pilot.py"), "explore", log, "--slot", str(slot), "--any-level", "--hops", "4",
                 "--shots", shots] + args, 90, out)
    died = count(log, "DG0") > n0
    t1 = time.time()
    while died and time.time() - t1 < 30 and count(log, "CC0") == 0:
        time.sleep(1)
    print("  death: %s, corpse lines %d" % (died, count(log, "CC0")), flush=True)
    return 0 if died else 1


def do_corpse(slot, log, timeout, out, shots):
    """Teleport back to the corpse at CC0's position (Nova at anything within 12) and left-click it until a CP0 line
    is logged."""
    import d2pilot
    cc = last_line(log, "CC0")
    if not cc or not cc.get("xy"):
        print("  corpse: no CC0 position", flush=True)
        return 1
    try:
        p = pilot_obj(slot)
    except Exception as e:  # noqa: BLE001
        print("  corpse: no pilot (%r)" % (e,), flush=True)
        return 1
    p.nova_key = "F1"
    st = d2pilot.LogState(log)
    gx, gy = cc["xy"]
    t0 = time.time()
    n0 = count(log, "CP0")
    tries = 0
    while time.time() - t0 < timeout and count(log, "CP0") == n0:
        st.poll()
        if not st.pos:
            time.sleep(0.5)
            continue
        px, py = st.pos[0], st.pos[1]
        d = ((gx - px) ** 2 + (gy - py) ** 2) ** 0.5
        if d > 4:
            # in a town Teleport does nothing: walk there (left clicks), Teleport outside
            p.walk = st.pos[2] in TOWNS
            k = min(1.0, (6.0 if p.walk else 10.0) / d)
            p.teleport(int((gx - px) * k), int((gy - py) * k))
            time.sleep(0.8)
            near = [m for m in st.mon if d2pilot.live(m) and ((m["x"] - px) ** 2 + (m["y"] - py) ** 2) ** 0.5 < 18]
            if near:
                p.nova(); p.nova()
                time.sleep(0.4)
            continue
        near = [m for m in st.mon if d2pilot.live(m) and ((m["x"] - px) ** 2 + (m["y"] - py) ** 2) ** 0.5 < 18]
        if near:   # at the corpse: clear what is around it before clicking (the killer waits there)
            p.nova(); p.nova()
            time.sleep(0.4)
            continue
        sx, sy = p.screen(gx - px, gy - py)
        oy = (-10, -20, 0, -30)[tries % 4]
        p.dpy.click(p.off[0] + int(sx), p.off[1] + int(sy) + oy, hold=0.2)
        tries += 1
        time.sleep(1.5)
    print("  corpse: CP0 lines %d (clicks %d)" % (count(log, "CP0") - n0, tries), flush=True)
    return 0 if count(log, "CP0") > n0 else 1


def saves_dir(slot):
    return os.path.join(ROOT, "workspace", "wineprefix-%d" % slot, "drive_c", "users", os.environ.get("USER", "igor"),
                        "Saved Games", "Diablo II")


def run_newchar(slot, tag, run, seed, specs, log, out, shots):
    import player_sessions as ps
    sp = [ps.parse_spec(s) for s in specs]
    names = ["h6g%s%s" % (ps.TAG3[c].lower(), "x" if g == "x" else "c") for c, g, _ in sp]
    steps = os.path.join(shots, "newchar.steps")
    ps.newchar_steps(sp, names, steps, os.path.relpath(shots, ROOT))
    rc = sh(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb", GDB, "--steps",
                  steps, "--after", "3", "--log", log], 120 + 60 * len(sp), out)
    written = os.path.join(LOGS, "%s-newchar-written" % run)
    os.makedirs(written, exist_ok=True)
    for nm in names:
        src = os.path.join(saves_dir(slot), nm + ".d2s")
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(written, nm + ".d2s"))
            print("written %s" % nm, flush=True)
    return rc


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
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
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    if save is None:
        rc = run_newchar(slot, tag, run, seed, cmds[0][1], log, out, shots)
        print("  -> %s" % rc, flush=True)
        sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
        out.close()
        return
    path = os.path.join(saves, save + ".d2s")
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 GDB_QUEST if name == "anc" else GDB, "--steps",
                                 os.path.join(HERE, "gdb", "%s.steps" % steps), "--after", "1800",
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
        if kind == "qs":
            rc = sh(PY + [os.path.join(HERE, "quest_sessions.py"), "act", "--slot", str(slot), log] + args, timeout,
                    out)
        elif kind == "pilot":
            rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                    ["--shots", shots], timeout, out)
        elif kind == "until":
            tag_, n = args
            t1 = time.time()
            while time.time() - t1 < timeout and count(log, tag_) < n:
                time.sleep(2)
            rc = 0 if count(log, tag_) >= n else 1
            print("  %s lines: %d" % (tag_, count(log, tag_)), flush=True)
        elif kind == "xd":
            rc = xdrive(slot, args, out, shots)
        elif kind == "death":
            rc = do_death(slot, log, args, timeout, out, shots)
        elif kind == "corpse":
            rc = do_corpse(slot, log, timeout, out, shots)
        print("  %s -> %s" % (kind, rc), flush=True)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run", "recipes"):
        print(__doc__)
        return 2
    if argv[0] == "recipes":
        return recipes()
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-10s %-10s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
        return 0
    a = argv[1:]
    opt = {}
    names = []
    k = 0
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

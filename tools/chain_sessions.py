#!/usr/bin/env python3
"""Scripted harness sessions for plan 0048 Phase 2 (the end-to-end run): one game per session on one slot, logged by
tools/gdb/chain.gdb (every loggers whose lines tools/chain.py check composes), driven by tools/d2pilot.py (Teleport on
the left button, Nova on F1, Energy Shield on F2: tools/d2s_recipes/uniqnova.json and uniqclassic.json).

Usage:
  python3 -I tools/chain_sessions.py list
  python3 -I tools/chain_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]
  python3 -I tools/chain_sessions.py volume LOG [LOG ...]      # lines and MB per tag, game minutes (PLR "gf")
  python3 -I tools/chain_sessions.py table REC.session.json ...  # the run record's session table

Each SESSION names a row of SESSIONS below: the save (<DIR>/<Name>.d2s), the difficulty steps file, the map seed, the
commands run in order, and the session's wall-time limit. The log goes to workspace/logs/chain-p2/<RUN>-s<slot>-<seed>-
<SESSION>.log, the pilot's output beside it (.pilot.txt) and a session record (.session.json: wall times, the game
frames of the first and last PLR line, the log size, why it ended). A watchdog ends the session when
  * the raw log reaches CAP bytes (plan 0048 Phase 1 review ruling 3: the session stops logging and is kept as a
    development log; the record says "cap"),
  * the wall-time limit is reached,
  * the log has not grown for QUIET s (after the first 150 s) or gdb reports the game exited;
then the slot is stopped (tools/slots.py stop N) and its saves directory returned to the TAG aside, so every session
starts from the save it names. Nothing here feeds a model: the pilot only decides where to click.
"""
import collections
import json
import os
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "chain-p2")
QUIET = 90
CAP = 500 * 1000 * 1000
GDB = os.path.join(HERE, "gdb", "chain.gdb")

EXP, CLS = "UniqNova", "UniqClassic"
KEYS = ["--nova-key", "F1", "--es-key", "F2"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def nova(diff):
    return ["--nova", "3", "--drink", "0.5"] + KEYS + (["--es", "30"] if diff != "normal" else [])


LOOT = ["--loot", "24", "--loot-max", "6", "--persist", "8"]


def wp(tab, row, classic=False):
    return ("pilot", ["wp", "--wp-find", str(tab), str(row)] + (CLASSIC_WP if classic else []), 90)


def explore(hops, diff, any_level=True):
    return ("pilot", ["explore", "--hops", str(hops)] + nova(diff) + LOOT + (["--any-level"] if any_level else []),
            60 + 6 * hops)


def descend(rows, diff):
    return ("pilot", ["farm", "--sweep", "--descend", rows, "--descend-time", "200", "--time", "5"] + nova(diff), 260)


def S(save, diff, seed, cmds, limit):
    return (save, "enter-" + diff, seed, cmds, limit)


SESSIONS = {
    # the smoke session (Phase 1 review ruling 3): one act, one difficulty, at most 20 game minutes; Cold Plains and
    # whatever the explore reaches from it (Burial Grounds: Blood Raven, class 267, oracle 13)
    "smoke": S(EXP, "normal", 4801, [wp(1, 2), explore(400, "normal")], 20 * 60),
}


def act_session(save, diff, seed, tab, row, limit=15 * 60):
    classic = save == CLS
    return S(save, diff, seed, [wp(tab, row, classic), explore(1500, diff), explore(1500, diff)], limit)


# the counted sessions: one act of one game type in one difficulty each, the waypoint chosen so that every generator
# kind (DrlgType 1 maze, 2 preset, 3 outdoor) comes in each game type; the town of the act is a preset level too.
# (name: save, difficulty, seed, waypoint tab, row)
PLAN = [
    ("xn1", EXP, "normal", 4806, 1, 2),      # Cold Plains (outdoor; Burial Grounds: Blood Raven, class 267)
    ("xn2", EXP, "normal", 4802, 2, 4),      # Halls of the Dead 2 (maze)
    ("xn3", EXP, "normal", 4803, 3, 2),      # Spider Forest (outdoor)
    ("xn4", EXP, "normal", 4804, 4, 2),      # City of the Damned (outdoor)
    ("xn5", EXP, "normal", 4805, 5, 4),      # Crystalline Passage (maze)
    ("xm1", EXP, "nightmare", 4811, 1, 9),   # Catacombs 2 (maze)
    ("xm2", EXP, "nightmare", 4812, 2, 3),   # Dry Hills (outdoor)
    ("xm3", EXP, "nightmare", 4813, 3, 9),   # Durance of Hate 2
    ("xm4", EXP, "nightmare", 4814, 4, 3),   # River of Flame
    ("xm5", EXP, "nightmare", 4815, 5, 2),   # Frigid Highlands (outdoor)
    ("xh1", EXP, "hell", 4821, 1, 2),        # Cold Plains (outdoor; Burial Grounds: Blood Raven, class 267)
    ("xh2", EXP, "hell", 4822, 2, 8),        # Arcane Sanctuary (preset)
    ("xh3", EXP, "hell", 4823, 3, 4),        # Flayer Jungle (outdoor)
    ("xh4", EXP, "hell", 4824, 4, 2),        # City of the Damned
    ("xh5", EXP, "hell", 4825, 5, 5),        # Halls of Pain (maze)
    ("cn1", CLS, "normal", 4831, 1, 9),      # Catacombs 2 (maze)
    ("cn2", CLS, "normal", 4832, 2, 3),      # Dry Hills (outdoor)
    ("cn3", CLS, "normal", 4833, 3, 2),      # Spider Forest (outdoor)
    ("cn4", CLS, "normal", 4834, 4, 2),      # City of the Damned
    ("cm1", CLS, "nightmare", 4841, 1, 2),   # Cold Plains (outdoor; Blood Raven)
    ("cm2", CLS, "nightmare", 4842, 2, 4),   # Halls of the Dead 2 (maze)
    ("cm3", CLS, "nightmare", 4843, 3, 4),   # Flayer Jungle (outdoor)
    ("cm4", CLS, "nightmare", 4844, 4, 3),   # River of Flame
    ("ch1", CLS, "hell", 4851, 1, 5),        # Black Marsh (outdoor)
    ("ch2", CLS, "hell", 4852, 2, 8),        # Arcane Sanctuary (preset)
    ("ch3", CLS, "hell", 4853, 3, 9),        # Durance of Hate 2
    ("ch4", CLS, "hell", 4854, 4, 2),        # City of the Damned
]
# oracle 13 (Phase 1 review ruling 2): Blood Raven (class 267, MonPlace place_bloodraven) in the Graveyard preset
# (LvlPrest Def 108) of the Burial Grounds (level 17), next to the Cold Plains waypoint; explore after
def raven(save, diff, seed):
    return S(save, diff, seed, [wp(1, 2, save == CLS),
                                ("pilot", ["explore", "--hops", "300", "--to-pdef", "108", "--pdef-any"] + nova(diff),
                                 400),
                                explore(1500, diff)], 15 * 60)


SESSIONS["raven-xn"] = raven(EXP, "normal", 4807)
SESSIONS["raven-cn"] = raven(CLS, "normal", 4837)
for _n, _sv, _d, _sd, _t, _r in PLAN:
    SESSIONS[_n] = act_session(_sv, _d, _sd, _t, _r)


def sh(args, timeout=None, log=None, holder=None):
    print("$ " + " ".join(args), flush=True)
    try:
        p = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        if holder is not None:
            holder["p"] = p
        return p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait(10)
        print("  (timeout after %s s)" % timeout, flush=True)
        return None
    finally:
        if holder is not None:
            holder["p"] = None


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


def plr_frames(log):
    """(first gf, last gf, levels seen) of the PLR lines."""
    first = last = None
    lids = []
    try:
        for ln in open(log, errors="replace"):
            if ln.startswith("PLR "):
                try:
                    d = json.loads(ln[4:])
                except ValueError:
                    continue
                if d.get("gf") is not None:
                    first = d["gf"] if first is None else first
                    last = d["gf"]
                if d.get("lid") is not None and (not lids or lids[-1] != d["lid"]):
                    lids.append(d["lid"])
    except OSError:
        pass
    return first, last, lids


def watchdog(log, holder, stop, limit, t_entry):
    t0 = time.time()
    size, t_size = -1, time.time()
    while not stop.get("done"):
        time.sleep(3)
        if stop.get("done"):
            return
        now = time.time()
        try:
            n = os.path.getsize(log)
        except OSError:
            n = -1
        if n != size:
            size, t_size = n, now
        why = None
        if n >= CAP:
            why = "cap"
        elif now - t_entry >= limit:
            why = "time"
        elif now - t_size > QUIET and now - t0 > 150:
            why = "quiet: log unchanged for %d s" % (now - t_size)
        else:
            try:
                with open(log, "rb") as fh:
                    fh.seek(max(0, n - 4096))
                    tail = fh.read()
                if b"[Inferior " in tail and b" exited" in tail:
                    why = "exited: the game exited (gdb's Inferior line)"
            except OSError:
                pass
        if why:
            stop["why"] = why
            print("WATCHDOG: %s; ending the session" % why, flush=True)
            if why == "cap":
                # stop logging at once: the slot stop kills gdb and the game
                subprocess.run(PY + [os.path.join(HERE, "slots.py"), "stop", str(stop["slot"])], cwd=ROOT,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
            p = holder.get("p")
            if p is not None:
                try:
                    p.kill()
                except OSError:
                    pass
            return


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds, limit = SESSIONS[name]
    path = os.path.join(saves, save + ".d2s")
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, path, steps, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    env = dict(os.environ, MONSPAWN_WATCH="")
    t_launch = time.time()
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 GDB, "--steps", os.path.join(HERE, "gdb", "%s.steps" % steps), "--after",
                                 str(limit + 600), "--install", tag, path, "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=env)
    t_entry = None
    while time.time() - t_launch < 240:
        time.sleep(3)
        hide_window(slot)
        try:
            if "PLR " in open(log, errors="replace").read():
                t_entry = time.time()
                break
        except OSError:
            pass
    if t_entry is None:
        t_entry = time.time()
        print("  no PLR line in 240 s", flush=True)
    time.sleep(3)
    hide_window(slot)
    holder, stop = {"p": None}, {"slot": slot}
    th = threading.Thread(target=watchdog, args=(log, holder, stop, limit, t_entry), daemon=True)
    th.start()
    for kind, args, timeout in cmds:
        if stop.get("why"):
            break
        left = limit - (time.time() - t_entry)
        if left <= 5:
            break
        rc = sh(PY + [os.path.join(HERE, "d2pilot.py"), args[0], log, "--slot", str(slot)] + args[1:] +
                ["--shots", shots], min(timeout, left), out, holder)
        print("  -> %s" % rc, flush=True)
    t_end = time.time()
    stop["done"] = True
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        drv.kill()
    out.close()
    f0, f1, lids = plr_frames(log)
    rec = {"session": name, "save": save, "steps": steps, "seed": seed, "log": os.path.basename(log),
           "wall_from_launch_s": round(t_end - t_launch, 1), "wall_from_entry_s": round(t_end - t_entry, 1),
           "gf_first": f0, "gf_last": f1,
           "game_min": round((f1 - f0) / 25.0 / 60.0, 2) if f0 is not None and f1 is not None else None,
           "bytes": os.path.getsize(log) if os.path.exists(log) else 0, "levels": lids,
           "ended": stop.get("why") or "commands done", "limit_s": limit}
    with open(os.path.join(LOGS, stem + ".session.json"), "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print("=== %s done: %s" % (name, json.dumps(rec, sort_keys=True)), flush=True)


def volume(paths):
    for p in paths:
        n, b = collections.Counter(), collections.Counter()
        for ln in open(p, "rb"):
            tag = ln.split(b" ", 1)[0][:12].decode("ascii", "replace").strip()
            n[tag] += 1
            b[tag] += len(ln)
        f0, f1, lids = plr_frames(p)
        gm = (f1 - f0) / 25.0 / 60.0 if f0 is not None and f1 is not None and f1 > f0 else None
        tot = sum(b.values())
        print("%s: %d lines, %.1f MB, game minutes %s, levels %s" % (os.path.basename(p), sum(n.values()), tot / 1e6,
                                                                     "%.2f" % gm if gm else "-", lids))
        if gm:
            print("  MB per game minute %.2f" % (tot / 1e6 / gm))
        for tag, c in sorted(n.items(), key=lambda kv: -b[kv[0]])[:40]:
            print("  %-12s %9d lines %8.2f MB" % (tag, c, b[tag] / 1e6))
    return 0


def table(paths):
    """A markdown row per session record (.session.json)."""
    print("| Log | Seed | Character | Difficulty | Levels (PLR order) | Wall min | Game min | MB | Ended |")
    print("|---|---|---|---|---|---|---|---|---|")
    for p in paths:
        r = json.load(open(p))
        print("| `%s` | %d | %s | %s | %s | %.1f | %s | %.1f | %s |" % (
            r["log"], r["seed"], r["save"], r["steps"].replace("enter-", ""), ", ".join(map(str, r["levels"])),
            r["wall_from_entry_s"] / 60.0, r["game_min"], r["bytes"] / 1e6, r["ended"]))
    return 0


def main(argv):
    if argv and argv[0] == "table":
        return table(argv[1:])
    if not argv or argv[0] not in ("list", "run", "volume"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-10s %-12s %-16s %d %d step(s) %ds" % (k, v[0], v[1], v[2], len(v[3]), v[4]))
        return 0
    if argv[0] == "volume":
        return volume(argv[1:])
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

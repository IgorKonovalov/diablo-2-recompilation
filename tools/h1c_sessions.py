#!/usr/bin/env python3
"""Session runner for plan 0038 batch H1c (run:2026-10-27-sweep-d2s-legacy): loads of tool-built saves
(tools/d2s.py build) under tools/gdb/d2s-h1c.gdb on one harness slot.

    for r in leg87merc leg87new leg71merc leg71uniq leg92props leg71sock leg71act2: python3 -I tools/d2s.py build <excel-dir> tools/d2s_recipes/$r.json workspace/samples/d2s-owner/smpsor-l50.d2s workspace/runtime/h1c/$r/<Name>.d2s
    python3 -I tools/h1c_sessions.py list
    python3 -I tools/h1c_sessions.py run --slot N --tag TAG --cases DIR --run RUN [--only K,K..] NAME [NAME ...]

Each session: the slot's saves directory restored to TAG's aside and set aside again, the session's first listed
save installed alone (tools/d2run.py --install), the game started at the main menu (tools/gdb/h1a-menu.steps) with
the logger attached there, then one load per entry of the session's list, all in the same game process:

  (case, list, swap, diff, then)
    1. `list` (a case directory under DIR) is copied over the character's .d2s in the slot's saves directory
    2. SINGLE PLAYER (400, 307): the character screen reads that file (the client's checks, 0x00438F70 ->
       0x0043C8A0: length, magic, version, the class, level and status it shows)
    3. `swap` is copied over the same file (the swap: the server's reader then reads it, while the client's
       choices - the character's name, status and the difficulty offered - come from `list`)
    4. OK (690, 556), and the difficulty `diff` (normal 280 | nightmare 315 | hell 350 | none)
    5. waits for the next PLD line (ClientAddPlayerToGame's PlayerLoad result) or 40 s
    6. `then` = "savexit": Save and Exit (two WDONE lines), the written file kept as workspace/logs/h1c/<stem>-saves/<case>/;
       `then` = "menu": screenshots and a click on empty background (a failed load is back at the main menu);
       a load that passed is saved and exited all the same, its file not kept
    7. when the game process is gone (a halt), the session stops after that case
Each case's first log line is recorded in workspace/logs/h1c/<stem>.marks.jsonl. The copies are made by this runner into the slot's saves directory only while TAG is set aside (the session's own
characters; tools/saves.py restores the directory at the next session and at the end). The session ends with
tools/slots.py stop N. Stdlib only.
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

import slots  # noqa: E402
from h1a_sessions import wait_ready  # noqa: E402  (the RDY start wait, shared with H1a)

PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h1c")
DIFF_Y = {"normal": 280, "nightmare": 315, "hell": 350}

# name: (character name, seed, loads); one build per session, listed and swapped as the same file
SESSIONS = {
    "leg87merc": ("Leg87Merc", 27301, [("leg87merc", "leg87merc", "leg87merc", "normal", "savexit")]),
    "leg87new": ("Leg87New", 27302, [("leg87new", "leg87new", "leg87new", "normal", "savexit")]),
    "leg71merc": ("Leg71Merc", 27303, [("leg71merc", "leg71merc", "leg71merc", "normal", "savexit")]),
    "leg71uniq": ("Leg71Uniq", 27304, [("leg71uniq", "leg71uniq", "leg71uniq", "normal", "savexit")]),
    "leg92props": ("Leg92Props", 27305, [("leg92props", "leg92props", "leg92props", "normal", "savexit")]),
    "leg71act2": ("Leg71Act2", 27307, [("leg71act2", "leg71act2", "leg71act2", "normal", "savexit")]),
    "leg71sock": ("Leg71Sock", 27306, [("leg71sock", "leg71sock", "leg71sock", "normal", "savexit")]),
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


def lines(log, tag):
    try:
        return [ln for ln in open(log, errors="replace") if ln.startswith(tag + " ")]
    except OSError:
        return []


def wait_count(log, tag, n, secs):
    t0 = time.time()
    while time.time() - t0 < secs:
        if len(lines(log, tag)) >= n:
            return True
        time.sleep(0.5)
    return False


def run_session(name, slot, tag, cases, run, only=None):
    cname, seed, loads = SESSIONS[name]
    if only:
        loads = [ld for ld in loads if ld[0] in only]
    saves_dir = slots.saves_dir(slot, os.path.join(ROOT, "workspace"))
    target = os.path.join(saves_dir, cname + ".d2s")

    def src(case):
        return os.path.join(cases, case, cname + ".d2s")

    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    shots = os.path.join(LOGS, stem + "-shots")
    keep = os.path.join(LOGS, stem + "-saves")
    marks = os.path.join(LOGS, stem + ".marks.jsonl")
    os.makedirs(shots, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".pilot.txt"), "a")
    print("=== %s: %s, seed %d -> %s" % (name, cname, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    if sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60) != 0:
        print("aside refused; stop", flush=True)
        return 1
    drv = subprocess.Popen(PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 os.path.join(HERE, "gdb", "d2s-h1c.gdb"), "--steps",
                                 os.path.join(HERE, "gdb", "h1a-menu.steps"), "--after", "3000",
                                 "--install", tag, src(loads[0][1]), "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t1 = time.time()
    ok = wait_ready(log, 120, gone=lambda: drv.poll() is not None, tick=lambda: hide_window(slot))
    print("  %s after %.0f s" % ("RDY seen" if ok else "no RDY line", time.time() - t1), flush=True)
    if drv.poll() is not None:
        print("  driver gone before the first case: stop", flush=True)
        out.close()
        return 1
    time.sleep(8)   # the steps file starts up to --attach-wait (5 s) after the exec of gdb and lasts 2 s
    hide_window(slot)

    def xd(*a):
        return sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + list(a),
                  30, out)

    def put(case):
        shutil.copyfile(src(case), target)
        print("  copied %s -> %s" % (src(case), target), flush=True)

    for case, lst, swap, diff, then in loads:
        print("--- %s: list %s, swap %s, %s, %s" % (case, lst, swap, diff, then), flush=True)
        with open(marks, "a") as fm:  # where each case starts in the log: its line count before the case
            nl = sum(1 for _ in open(log, errors="replace")) if os.path.exists(log) else 0
            fm.write(json.dumps({"case": case, "list": lst, "swap": swap, "diff": diff, "then": then,
                                 "line": nl, "time": time.time()}) + "\n")
        n0 = len(lines(log, "PLD"))
        put(lst)
        xd("click", "700", "150")
        time.sleep(1)
        xd("click", "400", "307")
        time.sleep(3)
        xd("shot", os.path.join(shots, "%s-list.png" % case))
        put(swap)
        xd("click", "690", "556")
        time.sleep(2)
        if diff in DIFF_Y:
            xd("click", "400", str(DIFF_Y[diff]))
        ok = wait_count(log, "PLD", n0 + 1, 40)
        pld = lines(log, "PLD")
        code = json.loads(pld[-1].split(" ", 1)[1])["code"] if ok else None
        print("  PLD %s -> code %s" % ("seen" if ok else "missing", code), flush=True)
        if code == 0 and then == "savexit":
            time.sleep(10)
            xd("shot", os.path.join(shots, "%s-ingame.png" % case))
            n0w = len(lines(log, "WDONE"))
            for _ in range(4):
                xd("key", "Escape")
                time.sleep(1.5)
                xd("click", "400", "268")
                if wait_count(log, "WDONE", n0w + 2, 30):
                    break
            time.sleep(6)
            dst = os.path.join(keep, case, cname + ".d2s")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(target):
                shutil.copyfile(target, dst)
                print("  kept %s" % dst, flush=True)
        else:
            time.sleep(6)
            xd("shot", os.path.join(shots, "%s-after.png" % case))
            if code != 0:
                xd("click", "700", "150")   # empty background (an error box, if one were up, shows in the shots
                time.sleep(2)               # before and after)
                xd("shot", os.path.join(shots, "%s-after2.png" % case))
            else:
                n0w = len(lines(log, "WDONE"))
                xd("key", "Escape")
                time.sleep(1.5)
                xd("click", "400", "268")
                wait_count(log, "WDONE", n0w + 2, 30)
                time.sleep(6)
        hide_window(slot)
        if drv.poll() is not None:
            print("  driver gone after %s: stop" % case, flush=True)
            break
    xd("shot", os.path.join(shots, "end.png"))
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()
    return 0


def main(argv):
    if not argv or argv[0] not in ("list", "run"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-8s %-16s %d %s" % (k, v[0], v[1], " ".join(ld[0] for ld in v[2])))
        return 0
    a = argv[1:]
    opt, names, k = {}, [], 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--cases", "--run", "--only"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        else:
            names.append(a[k])
            k += 1
    if not names or any(n not in SESSIONS for n in names) or not {"slot", "tag", "cases", "run"} <= set(opt):
        print(__doc__)
        return 2
    if int(opt["slot"]) == 0:
        print("slot 0 is the owner's")
        return 2
    only = set(opt["only"].split(",")) if "only" in opt else None
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], opt["cases"], opt["run"], only)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

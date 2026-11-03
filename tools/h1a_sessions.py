#!/usr/bin/env python3
"""Session runner for plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load): loads of tool-built saves
(tools/h1a_saves.py) under tools/gdb/d2s-h1a.gdb on one harness slot.

    python3 -I tools/h1a_saves.py <excel-dir> workspace/runtime/h1a      # the cases
    python3 -I tools/h1a_sessions.py list
    python3 -I tools/h1a_sessions.py run --slot N --tag TAG --cases DIR --run RUN [--only K,K..] [--status F]
                                         NAME [NAME ...]

Written on the shared runner library tools/harness_runner.py (plan 0056 Phase 1, its worked example): install, launch,
the RDY wait, the case marks, stop and the batch come from there; the session table and the load steps below are this
runner's own. The kept H1a logs (run:2026-10-27-sweep-d2s-load) were made by the pre-library revision at main
efac8f91, whose steps and timings these are unchanged.

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
    6. `then` = "savexit": Save and Exit (two WDONE lines), the written file kept as workspace/logs/h1a/<stem>-saves/<case>/;
       `then` = "menu": screenshots and a click on empty background (a failed load is back at the main menu);
       a load that passed is saved and exited all the same, its file not kept
    7. when the game process is gone (a halt), the session stops after that case
Each case's first log line is recorded in workspace/logs/h1a/<stem>.marks.jsonl (tools/sweep_h1a.py reads it), and
the library's marks (launch, ready, each case's start and end) in <stem>.marks.tsv. The copies are made by this runner
into the slot's saves directory only while TAG is set aside (the session's own characters; tools/saves.py restores the
directory at the next session and at the end). The session ends with tools/slots.py stop N, confirmed idle. The names
run as one batch (hr.batch): one status file at the end, workspace/logs/h1a/<RUN>-s<N>.status.json unless --status
names another (a session is kept when every load ran and the slot stopped idle; a halt after a case is a kept end).
Stdlib only.
"""
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import harness_runner as hr  # noqa: E402
import slots  # noqa: E402

PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h1a")
DIFF_Y = {"normal": 280, "nightmare": 315, "hell": 350}

MAIN = [
    ("magic", "base", "magic", "none", "menu"),
    ("short", "base", "short", "none", "menu"),
    ("v97", "base", "v97", "none", "menu"),
    ("v91", "base", "v91", "none", "menu"),
    ("class8", "base", "class8", "none", "menu"),
    ("hcon", "base", "hc", "none", "menu"),
    ("hcsoft", "hc", "base", "none", "menu"),
    ("hcdead", "hc", "hcdead", "none", "menu"),
    ("clson", "base", "classic", "none", "menu"),
    ("expon", "classic", "base", "none", "menu"),
    ("prog4", "prog5", "prog4", "nightmare", "menu"),
    ("prog0", "prog10", "base", "hell", "menu"),
    ("both", "base", "both", "none", "menu"),
    ("wpbad", "base", "wpbad", "none", "menu"),
    ("stubtrail", "base", "stubtrail", "none", "menu"),
    ("bigbad", "base", "bigbad", "none", "menu"),
    ("setbad", "base", "setbad", "none", "menu"),
    ("big8k", "base", "big8k", "none", "savexit"),
    ("fields", "base", "fields", "none", "savexit"),
    ("skills29", "base", "skills29", "none", "savexit"),
    ("items", "base", "items", "none", "savexit"),
    ("v94", "base", "v94", "none", "savexit"),
    ("prog5", "prog5", "prog5", "nightmare", "savexit"),
    ("prog10", "prog10", "prog10", "hell", "savexit"),
    ("stubok", "base", "stubok", "none", "savexit"),
    ("uniqbad", "base", "uniqbad", "none", "savexit"),
]

# name: (character name, seed, loads)
SESSIONS = {
    "main": ("qitsor", 27201, MAIN),
    "stub7": ("qitsor", 27205, [("stub7", "base", "stub7", "none", "savexit")]),
    "name15": ("qitsorfifteenzz", 27202, [("name15", "name15", "name15", "none", "savexit")]),
    "mercmf": ("MercMF", 27203, [("mercmf", "mercmf", "mercmf", "normal", "savexit")]),
    "order": ("qitsor", 27204, [("hdrshort", "base", "hdrshort", "none", "menu"),
                                ("v97sum", "base", "v97sum", "none", "menu"),
                                ("namehc", "base", "namehc", "none", "menu"),
                                ("class8hc", "base", "class8hc", "none", "menu"),
                                ("param", "base", "param", "none", "savexit"),
                                ("slots8", "base", "slots8", "none", "savexit"),
                                ("v94s12", "base", "v94s12", "none", "savexit"),
                                ("act6", "base", "act6", "none", "savexit"),
                                ("class7", "base", "class7", "none", "savexit")]),
}


sh = hr.sh
hide_window = hr.hide_window
lines = hr.lines

READY = "RDY"   # the logger's ready line: tools/gdb/d2s-h1a.gdb (and d2s-h1c.gdb) echo it once every logger file
#                is sourced, right before `continue`. It keys the start wait on a line that precedes the first case:
#                the TBL lines this wait once counted come only from a load, which the runner itself starts.


def wait_ready(log, secs, gone=lambda: False, tick=lambda: None, step=0.5):
    """The library's wait (tools/harness_runner.py) on the RDY line, as a bool: True once the log holds it, False
    when the driver is gone (without waiting out secs) or secs pass. tools/h1c_sessions.py imports it."""
    return hr.wait_ready(log, READY, secs, gone=gone, tick=tick, step=step) == hr.READY


def run_session(name, slot, tag, cases, run, only=None):
    """One session on the library (tools/harness_runner.py): install, launch, the RDY wait, the loads, stop.
    True when every load ran and the slot stopped idle; (False, why) otherwise."""
    cname, seed, loads = SESSIONS[name]
    if only:
        loads = [ld for ld in loads if ld[0] in only]
    saves_dir = slots.saves_dir(slot, os.path.join(ROOT, "workspace"))
    target = os.path.join(saves_dir, cname + ".d2s")

    def src(case):
        return os.path.join(cases, case, cname + ".d2s")

    stem = hr.new_stem(LOGS, run, slot, seed, name)
    log = stem + ".log"
    shots = stem + "-shots"
    keep = stem + "-saves"
    marks = stem + ".marks.jsonl"   # the checker's input (tools/sweep_h1a.py); <stem>.marks.tsv is the library's
    os.makedirs(shots, exist_ok=True)
    out = open(stem + ".pilot.txt", "a")
    print("=== %s: %s, seed %d -> %s" % (name, cname, seed, log), flush=True)
    try:
        hr.install(slot, tag)
    except hr.HarnessError as e:
        print("%s; stop" % e, flush=True)
        out.close()
        return False, str(e)
    drv = hr.launch(slot, seed, log, gdb=os.path.join(HERE, "gdb", "d2s-h1a.gdb"),
                    steps=os.path.join(HERE, "gdb", "h1a-menu.steps"), after=3000, install=(tag, [src(loads[0][1])]),
                    out=out, stem=stem)
    t1 = time.time()
    r = hr.wait_ready(log, READY, 120, proc=drv, tick=lambda: hide_window(slot))
    print("  %s after %.0f s" % ({hr.READY: "RDY seen", hr.TIMEOUT: "no RDY line", hr.GONE: "driver gone"}[r],
                                 time.time() - t1), flush=True)
    hr.mark(stem, "-", "ready" if r == hr.READY else "fail", log, r)
    if drv.poll() is not None:
        print("  driver gone before the first case: stop", flush=True)
        hr.stop(slot, drv, out=out)
        out.close()
        return False, "driver gone before the first case"
    time.sleep(8)   # the steps file starts up to --attach-wait (5 s) after the exec of gdb and lasts 2 s
    hide_window(slot)

    def xd(*a):
        return sh(PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"] + list(a),
                  30, out)

    def put(case):
        shutil.copyfile(src(case), target)
        print("  copied %s -> %s" % (src(case), target), flush=True)

    ran, why = 0, ""
    for case, lst, swap, diff, then in loads:
        print("--- %s: list %s, swap %s, %s, %s" % (case, lst, swap, diff, then), flush=True)
        with open(marks, "a") as fm:  # where each case starts in the log: its line count before the case
            nl = hr.line_count(log)
            fm.write(json.dumps({"case": case, "list": lst, "swap": swap, "diff": diff, "then": then,
                                 "line": nl, "time": time.time()}) + "\n")
        hr.mark(stem, case, "start", log, "list=%s swap=%s diff=%s then=%s" % (lst, swap, diff, then))
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
        ok = hr.wait_count(log, "PLD", n0 + 1, 40)
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
                if hr.wait_count(log, "WDONE", n0w + 2, 30):
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
                hr.wait_count(log, "WDONE", n0w + 2, 30)
                time.sleep(6)
        hide_window(slot)
        ran += 1
        if drv.poll() is not None:
            # a halt (class7, stub7) is a case's expected end: the case is logged, the session stops after it
            hr.mark(stem, case, "end", log, "pld=%s driver gone" % code)
            print("  driver gone after %s: stop" % case, flush=True)
            why = "driver gone after %s" % case
            break
        hr.mark(stem, case, "end", log, "pld=%s" % code)
    xd("shot", os.path.join(shots, "end.png"))
    idle = hr.stop(slot, drv, out=out)
    out.close()
    if not idle:
        return False, "slot %d not idle after stop" % slot
    return True, "%d of %d loads%s" % (ran, len(loads), "; " + why if why else "")


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
        if a[k] in ("--slot", "--tag", "--cases", "--run", "--only", "--status"):
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
    slot = int(opt["slot"])
    os.makedirs(LOGS, exist_ok=True)
    status = opt.get("status") or os.path.join(LOGS, "%s-s%d.status.json" % (opt["run"], slot))
    st = hr.batch(names, lambda n: run_session(n, slot, opt["tag"], opt["cases"], opt["run"], only), status)
    print("BATCH %s -> %s" % (hr.summary(st), status), flush=True)
    return 0 if st["done"] and not st["failed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

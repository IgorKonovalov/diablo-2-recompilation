#!/usr/bin/env python3
"""Scripted harness sessions for plan 0038 batch H3b (data-load): one program run per session on one slot, gdb on the
game from before its startup code (tools/d2run.py --early), logged by tools/gdb/excel.gdb (pilot.py, strings.py,
excel.py), driven by xdrive steps files (tools/gdb/h3b-*.steps); no pilot play.

Usage:
  python3 -I tools/h3b_sessions.py list
  python3 -I tools/h3b_sessions.py stage --slot N        # make the session game directories in the slot's prefix
  python3 -I tools/h3b_sessions.py unstage --slot N      # remove them (and every file a session wrote there)
  python3 -I tools/h3b_sessions.py run --slot N --tag TAG --save FILE.d2s --run RUN SESSION [SESSION ...]

Game directories (stage): all under <prefix of slot N>/h3b/, never in the shared workspace/runtime/game, each holding a
symlink to every entry of workspace/runtime/game plus its own files:
  txt     an empty data/global/excel/ for the .bin files a -txt compile writes;
  loose   data/global/excel/difficultylevels.bin = the archive copy (workspace/merged) + 4 zero bytes (same records,
          another size), data/local/lng/eng/patchstring.tbl = tools/tbl_crc_case.py's "bad" variant (one value byte
          changed, stock crc kept: a load of it is fatal), data/local/use = 0x0B (RUS; the slot has no rus tables);
  direct  the same .bin, tbl_crc_case.py's "fixed" variant (crc recomputed), data/local/use = 00 00 00 00 (ENG, 4
          bytes against the archive copy's 1);
  rus     data/local/use = 0x0B only (run with -direct: RUS, whose tables the install does not have);
  clamp   data/local/use = 0x0E only (run with -direct: 14, above the clamp bound 13).
The stock session runs in workspace/runtime/game itself (read only: nothing is written there but the game's own
BnetLog/key files).

Each SESSION row of SESSIONS: game directory, extra game switches, map seed, and phases. Phase "steps F" plays the
steps file F through tools/xdrive.py; "wait_plr" waits (at most 300 s) for the first PLR line (in game); "sleep S".
The first phase is d2run's own --steps (the menu to the game). The log goes to workspace/logs/h3b/<RUN>-s<slot>-<seed>-
<SESSION>.log, the record dumps (H3B_DUMP) to <same stem>-dump/, the screenshots to <stem>-shots/. After the last
phase the session waits for the game to exit (the quit steps) at most 90 s, then stops the slot (tools/slots.py stop
N) and returns its saves directory to the TAG aside. Nothing here feeds a model.
"""
import glob
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGS = os.path.join(ROOT, "workspace", "logs", "h3b")
SHOTS = os.path.join(LOGS, "shots")
GAME = os.path.join(ROOT, "workspace", "runtime", "game")
MERGED = os.path.join(ROOT, "workspace", "merged")
GDB = os.path.join(HERE, "gdb", "excel.gdb")
PAD_TABLE = "difficultylevels"


def steps(name):
    return ("steps", os.path.join(HERE, "gdb", "h3b-%s.steps" % name))


ENTER = os.path.join(HERE, "gdb", "enter-normal.steps")
PLAY = [("wait_plr", None), ("sleep", 10), steps("hover"), steps("leave")]
SESSIONS = {
    # stock start (startup rows), the rare-item hover, the item-code and TC-name lookups in play, the video archive on
    # demand (a cinematic from the main menu), program exit (excel unload, STRTABLE_Unload)
    "stock": ("stock", "", 3101, PLAY + [steps("cine"), steps("quit")]),
    # -txt without -direct: the .txt compile writes .bin files into the session directory; the game still loads the
    # archive .bin
    "txt": ("txt", "-txt", 3102, [("wait_plr", None), ("sleep", 5), steps("leave"), steps("quit")]),
    # loose files without -direct: none is read
    "loose": ("loose", "", 3103, [("wait_plr", None), ("sleep", 5), steps("leave"), steps("quit")]),
    # the same kind of loose files with -direct (the control): each is read from disk
    "direct": ("direct", "-direct", 3104, [("wait_plr", None), ("sleep", 5), steps("leave"), steps("quit")]),
    # -direct -txt: the compiled .bin files are written to disk and then read from there
    "dtxt": ("txt", "-direct -txt", 3105, [("wait_plr", None), ("sleep", 5), steps("leave"), steps("quit")]),
    # -direct with a loose use byte 0x0B (RUS): the slot has no lng\rus tables, so the string-table load fails
    "rus": ("rus", "-direct", 3106, [("wait_plr", None)]),
    # -direct with a loose use byte 0x0E (14, above 13): clamped to 0
    "clamp": ("clamp", "-direct", 3107, [("wait_plr", None), ("sleep", 5), steps("leave"), steps("quit")]),
}


def slot_root(slot):
    return os.path.join(ROOT, "workspace", "wineprefix-%d" % slot, "h3b")


def game_dir(slot, kind):
    return GAME if kind == "stock" else os.path.join(slot_root(slot), "game-" + kind)


def link_game(dst):
    os.makedirs(dst)
    for e in sorted(os.listdir(GAME)):
        if e in ("BlizzardError",):
            continue
        os.symlink(os.path.join(GAME, e), os.path.join(dst, e))


def put(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def cmd_stage(slot):
    root = slot_root(slot)
    if os.path.exists(root):
        sys.exit("%s exists: unstage first" % root)
    os.makedirs(root)
    tbl = os.path.join(MERGED, "data", "local", "lng", "eng", "patchstring.tbl")
    subprocess.run(PY + [os.path.join(HERE, "tbl_crc_case.py"), GAME, tbl, root], check=True)
    # tbl_crc_case.py makes game-tbl-fixed/ and game-tbl-bad/ (symlinks + the loose patchstring.tbl)
    os.rename(os.path.join(root, "game-tbl-bad"), os.path.join(root, "game-loose"))
    os.rename(os.path.join(root, "game-tbl-fixed"), os.path.join(root, "game-direct"))
    pad = open(os.path.join(MERGED, "data", "global", "excel", PAD_TABLE + ".bin"), "rb").read() + b"\0" * 4
    for kind, use in (("loose", b"\x0b"), ("direct", b"\0\0\0\0")):
        d = os.path.join(root, "game-" + kind)
        put(os.path.join(d, "data", "global", "excel", PAD_TABLE + ".bin"), pad)
        put(os.path.join(d, "data", "local", "use"), use)
    for kind, use in (("rus", b"\x0b"), ("clamp", b"\x0e")):
        link_game(os.path.join(root, "game-" + kind))
        put(os.path.join(root, "game-" + kind, "data", "local", "use"), use)
    link_game(os.path.join(root, "game-txt"))
    os.makedirs(os.path.join(root, "game-txt", "data", "global", "excel"))
    for p in sorted(glob.glob(os.path.join(root, "game-*", "data", "**", "*"), recursive=True)):
        if os.path.isfile(p):
            print("%s %d" % (os.path.relpath(p, root), os.path.getsize(p)))
    return 0


def cmd_unstage(slot):
    root = slot_root(slot)
    if os.path.isdir(root):
        shutil.rmtree(root)
        print("removed %s" % root)
    return 0


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                              timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def log_has(log, needle):
    try:
        with open(log, "rb") as f:
            return needle in f.read()
    except OSError:
        return False


def game_gone(log):
    try:
        with open(log, "rb") as f:
            f.seek(max(0, os.path.getsize(log) - 4096))
            t = f.read()
        return b"[Inferior " in t and b" exited" in t
    except OSError:
        return False


def run_session(name, slot, tag, save, run):
    kind, args, seed, phases = SESSIONS[name]
    gd = game_dir(slot, kind)
    if not os.path.isdir(gd):
        sys.exit("no game directory %s (stage first)" % gd)
    os.makedirs(LOGS, exist_ok=True)
    stem = "%s-s%d-%d-%s" % (run, slot, seed, name)
    k = 2
    while os.path.exists(os.path.join(LOGS, stem + ".log")):
        stem = "%s-s%d-%d-%s-r%d" % (run, slot, seed, name, k)
        k += 1
    log = os.path.join(LOGS, stem + ".log")
    dump = os.path.join(LOGS, stem + "-dump")
    shots = os.path.join(LOGS, stem + "-shots")
    os.makedirs(dump)
    os.makedirs(shots)
    os.makedirs(SHOTS, exist_ok=True)
    out = open(os.path.join(LOGS, stem + ".driver.txt"), "a")
    print("=== %s: %s %r seed %d -> %s" % (name, gd, args, seed, log), flush=True)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "aside", tag], 60)
    env = dict(os.environ, H3B_DUMP=dump)
    argv = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(slot), "--early", "--seed", str(seed), "--gdb", GDB,
                 "--steps", ENTER, "--after", "1800", "--install", tag, save, "--log", log, "--game-dir", gd]
    if args:
        argv += ["--game-args=" + args]
    print("$ " + " ".join(argv), flush=True)
    drv = subprocess.Popen(argv, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True, env=env)
    xd = PY + [os.path.join(HERE, "xdrive.py"), "--slot", str(slot), "--window", "Diablo II"]
    ok = True
    for ph, arg in phases:
        if game_gone(log):
            print("  the game exited before phase %s %s" % (ph, arg or ""), flush=True)
            ok = False
            break
        if ph == "wait_plr":
            t0 = time.time()
            while time.time() - t0 < 300 and not log_has(log, b"\nPLR ") and not game_gone(log):
                time.sleep(2)
            print("  in game after %.0f s: %s" % (time.time() - t0, log_has(log, b"\nPLR ")), flush=True)
            if not log_has(log, b"\nPLR "):
                ok = False
                break
        elif ph == "sleep":
            time.sleep(arg)
        elif ph == "steps":
            sh(xd + ["run", arg], 300, out)
            for p in glob.glob(os.path.join(SHOTS, "*.png")):
                shutil.move(p, os.path.join(shots, os.path.basename(p)))
    t0 = time.time()
    while ok and time.time() - t0 < 90 and not game_gone(log):
        time.sleep(2)
    print("  game exited by itself: %s" % game_gone(log), flush=True)
    sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        drv.kill()
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag], 60)
    out.close()
    print("=== %s done" % name, flush=True)


def main(argv):
    if not argv or argv[0] not in ("list", "run", "stage", "unstage"):
        print(__doc__)
        return 2
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-7s %-7s %-8r %d %s" % (k, v[0], v[1], v[2], " ".join(p[0] for p in v[3])))
        return 0
    a = argv[1:]
    opt, names, k = {}, [], 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--save", "--run"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        else:
            names.append(a[k])
            k += 1
    if argv[0] in ("stage", "unstage"):
        if set(opt) != {"slot"} or int(opt["slot"]) < 1:
            print(__doc__)
            return 2
        return (cmd_stage if argv[0] == "stage" else cmd_unstage)(int(opt["slot"]))
    if not names or any(n not in SESSIONS for n in names) or set(opt) != {"slot", "tag", "save", "run"}:
        print(__doc__)
        return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], os.path.abspath(opt["save"]), opt["run"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

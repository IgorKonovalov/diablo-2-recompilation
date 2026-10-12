#!/usr/bin/env python3
"""Screen-driven helpers for the wine harness display (kill loop, waypoint finder, play recorder).

    python3 -I tools/d2hunt.py hunt   <seconds> [--log LOG] [--tag TCR] [--button 1|3] [dir ...]
    python3 -I tools/d2hunt.py findwp
    python3 -I tools/d2hunt.py wpmenu
    python3 -I tools/d2hunt.py record <out-dir>
    python3 -I tools/d2hunt.py relaunch <seconds> [--row Y] [--enter S] [--button 1|3] [--hunt S]
                                        [--dirs n,e,s,w] -- <tools/d2run.py arguments with {n}>

All coordinates are relative to the 800x600 "Diablo II" window on the harness display (default :7,
--display to change); input goes through tools/xdrive.py (XTEST). Nothing here reads game memory:
pair it with tools/d2run.py and a gdb logger. First used (as session scratch scripts) in
run:2026-10-11-tc-drops (plan 0004 Phase 2, docs/findings/items/experiments.md), committed for plan 0011
and the monster plans.

hunt    Hover-scan kill loop. Moves the pointer over rings around the character (screen centre
        400,270); when the game's top-centre monster name bar (dark red, RGB about 56,8,4) shows,
        holds a mouse button on that point for 1.6 s (--button 3 = right skill, e.g. War Cry; default 1).
        Otherwise walks one step, cycling through the directions given (n ne e se s sw w nw; default
        n e s w), three steps per direction. Stops after <seconds>, or when the life globe looks empty
        (exit 2). With --log, prints how many lines of the log start with --tag (default TCR).
findwp  Walks to the town waypoint by sight: looks for its two blue flames (b > 200, b - r > 50,
        g > 120) and clicks under their centre; otherwise walks a growing W/N/E/S spiral. Exit 0
        once `wpmenu` sees the menu, 1 after 32 tries.
wpmenu  Exit 0 if the waypoint menu is open (the blue first row of the Act tab at 160,132).
record  Records an owner-played session: window-relative pointer position and button mask every
        0.2 s to <out-dir>/input.tsv (mask bit 8 left, 10 right), a screenshot every 10 s
        (<out-dir>/shot-NNNNN.png), until the game window disappears.

relaunch  The unattended session loop of run:2026-10-11-tc-drops (sessions 4-5), committed for plan 0011.
        Runs tools/d2run.py with the given arguments (every "{n}" replaced by the attempt number, so
        --log workspace/logs/x-{n}.log gives one log per attempt), waits --enter seconds (default 60:
        attach + menu steps), then `findwp`, clicks waypoint row Y of the Act tab (default 173 = Cold
        Plains; 208 Stony Field, 243 Dark Wood, 278 Black Marsh) and hunts for --hunt seconds (default
        600) or until the character dies. Then it ends that game with `wineserver -k` on the prefix
        d2run.py was given (its --prefix, default workspace/wineprefix), waits for the d2run.py process
        to exit, and starts the next attempt, until <seconds> have passed. A missed waypoint ends the
        attempt the same way. It never touches the saves directory: install the character first with
        tools/saves.py.

The pixel thresholds were tuned on the 1.14d game at 800x600 in run:2026-10-11-tc-drops; NPCs wander,
so findwp can need a rerun. Stdlib only.
"""
import ctypes as C
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import xdrive  # noqa: E402

CX, CY = 400, 270
DIRS = dict(n=(0, -1), ne=(1, -1), e=(1, 0), se=(1, 1), s=(0, 1), sw=(-1, 1), w=(-1, 0), nw=(-1, -1))


class Screen:
    def __init__(self, display):
        self.d = xdrive.Display(display)
        self.ox, self.oy = self.d.origin("Diablo II")

    def grab(self, x, y, w, h):
        """BGRX bytes of a window-relative rectangle, and the bytes per line."""
        img = xdrive.X11.XGetImage(self.d.d, self.d.root, self.ox + x, self.oy + y, w, h, 0xFFFFFFFF, 2)
        im = xdrive.XImage.from_address(img)
        raw = C.string_at(im.data, im.bytes_per_line * h)
        bpl = im.bytes_per_line
        xdrive.X11.XFree.argtypes = [C.c_void_p]
        xdrive.X11.XFree(C.cast(im.data, C.c_void_p))
        xdrive.X11.XFree(img)
        return raw, bpl

    def move(self, x, y):
        self.d.move(self.ox + x, self.oy + y)

    def press(self, x, y, hold, btn=1):
        self.move(x, y)
        time.sleep(0.12)
        xdrive.XTST.XTestFakeButtonEvent(self.d.d, btn, 1, 0)
        self.d.flush()
        time.sleep(hold)
        xdrive.XTST.XTestFakeButtonEvent(self.d.d, btn, 0, 0)
        self.d.flush()

    def click(self, x, y):
        self.d.click(self.ox + x, self.oy + y)

    def name_bar(self):
        """Pixels of the monster name bar on one row at the top centre."""
        raw, _ = self.grab(250, 26, 300, 1)
        n = 0
        for i in range(0, 1200, 8):
            b, g, r = raw[i], raw[i + 1], raw[i + 2]
            if 48 <= r <= 72 and g <= 24 and b <= 16:
                n += 1
        return n

    def alive(self):
        raw, _ = self.grab(55, 550, 30, 1)
        return sum(1 for i in range(0, 120, 4) if raw[i + 2] >= 70 and raw[i + 1] < 20) > 5

    def wp_menu(self):
        raw, bpl = self.grab(160, 132, 140, 14)
        n = sum(1 for y in range(14) for x in range(140) if raw[y * bpl + 4 * x] > 150 and raw[y * bpl + 4 * x + 2] < 120)
        return n > 100

    def flames(self):
        raw, bpl = self.grab(0, 0, 800, 500)
        pts = []
        for y in range(0, 500, 2):
            for x in range(0, 800, 2):
                o = y * bpl + 4 * x
                b, g, r = raw[o], raw[o + 1], raw[o + 2]
                if b > 200 and b - r > 50 and g > 120:
                    pts.append((x, y))
        return pts


def count_tag(log, tag):
    try:
        with open(log, errors="replace") as fh:
            return sum(1 for ln in fh if ln.startswith(tag))
    except OSError:
        return -1


def hunt(scr, seconds, dirs, button, log, tag):
    ring = [(int(CX + r * math.cos(a)), int(CY + r * 0.6 * math.sin(a)))
            for r in (45, 110, 190, 290) for a in [k * math.pi / 5 for k in range(10)]]
    dirs = dirs or ["n", "e", "s", "w"]
    end = time.time() + seconds
    step = hits = 0
    dead = False
    while time.time() < end:
        if not scr.alive():
            time.sleep(1.5)
            if not scr.alive():
                dead = True
                break
        found = False
        for (x, y) in ring:
            if not (10 < x < 790 and 40 < y < 500):
                continue
            scr.move(x, y)
            time.sleep(0.035)
            if scr.name_bar() > 12:
                scr.press(x, y, 1.6, button)
                hits += 1
                found = True
                break
        if not found:
            dx, dy = DIRS[dirs[(step // 3) % len(dirs)]]
            scr.press(CX + dx * 300, CY + dy * 190, 0.9)
            step += 1
    extra = f" {tag}={count_tag(log, tag)}" if log else ""
    print(f"attacks={hits} walks={step}{extra} dead={dead}")
    return 2 if dead else 0


def findwp(scr):
    legs = [(80, 250), (400, 60), (720, 250), (400, 460)]  # W N E S screen edges
    search = []
    for k in range(1, 8):
        search += [legs[(k - 1) % 4]] * ((k + 1) // 2)
    if scr.wp_menu():
        print("wp menu already open")
        return 0
    for t in range(32):
        p = scr.flames()
        if len(p) > 15:
            cx = sum(x for x, _ in p) // len(p)
            cy = sum(y for _, y in p) // len(p)
            scr.click(cx, min(cy + 15, 490))
            time.sleep(3.5)
            if scr.wp_menu():
                print("wp menu open after", t)
                return 0
            continue
        x, y = search[t % len(search)]
        scr.click(x, y)
        time.sleep(2.2)
    print("waypoint not found")
    return 1


def record(scr, out):
    X = xdrive.X11
    X.XQueryPointer.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong), C.POINTER(C.c_ulong),
                                C.POINTER(C.c_int), C.POINTER(C.c_int), C.POINTER(C.c_int),
                                C.POINTER(C.c_int), C.POINTER(C.c_uint)]
    os.makedirs(out, exist_ok=True)
    d = scr.d
    with open(os.path.join(out, "input.tsv"), "a", buffering=1) as f:
        f.write("# t\tx\ty\tmask\n")
        t0 = time.time()
        last_shot = 0
        n = 0
        rr, cc = C.c_ulong(), C.c_ulong()
        rx, ry, wx, wy, m = C.c_int(), C.c_int(), C.c_int(), C.c_int(), C.c_uint()
        prev = None
        while True:
            now = time.time()
            X.XQueryPointer(d.d, d.root, C.byref(rr), C.byref(cc), C.byref(rx), C.byref(ry),
                            C.byref(wx), C.byref(wy), C.byref(m))
            cur = (rx.value - scr.ox, ry.value - scr.oy, m.value & 0x1F00)
            if cur != prev:
                f.write("%.2f\t%d\t%d\t%x\n" % ((now - t0,) + cur))
                prev = cur
            if now - last_shot >= 10:
                if not d.find("Diablo II"):
                    break
                d.shot(os.path.join(out, "shot-%05d.png" % n), scr.ox, scr.oy, xdrive.GAME_W, xdrive.GAME_H)
                n += 1
                last_shot = now
            time.sleep(0.2)
    print("recorded", n, "shots")
    return 0


def relaunch(display, total, row, enter, button, hunt_s, dirs, run_args):
    root = os.path.dirname(HERE)
    prefix = os.path.join(root, "workspace", "wineprefix")
    if "--prefix" in run_args:
        prefix = os.path.abspath(run_args[run_args.index("--prefix") + 1])
    end = time.time() + total
    n = 0
    while time.time() < end:
        n += 1
        args = [a.replace("{n}", str(n)) for a in run_args]
        print(f"relaunch #{n}: d2run.py {' '.join(args)}", flush=True)
        proc = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "d2run.py")] + args,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        time.sleep(enter)
        rc = None
        if proc.poll() is None:
            scr = Screen(display)
            if findwp(scr) == 0:
                scr.click(200, row)
                time.sleep(6)
                rc = hunt(scr, min(hunt_s, max(0, end - time.time())), dirs, button, None, "TCR")
        print(f"relaunch #{n}: hunt rc={rc}", flush=True)
        subprocess.run(["wineserver", "-k"], env=dict(os.environ, WINEPREFIX=prefix), stderr=subprocess.DEVNULL)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            proc.kill()
        time.sleep(3)
    return 0


def take(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    argv = list(argv)
    display = take(argv, "--display", ":7")
    cmd = argv.pop(0)
    if cmd == "record" and len(argv) == 1:
        d = xdrive.Display(display)
        while not d.find("Diablo II"):
            time.sleep(2)
        return record(Screen(display), argv[0])
    if cmd == "hunt" and argv:
        log, tag = take(argv, "--log"), take(argv, "--tag", "TCR")
        button = int(take(argv, "--button", "1"))
        seconds = float(argv.pop(0))
        return hunt(Screen(display), seconds, argv, button, log, tag)
    if cmd == "relaunch" and "--" in argv:
        i = argv.index("--")
        run_args, argv = argv[i + 1:], argv[:i]
        row = int(take(argv, "--row", "173"))
        enter = float(take(argv, "--enter", "60"))
        button = int(take(argv, "--button", "1"))
        hunt_s = float(take(argv, "--hunt", "600"))
        dirs = take(argv, "--dirs", "n,e,s,w").split(",")
        if len(argv) == 1:
            return relaunch(display, float(argv[0]), row, enter, button, hunt_s, dirs, run_args)
    if cmd == "findwp" and not argv:
        return findwp(Screen(display))
    if cmd == "wpmenu" and not argv:
        ok = Screen(display).wp_menu()
        print("wpmenu", "open" if ok else "closed")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

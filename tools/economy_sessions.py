#!/usr/bin/env python3
"""Plan 0043 Phase 2 session driver: hover sweeps and clicks in an open trade or gamble window.

Usage:
  python3 -I tools/economy_sessions.py --slot N act TOKEN...
  python3 -I tools/economy_sessions.py --slot N tour --seed S --diff D --log LOG --save F.d2s ACT:NPC:KIND:TOK+TOK...
  python3 -I tools/economy_sessions.py --watchdog QUIET,LIMIT --slot N tour|die ...   # supervised (plan 0043 P2b)

tour plays one game: d2run.py with tools/gdb/economy.gdb and the save installed, then for each stop a waypoint hop to
the act's town (d2pilot.py wpchain), d2pilot.py npc NPC KIND --stay, the tokens (with "=" for ":" inside a token,
e.g. sell=9,0), Escape; then slots.py stop and saves.py restore.

Run it after `tools/d2pilot.py npc <log> <name> trade|gamble --stay` has opened the window. Each hover leaves the
pointer on a cell for --dwell seconds, during which the client prices the item under it every frame
(ITEMS_TradePriceCore, logged by tools/gdb/economy.py). Tokens:

  store[:T]      hover the 10 x 10 store grid of tab T (1..4; no T: every tab, clicking each tab first)
  grid           hover the 10 x 10 grid as it is (the gamble window has no tabs)
  inv            hover the 10 x 4 inventory grid
  equip          hover the ten paper-doll slots
  repair         click the repair button (single item), hover the inventory and paper doll, click it again
  repairall      hover the repair-all button, then click it (NpcRepair, packet bit 31)
  fix:inv:c,r    (plan 0043 Phase 2b) a single-item repair: click the repair button, then the inventory cell (c, r)
                 (NpcRepair with one item id); fix:eq:SLOT the same on a paper-doll slot
  hoverall       hover the repair-all button only
  sell:c,r       pick up the inventory item at cell (c, r) and click it onto the store grid (a sale)
  buy:T:c,r      right-click the store cell (c, r) of tab T (a purchase)
  click:x,y      left click (window-relative);  rclick:x,y right click;  key:NAME;  sleep:S;  shot:PATH

Window-relative coordinates on the 800 x 600 frame, measured from screenshots (run:2026-10-17-economy): store cell
(c, r) at (110 + 29c, 138 + 29r), tabs at x 122, 200, 281, 361 and y 74; inventory cell (c, r) at
(432 + 29c, 330 + 29r); buttons at y 461: buy 213, sell 264, repair 315, repair all 366. The paper doll as
tools/d2pilot.py insert's `eq:` cells. Nothing here feeds a model.
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import slots  # noqa: E402
import xdrive  # noqa: E402

TABS = [(122, 74), (200, 74), (281, 74), (361, 74)]
EQUIP = {"head": (562, 92), "tors": (562, 177), "rarm": (447, 163), "larm": (678, 163), "neck": (620, 104),
         "glov": (447, 266), "belt": (562, 252), "feet": (678, 266), "rrin": (505, 252), "lrin": (620, 252)}
B_REPAIR, B_REPAIRALL = (315, 461), (366, 461)


def store_xy(c, r):
    return 110 + 29 * c, 138 + 29 * r


def inv_xy(c, r):
    return 432 + 29 * c, 330 + 29 * r


class Drv:
    def __init__(self, display, dwell):
        self.dpy = xdrive.Display(display)
        self.off = self.dpy.origin("Diablo II")
        self.dwell = dwell

    def move(self, x, y, dwell=None):
        self.dpy.move(self.off[0] + x, self.off[1] + y)
        time.sleep(self.dwell if dwell is None else dwell)

    def click(self, x, y, button=1):
        self.dpy.click(self.off[0] + x, self.off[1] + y, button=button, hold=0.12)
        time.sleep(0.3)

    def grab(self, x0, y0, w, h):
        import ctypes as C
        img = xdrive.X11.XGetImage(self.dpy.d, self.dpy.root, self.off[0] + x0, self.off[1] + y0, w, h, 0xFFFFFFFF, 2)
        if not img:
            return None, 0
        im = xdrive.XImage.from_address(img)
        return C.string_at(im.data, im.bytes_per_line * h), im.bytes_per_line

    def occupied(self, x, y):
        """A grid cell holds an item: the mean of the brightest channel over a 13 x 13 patch at its centre is above
        26 (empty cells measure 15..20, item cells 30 and up, from screenshots of run:2026-10-17-economy)."""
        raw, bpl = self.grab(x - 6, y - 6, 13, 13)
        if raw is None:
            return True
        s = n = 0
        for yy in range(0, 13, 2):
            for xx in range(0, 13, 2):
                o = yy * bpl + 4 * xx
                s += max(raw[o], raw[o + 1], raw[o + 2])
                n += 1
        return s / n > 26

    def grid(self, xy, cols, rows):
        self.dpy.move(self.off[0] + 790, self.off[1] + 590)     # the pointer off the grid while it is sampled
        time.sleep(0.15)
        cells = [xy(c, r) for r in range(rows) for c in range(cols)]
        for x, y in [p for p in cells if self.occupied(*p)]:
            self.move(x, y)

    def equip(self):
        for xy in EQUIP.values():
            self.move(*xy)


def run(drv, tokens):
    for tok in tokens:
        kind, _, rest = tok.partition(":")
        if kind == "store":
            tabs = [int(rest)] if rest else [1, 2, 3, 4]
            for t in tabs:
                drv.click(*TABS[t - 1])
                drv.grid(store_xy, 10, 10)
        elif kind == "grid":
            drv.grid(store_xy, 10, 10)
        elif kind == "inv":
            drv.grid(inv_xy, 10, 4)
        elif kind == "equip":
            drv.equip()
        elif kind == "repair":
            drv.click(*B_REPAIR)
            drv.grid(inv_xy, 10, 4)
            drv.equip()
            drv.click(*B_REPAIR)
        elif kind == "fix":
            where, _, cell = rest.partition(":")
            xy = EQUIP[cell] if where == "eq" else inv_xy(*(int(v) for v in cell.split(",")))
            drv.click(*B_REPAIR)
            time.sleep(0.4)
            drv.move(*xy, dwell=0.4)
            drv.click(*xy)
            time.sleep(1.0)
        elif kind == "hoverall":
            drv.move(*B_REPAIRALL, dwell=0.6)
        elif kind == "repairall":
            drv.move(*B_REPAIRALL, dwell=0.6)
            drv.click(*B_REPAIRALL)
            time.sleep(0.5)
        elif kind == "sell":
            c, r = (int(v) for v in rest.split(","))
            drv.click(*inv_xy(c, r))
            time.sleep(0.3)
            drv.click(250, 250)
            time.sleep(0.5)
        elif kind == "buy":
            t, cr = rest.split(":")
            c, r = (int(v) for v in cr.split(","))
            drv.click(*TABS[int(t) - 1])
            drv.click(*store_xy(c, r), button=3)
            time.sleep(0.5)
        elif kind in ("click", "rclick"):
            x, y = (int(v) for v in rest.split(","))
            drv.click(x, y, button=1 if kind == "click" else 3)
        elif kind == "key":
            drv.dpy.key(rest)
            time.sleep(0.3)
        elif kind == "sleep":
            time.sleep(float(rest))
        elif kind == "shot":
            drv.dpy.shot(rest, drv.off[0], drv.off[1], 800, 600)
        else:
            raise SystemExit("unknown token %r" % tok)


# ------------------------------------------------------------------------------------------------ tours

ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
STEPS = {"normal": "tools/gdb/enter-normal.steps", "nightmare": "tools/gdb/enter-nightmare.steps",
         "hell": "tools/gdb/enter-hell.steps"}
TOWNS = {1: 1, 40: 2, 75: 3, 103: 4, 109: 5}


def sh(cmd, timeout=None):
    import subprocess
    print("+ " + " ".join(cmd), flush=True)
    try:
        return subprocess.run(cmd, cwd=ROOT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("  (timed out after %s s)" % timeout, flush=True)
        return 124


def tool(args, timeout=None):
    return sh(PY + [os.path.join(HERE, args[0])] + list(args[1:]), timeout=timeout)


def last(log, tag):
    v = None
    try:
        with open(log, errors="replace") as fh:
            for ln in fh:
                if ln.startswith(tag + " "):
                    v = ln
    except OSError:
        pass
    if v is None:
        return None
    import json
    try:
        return json.loads(v[len(tag) + 1:])
    except ValueError:
        return None


def launch(a):
    import subprocess
    if os.path.exists(a.log):
        # an older log of the same name would satisfy the PLR wait at once; keep it as a development log
        keep = a.log[:-4] + "-dev%d.log" % int(time.time()) if a.log.endswith(".log") else a.log + ".dev"
        os.rename(a.log, keep)
        print("launch: kept the older log as %s" % keep, flush=True)
    tool(["saves.py", "--slot", str(a.slot), "restore", a.tag])
    tool(["saves.py", "--slot", str(a.slot), "aside", a.tag])
    out = open(a.log + ".d2run.out", "w")
    cmd = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(a.slot), "--seed", str(a.seed), "--gdb", a.gdb,
                "--steps", STEPS[a.diff], "--after", str(a.after), "--install", a.tag] + a.save + ["--log", a.log]
    print("+ " + " ".join(cmd), flush=True)
    subprocess.Popen(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                     start_new_session=True)


def town(log):
    p = last(log, "PLR")
    return TOWNS.get(p["lid"]) if p else None


def go_town(a, act):
    for _ in range(3):
        if town(a.log) == act:
            return True
        tool(["d2pilot.py", "--slot", str(a.slot), "npc", a.log, "waypoint", "walk"], timeout=90)
        tool(["d2pilot.py", "--slot", str(a.slot), "wpchain", a.log, "--chain", "%d,1" % act], timeout=25)
        time.sleep(2)
    return town(a.log) == act


def cmd_tour(a, drv_factory):
    """One game: for each stop ACT:NPC:KIND:TOK+TOK..., hop to the act's town, open the NPC's window, play the
    tokens, close it with Escape."""
    launch(a)
    try:
        t0 = time.time()
        while time.time() - t0 < 150 and last(a.log, "PLR") is None:
            time.sleep(2)
        if last(a.log, "PLR") is None:
            print("tour: no PLR line")
            return 1
        time.sleep(3)
        drv = drv_factory()
        for stop in a.stops:
            act, npc, kind, toks = (stop.split(":", 3) + [""])[:4]
            if not go_town(a, int(act)):
                print("tour: did not reach act %s for %s" % (act, npc), flush=True)
                continue
            kind, _, item = kind.partition("@")      # plan 0043 P2b: imbue@inv=0,0 -> imbue --item inv:0,0
            extra = ["--item", item.replace("=", ":")] if item else ["--stay"]
            rc = tool(["d2pilot.py", "--slot", str(a.slot), "npc", a.log, npc, kind] + extra, timeout=180)
            if rc != 0:
                print("tour: %s %s did not open (rc %d)" % (npc, kind, rc), flush=True)
                drv.dpy.key("Escape")
                continue
            if toks:
                run(drv, [t.replace("=", ":") for t in toks.split("+")])
            drv.dpy.key("Escape")
            time.sleep(1.0)
        return 0
    finally:
        if not a.keep:
            tool(["slots.py", "stop", str(a.slot)])
            time.sleep(2)
            tool(["saves.py", "--slot", str(a.slot), "restore", a.tag])


def count(log, tag):
    n = 0
    try:
        with open(log, errors="replace") as fh:
            for ln in fh:
                if ln.startswith(tag + " "):
                    n += 1
    except OSError:
        pass
    return n


def cmd_die(a, drv_factory):
    """One game: a.deaths times, walk to the town waypoint, take it to --wp (a dangerous level), stand until the
    logger shows PLAYER_DeathGoldLoss's exit (DG1), press Escape until the player is back in a town. With
    --resurrect [ACT:]NPC, first resurrect the dead mercenary there (MR1)."""
    launch(a)
    try:
        t0 = time.time()
        while time.time() - t0 < 150 and last(a.log, "PLR") is None:
            time.sleep(2)
        if last(a.log, "PLR") is None:
            print("die: no PLR line")
            return 1
        time.sleep(3)
        drv = drv_factory()
        if a.resurrect:
            act, _, npc = a.resurrect.rpartition(":")
            if act and not go_town(a, int(act)):
                print("die: did not reach act %s" % act, flush=True)
            rc = tool(["d2pilot.py", "--slot", str(a.slot), "npc", a.log, npc, "resurrect"], timeout=180)
            print("die: %s resurrect rc %d" % (npc, rc), flush=True)
            drv.dpy.key("Escape")
            time.sleep(1.0)
        for k in range(a.deaths):
            n0 = count(a.log, "DG1")
            for _ in range(3):      # a walk can stall after a menu (run:2026-10-17-economy); retry from where it is
                tool(["d2pilot.py", "--slot", str(a.slot), "npc", a.log, "waypoint", "walk"], timeout=90)
                tool(["d2pilot.py", "--slot", str(a.slot), "wpchain", a.log, "--chain", a.wp], timeout=25)
                if not town(a.log) or count(a.log, "DG1") > n0:
                    break
                drv.dpy.key("Escape")
                time.sleep(2)
            t1 = time.time()
            while time.time() - t1 < a.wait and count(a.log, "DG1") == n0:
                if town(a.log):
                    time.sleep(1)
                    continue
                # walk towards unactivated rooms until something kills the 5-hit-point character
                tool(["d2pilot.py", "--slot", str(a.slot), "explore", a.log, "--walk", "--hops", "8"],
                     timeout=max(5, int(a.wait - (time.time() - t1))))
            if count(a.log, "DG1") == n0:
                print("die: no death within %d s (death %d)" % (a.wait, k + 1), flush=True)
                break
            print("die: death %d" % (k + 1), flush=True)
            time.sleep(3)
            for _ in range(10):
                drv.dpy.key("Escape")
                time.sleep(2)
                if town(a.log):
                    break
            time.sleep(3)
        return 0
    finally:
        if not a.keep:
            tool(["slots.py", "stop", str(a.slot)])
            time.sleep(2)
            tool(["saves.py", "--slot", str(a.slot), "restore", a.tag])


def supervise(argv, log, quiet, limit):
    """Plan 0043 Phase 2b, after a driver hung ~9 h on 2026-10-18 still clicking after its game had exited (the
    pattern of tools/quest_sessions.py on lane/p42q): run this command again without --watchdog in its own process
    group and watch its log; abort when the log has not grown for `quiet` s (after the first 150 s), when gdb's
    "[Inferior ... exited" line is in its tail, or after `limit` s; on abort kill the group, stop the slot and restore
    the saves set aside."""
    import signal
    import subprocess
    slot, tag = None, "p43h"
    for k, v in zip(argv, argv[1:]):
        if k == "--slot":
            slot = v
        elif k == "--tag":
            tag = v
    child = subprocess.Popen(PY + [os.path.abspath(__file__)] + argv, cwd=ROOT, start_new_session=True)
    t0 = time.time()
    size, t_size, why = -1, time.time(), None
    while child.poll() is None:
        time.sleep(2)
        now = time.time()
        if os.path.exists(log):
            n = os.path.getsize(log)
            if n != size:
                size, t_size = n, now
            elif now - t_size > quiet and now - t0 > 150:
                why = "log unchanged for %d s" % (now - t_size)
            with open(log, "rb") as fh:
                fh.seek(max(0, n - 4096))
                tail = fh.read()
            if b"[Inferior " in tail and b" exited" in tail:
                why = why or "the game exited (gdb's Inferior line)"
        elif now - t0 > 180:
            why = "no log after 180 s"
        if now - t0 > limit:
            why = why or "session over %d s" % limit
        if why:
            print("WATCHDOG: %s; aborting the session" % why, flush=True)
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except OSError:
                pass
            child.wait(timeout=30)
            sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(slot)])
            sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(slot), "restore", tag])
            return 2
    return child.returncode


def main(argv):
    if "--watchdog" in argv:
        k = argv.index("--watchdog")
        quiet, limit = (int(v) for v in argv[k + 1].split(","))
        rest = argv[:k] + argv[k + 2:]
        return supervise(rest, rest[rest.index("--log") + 1], quiet, limit)
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--dwell", type=float, default=0.07)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("act")
    p.add_argument("tokens", nargs="+")
    p = sub.add_parser("tour")
    p.add_argument("--tag", default="p43h")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--diff", choices=sorted(STEPS), default="normal")
    p.add_argument("--gdb", default="tools/gdb/economy.gdb")
    p.add_argument("--after", type=int, default=3600)
    p.add_argument("--log", required=True)
    p.add_argument("--save", action="append", required=True)
    p.add_argument("--keep", action="store_true", help="leave the game running at the end")
    p.add_argument("stops", nargs="+")
    p = sub.add_parser("die")
    p.add_argument("--tag", default="p43h")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--diff", choices=sorted(STEPS), default="hell")
    p.add_argument("--gdb", default="tools/gdb/economy.gdb")
    p.add_argument("--after", type=int, default=1800)
    p.add_argument("--log", required=True)
    p.add_argument("--save", action="append", required=True)
    p.add_argument("--keep", action="store_true")
    p.add_argument("--wp", default="4,2", help="waypoint tab,row of the level to die in")
    p.add_argument("--deaths", type=int, default=2)
    p.add_argument("--wait", type=int, default=120)
    p.add_argument("--resurrect", default="", help="[ACT:]NPC: first travel to ACT's town and resurrect the mercenary at NPC (e.g. 5:qualres)")
    a = ap.parse_args(argv)
    display = slots.display(a.slot)
    if a.cmd == "act":
        run(Drv(display, a.dwell), a.tokens)
        return 0
    if a.cmd == "die":
        return cmd_die(a, lambda: Drv(display, a.dwell))
    return cmd_tour(a, lambda: Drv(display, a.dwell))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

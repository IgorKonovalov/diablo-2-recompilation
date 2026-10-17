"""Scripted harness sessions for plan 0042 Phase 2 (quests and travel): one game per session on one slot, logged by
tools/gdb/quest-state.gdb, driven by tools/d2pilot.py's Pilot (clicks, Teleport, the waypoint menu) and the
actions below.

Usage:
  python3 -I tools/quest_sessions.py list
  python3 -I tools/quest_sessions.py run --slot N --tag TAG --run RUN SESSION [SESSION ...]
  python3 -I tools/quest_sessions.py act --slot N LOG ACTION [ACTION ...]      # actions on a running session

A session installs one save (workspace/runtime/quest-saves-p42/<Name>/<Name>.d2s), launches the game with
tools/d2run.py (seed, difficulty steps), plays its action list, and stops the slot (tools/slots.py stop N); the
slot's saves directory goes back to the TAG aside after each session. The log goes to
workspace/logs/quests/<RUN>-<SESSION>.log. Actions:

  talk:CLS:N          talk N times to the nearest unit of MonStats class CLS (walk, click it, wait for the
                      dispatched event 0 with that class, Escape, wait for event 2)
  menu:NAME:LINE:N    d2pilot.py npc NAME with --menu-line LINE (an NPC menu action, e.g. Warriv's travel), N times
  tp:N                N town-portal cycles: open (the book at inventory cell 0,0, right click), go through the field
                      end, come back through the town end (the owner: both ends freed)
  wp:CHAIN            d2pilot.py wpchain --chain CHAIN (space-separated TAB,ROW hops; '_' for a space here)
  towp                d2pilot.py npc waypoint walk (next to the town waypoint)
  explore:HOPS        d2pilot.py explore --hops HOPS (Nova, new rooms)
  walk:HOPS           d2pilot.py explore --any-level --walk --hops HOPS (a town)
  warp:REC            d2pilot.py farm --descend REC --time 1 (find and take the LvlWarp row REC)
  objop:CLS:N         d2pilot.py objop --obj-cls CLS --times N (Teleport to the object, operate it)
  qlog                open the quest log, click the act tabs, close it (packet 0x58 for the entries shown)
  key:K, sleep:S, shot:NAME
Nothing here feeds a model.
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
PY = [sys.executable, "-I"]
SAVES = [os.path.join(ROOT, "workspace", "runtime", "quest-saves-p42"),      # quest_saves.py build (plan 0042 P0)
         os.path.join(ROOT, "workspace", "runtime", "quest-saves-p42h")]     # d2s.py build of quest-tpc (Phase 2)
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]

# name: (save Name, steps, seed, [actions], extra pilot args)
SESSIONS = {}


def sess(name, save, steps, seed, actions, extra=None):
    SESSIONS[name] = (save, steps, seed, actions, extra or [])


def sh(args, timeout=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


class Tail:
    """New JSON lines of the log after an offset."""

    def __init__(self, path):
        self.path = path
        self.off = os.path.getsize(path) if os.path.exists(path) else 0

    def mark(self):
        self.off = os.path.getsize(self.path)

    def lines(self):
        with open(self.path, errors="replace") as f:
            f.seek(self.off)
            data = f.read()
        out = []
        for line in data.splitlines():
            tag, _, rest = line.partition(" ")
            if rest.startswith("{"):
                try:
                    out.append((tag, json.loads(rest)))
                except ValueError:
                    pass
        return out

    def wait(self, pred, timeout):
        t0 = time.time()
        while time.time() - t0 < timeout:
            for tag, d in self.lines():
                if pred(tag, d):
                    return d
            time.sleep(0.15)
        return None


def last(path, tag):
    v = None
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith(tag + " "):
                v = line
    if v is None:
        return None
    try:
        return json.loads(v[len(tag) + 1:])
    except ValueError:
        return None


class Driver:
    def __init__(self, slot, log, extra):
        import d2pilot
        self.slot, self.log, self.extra = slot, log, extra
        self.d2p = d2pilot

        class A:
            display = ":%d" % (7 + slot)
            cx, cy, view_h = 400, 290, 571
        self.p = d2pilot.Pilot(A)
        self.st = d2pilot.LogState(log)

    def pos(self):
        self.st.poll()
        return self.st.pos

    def npc_units(self, cls):
        out = []
        for tag in ("NPCQ", "NPC"):
            d = last(self.log, tag)
            if d:
                out += [u for u in d["n"] if u[0] == cls]
        return out

    def click_rel(self, dx, dy, up=0, button=1):
        sx, sy = self.p.screen(dx, dy)
        sx, sy = max(10, min(790, sx)), max(10, min(530, sy - up))
        self.p.dpy.click(self.p.off[0] + int(sx), self.p.off[1] + int(sy), button=button, hold=0.08)

    def walk_towards(self, x, y, near):
        for _ in range(30):
            pos = self.pos()
            if not pos:
                time.sleep(0.5)
                continue
            dx, dy = x - pos[0], y - pos[1]
            d = math.hypot(dx, dy)
            if d <= near:
                return True
            k = min(9.0, d) / d
            self.click_rel(dx * k, dy * k)
            time.sleep(1.0)
        return False

    def talk(self, cls, n):
        done = 0
        for i in range(n * 3 + 120):
            if done >= n:
                break
            units = self.npc_units(cls)
            pos = self.pos()
            if not units or not pos:
                # not seen: walk towards the nearest part of the town not yet walked (d2pilot.explore_step)
                if pos:
                    tgt = self.d2p.explore_step(self.st, 9)
                    if tgt is False:
                        print("talk %d: not seen anywhere in level %s" % (cls, pos[2]), flush=True)
                        return done
                    if tgt:
                        self.click_rel(tgt[0] - pos[0], tgt[1] - pos[1])
                        time.sleep(1.1)
                        continue
                time.sleep(1.0)
                continue
            u = min(units, key=lambda u: math.hypot(u[3] - pos[0], u[4] - pos[1]))
            if math.hypot(u[3] - pos[0], u[4] - pos[1]) > 10:
                self.walk_towards(u[3], u[4], 8)
                units = self.npc_units(cls)
                pos = self.pos()
                u = min(units, key=lambda u: math.hypot(u[3] - pos[0], u[4] - pos[1]))
            t = Tail(self.log)
            self.click_rel(u[3] - pos[0], u[4] - pos[1], up=40)
            d = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "de" and d.get("ph") == 0 and d.get("ev") == 0
                       and d.get("ucls") == cls, 8)
            if not d:
                print("talk %d: no event 0 (try %d)" % (cls, i + 1), flush=True)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
                continue
            time.sleep(0.6)
            t.mark()
            self.p.dpy.key("Escape")
            t.wait(lambda tag, d: tag == "EV" and d.get("k") == "de" and d.get("ph") == 1 and d.get("ev") == 2, 4)
            done += 1
            print("talk %d: %d/%d" % (cls, done, n), flush=True)
            time.sleep(0.4)
        return done

    def tp(self, n):
        import d2pilot
        done = 0
        for i in range(n * 2):
            if done >= n:
                break
            pos0 = self.pos()
            t = Tail(self.log)
            self.p.dpy.key("i")
            time.sleep(0.5)
            x, y = d2pilot.cell_xy("inv:0,0")
            self.p.dpy.click(self.p.off[0] + x, self.p.off[1] + y, button=3, hold=0.08)
            time.sleep(0.4)
            self.p.dpy.key("i")
            d = t.wait(lambda tag, d: tag == "EV" and d.get("k") == "tp" and d.get("ph") == 1, 6)
            if not d:
                print("tp: no open (try %d)" % (i + 1), flush=True)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
                continue
            fld = t.wait(lambda tag, d: tag == "PU" and d.get("at") == "field1", 2)
            par = t.wait(lambda tag, d: tag == "PU" and d.get("at") == "partner2", 2)
            if not fld or not par:
                print("tp: open refused or no pair", flush=True)
                time.sleep(1.0)
                continue
            time.sleep(1.2)
            ok = False
            for k in range(4):
                pos = self.pos()
                t2 = Tail(self.log)
                self.click_rel(fld["opos"][0] - pos[0], fld["opos"][1] - pos[1], up=30 + 10 * k)
                if t2.wait(lambda tag, d: tag == "EV" and d.get("k") == "portal" and d.get("ph") == 1, 6):
                    ok = True
                    break
            if not ok:
                print("tp: field end not taken", flush=True)
                continue
            time.sleep(2.0)
            ok = False
            for k in range(5):
                pos = self.pos()
                t3 = Tail(self.log)
                self.click_rel(par["opos"][0] - pos[0], par["opos"][1] - pos[1], up=30 + 10 * k)
                if t3.wait(lambda tag, d: tag == "EV" and d.get("k") == "portal" and d.get("ph") == 1, 6):
                    ok = True
                    break
                time.sleep(0.5)
            if not ok:
                print("tp: town end not taken", flush=True)
                return done
            done += 1
            print("tp: %d/%d" % (done, n), flush=True)
            time.sleep(2.0)
        return done

    def pilot(self, args, timeout=900):
        return sh(PY + [os.path.join(HERE, "d2pilot.py")] + args[:1] + [self.log] + args[1:] +
                  ["--slot", str(self.slot)] + self.extra, timeout=timeout)

    def run(self, actions):
        for a in actions:
            kind, _, rest = a.partition(":")
            print("== %s" % a, flush=True)
            if kind == "talk":
                c, n = rest.split(":")
                self.talk(int(c), int(n))
            elif kind == "menu":
                name, line, n = rest.split(":")
                self.pilot(["npc", name, "talk", "--menu-line", line, "--repeat", "1", "--done-wait", "3"],
                           timeout=120)
            elif kind == "tp":
                self.tp(int(rest))
            elif kind == "wp":
                self.pilot(["wpchain", "--chain", rest.replace("_", " "), "--linger", "0.1"], timeout=1800)
            elif kind == "towp":
                self.pilot(["npc", "waypoint", "walk"], timeout=180)
            elif kind == "explore":
                self.pilot(["explore", "--hops", rest, "--nova", "2"], timeout=900)
            elif kind == "walk":
                self.pilot(["explore", "--any-level", "--walk", "--hops", rest], timeout=600)
            elif kind == "warp":
                self.pilot(["farm", "--descend", rest, "--time", "1", "--descend-time", "150"], timeout=400)
            elif kind == "objop":
                c, n = rest.split(":")
                self.pilot(["objop", "--obj-cls", c, "--times", n, "--time", "240", "--done-wait", "4"], timeout=400)
            elif kind == "qlog":              # the quest log: open it, click each act tab, close it
                self.p.dpy.key("q")
                time.sleep(1.0)
                for k in range(5):
                    self.p.dpy.click(self.p.off[0] + 120 + 60 * k, self.p.off[1] + 80, button=1, hold=0.08)
                    time.sleep(0.8)
                self.p.dpy.key("Escape")
                time.sleep(0.5)
            elif kind == "key":
                self.p.dpy.key(rest)
                time.sleep(0.5)
            elif kind == "sleep":
                time.sleep(float(rest))
            elif kind == "shot":
                self.p.shot(os.path.join(ROOT, "workspace", "logs", "quests", rest + ".png"))
            else:
                print("unknown action %s" % a, flush=True)


def run_session(args, name):
    save, steps, seed, actions, extra = SESSIONS[name]
    log = os.path.join("workspace", "logs", "quests", "%s-%s.log" % (args.run, name))
    if os.path.exists(os.path.join(ROOT, log)):
        print("%s exists; not overwriting" % log)
        return 1
    sv = [os.path.join(d, save, save + ".d2s") for d in SAVES if os.path.exists(os.path.join(d, save, save + ".d2s"))][0]
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
    sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "aside", args.tag])
    launch = PY + [os.path.join(HERE, "d2run.py"), "--slot", str(args.slot), "--seed", str(seed), "--gdb",
                   "tools/gdb/quest-state.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after", "3600",
                   "--install", args.tag, sv, "--log", log]
    print("$ " + " ".join(launch), flush=True)
    subprocess.Popen(launch, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 120:
        if os.path.exists(os.path.join(ROOT, log)) and last(os.path.join(ROOT, log), "PLR"):
            break
        time.sleep(1)
    time.sleep(3)
    try:
        Driver(args.slot, os.path.join(ROOT, log), extra).run(actions)
    finally:
        time.sleep(2)
        sh(PY + [os.path.join(HERE, "slots.py"), "stop", str(args.slot)])
        sh(PY + [os.path.join(HERE, "saves.py"), "--slot", str(args.slot), "restore", args.tag])
    print("session %s done: %s" % (name, log), flush=True)
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("list", "run", "act"))
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--slot", type=int)
    ap.add_argument("--tag", default="p42h")
    ap.add_argument("--run", default="2026-10-17-quests")
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for k, v in SESSIONS.items():
            print(k, v)
        return 0
    if args.slot is None or args.slot == 0:
        print("--slot N (N >= 1) is required")
        return 2
    if args.cmd == "act":
        log, actions = args.rest[0], args.rest[1:]
        Driver(args.slot, os.path.abspath(log), []).run(actions)
        return 0
    for name in args.rest:
        run_session(args, name)
    return 0


# ---- the sessions of run:2026-10-17-quests (save Name, steps, seed, actions, extra pilot args)
CLS = CLASSIC_WP
sess("dev-act", "ActTwoWarriv", "enter-normal", 4290, ["menu:warriv:2:1", "sleep:3", "menu:warriv2:2:1", "sleep:3"])
X_A = "2,4 2,5 2,6 2,7 2,8 2,9 3,1 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 4,1 4,2 4,3 5,1 5,2 5,3 5,4 5,5 5,6 5,7 5,8 5,9"
X_B = "1,1 1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 2,1 2,2 2,3 3,1 4,1 5,1 2,1"
C_A = "1,2 1,3 1,4 1,5 1,6 1,7 1,8 1,9 2,1 2,2 2,3 2,4 2,5 2,6 2,7 2,8 2,9 3,1 3,2 3,3 3,4 3,5 3,6 3,7 3,8 3,9 4,1 4,2 4,3"
C_B = "1,1 2,1 3,1 4,1 1,1"
TALK1 = ["menu:akara:1:1", "key:Escape", "menu:kashya:1:1", "key:Escape", "menu:charsi:1:1", "key:Escape",
         "menu:gheed:1:1", "key:Escape", "menu:warriv:1:1", "key:Escape", "qlog"]
sess("x-act", "ActTwoWarriv", "enter-normal", 4211, ["menu:warriv:2:1", "sleep:2", "menu:warriv2:2:1", "sleep:2"] * 11)
sess("x-lut", "QuestBookLost", "enter-normal", 4212, ["walk:25", "talk:331:22", "qlog", "towp", "wp:2,3", "tp:10",
                                                      "wp:" + X_A.replace(" ", "_"), "tp:6",
                                                      "wp:" + X_B.replace(" ", "_"), "tp:1"])
sess("x-summit0", "QuestSummit", "enter-normal", 4213, ["towp", "wp:5,8", "warp:74", "warp:79", "warp:80", "tp:3"])
sess("x-summit1", "TravelWpFive", "enter-normal", 4214, ["towp", "wp:5,8", "warp:74", "warp:79"])
sess("x-orb", "ActFourDurance", "enter-normal", 4215, ["towp", "wp:3,8", "objop:404:3"])
sess("x-off", "TravelWpOne", "enter-normal", 4216, TALK1)
sess("x-fresh", "QuestFresh", "enter-normal", 4217, TALK1)
sess("c-tp", "QuestPortalC", "enter-normal", 4221, TALK1 + ["towp", "wp:1,2", "tp:10", "wp:" + C_A.replace(" ", "_"), "tp:6",
                                                            "wp:" + C_B.replace(" ", "_"), "tp:1"], CLS)
sess("nm-lut", "QuestBookLost", "enter-nightmare", 4222, ["walk:25", "talk:331:22", "towp", "wp:2,3", "tp:10",
                                                          "wp:" + X_A.replace(" ", "_"), "tp:6"], ["--es", "30"])
sess("h-lut", "QuestBookLost", "enter-hell", 4223, ["wp:2,3", "tp:10", "wp:" + X_A.replace(" ", "_"), "tp:6",
                                                    "wp:" + X_B.replace(" ", "_")], ["--es", "30"])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

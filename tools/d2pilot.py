#!/usr/bin/env python3
"""Scripted exploration for agent-driven harness runs (plan 0018 Phase 2): Teleport hops to standable cells, Nova
casts, belt potions, steered by the live gdb log.

    python3 -I tools/d2pilot.py where <run.log>
    python3 -I tools/d2pilot.py explore <run.log> [--hops N] [--hop R] [--nova K] [--potion P] [--shots DIR]
                                                  [--to-pdef DEF] [--display :7] [--cx X --cy Y]
    python3 -I tools/d2pilot.py hop <run.log> <dx> <dy>          # one Teleport to the player + (dx, dy) sub-tiles

The log must be written with tools/gdb/mon-special.gdb (PLR: the player's position from its collision mark, RL: the
level's DRLG rooms, RRESEED: room activation, CB: each activated room's collision grid). Nothing here feeds a model:
it only decides where to click. A target is a cell whose activation-time collision value has none of the player's
blocking bits (0x1C09, drlg/0005) in a 3x3 square, reached on a breadth-first path over such cells towards the nearest
DRLG room of the current level that has not been activated yet (the population pass runs at activation). Clicks are
window-relative on the 800x600 game window: screen = (cx + 16 (dx - dy), cy + 8 (dx + dy)) for a sub-tile offset
(dx, dy) from the player. Teleport is the left skill cast with Shift held; Nova the right skill. The game window must
have been activated (the steps file's first click does that). --es N casts Energy Shield every N seconds (on the
weapon-swap set's right button with --es-swap 1, else on the main right button); the life orb is sampled after every
hop and a belt potion is drunk below --drink (the orb turns green when poisoned; both colours count as life).
"""
import argparse
import collections
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import collision  # noqa: E402

BLOCK = 0x1C09


class LogState:
    def __init__(self, path):
        self.path = path
        self.f = open(path, errors="replace")
        self.buf = ""
        self.pos = None             # (x, y, lid, room)
        self.rl = {}                # DRLG room -> (level pointer, rect in tiles)
        self.pdef = {}              # DRLG room -> LvlPrest Def of its preset (RL "pdef")
        self.lid_of = {}            # DRLG room -> level id
        self.lptr = {}              # level id -> level pointer
        self.active = set()         # DRLG rooms activated
        self.cells = {}             # (x, y) -> collision value at activation
        self.n_plr = 0
        self.specials = 0

    def poll(self):
        data = self.f.read()
        if not data:
            return
        data = self.buf + data
        lines = data.split("\n")
        self.buf = lines.pop()
        for line in lines:
            tag, _, rest = line.partition(" ")
            if tag not in ("PLR", "RL", "RRESEED", "CB", "SMA0", "SU0"):
                continue
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "PLR":
                self.pos = (d["x"], d["y"], d["lid"], d["room"])
                self.n_plr += 1
            elif tag == "RL":
                self.rl[d["room"]] = (d["level"], d["rect"])
                self.pdef[d["room"]] = d.get("pdef")
            elif tag == "RRESEED":
                self.lid_of[d["room"]] = d["level"]
                self.active.add(d["room"])
                if d["room"] in self.rl:
                    self.lptr[d["level"]] = self.rl[d["room"]][0]
            elif tag == "CB":
                z = collision.unz(d["z"])
                c = z.get("cells")
                x0, y0, w, h = d["rect"]
                if c and c[4]:
                    vals = collision.u16cells(c[4])
                    for j in range(h):
                        for i in range(w):
                            self.cells[(x0 + i, y0 + j)] = vals[j * w + i]
            elif tag in ("SMA0", "SU0"):
                self.specials += 1

    def frontier(self, lid):
        lp = self.lptr.get(lid)
        if lp is None:
            return []
        return [(r, rect) for r, (p, rect) in self.rl.items() if p == lp and r not in self.active]

    def level_rooms(self, lid):
        lp = self.lptr.get(lid)
        return [r for r, (p, _) in self.rl.items() if p == lp] if lp is not None else []


def standable(cells, x, y):
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            v = cells.get((x + dx, y + dy))
            if v is None or v & BLOCK:
                return False
    return True


def in_rect(x, y, rect):
    x0, y0, w, h = (5 * v for v in rect)
    return x0 <= x < x0 + w and y0 <= y < y0 + h


def pick_on_path(st, path, hop, bad):
    """The farthest standable cell of path within the hop radius of the player (None if none)."""
    px, py = st.pos[0], st.pos[1]
    cells = st.cells
    # resume from the path cell nearest to the player
    j0 = min(range(len(path)), key=lambda j: (path[j][0] - px) ** 2 + (path[j][1] - py) ** 2)
    pick = alt = None
    for c in path[j0 + 1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if c in bad:
            continue
        if standable(cells, *c):
            pick = c
        elif not cells.get(c, BLOCK) & BLOCK and math.hypot(c[0] - px, c[1] - py) >= 3:
            alt = c                     # a free cell on a narrow path (its 3x3 square is not all free)
    return pick or alt


def plan(st, hop, bad, limit=400000, targets=None, want_path=False, skip=()):
    """Breadth-first search from the player to a standable cell inside, or next to an unknown cell of, a target room
    (default: the level's rooms not activated yet); returns the farthest cell of that path within the hop radius."""
    px, py, lid, _ = st.pos
    fr = [e for e in st.frontier(lid) if e[0] not in skip] if targets is None else targets
    if not fr:
        return None, "level done (%d rooms skipped)" % len(skip)
    cells = st.cells
    start = (px, py)
    prev = {start: None}
    q = collections.deque([start])
    goal = None
    while q and len(prev) < limit:
        c = q.popleft()
        x, y = c
        if targets is not None and c != start and any(in_rect(x, y, rect) for _, rect in fr):
            goal = c
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in prev:
                continue
            if n not in cells:
                if c != start and any(in_rect(n[0], n[1], rect) for _, rect in fr):
                    goal = c
                    break
                continue
            if cells[n] & BLOCK:
                continue
            prev[n] = c
            q.append(n)
        if goal:
            break
    if goal is None:
        # nothing reachable over known cells: aim at the nearest frontier room's centre
        r, rect = min(fr, key=lambda e: (5 * e[1][0] + 2.5 * e[1][2] - px) ** 2 + (5 * e[1][1] + 2.5 * e[1][3] - py) ** 2)
        tx, ty = 5 * rect[0] + 2.5 * rect[2], 5 * rect[1] + 2.5 * rect[3]
        d = math.hypot(tx - px, ty - py) or 1
        best = None
        reach = int(hop * 1.8)          # Teleport crosses blocked ground: any known standable cell in reach
        for y in range(py - reach, py + reach + 1):
            for x in range(px - reach, px + reach + 1):
                if math.hypot(x - px, y - py) > reach or (x, y) in bad or not standable(cells, x, y):
                    continue
                k = math.hypot(tx - x, ty - y)
                if best is None or k < best[0]:
                    best = (k, (x, y))
        if best and best[0] >= d - 2:
            best = None                 # no cell closer to the room: the caller skips it
        plan.last_room = r
        return (best[1] if best else None), "towards room centre %.0f away" % d
    path = []
    c = goal
    while c is not None:
        path.append(c)
        c = prev[c]
    path.reverse()
    if want_path:
        return path, "path %d to the frontier, %d rooms left" % (len(path), len(fr))
    pick = None
    for c in path[1:]:
        if math.hypot(c[0] - px, c[1] - py) > hop:
            break
        if standable(cells, *c) and c not in bad:
            pick = c
    if pick is None:
        for c in path[1:]:
            if c not in bad and math.hypot(c[0] - px, c[1] - py) <= hop and cells.get(c, BLOCK) & BLOCK == 0:
                pick = c
    return pick, "path %d to the frontier, %d rooms left" % (len(path), len(fr))


class Pilot:
    def __init__(self, args):
        import xdrive
        self.dpy = xdrive.Display(args.display)
        self.off = self.dpy.origin("Diablo II")
        self.cx, self.cy = args.cx, args.cy

    def screen(self, dx, dy):
        sx = self.cx + 16 * (dx - dy)
        sy = self.cy + 8 * (dx + dy)
        return sx, sy

    def teleport(self, dx, dy):
        sx, sy = self.screen(dx, dy)
        sx, sy = max(10, min(790, sx)), max(10, min(540, sy))
        self.dpy.keystate("Shift_L", True)
        time.sleep(0.05)
        self.dpy.click(self.off[0] + int(sx), self.off[1] + int(sy), button=1, hold=0.12)
        time.sleep(0.05)
        self.dpy.keystate("Shift_L", False)

    def nova(self):
        self.dpy.keystate("Shift_L", True)
        time.sleep(0.05)
        self.dpy.click(self.off[0] + self.cx, self.off[1] + self.cy, button=3, hold=0.12)
        time.sleep(0.05)
        self.dpy.keystate("Shift_L", False)

    def shield(self, swap):
        """Energy Shield: on the right button of the weapon-swap set (swap: W, right click, W) or of the main set."""
        if swap:
            self.dpy.key("w")
            time.sleep(0.4)
        self.dpy.click(self.off[0] + self.cx, self.off[1] + self.cy, button=3, hold=0.12)
        time.sleep(0.6)
        if swap:
            self.dpy.key("w")
            time.sleep(0.4)

    def potion(self, k):
        self.dpy.key(str(k))

    def hp(self):
        """Fill of the life orb, 0..1: rows of the orb (window 50..95 x 496..556) with more than 10 red (or, poisoned,
        green) pixels."""
        import ctypes as C
        import xdrive
        X = xdrive.X11
        x0, y0, w, h = self.off[0] + 50, self.off[1] + 496, 45, 60
        img = X.XGetImage(self.dpy.d, self.dpy.root, x0, y0, w, h, 0xFFFFFFFF, 2)
        if not img:
            return None
        im = xdrive.XImage.from_address(img)
        raw = C.string_at(im.data, im.bytes_per_line * h)
        rows = 0
        for y in range(h):
            line = raw[y * im.bytes_per_line: y * im.bytes_per_line + 4 * w]
            n = 0
            for x in range(w):
                b, g, r = line[4 * x], line[4 * x + 1], line[4 * x + 2]
                if (r > 90 and r > 2 * g) or (g > 55 and g > 2 * r and g > 2 * b):   # red, or green when poisoned
                    n += 1
            if n > 10:
                rows += 1
        return rows / 56.0

    def shot(self, path):
        import xdrive
        self.dpy.shot(path, self.off[0], self.off[1], xdrive.GAME_W, xdrive.GAME_H)


def cmd_where(args):
    st = LogState(args.log)
    st.poll()
    if not st.pos:
        print("no PLR yet")
        return 1
    x, y, lid, room = st.pos
    lr = st.level_rooms(lid)
    print("player (%d, %d) level %s; level rooms %d, activated %d, frontier %d; specials so far %d" % (
        x, y, lid, len(lr), sum(1 for r in lr if r in st.active), len(st.frontier(lid)), st.specials))
    return 0


def cmd_hop(args):
    st = LogState(args.log)
    st.poll()
    p = Pilot(args)
    before = st.pos
    p.teleport(args.dx, args.dy)
    time.sleep(1.0)
    st.poll()
    print("before %s after %s (target %+d %+d)" % (before[:2] if before else None, st.pos[:2] if st.pos else None,
                                                    args.dx, args.dy))
    return 0


def cmd_explore(args):
    st = LogState(args.log)
    st.poll()
    p = Pilot(args)
    if not st.pos:
        print("no PLR yet")
        return 1
    lid0 = st.pos[2]
    targets = None
    if args.to_pdef is not None:
        targets = [(r, rect) for r, (lp, rect) in st.rl.items() if st.pdef.get(r) == args.to_pdef
                   and lp == st.lptr.get(lid0)]
        print("target rooms with preset def %d: %s" % (args.to_pdef, [rect for _, rect in targets]))
        if not targets:
            return 1
    bad = set()
    hist = []
    npot = 0
    skip = set()
    cache = None
    stuck = 0
    k = 0
    last = None
    t0 = time.time()
    t_es = None
    for k in range(1, args.hops + 1):
        if args.es and (t_es is None or time.time() - t_es > args.es):
            p.shield(args.es_swap)
            t_es = time.time()
        st.poll()
        if st.pos[2] != lid0:
            print("level changed %s -> %s (death or a warp); stop" % (lid0, st.pos[2]))
            break
        if targets is not None and any(in_rect(st.pos[0], st.pos[1], rect) for _, rect in targets):
            print("hop %d: inside the target room at (%d, %d); stop" % (k, st.pos[0], st.pos[1]))
            break
        tgt = None
        if cache and (targets is not None or set(cache[1]) & {r for r, _ in st.frontier(lid0)} - skip):
            tgt = pick_on_path(st, cache[0], args.hop, bad)
            why = "cached path"
        if tgt is None:
            plan.last_room = None
            path, why = plan(st, args.hop, bad, targets=targets, want_path=True, skip=skip)
            while path is None and plan.last_room is not None and targets is None:
                skip.add(plan.last_room)          # unreachable from here: try the next nearest room
                plan.last_room = None
                path, why = plan(st, args.hop, bad, want_path=True, skip=skip)
            if isinstance(path, list):
                fr = targets if targets is not None else st.frontier(lid0)
                end = path[-1]
                near = [r for r, rect in fr if any(in_rect(end[0] + dx, end[1] + dy, rect)
                                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))]
                cache = (path, near or [r for r, _ in fr])
                tgt = pick_on_path(st, path, args.hop, bad)
            else:
                cache = None
                tgt = path
        if tgt is None:
            print("hop %d: no target (%s); stop" % (k, why))
            break
        px, py = st.pos[0], st.pos[1]
        p.teleport(tgt[0] - px, tgt[1] - py)
        time.sleep(args.wait)
        st.poll()
        moved = (st.pos[0], st.pos[1]) != (px, py)
        if not moved:
            stuck += 1
            bad.add(tgt)
            cache = None
            if stuck >= 6:
                for _ in range(3):
                    a = random.uniform(0, 2 * math.pi)
                    p.teleport(int(args.hop * math.cos(a)), int(args.hop * math.sin(a)))
                    time.sleep(args.wait)
                stuck = 0
        else:
            stuck = 0
        hist.append((st.pos[0], st.pos[1]))
        if len(hist) >= 20 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-20:]) < 15:
            if cache:
                skip.update(cache[1])           # the rooms this path aims at stay out of reach: give them up
        if (len(hist) >= 10 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-10:]) < 6) or \
                (len(hist) >= 20 and max(math.hypot(a[0] - hist[-1][0], a[1] - hist[-1][1]) for a in hist[-20:]) < 15):
            # no progress over ten hops (monsters in the way): two long hops to random standable cells
            for _ in range(2):
                st.poll()
                qx, qy = st.pos[0], st.pos[1]
                cand = [(x, y) for y in range(qy - 18, qy + 19) for x in range(qx - 18, qx + 19)
                        if 12 <= math.hypot(x - qx, y - qy) <= 18 and standable(st.cells, x, y)]
                if cand:
                    x, y = random.choice(cand)
                    p.teleport(x - qx, y - qy)
                    time.sleep(args.wait)
            cache = None
            hist.clear()
            print("hop %d: no progress over ten hops, two long random hops" % k)
        if args.nova and k % args.nova == 0:
            p.nova()
            time.sleep(0.25)
        if args.potion and k % args.potion == 0:
            p.potion(1 + (k // args.potion) % 4)
        hp = p.hp()
        if hp is not None and hp < 0.05:
            time.sleep(0.5)
            if (p.hp() or 0) < 0.05:
                print("hop %d: the life orb is empty (death); stop" % k)
                break
        if hp is not None and hp < args.drink:
            npot += 1
            p.potion(1 + npot % 4)
            print("hop %d: life %.2f, potion %d" % (k, hp, 1 + npot % 4))
        if args.shots and k % args.shot_every == 0:
            p.shot(os.path.join(args.shots, "pilot-%04d.png" % k))
        if args.verbose or k % 10 == 0:
            print("hop %d: (%d, %d) -> %s %s; moved %s; frontier %d; specials %d; %.0f s" % (
                k, px, py, tgt, why, moved, len(st.frontier(lid0)), st.specials, time.time() - t0))
            sys.stdout.flush()
        last = tgt
    st.poll()
    print("done after %d hops: level %s frontier %d, specials seen %d" % (k, lid0, len(st.frontier(lid0)), st.specials))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("where", "explore", "hop"))
    ap.add_argument("log")
    ap.add_argument("dx", nargs="?", type=int, default=0)
    ap.add_argument("dy", nargs="?", type=int, default=0)
    ap.add_argument("--display", default=":7")
    ap.add_argument("--cx", type=int, default=400)
    ap.add_argument("--cy", type=int, default=290)
    ap.add_argument("--hops", type=int, default=200)
    ap.add_argument("--hop", type=float, default=10.0)
    ap.add_argument("--wait", type=float, default=0.45)
    ap.add_argument("--nova", type=int, default=2)
    ap.add_argument("--potion", type=int, default=0)
    ap.add_argument("--es", type=float, default=0, help="cast Energy Shield every this many seconds (0: never)")
    ap.add_argument("--es-swap", type=int, default=1, help="1: Energy Shield is the swap set's right skill")
    ap.add_argument("--drink", type=float, default=0.6, help="drink a belt potion below this life-orb fill")
    ap.add_argument("--to-pdef", type=int, help="go to the room of this LvlPrest Def in the current level, then stop")
    ap.add_argument("--shots")
    ap.add_argument("--shot-every", type=int, default=25)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    return {"where": cmd_where, "explore": cmd_explore, "hop": cmd_hop}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

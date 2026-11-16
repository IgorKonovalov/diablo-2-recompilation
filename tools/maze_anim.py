"""Animate the maze generator (docs/specs/drlg/maze.md) room by room, with the game's own tiles.

Usage:
  python3 -I tools/maze_anim.py <root> <level> <seed> [--out DIR] [--scale N] [--gif-factor N]

<root> is the merged data tree (workspace/merged); <level> a maze level id (8-12, 34-36, 47-49, 65);
<seed> the level seed. The seed is an illustrative input, not the level seed a game seed produces
(same as `maze_render.py gen`). DIR defaults to workspace/render/anim/maze-<level>-<seed hex>/ and must
stay under workspace/ (anything else is refused). Outputs, all regenerable and never committed:
  frame-NNN.png   one frame per step: isometric tile view, top-down mini-map inset, caption strip
  maze.gif        the frames as an animated GIF (global palette = the level's game palette; the UI
                  colours are the nearest palette entries; frames after the first are cropped to the
                  changed rows)
  index.html      local step-through page (prev/next/play/pause, slider, arrow keys) with each step's
                  calculations (draw values, picked room and side, overlaps, merge rolls, Def from exits)
  steps.json      the captions and calculations

Steps: the first room; each room placed, in the order the replay model (tools/maze_replay.py, reading of
docs/findings/drlg/0006-maze.md) creates them, with the door links the model adds; one step per special or
theme re-assignment of existing rooms; then each room's LvlPrest Def and preset file (forced index, else
seed lo % file count, as maze_render.py reads it) with its tiles drawn; the final composite. Rooms the
model creates and frees again while probing (finder, sec. B) are not shown. The model stops before the
placement shift (sec. G1, one translation of every room to the level's origin in the act), so the
rectangles are drawn relative to the bounding box; the shift would not change the picture. The canvas is
fixed to the final level's bounds. Drawn like the game builds a room's tiles (drlg/0001): blank floors
(0, 30, 0/1) hidden, an orientation-3 wall paired with its orientation-4 tile; no shadows, lighting or rarity
variants. Stdlib only.
"""
import csv
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds1  # noqa: E402
import maze_render  # noqa: E402
import palette  # noqa: E402
import png  # noqa: E402

from anim_common import FONT, encode_gif, lzw_decode, lzw_encode, safe_out, text, wrap  # noqa: E402,F401
import anim_common  # noqa: E402


# ---------------------------------------------------------------- model trace
def trace(root, level, seed):
    """Run the replay model. Returns (steps, rooms, rng draws). Room numbers are placement order of the kept rooms."""
    excel = maze_render._excel(root)
    saved, sys.argv = sys.argv, ["maze_replay.py", excel]    # maze_replay reads its excel dir at import
    try:
        import maze_replay as M
    finally:
        sys.argv = saved
    rows = list(csv.reader(open(os.path.join(excel, "lvlprest.txt"), encoding="latin-1"), delimiter="\t"))
    h, lp = rows[0], {}
    for row in rows[1:]:
        if len(row) > 20 and row[h.index("Def")].strip().isdigit():
            lp[int(row[h.index("Def")])] = (row[h.index("Name")], int(row[h.index("Files")] or 0),
                                            [row[h.index("File%d" % i)] for i in range(1, 7)])
    if level not in M.MAZE:
        raise SystemExit("level %d is not in the maze set of lvlmaze.txt" % level)
    count = [0]
    orig_step, o_connect, o_special, o_themes = M.Seed.step, M.connect, M.special, M.themes
    o_growth, o_merge, o_defcalc = M.growth, M.merge, M.defcalc
    notes = []          # (len(ev) when made, post?, formatter(nm) -> str); see calc_for below
    DN = ["west", "north", "east", "south"]

    def note(f, post=False):
        notes.append((len(ev), post, f))

    def growth(L):      # maze_replay.growth (0x00671210) with each draw logged; same calls, same order
        tgt = M.MAZE[L.id]["rooms"][L.diff]
        note(lambda nm: "Growth phase starts: grow until the level has %d rooms (LvlMaze Rooms, normal "
             "difficulty); it has %d." % (tgt, len(L.rooms)))
        while len(L.rooms) < tgt:
            n = len(L.rooms)
            lo = L.seed.step()
            k = lo & (n - 1) if n & (n - 1) == 0 else lo % n
            P = L.rooms[k]
            dlo = P.seed.step()
            d = dlo & 3
            how = "lo & %d" % (n - 1) if n & (n - 1) == 0 else "lo %% %d" % n
            note(lambda nm, lo=lo, k=k, n=n, P=P, how=how: "Pick a parent: level draw lo = %#010x; %s = %d; "
                 "position %d of the %d-room list (newest first) is %s." % (lo, how, k, k, n, nm(P)))
            note(lambda nm, dlo=dlo, d=d, P=P: "Pick a side: %s's own seed draw lo = %#010x; lo & 3 = %d = %s." % (
                nm(P), dlo, d, DN[d]))
            if P.lock:
                note(lambda nm, P=P: "%s is locked (a fixed room): no room is made, both draws stay spent; pick "
                     "again." % nm(P).capitalize())
                continue
            before = count[0]
            R = M.grow(L, P, d)
            if R is None:
                note(lambda nm, P=P, d=d, b=count[0] - before: "A new room (level draw for its seed, %d draws) "
                     "would sit %s of %s but overlaps a room already there: it is dropped, the draws stay "
                     "spent; pick again." % (b, DN[d], nm(P)))

    def merge(L, R):    # maze_replay.merge with each roll logged
        if R.lock:
            return
        mg = M.MAZE[L.id]["merge"]
        for P in list(L.rooms):
            if P is R or P.lock:
                continue
            gx, gy = M.gap(R, P)
            if gx < 1 and gy < 1 and gx != gy:
                if any(o is P for (o, _) in R.adj):
                    continue
                lo = P.seed.step()
                ok = lo % 1000 < mg
                note(lambda nm, P=P, lo=lo, ok=ok, mg=mg: "Merge roll with neighbour %s: its seed draw lo %% 1000 "
                     "= %d, %s Merge %d: %s." % (nm(P), lo % 1000, "<" if ok else ">=", mg,
                                                  "a door is opened" if ok else "no door"))
                if ok:
                    d = M.adjdir(P, R)
                    if d != -1:
                        M.connect(P, R, d)
                        M.defcalc(L, P)

    def defcalc(L, R):
        before = R.d
        dirs = [DN[d] for (_, d) in R.adj]
        mask = 0
        for (_, d) in R.adj:
            mask |= {0: 1, 1: 8, 2: 2, 3: 4}.get(d, 0)
        r_ = o_defcalc(L, R)
        if R.d != before or mask:
            base = M.BASE.get(L.lt, 0)
            note(lambda nm, R=R, dirs=dirs, mask=mask, base=base, v=R.d: "Def of %s from its open sides (%s): "
                 "base %d + side mask %d (west 1, east 2, south 4, north 8) = Def %d." % (
                     nm(R), ", ".join(sorted(set(dirs))) or "none", base, mask, v), post=True)
        return r_

    def step(s):
        count[0] += 1
        return orig_step(s)
    ev, inserted, pending, num = [], [], {}, {}

    class TList(list):
        def insert(self, i, R):
            super().insert(i, R)
            if R not in num:
                num[R] = len(num)
                inserted.append(R)
            ev.append(("place", R, count[0], pending.pop(R, [])))

    def connect(A, B, d):
        if A in num and B in num:
            if not any(o is B for (o, _) in A.adj):
                ev.append(("link", A, B, d, count[0]))
        else:
            X, other = (A, B) if A not in num else (B, A)
            pending.setdefault(X, []).append((other, d if X is A else (d - 2) & 3))
        return o_connect(A, B, d)

    def diffwrap(name, orig):
        def f(L, *a, **k):
            before = {R: (R.d, R.lock, R.idx) for R in L.rooms}
            r = orig(L, *a, **k)
            ch = [(R, before[R], (R.d, R.lock, R.idx)) for R in L.rooms
                  if R in before and before[R] != (R.d, R.lock, R.idx)]
            ev.append((name, ch, count[0]))
            return r
        return f
    M.Seed.step, M.connect = step, connect
    M.growth, M.merge, M.defcalc = growth, merge, defcalc
    M.special, M.themes = diffwrap("special", o_special), diffwrap("themes", o_themes)
    try:
        M.Room.n = 0
        L = M.Level(level, M.Seed(seed & 0xFFFFFFFF, 0x29A))
        L.rooms = TList()
        s = M.Seed(seed ^ 0x5bd1e995, 0x29A)
        first = M.Seed(s.step(), 666)
        first.step()
        n0 = count[0]
        if L.lt == 10 and level == 34:
            note(lambda nm: "Start shape (spec E): four rooms attached to room 1 on all sides, no pick; room 1 "
                 "becomes a locked fixed room.")
        elif L.lt == 10:
            note(lambda nm: "Start shape (spec E): one level draw, lo & 1, picks the arms: 0 north and south, "
                 "1 west and east of room 1; room 1 becomes a locked fixed room.")
        elif L.lt == 13:
            note(lambda nm: "Start shape (spec E): a ring of rooms is grown first; it closes with a door link.")
        M.run(L, first)
    finally:
        M.Seed.step, M.connect, M.special, M.themes = orig_step, o_connect, o_special, o_themes
        M.growth, M.merge, M.defcalc = o_growth, o_merge, o_defcalc
    alive = set(L.rooms)
    final = [R for R in inserted if R in alive]
    num = {R: i for i, R in enumerate(final)}
    steps, shown, links = [], [final[0]], []
    dn = DN

    def nm(R):
        return "room %d" % (num[R] + 1) if R in num else "a dropped trial room"
    calc_for = [[] for _ in range(len(ev) + 1)]       # notes made before event j belong to it, post notes to j - 1
    for j, post, f in notes:
        calc_for[max(j - 1, 0) if post else j].append(f(nm))
    carry, last_rng = [], [0]

    def add(kind, txt, rng, new, link=None, calc=None):
        if link:
            links.append(link)
        c = carry + (calc or [])
        carry.clear()
        c.insert(0, "RNG draws in this step: %d (level seed and room seeds together); %d so far." % (
            rng - last_rng[0], rng))
        last_rng[0] = rng
        steps.append(dict(kind=kind, text=txt, rooms=[num[R] for R in shown], new=new, rng=rng, links=list(links),
                          calc=c))
    carry.append("Setup (illustrative, like the seed): one draw on a helper seed made from the input gives room 1 "
                 "its seed, which is advanced once. The level seed is the input itself.")
    add("start", "First room, %d by %d tiles (lvlmaze SizeX by SizeY), at the origin. The level seed gives the room its "
        "own seed." % (M.MAZE[level]["sx"], M.MAZE[level]["sy"]), n0, 0)
    for j, e in enumerate(ev):
        ec = calc_for[j]
        if e[0] == "place":
            R = e[1]
            if R not in alive or R is final[0]:
                carry.extend(ec)
                continue
            shown.append(R)
            pend = [(o, d) for (o, d) in e[3] if o in alive]
            t = "Room %d placed" % (num[R] + 1)
            lk = None
            if pend:
                o, d = pend[0]
                t += " %s of room %d." % (dn[(d + 2) & 3], num[o] + 1)
                lk = (num[o], num[R])
            else:
                t += "."
            if R.lock:
                t += " Fixed Def and file index (locked)."
            add("place", t, e[2], num[R], lk, ec)
            for (o, d) in pend[1:]:
                add("link", "Rooms %d and %d joined by a merge link (merge roll lo %% 1000 < Merge)."
                    % (num[R] + 1, num[o] + 1), e[2], num[R], (num[R], num[o]), ["Shown separately; the roll is "
                    "in the previous step."])
        elif e[0] == "link":
            if e[1] in alive and e[2] in alive:
                add("link", "Rooms %d and %d joined by a door link (the ring closes)." % (num[e[1]] + 1, num[e[2]] + 1),
                    e[4], None, (num[e[1]], num[e[2]]), ec)
            else:
                carry.extend(ec)
        else:
            carry.extend(ec)
            if e[0] == "themes":
                carry.append("Themes: one level draw picks a start in a 15-entry list, 15 pairs of level draws "
                             "shuffle it, then free rooms whose Def matches an entry get the themed Def (+15).")
            else:
                carry.append("Special room: the level's special-room table (entry chosen by a rotating index "
                             "from one level draw) names a Def; the first free room with that Def takes the "
                             "special Def and file, or a new room is attached for it.")
            for R, _b, a_ in e[1]:
                if R in alive:
                    what = "special-room table entry" if e[0] == "special" else "theme step"
                    add("assign", "Room %d: %s sets Def %d, forced file index %s." % (
                        num[R] + 1, what, a_[0], a_[2] if a_[2] >= 0 else "none"), e[2], num[R])
    if carry and steps:
        steps[-1]["calc"] += carry
    rooms = []
    for R in final:
        name, nf, files = lp[R.d]
        live = [f for f in files[:max(nf, 1)] if f and f != "0"]
        if R.idx >= 0 or not live:
            k = max(R.idx, 0)
            how = "forced index %d" % R.idx if R.idx >= 0 else "no file"
        else:
            k = R.seed.lo % len(live)
            how = "room seed lo %#010x %% %d files = %d" % (R.seed.lo, len(live), k)
        rooms.append(dict(rect=[R.x, R.y, R.w, R.h], d=R.d, name=name, how=how,
                          file=live[k % len(live)] if live else None))
    return steps, rooms, count[0]


# ---------------------------------------------------------------- drawing
def nearest(pal, rgb):
    return min(range(1, 256), key=lambda i: sum((pal[i * 3 + k] - rgb[k]) ** 2 for k in range(3)))


def line(cv, W, H, a, b, col, thick=1):
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
    for t in range(n + 1):
        x, y = a[0] + (b[0] - a[0]) * t // n, a[1] + (b[1] - a[1]) * t // n
        for dd in range(thick):
            if 0 <= y + dd < H and 0 <= x < W:
                cv[(y + dd) * W + x] = col


def fill_poly(cv, W, H, pts, col):
    for y in range(max(min(p[1] for p in pts), 0), min(max(p[1] for p in pts), H - 1) + 1):
        xs = []
        for i in range(len(pts)):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % len(pts)]
            if ya != yb and min(ya, yb) <= y < max(ya, yb):
                xs.append(xa + (xb - xa) * (y - ya) // (yb - ya))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(max(a, 0), min(b, W - 1) + 1):
                cv[y * W + x] = col


def _levels(root):
    """Levels.txt: id -> {name, vis[0..7]} (tbl:Levels.txt:Vis0..7, LevelName)."""
    rows = list(csv.reader(open(os.path.join(maze_render._excel(root), "levels.txt"), encoding="latin-1"),
                           delimiter="\t"))
    h, out = rows[0], {}
    for row in rows[1:]:
        if len(row) > h.index("Vis7") and row[h.index("Id")].strip().isdigit():
            out[int(row[h.index("Id")])] = dict(name=row[h.index("LevelName")],
                                                vis=[int(row[h.index("Vis%d" % k)] or 0) for k in range(8)])
    return out


def build(root, level, seed, scale):
    steps, rooms, total = trace(root, level, seed)
    r = maze_render.Renderer(root, scale)
    tw, th, pad = r.tw, r.th, r.pad
    x0 = min(q["rect"][0] for q in rooms)
    y0 = min(q["rect"][1] for q in rooms)
    gw = max(q["rect"][0] + q["rect"][2] for q in rooms) + 1 - x0
    gh = max(q["rect"][1] + q["rect"][3] for q in rooms) + 1 - y0
    pal_name, per_room = None, []
    lv = _levels(root)
    vis = lv[level]["vis"]
    warps = []          # (room index, slot m, dest level, centre gx, centre gy) of the warp slot cells (warps.md, fmt:ds1)
    for qi, q in enumerate(rooms):
        cells = []
        if q["file"]:
            rel, d = r._load(q["file"])
            for m, pts in sorted(ds1._scan_cells(d)["slot"].items()):
                dest = vis[m] if m < len(vis) else 0
                if dest:
                    cx = sum(p[0] for p in pts) / len(pts) + 0.5
                    cy = sum(p[1] for p in pts) / len(pts) + 0.5
                    warps.append((qi, m, dest, q["rect"][0] - x0 + cx, q["rect"][1] - y0 + cy))
            pal_name = pal_name or palette.palette_for_tiles(rel)
            own = ds1._own_dt1s(d, r.tiles)
            lay = d["layers"]
            for name in lay:
                kind = "floor" if name.startswith("floor") else "wall" if name.startswith("wall") else None
                if not kind:
                    continue
                ori = lay.get("orient" + name[4:]) if kind == "wall" else None
                for cy in range(d["rows"]):
                    for cx in range(d["cols"]):
                        c = lay[name][cy * d["cols"] + cx]
                        if not c or c >> 31 or (kind == "floor" and ds1.blank_floor(c)):
                            continue
                        o = 0 if kind == "floor" else (ori[cy * d["cols"] + cx] if ori else 0)
                        if o in ds1.SKIP_ORIENT:
                            continue
                        gx, gy = q["rect"][0] - x0 + cx, q["rect"][1] - y0 + cy
                        if gx < gw and gy < gh:
                            cells.append((gx, gy, kind, (o, (c >> 20) & 63, (c >> 8) & 63), own))
                            if o == 3:                   # second pick for orientation 4 (drlg/0001, 0x0066E9B0)
                                cells.append((gx, gy, kind, (4, (c >> 20) & 63, (c >> 8) & 63), own))
        per_room.append(cells)
    pal = bytearray(palette.load(root, pal_name))
    IW = (gw + gh) * tw // 2 + tw
    IH = (gw + gh) * th // 2 + pad + th
    ox, oy = gh * tw // 2, pad
    cache = {}
    top, bot = pad, pad + (gw + gh) * th // 2 + th      # rows used by footprints
    for cells in per_room:
        for gx, gy, _k, key, own in cells:
            if (key, id(own)) not in cache:
                cache[(key, id(own))] = r.tiles.lookup(key, own)[0]
            by = pad + (gx + gy) * th // 2
            for dy, _dx, _run in cache[(key, id(own))] or ():
                top, bot = min(top, by + dy), max(bot, by + dy + 1)
    top = max(top - 6, 0)
    oy = pad - top                                      # trim the empty margin; fixed for every frame
    IH = bot - top + 6
    CW = max(IW, 760)
    ix = (CW - IW) // 2
    CH = IH + 5 * 18 + 8
    C = {k: nearest(pal, v) for k, v in dict(
        panel=(24, 24, 32), fill=(60, 70, 110), edge=(150, 160, 220), new=(255, 220, 60), txt=(235, 235, 235),
        dim=(140, 140, 140), link=(80, 220, 120), warp=(90, 230, 255), floor=(190, 180, 150), wall=(110, 70, 50)).items()}
    ms = max(2, min(200 // max(gw, gh), 8))
    mw, mh = gw * ms, gh * ms
    mx, my = CW - mw - 14, 28

    def P(cx, cy):
        return (ix + ox + (cx - cy) * tw // 2 + tw // 2, oy + (cx + cy) * th // 2)

    def rect_pts(rc):
        rx, ry = rc[0] - x0, rc[1] - y0
        return [P(rx, ry), P(rx + rc[2], ry), P(rx + rc[2], ry + rc[3]), P(rx, ry + rc[3])]

    def center(i):
        p = rect_pts(rooms[i]["rect"])
        return ((p[0][0] + p[2][0]) // 2, (p[0][1] + p[2][1]) // 2)

    def mcenter(i):
        q = rooms[i]["rect"]
        return (mx + int((q[0] - x0 + q[2] / 2) * ms), my + int((q[1] - y0 + q[3] / 2) * ms))

    def P2(fx, fy):
        return (ix + ox + int((fx - fy) * tw / 2) + tw // 2, oy + int((fx + fy) * th / 2))

    def wlabel(dest):
        kind = "ENTRY" if dest < level else "EXIT"
        return "%s: %s" % (kind, lv.get(dest, {}).get("name", "LEVEL %d" % dest))

    def frame(k, st, done, lead, total_steps):
        cv = bytearray(CW * CH)
        vis = sorted(st["rooms"])
        for i in vis:
            if i < done:
                continue
            pts = rect_pts(rooms[i]["rect"])
            fill_poly(cv, CW, IH, pts, C["fill"])
            for a in range(4):
                line(cv, CW, IH, pts[a], pts[(a + 1) % 4], C["new"] if i == lead else C["edge"], 2)
        cells = []
        for i in range(done):
            cells += per_room[i]
        cells.sort(key=lambda c: (c[2] != "floor", c[0] + c[1]))
        for gx, gy, _k, key, own in cells:
            if (key, id(own)) not in cache:
                cache[(key, id(own))] = r.tiles.lookup(key, own)[0]
            bx, by = ix + ox + (gx - gy) * tw // 2, oy + (gx + gy) * th // 2
            for dy, dx, run in cache[(key, id(own))] or ():
                y, x = by + dy, bx + dx
                if 0 <= y < IH:
                    a, b = max(x, 0), min(x + len(run), CW)
                    if a < b:
                        cv[y * CW + a:y * CW + b] = run[a - x:b - x]
        if lead is not None and lead < done:
            pts = rect_pts(rooms[lead]["rect"])
            for a in range(4):
                line(cv, CW, IH, pts[a], pts[(a + 1) % 4], C["new"], 2)
        for lk in st["links"]:
            line(cv, CW, IH, center(lk[0]), center(lk[1]), C["link"], 3)
        # mini-map inset
        for yy in range(-6, mh + 6):
            cv[(my + yy) * CW + mx - 6:(my + yy) * CW + mx + mw + 6] = bytes([C["panel"]]) * (mw + 12)
        for i in vis:
            rx, ry, rw, rh = rooms[i]["rect"]
            ax, ay = mx + (rx - x0) * ms, my + (ry - y0) * ms
            for yy in range(rh * ms + 1):
                for xx in range(rw * ms + 1):
                    edge = yy in (0, rh * ms) or xx in (0, rw * ms)
                    cv[(ay + yy) * CW + ax + xx] = (C["new"] if i == lead else C["edge"]) if edge else (
                        C["floor"] if i < done else C["fill"])
        for i in vis:
            if i < done:
                for gx, gy, kind, _k, _o in per_room[i]:
                    if kind == "wall":
                        for yy in range(ms):
                            o = (my + gy * ms + yy) * CW + mx + gx * ms
                            cv[o:o + ms] = bytes([C["wall"]]) * ms
        for lk in st["links"]:
            line(cv, CW, CH, mcenter(lk[0]), mcenter(lk[1]), C["link"], 2)
        for qi, m, dest, fx, fy in (warps if done == len(rooms) and lead is None else ()):   # final frame only
            cx, cy = P2(fx, fy)
            dx, dy = tw * 3 // 2, th * 3 // 2
            pts = [(cx, cy - dy), (cx + dx, cy), (cx, cy + dy), (cx - dx, cy)]
            for a in range(4):
                line(cv, CW, IH, pts[a], pts[(a + 1) % 4], C["warp"], 3)
            for yy in range(cy - 3, cy + 4):
                cv[yy * CW + cx - 3:yy * CW + cx + 4] = bytes([C["warp"]]) * 7
            lab = wlabel(dest)
            lw, lx, ly = len(lab) * 12 + 8, min(max(cx - len(lab) * 6 - 4, 2), CW - len(lab) * 12 - 10), cy - dy - 26
            ly = max(ly, 24)
            for yy in range(ly, ly + 20):
                cv[yy * CW + lx:yy * CW + lx + lw] = bytes([C["panel"]]) * lw
            text(cv, CW, CH, lx + 4, ly + 3, lab, C["warp"])
            mxx, myy = mx + int(fx * ms), my + int(fy * ms)
            for yy in range(myy - 3, myy + 4):
                cv[yy * CW + mxx - 3:yy * CW + mxx + 4] = bytes([C["warp"]]) * 7
        # caption strip
        cv[IH * CW:] = bytes([C["panel"]]) * (CW * (CH - IH))
        text(cv, CW, CH, 10, IH + 6, "STEP %d/%d    RNG DRAWS SO FAR: %d" % (k + 1, total_steps, st["rng"]), C["new"])
        for j, ln in enumerate(wrap(st["text"], (CW - 20) // 12)[:3]):
            text(cv, CW, CH, 10, IH + 6 + 18 * (j + 1), ln, C["txt"])
        text(cv, CW, CH, 10, 8, "LEVEL %d  SEED %#X  (ILLUSTRATIVE INPUT)" % (level, seed), C["dim"])
        return bytes(cv)

    n = len(rooms)
    total_steps = len(steps) + n + 1
    frames, caps = [], []
    for st in steps:
        frames.append(frame(len(frames), st, 0, st["new"], total_steps))
        caps.append(dict(text=st["text"], calc=st["calc"]))
    for i, q in enumerate(rooms):
        txt = "Room %d: Def %d (%s), preset file %s (%s)." % (
            i + 1, q["d"], q["name"], (q["file"] or "none").replace("\\", "/").split("/")[-1], q["how"])
        frames.append(frame(len(frames), dict(text=txt, rng=total, rooms=range(n), links=[]), i + 1, i, total_steps))
        caps.append(dict(text=txt, calc=[
            "Def %d is the room's LvlPrest row (%s); its File1..6 columns list the preset maps (DS1) it may use."
            % (q["d"], q["name"]),
            "File choice: %s." % q["how"],
            "The tiles drawn are that DS1's floor and wall cells, looked up in the level type's tile files (DT1)."] + [
            "This preset holds a warp: wall cells of orientation 10/11 with slot %d, so Levels Vis%d = %d (%s); "
            "marked in cyan on the final frame (drlg/warps.md, warp slot cell)." % (m, m, dest, lv.get(dest, {}).get("name", "?"))
            for qi, m, dest, _fx, _fy in warps if qi == i]))
    txt = ("Final composite: %d rooms after %d RNG draws. Drawn relative to the layout's corner; the game "
           "then moves the whole level to its place in the act (not drawn, shape unchanged)." % (n, total))
    frames.append(frame(len(frames), dict(text=txt, rng=total, rooms=range(n), links=[]), n, None, total_steps))
    wl = ["Warp (cyan mark): room %d, DS1 wall cells of orientation 10/11 with slot %d, so Levels Vis%d = %d (%s) "
          "(drlg/warps.md, warp slot cell). %s is by level order: the lower id is taken as the way in. The act's "
          "link lists can override Vis at run time (warps.md § C); not modelled here."
          % (qi + 1, m, m, dest, lv.get(dest, {}).get("name", "?"), wlabel(dest).split(":")[0].capitalize())
          for qi, m, dest, _fx, _fy in warps]
    caps.append(dict(text=txt, calc=wl + [
        "Placement shift (spec drlg/maze.md G1): growth never looks at where the level sits in the act; rooms grow "
        "freely around the first room, so coordinates can go negative.",
        "At the end the game takes the bounding box of all rooms (x0, y0) and adds (level.x - x0, level.y - y0) to "
        "every room, so the box's top-left corner lands on the level's origin in the act map.",
        "It is one translation for all rooms: shape, doors and Defs do not change. This picture is already drawn "
        "relative to the box corner, so the shifted level would look the same."]))
    return frames, caps, CW, CH, bytes(pal)


MAZE_HELP = """<li>Rooms are LvlMaze SizeX by SizeY tile blocks. A room is placed flush against a parent room on one of four sides:
0 west, 1 north, 2 east, 3 south.</li>
<li>Two random streams are used: the level seed (which room to grow from, each new room's seed) and every room's own
seed (which side to grow on, merge rolls, and at the end which preset file the room uses).</li>
<li>A draw advances a seed (lo, hi) as lo*0x6AC690C5 + hi (64-bit) and returns the new lo. "lo % n" picks one of n.</li>
<li>Blue outline: placed room; yellow: this step's room; green line: a door between two rooms;
cyan diamond: a warp (entry or exit stairs) from the preset map, labelled with the level it leads to.</li>
<li>The seed is an illustrative input, not one the game derives from a game seed. Rooms the model tries and drops
are listed in the calculations but not drawn.</li>"""


def write_html(path, caps, W, H):
    anim_common.write_html(path, caps, W, H, "maze animation", MAZE_HELP)


def main(argv):
    argv = list(argv)
    opts = {"--out": None, "--scale": "8", "--gif-factor": "1"}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root, level, seed = argv[0], int(argv[1]), int(argv[2], 0)
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "maze-%d-%x" % (level, seed))
    out = safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, W, H, pal = build(root, level, seed, int(opts["--scale"]))
    for i, f in enumerate(frames):
        png.write_indexed(os.path.join(out, "frame-%03d.png" % i), W, H, f, pal, transparent=())
    write_html(os.path.join(out, "index.html"), caps, W, H)
    json.dump(caps, open(os.path.join(out, "steps.json"), "w"), indent=1)
    fac = int(opts["--gif-factor"])
    if fac > 1:
        gw, gh = W // fac, H // fac
        frames = [b"".join(f[y * fac * W:y * fac * W + gw * fac:fac] for y in range(gh)) for f in frames]
        W, H = gw, gh
    delays = [90] * len(frames)
    delays[-1] = 500
    with open(os.path.join(out, "maze.gif"), "wb") as fh:
        fh.write(encode_gif(frames, W, H, pal, delays))
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

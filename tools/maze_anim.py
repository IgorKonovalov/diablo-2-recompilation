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
  index.html      local step-through page (prev/next/play/pause, slider, arrow keys)
  steps.json      the captions

Steps: the first room; each room placed, in the order the replay model (tools/maze_replay.py, reading of
docs/findings/drlg/0006-maze.md) creates them, with the door links the model adds; one step per special or
theme re-assignment of existing rooms; then each room's LvlPrest Def and preset file (forced index, else
seed lo % file count, as maze_render.py reads it) with its tiles drawn; the final composite. Rooms the
model creates and frees again while probing (finder, sec. B) are not shown. The model stops before the
placement shift (sec. G), so the rectangles are the window's, relative to the bounding box. The canvas is
fixed to the final level's bounds. Stdlib only.
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

# ---------------------------------------------------------------- 5x7 bitmap font (upper case only)
_F = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", ",": "00000 00000 00000 00000 01100 00100 01000",
    ":": "00000 01100 01100 00000 01100 01100 00000", "=": "00000 00000 11111 00000 11111 00000 00000",
    "%": "11001 11010 00010 00100 01000 01011 10011", "#": "01010 01010 11111 01010 11111 01010 01010",
    "+": "00000 00100 00100 11111 00100 00100 00000", "-": "00000 00000 00000 11111 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000", "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000", ">": "10000 01000 00100 00010 00100 01000 10000",
    "<": "00001 00010 00100 01000 00100 00010 00001", "'": "00100 00100 01000 00000 00000 00000 00000",
    "_": "00000 00000 00000 00000 00000 00000 11111", " ": "00000 00000 00000 00000 00000 00000 00000",
    "?": "01110 10001 00001 00010 00100 00000 00100", ";": "00000 01100 01100 00000 01100 00100 01000",
}
FONT = {c: [[int(b) for b in row] for row in g.split()] for c, g in _F.items()}


def text(canvas, W, H, x, y, s, idx, sc=2):
    for ch in s.upper():
        g = FONT.get(ch, FONT["?"])
        for gy in range(7):
            for gx in range(5):
                if g[gy][gx]:
                    for yy in range(sc):
                        for xx in range(sc):
                            px, py = x + gx * sc + xx, y + gy * sc + yy
                            if 0 <= px < W and 0 <= py < H:
                                canvas[py * W + px] = idx
        x += 6 * sc


def wrap(s, width_chars):
    lines, cur = [], ""
    for w in s.split():
        if cur and len(cur) + 1 + len(w) > width_chars:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    return lines + [cur] if cur else lines


# ---------------------------------------------------------------- GIF writer (LZW, stdlib)
def lzw_encode(indices, min_code=8):
    clear, end = 1 << min_code, (1 << min_code) + 1
    out, acc, nacc = bytearray(), 0, 0

    def emit(code, size):
        nonlocal acc, nacc
        acc |= code << nacc
        nacc += size
        while nacc >= 8:
            out.append(acc & 255)
            acc >>= 8
            nacc -= 8
    table, nxt, size = {}, end + 1, min_code + 1
    emit(clear, size)
    cur = None
    for b in indices:
        if cur is None:
            cur = b
            continue
        k2 = (cur, b)
        if k2 in table:
            cur = table[k2]
            continue
        emit(cur, size)
        if nxt < 4096:
            table[k2] = nxt
            if nxt == (1 << size) and size < 12:
                size += 1
            nxt += 1
        else:
            emit(clear, size)
            table, nxt, size = {}, end + 1, min_code + 1
        cur = b
    if cur is not None:
        emit(cur, size)
    emit(end, size)
    if nacc:
        out.append(acc & 255)
    return bytes(out)


def lzw_decode(data, min_code=8):
    """Inverse of lzw_encode (used by the test)."""
    clear, end = 1 << min_code, (1 << min_code) + 1
    acc = nacc = pos = 0
    size = min_code + 1
    table, out, prev = {}, bytearray(), None
    nxt = end + 1
    while True:
        while nacc < size and pos < len(data):
            acc |= data[pos] << nacc
            nacc += 8
            pos += 1
        if nacc < size:
            break
        code, acc, nacc = acc & ((1 << size) - 1), acc >> size, nacc - size
        if code == clear:
            table = {i: bytes([i]) for i in range(clear)}
            size, prev, nxt = min_code + 1, None, end + 1
            continue
        if code == end:
            break
        e = table[code] if code in table else prev + prev[:1]
        out += e
        if prev is not None and nxt < 4096:
            table[nxt] = prev + e[:1]
            nxt += 1
            if nxt == (1 << size) and size < 12:
                size += 1
        prev = e
    return bytes(out)


def _blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        c = data[i:i + 255]
        out.append(len(c))
        out += c
    return bytes(out) + b"\0"


def encode_gif(frames, W, H, pal, delays):
    """frames: list of bytes (W*H indices); pal: 768 bytes. Frames after the first are cropped to the changed rows."""
    out = bytearray(b"GIF89a" + struct.pack("<HHBBB", W, H, 0xF7, 0, 0) + bytes(pal))
    out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"
    prev = None
    for f, d in zip(frames, delays):
        y0, y1 = 0, H
        if prev is not None:
            rows = [y for y in range(H) if f[y * W:(y + 1) * W] != prev[y * W:(y + 1) * W]]
            y0, y1 = (rows[0], rows[-1] + 1) if rows else (0, 1)
        out += b"\x21\xF9\x04\x04" + struct.pack("<HBB", d, 0, 0) + b"\0"
        out += b"\x2C" + struct.pack("<HHHHB", 0, y0, W, y1 - y0, 0)
        out += bytes([8]) + _blocks(lzw_encode(f[y0 * W:y1 * W]))
        prev = f
    return bytes(out) + b";"


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
    M.special, M.themes = diffwrap("special", o_special), diffwrap("themes", o_themes)
    try:
        M.Room.n = 0
        L = M.Level(level, M.Seed(seed & 0xFFFFFFFF, 0x29A))
        L.rooms = TList()
        s = M.Seed(seed ^ 0x5bd1e995, 0x29A)
        first = M.Seed(s.step(), 666)
        first.step()
        n0 = count[0]
        M.run(L, first)
    finally:
        M.Seed.step, M.connect, M.special, M.themes = orig_step, o_connect, o_special, o_themes
    alive = set(L.rooms)
    final = [R for R in inserted if R in alive]
    num = {R: i for i, R in enumerate(final)}
    steps, shown, links = [], [final[0]], []
    dn = ["west", "north", "east", "south"]

    def add(kind, txt, rng, new, link=None):
        if link:
            links.append(link)
        steps.append(dict(kind=kind, text=txt, rooms=[num[R] for R in shown], new=new, rng=rng, links=list(links)))
    add("start", "First room, %d by %d tiles (lvlmaze SizeX by SizeY), at the origin. The level seed gives the room its "
        "own seed." % (M.MAZE[level]["sx"], M.MAZE[level]["sy"]), n0, 0)
    for e in ev:
        if e[0] == "place":
            R = e[1]
            if R not in alive or R is final[0]:
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
            add("place", t, e[2], num[R], lk)
            for (o, d) in pend[1:]:
                add("link", "Rooms %d and %d joined by a merge link (merge roll lo %% 1000 < Merge)."
                    % (num[R] + 1, num[o] + 1), e[2], num[R], (num[R], num[o]))
        elif e[0] == "link":
            if e[1] in alive and e[2] in alive:
                add("link", "Rooms %d and %d joined by a door link (the ring closes)." % (num[e[1]] + 1, num[e[2]] + 1),
                    e[4], None, (num[e[1]], num[e[2]]))
        else:
            for R, _b, a_ in e[1]:
                if R in alive:
                    what = "special-room table entry" if e[0] == "special" else "theme step"
                    add("assign", "Room %d: %s sets Def %d, forced file index %s." % (
                        num[R] + 1, what, a_[0], a_[2] if a_[2] >= 0 else "none"), e[2], num[R])
    rooms = []
    for R in final:
        name, nf, files = lp[R.d]
        live = [f for f in files[:max(nf, 1)] if f and f != "0"]
        if R.idx >= 0 or not live:
            k = max(R.idx, 0)
            how = "forced index %d" % R.idx if R.idx >= 0 else "no file"
        else:
            k = R.seed.lo % len(live)
            how = "seed lo %% %d = %d" % (len(live), k)
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


def build(root, level, seed, scale):
    steps, rooms, total = trace(root, level, seed)
    r = maze_render.Renderer(root, scale)
    tw, th, pad = r.tw, r.th, r.pad
    x0 = min(q["rect"][0] for q in rooms)
    y0 = min(q["rect"][1] for q in rooms)
    gw = max(q["rect"][0] + q["rect"][2] for q in rooms) + 1 - x0
    gh = max(q["rect"][1] + q["rect"][3] for q in rooms) + 1 - y0
    pal_name, per_room = None, []
    for q in rooms:
        cells = []
        if q["file"]:
            rel, d = r._load(q["file"])
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
                        if not c or c >> 31:
                            continue
                        o = 0 if kind == "floor" else (ori[cy * d["cols"] + cx] if ori else 0)
                        if o in ds1.SKIP_ORIENT:
                            continue
                        gx, gy = q["rect"][0] - x0 + cx, q["rect"][1] - y0 + cy
                        if gx < gw and gy < gh:
                            cells.append((gx, gy, kind, (o, (c >> 20) & 63, (c >> 8) & 63), own))
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
        dim=(140, 140, 140), link=(80, 220, 120), floor=(190, 180, 150), wall=(110, 70, 50)).items()}
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
        caps.append(st["text"])
    for i, q in enumerate(rooms):
        txt = "Room %d: Def %d (%s), preset file %s (%s)." % (
            i + 1, q["d"], q["name"], (q["file"] or "none").replace("\\", "/").split("/")[-1], q["how"])
        frames.append(frame(len(frames), dict(text=txt, rng=total, rooms=range(n), links=[]), i + 1, i, total_steps))
        caps.append(txt)
    txt = ("Final composite: %d rooms after %d RNG draws in the model run. Illustrative seed; "
           "the placement shift is not modelled." % (n, total))
    frames.append(frame(len(frames), dict(text=txt, rng=total, rooms=range(n), links=[]), n, None, total_steps))
    caps.append(txt)
    return frames, caps, CW, CH, bytes(pal)


def write_html(path, caps, W, H):
    page = """<!doctype html><meta charset="utf-8"><title>maze animation</title>
<style>body{background:#111;color:#ddd;font:14px sans-serif;margin:0;padding:12px;text-align:center}
img{max-width:100%%;height:auto;image-rendering:pixelated;background:#000}button{font-size:16px;margin:4px;padding:4px 12px}
#cap{max-width:900px;margin:8px auto;min-height:3em}#s{width:60%%}</style>
<img id=f width=%d height=%d alt="frame"><div>
<button id=p>prev</button><button id=pl>play</button><button id=n>next</button>
<input id=s type=range min=0 value=0></div><div id=cap></div>
<script>
var caps=%s,i=0,t=null,f=document.getElementById('f'),s=document.getElementById('s');
s.max=caps.length-1;
function show(k){i=Math.max(0,Math.min(caps.length-1,k));f.src='frame-'+('000'+i).slice(-3)+'.png';
s.value=i;document.getElementById('cap').textContent=(i+1)+'/'+caps.length+'  '+caps[i];}
function stop(){if(t){clearInterval(t);t=null;document.getElementById('pl').textContent='play';}}
document.getElementById('p').onclick=function(){stop();show(i-1)};
document.getElementById('n').onclick=function(){stop();show(i+1)};
document.getElementById('pl').onclick=function(){if(t){stop();return;}
 if(i>=caps.length-1)show(0);document.getElementById('pl').textContent='pause';
 t=setInterval(function(){if(i>=caps.length-1)stop();else show(i+1)},900)};
s.oninput=function(){stop();show(+s.value)};
document.onkeydown=function(e){if(e.key=='ArrowRight'){stop();show(i+1)}else if(e.key=='ArrowLeft'){stop();show(i-1)}
 else if(e.key==' '){e.preventDefault();document.getElementById('pl').click()}};
show(0);
</script>
""" % (W, H, json.dumps(caps))
    with open(path, "w") as fh:
        fh.write(page)


def safe_out(out):
    ws = os.path.realpath(os.path.join(HERE, "..", "workspace"))
    real = os.path.realpath(out)
    if real == ws or not real.startswith(ws + os.sep):
        raise SystemExit("refusing output dir %s: it must be under workspace/" % out)
    return real


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

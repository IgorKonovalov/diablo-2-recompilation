"""Animate an outdoor level's cell grid and border pass (docs/specs/drlg/outdoor.md B, C, D and E): the level cut into
8 * 8 tile cells, the outline with its seam, the seam mark, the border pass piece by piece with the draws it makes, the
one preset Act I puts on the Burial Grounds, and the final cell bits. Schematic only (ADR-0036): our own boxes, grid and
palette, one box per cell with the piece number as a word; no tile, preset-file or picture is read or drawn.

Usage:
  python3 -I tools/outdoor_anim.py <root> <seed> [--diff D] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); the tool reads the Levels table and the
preset table there and the link tables of the game image beside it (the model's own loader), never a map or a picture.
<seed> is the map seed, decimal or 0x hex (an illustrative input, never a seed a game derives). --diff: 0 normal,
1 nightmare, 2 hell (default 0; the level's size depends on it). --theme: dark or light (default dark). --schematic is
accepted for the export builder and changes nothing. DIR defaults to workspace/render/anim/outdoor-<seed hex>-schematic/
and must stay under workspace/. The level is Act I's Burial Grounds (level 17), the one Act I level whose generator is
the seam mark, the border pass and one preset. Outputs:
  frame-NNN.png one frame per step; outdoor.gif the animated GIF; index.html the step-through page; steps.json the
  captions and calculations; schematic.json the marker's file list.

Every value is read from the DRLG model (tools/drlg.py: Act, act_links and Outdoor). The act's link builder gives the
level rectangle and its neighbour; the level seed starts at the act seed's first step plus the level number, the
window's start (outdoor § A). The model's outline, seam mark, placement and corner flood are called as they are, on an
instance whose methods record each call and a copy of the grids; nothing is computed here but the grouping of the
recorded placements by ring segment. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import drlg  # noqa: E402
import links_anim  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 520
CAP_Y = 410
LEVEL = 17
GX, GY, CW, CH = 300, 62, 40, 44          # the cell grid's origin and the size of a cell box
PX, PW = 520, 420                          # the right panel
SIDE = ["WEST", "NORTH", "EAST", "SOUTH"]  # a ring segment going up, right, down, left runs along this edge
DIRSIDE = {(0, -1): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3}
DIFFN = ["normal", "nightmare", "hell"]


def seed_hex(lo, hi):
    return "%08X:%08X" % (lo, hi)


def seed_cap(lo, hi):
    return "{%08x:%08x}" % (lo, hi)


def snap(O):
    return [row[:] for row in O.cell], [row[:] for row in O.g0], [row[:] for row in O.defg]


# ---------------------------------------------------------------- the model's own calls, recorded
class Run:
    """One run of the model's Act I outdoor generator for the level, with every placement, the ring and the grids at
    each boundary recorded. The model is not changed: the instance's methods are wrapped for the run."""


def trace(root, seed, diff):
    exe = os.path.join(os.path.dirname(os.path.abspath(root)), "install", "app", "game.exe")
    drlg.load_outdoor(root, exe)
    A = drlg.Act(0, seed, diff)
    drlg.act_links(A)
    O = drlg.Outdoor(A, LEVEL, drlg.Seed(A.base + LEVEL))
    O.seed.log = []
    R = Run()
    R.A, R.O, R.rect = A, O, list(O.rect)
    R.seed_in = (O.seed.lo, O.seed.hi)
    R.events = []            # in call order: ("place", dict) | ("mark", dict(name, before, after)) | ("ring", ...)
    state = {"in_border": False}
    place, ring_build, seam_mark = O.place, O.ring_build, O.seam_mark
    border_build, corner_flood = O.border_build, O.corner_flood

    def w_place(x, y, d, idx, flag=0):
        before = snap(O)
        first = d not in O.rot
        n0 = len(O.seed.log)
        r = place(x, y, d, idx, flag)
        R.events.append(("place", dict(x=x, y=y, d=d, idx_arg=idx, first=first, files=drlg.PREST[d]["files"],
                                       w=drlg.tdiv(drlg.PREST[d]["sx"], 8), h=drlg.tdiv(drlg.PREST[d]["sy"], 8),
                                       draws=list(O.seed.log[n0:]), seed=(O.seed.lo, O.seed.hi), before=before,
                                       after=snap(O), border=state["in_border"])))
        return r

    def w_ring():
        ring_build()
        R.ring = [(v.x, v.y, v.flags, v.type) for v in O.ring_list()]
        R.events.append(("ring", dict(after=snap(O), seed=(O.seed.lo, O.seed.hi))))

    def w_mark():
        before = snap(O)
        seam_mark()
        R.events.append(("mark", dict(before=before, after=snap(O), seed=(O.seed.lo, O.seed.hi))))

    def w_border():
        state["in_border"] = True
        R.events.append(("border_start", dict(before=snap(O))))
        border_build()
        state["in_border"] = False

    def w_flood():
        before = snap(O)
        corner_flood()
        R.events.append(("flood", dict(before=before, after=snap(O), seed=(O.seed.lo, O.seed.hi))))

    O.place, O.ring_build, O.seam_mark, O.border_build, O.corner_flood = w_place, w_ring, w_mark, w_border, w_flood
    O.run()
    del O.place, O.ring_build, O.seam_mark, O.border_build, O.corner_flood     # back to the class's methods
    R.seed_out = (O.seed.lo, O.seed.hi)
    R.draws = list(O.seed.log)
    return R


def segments(R):
    """Group the border pass's recorded placements by ring segment: -> [dict]. Segment i runs from ring vertex i to the
    next one; its edge pieces are the cells after the start up to and including the end (none when the segment's flag
    bit 1 is set, a town seam), then a corner piece at the end, when the pass placed one."""
    O = R.O
    ring = R.ring
    border = [e for k, e in R.events if k == "place" and e["border"]]
    flood = next(e for k, e in R.events if k == "flood")
    segs, pos = [], 0
    for i, (x, y, fl, ty) in enumerate(ring):
        nx, ny = ring[(i + 1) % len(ring)][:2]
        d = (drlg.sgn(nx - x), drlg.sgn(ny - y))
        ncell = 0 if fl & 2 else max(abs(nx - x), abs(ny - y))
        edge = border[pos:pos + ncell]
        pos += ncell
        corner = None
        if pos < len(border) and (border[pos]["x"], border[pos]["y"]) == (nx, ny):
            corner = border[pos]          # the next segment's first edge cell is a different cell
            pos += 1
        segs.append(dict(i=i, v=(x, y), n=(nx, ny), d=d, flags=fl, edge=edge, corner=corner))
    assert pos == len(border), (pos, len(border))
    # the grids at the end of each segment, and the seam opening: bit 0x400 newly set between the last edge piece and
    # the segment's end (the model writes it after the edge cells and before the corner)
    for j, s in enumerate(segs):
        last = s["corner"] or (s["edge"][-1] if s["edge"] else None)
        if j + 1 < len(segs):
            nxt = segs[j + 1]
            first = nxt["edge"][0] if nxt["edge"] else nxt["corner"]
            end = first["before"] if first else flood["before"]
        else:
            end = flood["before"]
        s["end"] = end
        mid = (s["edge"][-1]["after"] if s["edge"] else s["end"])
        s["open"] = [(cx, cy) for cy in range(O.ch) for cx in range(O.cw)
                     if end[0][cy][cx] & 0x400 and not mid[0][cy][cx] & 0x400]
        s["seed"] = last["seed"] if last else None
    R.segs, R.flood = segs, flood
    return segs


# ---------------------------------------------------------------- drawing
def cell_xy(cx, cy):
    return GX + cx * CW, GY + cy * CH


def draw_neighbours(k, R):
    """Each neighbour in the level's adjacency list, as a box at its true offset in cells, clipped to the free area."""
    O = R.O
    for n in O.adj:
        r = n["rect"]
        x0 = GX + (r[0] - R.rect[0]) * CW // 8
        y0 = GY + (r[1] - R.rect[1]) * CH // 8
        x1, y1 = x0 + r[2] * CW // 8, y0 + r[3] * CH // 8
        x0, x1, y0, y1 = max(x0, 12), min(x1, PX - 10), max(y0, GY), min(y1, CAP_Y - 28)
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        # the part of the neighbour beside the grid is clipped by the grid itself, drawn after
        lab = links_anim.nm(n["nbr"])
        k.rect(x0, y0, x1 - x0, y1 - y0, "bg")
        k.outline(x0, y0, x1 - x0, y1 - y0, "dim", 1)
        k.text_c((x0 + x1) // 2, max(y0, GY + O.ch * CH) + 8, lab, "dim", 2)
        k.text_c((x0 + x1) // 2, max(y0, GY + O.ch * CH) + 30, "LEVEL %d, %s SIDE" % (n["nbr"], SIDE[n["side"]]), "dim", 2)


def draw_grid(k, R, st, hot=(), seam=(), opening=(), lines=True):
    """The cell grid with what the state holds: st = dict(grids=(cell, g0, defg), roles={cell: role})."""
    O = R.O
    cell, g0, defg = st["grids"]
    for cy in range(O.ch):
        for cx in range(O.cw):
            x, y = cell_xy(cx, cy)
            role = st["roles"].get((cx, cy))
            fill = {"edge": "room", "corner": "qd_rare", "preset": "qd_set"}.get(role, "panel")
            k.rect(x, y, CW + 1, CH + 1, fill)
            k.outline(x, y, CW + 1, CH + 1, "grey", 1)
            d = defg[cy][cx]
            if role and d:
                idx = (cell[cy][cx] >> 16) & 0xF
                lab = "D%d" % d
                k.text_c(x + CW // 2, y + 2 + (0 if K.text_w(lab, 2) <= CW - 2 else 4), lab, "txt",
                         2 if K.text_w(lab, 2) <= CW - 2 else 1)
                k.text_c(x + CW // 2, y + 17, "I%d" % idx, "txt", 2)
            if (cx, cy) in opening or (role and cell[cy][cx] & 0x400):
                k.text_c(x + CW // 2, y + CH - 9, "OPEN", "txt", 1)
    for (cx, cy) in seam:
        x, y = cell_xy(cx, cy)
        k.outline(x + 1, y + 1, CW - 1, CH - 1, "warp", 2)
    for (cx, cy) in opening:
        x, y = cell_xy(cx, cy)
        k.outline(x + 3, y + 3, CW - 5, CH - 5, "door", 2)
    for (cx, cy) in hot:
        x, y = cell_xy(cx, cy)
        k.outline(x, y, CW + 1, CH + 1, "acc", 3)


def header(k, text):
    k.text(20, 14, text, "acc", 2, True)


def key_block(k, R):
    O = R.O
    r = R.rect
    k.text(20, GY, "BURIAL GROUNDS", "txt", 2)
    k.text(20, GY + 22, "LEVEL %d, ACT I" % LEVEL, "dim", 2)
    k.text(20, GY + 52, "AT %d, %d" % (r[0], r[1]), "txt", 2)
    k.text(20, GY + 74, "%d * %d TILES" % (r[2], r[3]), "txt", 2)
    k.text(20, GY + 96, "%d * %d CELLS" % (O.cw, O.ch), "txt", 2)
    k.text(20, GY + 126, "CELL (C, R):", "dim", 2)
    k.text(20, GY + 148, "COLUMN, ROW", "dim", 2)
    k.text(20, GY + 178, "D: PIECE NUMBER", "dim", 2)
    k.text(20, GY + 200, "I: FILE INDEX", "dim", 2)


def panel(k, lines, title=None):
    k.rect(PX, GY, PW, 6 * CH + 1, "panel")
    k.outline(PX, GY, PW, 6 * CH + 1, "dim", 1)
    y = GY + 8
    if title:
        k.text(PX + 8, y, title, "acc", 2, True)
        y += 26
    for ln in lines:
        s, c = (ln, "txt") if isinstance(ln, str) else ln
        k.text(PX + 8, y, s, c, 2)
        y += 20


LEGEND = [("room", "EDGE"), ("qd_rare", "CORNER"), ("qd_set", "PRESET"), ("warp", "SEAM CELL (OUTLINE)"),
          ("door", "OPENING (OUTLINE)")]


def build(root, seed, diff, theme):
    R = trace(root, seed, diff)
    O = R.O
    segs = segments(R)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    nb = O.adj[0]
    nbr = nb["nbr"]
    nname = links_anim.nice(nbr)
    empty = ([[0] * O.cw for _ in range(O.ch)], [[0] * O.cw for _ in range(O.ch)], [[0] * O.cw for _ in range(O.ch)])
    st0 = dict(grids=empty, roles={})
    ring_ev = next(e for kind, e in R.events if kind == "ring")
    mark_ev = next(e for kind, e in R.events if kind == "mark")
    nverts = len(R.ring)
    ncells = O.cw * O.ch

    # ---- 1: the cell grid
    sin = seed_hex(*R.seed_in)
    header(k, "BURIAL GROUNDS: THE CELL GRID")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, st0)
    panel(k, ["LEVEL SEED AT THE WINDOW", "START: " + sin, "",
              "%d / 8 = %d CELLS WIDE" % (R.rect[2], O.cw), "%d / 8 = %d CELLS TALL" % (R.rect[3], O.ch),
              "EACH CELL 8 * 8 TILES", "%d CELLS, ALL EMPTY" % ncells, "",
              "ONE NEIGHBOUR ON THE LIST:", "LEVEL %d, %s SIDE" % (nbr, SIDE[nb["side"]]), links_anim.nm(nbr)[:34]],
          "CELL GRID")
    k.legend(GX - 280, CAP_Y - 20, LEGEND, 1)
    k.caption("The level is cut into cells of 8 * 8 tiles: this level's rectangle, %d * %d tiles, gives %d * %d cells, all "
              "empty at the start of the window. Its one neighbour on the border list is %s, on the %s side."
              % (R.rect[2], R.rect[3], O.cw, O.ch, nname, SIDE[nb["side"]].lower()), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The level's rectangle %d * %d tiles is %d * %d cells of 8 * 8 tiles, all empty." % (R.rect[2], R.rect[3], O.cw, O.ch),
        calc=["Level %d rectangle (x, y, w, h) = (%d, %d, %d, %d) from the act's link builder, map seed %d, %s."
              % (LEVEL, R.rect[0], R.rect[1], R.rect[2], R.rect[3], seed, DIFFN[diff]),
              "Cells: %d / 8 = %d wide and %d / 8 = %d tall (signed division)." % (R.rect[2], O.cw, R.rect[3], O.ch),
              "The window starts at the level seed Init(base + %d) = %s (low:high); base is the act seed's first step."
              % (LEVEL, seed_cap(*R.seed_in)),
              "Adjacency list: %s." % "; ".join("level %d, side %d (%s)" % (n["nbr"], n["side"], SIDE[n["side"]].lower())
                                                for n in O.adj)]))

    # ---- 2: the outline
    ring_lines = []
    for i, (x, y, fl, ty) in enumerate(R.ring):
        ring_lines.append("VERTEX %d: CELL (%d, %d)%s" % (i, x, y, "  SEAM FLAG %d" % fl if fl else ""))
    header(k, "BURIAL GROUNDS: THE OUTLINE")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, st0)
    cx = lambda c: GX + c * CW + CW // 2        # noqa: E731
    cy = lambda r: GY + r * CH + CH // 2        # noqa: E731
    for i, (x, y, fl, ty) in enumerate(R.ring):
        nx, ny = R.ring[(i + 1) % nverts][:2]
        col = "warp" if fl & 1 else "edge"
        if x == nx:
            k.vline(cx(x), cy(y), cy(ny), col, 4)
        else:
            k.hline(cx(x), cx(nx), cy(y), col, 4)
    for i, (x, y, fl, ty) in enumerate(R.ring):
        k.rect(cx(x) - 5, cy(y) - 5, 11, 11, "acc")
        lx = cx(x) + (8 if x < O.cw - 1 else -18)
        ly = cy(y) + (-22 if y > 0 else 8)
        k.text(lx, ly, str(i), "txt", 2, True)
    panel(k, ring_lines + ["", "FLAG 1: THE SEGMENT TO THE", "NEXT VERTEX BORDERS A WALKABLE", "NEIGHBOUR"],
          "OUTLINE VERTICES")
    k.legend(GX - 280, CAP_Y - 20, [("acc", "VERTEX"), ("edge", "OUTLINE"), ("warp", "SEAM SEGMENT")], 1)
    seamv = [i for i, v in enumerate(R.ring) if v[2] & 1]
    k.caption("The outline is the rectangle's border as a ring of %d vertices, in cells, going up the west side first. An "
              "extra vertex is put wherever a seam starts or ends: here %d, so the segment from vertex %d to the "
              "next vertex carries the seam flag, because it borders %s."
              % (nverts, nverts - 4, seamv[0], nname), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The outline is a ring of %d vertices, %d of them put where a seam starts or ends (the seam with %s)." % (nverts, nverts - 4, nname),
        calc=["Ring from the rectangle's corners: west side going up, then north, east, south; each vertex in cells (column, row)."]
        + ["Vertex %d: (%d, %d), flags %d, type %d." % (i, x, y, fl, ty) for i, (x, y, fl, ty) in enumerate(R.ring)]
        + ["Flag bit 0: the segment to the next vertex borders a walkable neighbour; bit 1 would mark a preset level (a town)."]))

    # ---- 3: the seam mark
    cell, g0, defg = mark_ev["after"]
    seam_cells = [(x, y) for y in range(O.ch) for x in range(O.cw) if g0[y][x]]
    gv = {g0[y][x] for (x, y) in seam_cells}
    assert len(gv) == 1, gv
    gval = gv.pop()
    slot = next(j for j in range(8) if 0x10 << j == gval)
    stm = dict(grids=mark_ev["after"], roles={})
    st = stm
    header(k, "BURIAL GROUNDS: THE SEAM MARK")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, stm, seam=seam_cells)
    for (x, y) in seam_cells:
        px, py = cell_xy(x, y)
        k.text_c(px + CW // 2, py + 18, "SLOT %d" % slot, "txt", 1)
    panel(k, ["%d CELLS ON THE SEAM SEGMENT," % len(seam_cells), "FROM (%d, %d) TO (%d, %d)" % (
        seam_cells[0][0], seam_cells[0][1], seam_cells[-1][0], seam_cells[-1][1]), "",
        "CELL BIT 0X1: BORDER", "WARP-SLOT FLAG 0X%X ON EACH" % gval, "= 0X10 << %d: SLOT %d" % (slot, slot), "",
        "SLOT %d OF THE LEVEL" % slot, "NAMES LEVEL %d" % nbr, "(%s)" % links_anim.nm(nbr)[:30], "",
        "NO DRAW IS MADE"], "SEAM MARK")
    k.legend(GX - 280, CAP_Y - 20, [("warp", "SEAM CELL (OUTLINE)")], 1)
    k.caption("The seam mark sets the border bit, 0x1, and the warp-slot flag on every cell of the flagged segment, end "
              "cell included. The flag is 0x10 shifted by the slot of this level that names %s, here slot %d, so %d "
              "cells carry 0x%X. The mark makes no draw." % (nname, slot, len(seam_cells), gval), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The seam mark flags %d cells with border bit 0x1 and warp slot %d." % (len(seam_cells), slot),
        calc=["Each ring vertex with flag bit 0: its segment's cells (end included) get cell bit 0x1 (0x3 for a typed seam, "
              "type 0 here) and the warp-slot flag in the second grid.",
              "The flag is 0x10 << (the first slot k whose Vis names the neighbour, level %d) = 0x10 << %d = 0x%X." % (nbr, slot, gval),
              "Cells: %s." % ", ".join("(%d, %d)" % c for c in seam_cells), "No draw is made."]))

    # ---- the border pass: one frame per segment
    roles = {}
    nseg = len(segs)
    ndraw = 0
    for s in segs:
        v, n = s["v"], s["n"]
        for e in s["edge"]:
            for yy in range(e["y"], e["y"] + e["h"]):
                for xx in range(e["x"], e["x"] + e["w"]):
                    roles[(xx, yy)] = "edge"
        again = bool(s["corner"] and s["edge"] and s["corner"]["d"] == s["edge"][0]["d"])
        if s["corner"]:
            roles[(s["corner"]["x"], s["corner"]["y"])] = "edge" if again else "corner"
        st = dict(grids=s["end"], roles=dict(roles))
        side = SIDE[DIRSIDE[s["d"]]]
        hot = [(e["x"], e["y"]) for e in s["edge"]] + ([(s["corner"]["x"], s["corner"]["y"])] if s["corner"] else [])
        pl, calc = [], []
        title = "SEGMENT %d OF %d" % (s["i"] + 1, nseg)
        pl.append("FROM (%d, %d) TO (%d, %d)" % (v[0], v[1], n[0], n[1]))
        pl.append("%s EDGE%s" % (side, ", SEAM SEGMENT" if s["flags"] & 1 else ""))
        calc.append("Segment %d of %d runs from vertex %d (%d, %d) to (%d, %d): the %s edge, flags %d."
                    % (s["i"] + 1, nseg, s["i"], v[0], v[1], n[0], n[1], side.lower(), s["flags"]))
        draws_here = []
        if s["edge"]:
            e0 = s["edge"][0]
            idxs = [(e["after"][0][e["y"]][e["x"]] >> 16) & 0xF for e in s["edge"]]
            pl.append("EDGE PIECE %d ON %d CELLS" % (e0["d"], len(s["edge"])))
            fu = [e for e in s["edge"] if e["first"]]
            if fu:
                pl.append("FIRST USE OF PIECE %d:" % e0["d"])
                pl.append("  FILES %d, DRAW %08X" % (e0["files"], fu[0]["draws"][0]))
                draws_here += [(e["d"], e["files"], e["draws"][0]) for e in fu]
            else:
                pl.append("PIECE %d USED BEFORE: NO DRAW" % e0["d"])
            pl.append("  FILE INDEXES %s" % ", ".join(str((e["after"][0][e["y"]][e["x"]] >> 16) & 0xF) for e in s["edge"]))
            if s["corner"] and not again:
                pl.append("  (THE LAST CELL IS REPLACED)")
            calc.append("Edge piece %d (Files %d) on cells %s; file indexes taken from the piece's rotation: %s."
                        % (e0["d"], e0["files"], ", ".join("(%d, %d)" % (e["x"], e["y"]) for e in s["edge"]), idxs))
        else:
            pl.append("NO EDGE PIECES")
        if s["open"]:
            oc = s["open"][0]
            ov = s["end"][0][oc[1]][oc[0]]
            pl.append("SEAM OPENING AT (%d, %d):" % oc)
            pl.append("  INDEX %d, BIT 0X400" % ((ov >> 16) & 0xF))
            calc.append("Seam opening: the segment's middle cell (%d, %d) gets file index %d and bit 0x400, written after "
                        "its edge piece, so the rotation's index for that cell is overwritten (the draw was made)."
                        % (oc[0], oc[1], (ov >> 16) & 0xF))
        if s["corner"]:
            c = s["corner"]
            cidx = (s["end"][0][c["y"]][c["x"]] >> 16) & 0xF
            if again:
                pl.append("EDGE PIECE %d AGAIN AT (%d, %d)" % (c["d"], c["x"], c["y"]))
                pl.append("  THE TURN IS STRAIGHT; NO DRAW")
                pl.append("  FILE INDEX %d (NEXT IN TURN)" % cidx)
            else:
                pl.append("CORNER PIECE %d AT (%d, %d)" % (c["d"], c["x"], c["y"]))
            if c["first"]:
                pl.append("  FILES %d, DRAW %08X" % (c["files"], c["draws"][0]))
                draws_here.append((c["d"], c["files"], c["draws"][0]))
            elif not again:
                pl.append("  USED BEFORE: NO DRAW")
            if again:
                calc.append("The vertex at (%d, %d) is a straight turn: the corner lookup gives row 2 of the style table, "
                            "the edge piece %d again, placed at the end cell with the next file index %d." % (
                                c["x"], c["y"], c["d"], cidx))
            else:
                calc.append("Corner piece %d placed at the segment's end (%d, %d); it replaces the edge piece there." % (
                    c["d"], c["x"], c["y"]))
        else:
            pl.append("NO CORNER AT (%d, %d)" % n)
            calc.append("The corner lookup for the turn at (%d, %d) gives no piece: nothing is placed and no bit set." % n)
        ndraw += len(draws_here)
        if s["seed"]:
            pl.append("SEED " + seed_hex(*s["seed"]))
        calc.append("Draws on this segment: %d%s." % (len(draws_here), "" if not draws_here else " (" + ", ".join(
            "piece %d, Files %d, low word %d" % (d, f, lo) for d, f, lo in draws_here) + ")"))
        if s["seed"]:
            calc.append("Level seed after the segment: %s (low:high)." % seed_cap(*s["seed"]))
        cap = ("Border pass, segment %d of %d, the %s edge from (%d, %d) to (%d, %d): " % (
            s["i"] + 1, nseg, side.lower(), v[0], v[1], n[0], n[1]))
        if s["edge"]:
            cap += "edge piece %d goes on %d cells" % (s["edge"][0]["d"], len(s["edge"]))
            cap += ", its first use drawing a start among its %d files" % s["edge"][0]["files"] if any(
                e["first"] for e in s["edge"]) else ", with no draw (used before)"
            cap += "; "
        if s["open"]:
            cap += "the middle cell of the seam becomes the seam opening, index forced after its rotation draw; "
        if not s["corner"]:
            cap += "no piece at the end cell, the turn having no corner"
        elif again:
            cap += "the end cell is a straight turn, so the edge piece is placed there again with no new draw"
        else:
            cap += "corner piece %d at the end cell%s" % (s["corner"]["d"], ", drawn at its first use" if s["corner"]["first"] else "")
        cap += "."
        header(k, "BURIAL GROUNDS: BORDER PASS, " + title)
        key_block(k, R)
        draw_neighbours(k, R)
        draw_grid(k, R, st, hot=hot, seam=seam_cells, opening=s["open"])
        panel(k, pl, "SEGMENT %d OF %d" % (s["i"] + 1, nseg))
        k.legend(GX - 280, CAP_Y - 20, LEGEND, 1)
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text="Border pass, segment %d of %d (%s edge): %s." % (
            s["i"] + 1, nseg, side.lower(), "edge piece %d, then %s" % (s["edge"][0]["d"], ("the edge piece again" if again else "a corner piece") if s["corner"] else "no corner")
            if s["edge"] else "no edge pieces"), calc=calc))

    # ---- the corner flood
    fb, fa = R.flood["before"], R.flood["after"]
    covered = sum(1 for y in range(O.ch) for x in range(O.cw) if fa[0][y][x] & 0x100 and not fb[0][y][x] & 0x100)
    corners = [(0, 0), (O.cw - 1, 0), (0, O.ch - 1), (O.cw - 1, O.ch - 1)]
    cornerbits = [fb[0][y][x] & 1 for (x, y) in corners]
    st = dict(grids=R.flood["after"], roles=dict(roles))
    header(k, "BURIAL GROUNDS: THE CORNER FLOOD")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, st, seam=seam_cells, opening=segs[-1]["open"] + [o for s in segs[:-1] for o in s["open"]],
              hot=corners)
    panel(k, ["FROM EACH OF THE 4 CORNER", "CELLS THE FLOOD FILLS ROW BY", "ROW WHILE A CELL HAS NO", "BORDER BIT 0X1", "",
              "CORNER CELLS WITH BIT 0X1:", "%d OF 4" % sum(cornerbits), "", "CELLS COVERED (0X100): %d" % covered, "",
              "NO DRAW IS MADE"], "CORNER FLOOD")
    k.legend(GX - 280, CAP_Y - 20, LEGEND, 1)
    k.caption("The corner flood starts at each of the four corner cells and covers cells (bit 0x100) while they have no "
              "border bit. %d of the four corner cells carry the border bit, so it covers %d cells here. It makes no draw." % (sum(cornerbits), covered), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(text="The corner flood covers %d cells: %d of the four corners have the border bit." % (covered, sum(cornerbits)),
                     calc=["From each corner cell, row by row, a cell with no bit 0x1 gets bit 0x100 (covered).",
                           "Corner cells (0, 0), (%d, 0), (0, %d), (%d, %d) with bit 0x1: %s." % (
                               O.cw - 1, O.ch - 1, O.cw - 1, O.ch - 1, cornerbits),
                           "Cells newly covered: %d. No draw is made." % covered]))

    # ---- the preset
    pe = [e for kind, e in R.events if kind == "place" and not e["border"]]
    assert len(pe) == 1
    p = pe[0]
    for yy in range(p["y"], p["y"] + p["h"]):
        for xx in range(p["x"], p["x"] + p["w"]):
            roles[(xx, yy)] = "preset"
    st = dict(grids=p["after"], roles=dict(roles))
    hot = [(xx, yy) for yy in range(p["y"], p["y"] + p["h"]) for xx in range(p["x"], p["x"] + p["w"])]
    pidx = (p["after"][0][p["y"]][p["x"]] >> 16) & 0xF
    opens = [o for s in segs for o in s["open"]]
    header(k, "BURIAL GROUNDS: THE PRESET")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, st, hot=hot, seam=seam_cells, opening=opens)
    panel(k, ["PIECE %d AT CELL (%d, %d)" % (p["d"], p["x"], p["y"]), "%d * %d TILES = %d * %d CELLS" % (
        p["w"] * 8, p["h"] * 8, p["w"], p["h"]), "",
        "FIRST USE OF PIECE %d:" % p["d"], "  FILES %d, DRAW %08X" % (p["files"], p["draws"][0]), "  FILE INDEX %d" % pidx, "",
        "SEED OUT " + seed_hex(*R.seed_out), "",
        "ALL %d CELLS GET BIT 0X200" % (p["w"] * p["h"]), "(PRESET FOOTPRINT)"], "PRESET")
    k.legend(GX - 280, CAP_Y - 20, LEGEND, 1)
    k.caption("Act I then places one preset on this level, piece %d at cell (%d, %d), with the rotation. "
              "It is %d * %d cells, so %d cells get the footprint bit 0x200; its first use draws a start among %d file%s "
              "and the first file used is one past the draw, index %d."
              % (p["d"], p["x"], p["y"], p["w"], p["h"], p["w"] * p["h"], p["files"], "" if p["files"] == 1 else "s", pidx),
              CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(text="Piece %d is placed at cell (%d, %d): %d * %d cells of footprint." % (p["d"], p["x"], p["y"], p["w"], p["h"]),
                     calc=["Place(%d, %d, piece %d, file -1): size %d * %d tiles / 8 = %d * %d cells."
                           % (p["x"], p["y"], p["d"], p["w"] * 8, p["h"] * 8, p["w"], p["h"]),
                           "First use of the piece: one draw of Files = %d; low word %d; seed after %s (low:high)."
                           % (p["files"], p["draws"][0], seed_cap(*p["seed"])),
                           "Each covered cell: file index %d in bits 16 to 19, bit 0x200 set; the anchor cell holds the piece number."
                           % pidx]))

    # ---- the final grid
    fcell = R.O.cell
    free = sum(1 for y in range(O.ch) for x in range(O.cw) if not fcell[y][x] & 0x1B81)
    oc = opens[0]
    ov = fcell[oc[1]][oc[0]]
    st = dict(grids=snap(O), roles=dict(roles))
    header(k, "BURIAL GROUNDS: THE FINAL GRID")
    key_block(k, R)
    draw_neighbours(k, R)
    draw_grid(k, R, st, seam=seam_cells, opening=opens)
    panel(k, ["SEED OUT " + seed_hex(*R.seed_out), "DRAWS IN THE WINDOW: %d" % len(R.draws), "",
              "OPENING CELL (%d, %d): 0X%X" % (oc[0], oc[1], ov), "  INDEX %d (BITS 16 TO 19)" % ((ov >> 16) & 0xF),
              "  0X400 SEAM OPENING", "  0X200 PRESET FOOTPRINT", "  0X1 BORDER", "",
              "CELLS WITH NONE OF THE MASK", "BITS 0X1B81: %d" % free], "FINAL CELL BITS")
    k.legend(GX - 280, CAP_Y - 20, LEGEND, 1)
    capf = ("The window ends with %d draws. The seam opening cell holds 0x%X: file index %d, the opening bit 0x400, the "
            "footprint bit 0x200 and the border bit 0x1. %s" % (
                len(R.draws), ov, (ov >> 16) & 0xF,
                "No cell is free (none of the occupied-mask bits 0x1B81 is clear), so the rooms pass makes no out room "
                "here, only the embedded preset." if free == 0 else
                "%d cell%s still free (none of the occupied-mask bits 0x1B81 set)." % (free, "" if free == 1 else "s")))
    k.caption(capf, CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(text="The window ends after %d draws; %d cells are free." % (len(R.draws), free),
                     calc=["Seed after the window: %s (low:high)." % seed_cap(*R.seed_out),
                           "Cell (%d, %d) = 0x%X: index %d, opening 0x400, footprint 0x200, border 0x1." % (
                               oc[0], oc[1], ov, (ov >> 16) & 0xF),
                           "Free cells (none of the mask 0x1B81): %d." % free,
                           "Level draws in order (low words): %s." % ", ".join(str(d) for d in R.draws)]))
    return frames, caps, R


HELP = """<li>The grid is the level cut into cells of 8 * 8 tiles; each box is one cell, D is the piece number, I the file index.</li>
<li>First the outline ring and the seam mark, then the border pass walks the ring and puts an edge piece on each cell and a corner piece at each turn.</li>
<li>The first use of a piece in the level draws a start for its file rotation; the pieces then take the next file in turn.</li>
<li>Every value is computed by our model of the outdoor generator for the illustrative seed given, not observed in the game.</li>"""


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--diff": "0", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        n, diff = int(argv[1], 0), int(opts["--diff"])
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < n <= drlg.M32 and 0 <= diff <= 2 and opts["--theme"] in K.THEMES):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "outdoor-%x-schematic" % n)
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _R = build(argv[0], n, diff, opts["--theme"])
    K.write_illustration(out, "outdoor", frames, caps, W, H, K.palette(opts["--theme"])[1], "outdoor level animation",
                         HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Animate one normal group of monsters placed on a toy room (docs/specs/monsters/spawn.md sections F, H): the leader's
random point with its warp test, the probe and the exact placement, the group size, and each member's ring walk with the
cells it refused. Schematic only (ADR-0036): boxes, text and cells in our own palette; the room is our own toy and holds
no map art.

Usage:
  python3 -I tools/pack_anim.py <root> [<monster id>] [--seed N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the merged data tree (workspace/merged). <monster id> is a MonStats Id (default swarm1: MinGrp 4,
MaxGrp 8, no minions, a footprint of 2); its MinGrp and MaxGrp, footprint size and collision class are read from the
tables. --seed N (default 0xC0FFEE) is an illustrative input: the room seed and the leader's unit seed are each started
with Init(N); in a game they come from the DRLG and from the creation step. --theme: dark or light palette values.
--schematic is accepted for the export builder and changes nothing. DIR defaults to workspace/render/anim/ and must stay
under workspace/. Outputs: frame-NNN.png, pack.gif, index.html, steps.json, schematic.json (ADR-0036).

The model. The ring walk of MonSpawnTry and the warp-distance rule are the functions tools/spawn_place.py gives
tools/monspawn.py (spawn.md H2) and tools/collision.py (NearWarpTest); this tool calls them. The rest is the control
flow of spawn.md F2, H1 and H2 on a toy grid: SpawnPosPick's twenty tries (two room draws, the warp test, the
probe), the exact placement (three room draws, the centre tested once), the group size on the leader's seed, and a
radius-3 walk per member (rings s = 3, 6, 9) in the group's box. The cell test and the creation mark are
tools/collision.py's World.collision_test and pattern_op on a one-room world over the toy grid (H3, H4: the plus
footprint of size 2 against the mask of the class's spawn collision, a created monster's 0x1000 centre). Not shown: the creation draw on the game seed, the
class cell test (it passes every class but five), the region-id test (the toy has one region), the waypoint point of
NearWarpTest and its side effects, MonStats minions (this class has none), the unit's stats.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import collision  # noqa: E402
import excel_bin  # noqa: E402
import monpool  # noqa: E402
import rng  # noqa: E402
import schematic_kit as K  # noqa: E402
import spawn_place  # noqa: E402

W, H = 960, 500
CAP_Y = 424
CELL = 12
GX, GY = 100, 50                 # the toy room's first subtile; the grid is GW x GH subtiles
GW, GH = 40, 30
BOX = (105, 55, 135, 65)         # the logic box in subtiles: 5 x its tile rectangle (21, 11) to (27, 13)
OX, OY = 14, 40                  # the grid's pixel origin
WARP = (116, 66)                 # the toy's one warp point, in subtiles
WARP_DIST = 100                  # an illustrative WarpDist (a squared distance in subtiles)
SIZE = 2                         # the footprint used by the default class: the plus of five cells
HELP = """<li>The toy room: the light cells are the logic box, the dark cells outside it are only reached by a ring walk, the bright blocks are walls the grid marks as blocked.</li>
<li>The leader: a random point in the box (two room draws), refused when it is too close to the warp point, then a probe and the exact placement, each with three more room draws.</li>
<li>Each member: a walk round square rings 3, 6 and 9 subtiles from the leader (radius 3), each ring with its own three room draws. It starts at a random cell of the ring, moves before it tests, skips a cell outside the box untested, and takes the first cell whose footprint is clear.</li>
<li>Every value is computed by our model for the illustrative room and seed, not observed in the game.</li>"""

# the toy's walls: (x0, y0, w, h) in subtiles of the grid (offsets from GX, GY), value 0x0001 (tile bit 0)
WALLS = ((15, 9, 2, 5), (24, 7, 6, 2), (31, 12, 1, 3))


class Counting(spawn_place.S):
    """The model's seed with a count of its steps."""
    def __init__(self, t):
        super().__init__(t)
        self.n = 0

    def step(self):
        self.n += 1
        return super().step()


class Toy:
    """The toy room's grid. The collision test and the creation mark are the model's own (tools/collision.py
    World.collision_test and pattern_op, spawn.md H3, H4) on a world of this one room; only the grid is the toy's."""
    ROOM = 1

    def __init__(self, mask, size):
        self.mask, self.size = mask, size
        cells = [0] * (GW * GH)
        for wx, wy, ww, wh in WALLS:
            for y in range(wy, wy + wh):
                for x in range(wx, wx + ww):
                    cells[y * GW + x] = 0x0001
        self.world = collision.World.one_room(self.ROOM, GX, GY, GW, GH, cells)
        self.g = {(GX + i % GW, GY + i // GW): v for i, v in enumerate(cells) if v}     # the walls, for the frames

    def cell(self, x, y):
        """The cell's word with every bit kept, as CollisionTest reads it (0x27 for a cell in no room)."""
        return self.world.cell_test(self.ROOM, x, y, 0xFFFF)

    def test(self, x, y):
        return self.world.collision_test(self.ROOM, x, y, self.size, self.mask)

    def inside(self, x, y):
        return BOX[0] <= x < BOX[2] and BOX[1] <= y < BOX[3]

    def mark(self, x, y):
        # H4: the creation's pattern for this size (1 for size 2: the plus of the monster bit, the 0x1000 centre)
        self.world.pattern_op(self.ROOM, x, y, collision.PATTERN_BY_SIZE[self.size], 0x100, False)


def place(toy, rs, us, mn, mx):
    """spawn.md F2 with H1, H2 on the toy: returns the record of the whole group. rs: the room seed, us: the leader's
    unit seed (both Counting). Every try, probe, ring and cell is recorded for the frames."""
    x0, y0 = BOX[0] + 1, BOX[1] + 1
    w, h = BOX[2] - x0, BOX[3] - y0
    rec = {"tries": [], "w": w, "h": h, "x0": x0, "y0": y0}

    def probe_cells(cx, cy):
        cells = []

        def accept(x, y):
            if not toy.inside(x, y):
                cells.append((x, y, "out", 0))
                return False
            v = toy.test(x, y)
            cells.append((x, y, "block" if v else "ok", v))
            return v == 0
        n0 = rs.n
        found = spawn_place.ring_search(rs, cx, cy, -1, accept)
        return found, cells, rs.n - n0

    leader = None
    for t in range(20):
        a = rs.n
        x = x0 + rs.rangeb(w)
        y = y0 + rs.rangeb(h)
        tr = {"try": t + 1, "x": x, "y": y, "seed": rs.t(), "near": spawn_place.near_point([WARP[0]], [WARP[1]], WARP_DIST, x, y)}
        d2 = (x - WARP[0]) ** 2 + (y - WARP[1]) ** 2
        tr["d2"] = d2
        rec["tries"].append(tr)
        if tr["near"]:
            continue
        found, cells, nd = probe_cells(x, y)
        tr.update(probe=found, pcells=cells, pdraws=nd, pseed=rs.t())
        if found:
            leader = (x, y)
            break
    if leader is None:
        rec["leader"] = None
        return rec
    # the exact placement at the returned point: the same three draws, the centre tested once
    found, cells, nd = probe_cells(*leader)
    assert found == leader, (found, leader)
    rec["exact"] = {"cells": cells, "draws": nd, "seed": rs.t()}
    toy.mark(*leader)
    rec["leader"] = leader
    r = us.rangeb(mx - mn + 1)
    k = (mn - 1) + r
    rec.update(r=r, k=k, useed=us.t(), members=[])
    for i in range(k):
        cells = []
        n0 = rs.n
        s0 = rs.t()

        def accept(x, y, cells=cells):
            if not toy.inside(x, y):
                cells.append((x, y, "out", 0))
                return False
            v = toy.test(x, y)
            cells.append((x, y, "block" if v else "ok", v))
            return v == 0
        found = spawn_place.ring_search(rs, leader[0], leader[1], 3, accept)
        m = {"i": i + 1, "cells": cells, "found": found, "draws": rs.n - n0, "seed0": s0, "seed": rs.t()}
        if found:
            toy.mark(*found)
        rec["members"].append(m)
    return rec


def class_info(root, mid):
    excel = os.path.join(root, "data", "global", "excel")
    t = monpool.Tables(excel)
    h, rows = excel_bin.read_txt(excel_bin.find_file(excel, "monstats", ".txt"))
    cls = None
    for i, r in enumerate(rows):
        if r[0].strip() == mid:
            cls = i
    if cls is None:
        return None
    m2 = t.ms2rec(cls)
    return dict(cls=cls, name=mid, mn=t.ms[cls][0x2F], mx=t.ms[cls][0x30],
                size=struct.unpack("b", m2[8:9])[0], spawncol=m2[0x0A],
                minion=struct.unpack_from("<h", t.ms[cls], 0x26)[0])


def cells_n(n):
    return "1 cell" if n == 1 else "%d cells" % n


def hx(t):
    return "%08X:%08X" % t


def build(root, mid, seed, theme):
    ci = class_info(root, mid)
    assert ci is not None and ci["spawncol"] == 0 and ci["size"] == 2 and ci["minion"] < 0, ci
    mask = spawn_place.MASK_BY_SPAWNCOL[ci["spawncol"]]
    toy = Toy(mask, ci["size"])
    walls = dict(toy.g)
    rs = Counting((seed, rng.INIT_HIGH))
    us = Counting((seed, rng.INIT_HIGH))
    rec = place(toy, rs, us, ci["mn"], ci["mx"])
    assert rec["leader"] is not None
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    name = mid.upper()
    placed = {}          # (x, y) -> label of the creatures placed so far

    def header(s):
        k.text(14, 12, s, "acc", 2, True)

    def px(x, y):
        return OX + (x - GX) * CELL, OY + (y - GY) * CELL

    def room(tested=(), cur=None, notes=None):
        """The grid: the box, the walls, the warp point, the placed monsters, and the cells a walk just tested."""
        for yy in range(GH):
            for xx in range(GW):
                x, y = GX + xx, GY + yy
                p, q = px(x, y)
                ins = toy.inside(x, y)
                col = "room" if ins else "panel"
                if walls.get((x, y)):
                    col = "edge"
                k.rect(p, q, CELL - 1, CELL - 1, col)
        wx, wy = px(*WARP)
        k.rect(wx - 3, wy - 3, CELL + 5, CELL + 5, "warp")
        k.outline(wx - 3, wy - 3, CELL + 5, CELL + 5, "txt")
        for (x, y), lab in placed.items():
            p, q = px(x, y)
            k.box(p - 1, q - 1, CELL + 1, CELL + 1, [lab], "cur", "good" if lab == "L" else "acc", "txt", 1,
                  t=2 if lab == "L" else 1)
        for x, y, why, _v in tested:
            if (x, y) in placed:
                continue
            p, q = px(x, y)
            k.rect(p + 3, q + 3, CELL - 7, CELL - 7, {"out": "dim", "block": "bad", "ok": "good"}[why])
        if cur is not None:
            p, q = px(*cur)
            k.outline(p - 2, q - 2, CELL + 3, CELL + 3, "txt", 2)
        k.legend(OX, 408, [("room", "BOX"), ("edge", "WALL"), ("warp", "WARP POINT"), ("good", "TAKEN"),
                           ("bad", "BLOCKED"), ("dim", "OUTSIDE BOX")], 1, 14)

    def panel(lines, y=46):
        for i, ln in enumerate(lines):
            s, c, sc = ln if isinstance(ln, tuple) else (ln, "txt", 2)
            k.text(508, y, s, c, sc, sc == 3)
            y += 7 * sc + 8

    # ---- 1: the inputs
    header("A GROUP OF %s ON A TOY ROOM" % name)
    room()
    panel([("MINGRP %d, MAXGRP %d" % (ci["mn"], ci["mx"]), "txt", 2),
           ("FOOTPRINT: A PLUS OF 5 CELLS", "dim", 2),
           ("MASK %04X" % mask, "dim", 2),
           ("ROOM SEED %s" % hx((seed, rng.INIT_HIGH)), "dim", 2),
           ("LEADER SEED %s" % hx((seed, rng.INIT_HIGH)), "dim", 2),
           ("TOY: WARPDIST %d, ONE WARP POINT" % WARP_DIST, "dim", 2),
           ("LEADER: UP TO 20 RANDOM POINTS", "txt", 2),
           ("MEMBERS: RINGS 3, 6, 9 AROUND IT", "txt", 2)])
    k.caption("A group of %s: a leader at a random point of the box, then k members found by ring walks around it "
              "(spawn F2, H1, H2)." % mid, CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="A normal group of class %s on a toy room: the leader's point, then each member's cell." % mid,
        calc=["spawn.md F2: SpawnGroup(room, box, class, min = %d, max = %d): SpawnPosPick, the leader, the size draw, then k members." % (ci["mn"], ci["mx"]),
              "class %s (MonStats row %d): MinGrp %d, MaxGrp %d, footprint size %d, spawn collision 0, mask 0x%04X." % (
                  mid, ci["cls"], ci["mn"], ci["mx"], ci["size"], mask),
              "illustrative: room seed and leader seed each Init(%d); WarpDist %d; the room, its walls and the warp point are the toy's." % (seed, WARP_DIST)]))

    # ---- 2..: the leader's tries
    for tr in rec["tries"]:
        header("LEADER: TRY %d OF UP TO 20" % tr["try"])
        room(cur=(tr["x"], tr["y"]), tested=tr.get("pcells", ()))
        done = tr.get("probe")
        lines = [("TWO ROOM DRAWS", "dim", 2),
                 ("X = %d, Y = %d" % (tr["x"], tr["y"]), "txt", 3),
                 ("SEED AFTER %s" % hx(tr["seed"]), "dim", 2),
                 ("SQUARED DISTANCE TO THE WARP", "txt", 2),
                 ("POINT: %d" % tr["d2"], "txt", 2),
                 ("%d %s WARPDIST %d" % (tr["d2"], "<" if tr["near"] else ">=", WARP_DIST), "bad" if tr["near"] else "good", 2)]
        if tr["near"]:
            lines += [("TOO CLOSE: THE TRY IS REFUSED", "bad", 2), ("NO PROBE, NEXT TRY", "dim", 2)]
            cap = "Try %d: point (%d, %d), squared distance %d to the warp point, below WarpDist %d, so it is refused with no probe (spawn H1)." % (
                tr["try"], tr["x"], tr["y"], tr["d2"], WARP_DIST)
            text = "Try %d is point (%d, %d); it is too close to the warp point." % (tr["try"], tr["x"], tr["y"])
            calc = ["H1: x = %d + Range(room.seed, %d) = %d, y = %d + Range(room.seed, %d) = %d (2 room draws)." % (
                        rec["x0"], rec["w"], tr["x"], rec["y0"], rec["h"], tr["y"]),
                    "H1: NearWarpTest: squared distance %d < WarpDist %d, so the try continues with no probe." % (tr["d2"], WARP_DIST)]
        else:
            v = tr["pcells"][0]
            lines += [("PROBE: 3 ROOM DRAWS", "txt", 2),
                      ("PLUS AT THE CENTRE: %s" % ("CLEAR" if v[2] == "ok" else "NOT CLEAR"), "good" if v[2] == "ok" else "bad", 2)]
            if v[2] == "ok":
                lines.append(("THE LEADER'S POINT", "good", 2))
            else:
                lines.append(("NEXT TRY", "dim", 2))
            cap = "Try %d: point (%d, %d) is far enough from the warp point; the probe makes 3 room draws and tests the footprint at the centre once: %s (spawn H1, H2)." % (
                tr["try"], tr["x"], tr["y"], "clear, so this is the leader's point" if v[2] == "ok" else "not clear, so the next try")
            text = "Try %d is point (%d, %d); the probe %s." % (tr["try"], tr["x"], tr["y"],
                                                                 "finds it free" if v[2] == "ok" else "refuses it")
            calc = ["H1: x = %d + Range(room.seed, %d) = %d, y = %d + Range(room.seed, %d) = %d (2 room draws)." % (
                        rec["x0"], rec["w"], tr["x"], rec["y0"], rec["h"], tr["y"]),
                    "H1: NearWarpTest: squared distance %d >= WarpDist %d, so the probe runs: MonSpawnTry radius -1, flags 0x01 (3 room draws)." % (
                        tr["d2"], WARP_DIST),
                    "H2: the centre (%d, %d) is tested once: collision value 0x%04X, %s." % (
                        v[0], v[1], v[3], "0, taken" if v[2] == "ok" else "non-zero, refused")]
        panel(lines)
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))

    # ---- the exact placement
    lx, ly = rec["leader"]
    header("LEADER: THE EXACT PLACEMENT")
    placed[(lx, ly)] = "L"
    room()
    panel([("POINT (%d, %d)" % (lx, ly), "txt", 3),
           ("EXACT PLACEMENT: RADIUS -1", "txt", 2),
           ("3 ROOM DRAWS, CENTRE TESTED", "txt", 2),
           ("ONCE MORE: FREE", "good", 2),
           ("SEED AFTER %s" % hx(rec["exact"]["seed"]), "dim", 2),
           ("THE LEADER IS CREATED; ITS", "txt", 2),
           ("CENTRE GETS THE 0X1000 MARK", "txt", 2),
           ("THE MARK BLOCKS LATER CELLS", "dim", 2)])
    k.caption("The leader is created at (%d, %d): an exact placement still makes 3 room draws, and the created monster's "
              "centre blocks later placements through its 0x1000 mark (spawn H1, H4)." % (lx, ly), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The leader is placed at (%d, %d) and marks its centre." % (lx, ly),
        calc=["H1: MonSpawnTry radius -1, flags 0: 3 room draws, the centre tested once: free; the unit is created.",
              "H4: a created monster blocks through its 0x1000 cells, its centre for size 2.",
              "room seed after the leader = {%08x:%08x}." % rec["exact"]["seed"]]))

    # ---- the group size
    header("GROUP SIZE ON THE LEADER'S SEED")
    room()
    panel([("SIZE = (MIN - 1) + RANGE", "txt", 2),
           ("RANGE(LEADER SEED, %d) = %d" % (ci["mx"] - ci["mn"] + 1, rec["r"]), "txt", 2),
           ("K = %d + %d = %d MEMBERS" % (ci["mn"] - 1, rec["r"], rec["k"]), "good", 3),
           ("THE GROUP HAS %d MONSTERS" % (1 + rec["k"]), "txt", 2),
           ("LEADER SEED %s" % hx(rec["useed"]), "dim", 2),
           ("FAILED MEMBERS ARE MISSING", "dim", 2)])
    k.caption("The group size is drawn on the leader's seed: Range(seed, %d) = %d, so k = %d + %d = %d members after the "
              "leader; a member whose placement fails is missing (spawn F2)." % (
                  ci["mx"] - ci["mn"] + 1, rec["r"], ci["mn"] - 1, rec["r"], rec["k"]), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The leader's seed draws the group size: %d members after the leader." % rec["k"],
        calc=["F2: k = (min - 1) + Range(leader.seed, max - min + 1) = %d + %d = %d." % (ci["mn"] - 1, rec["r"], rec["k"]),
              "F2: the draw is on the leader's unit seed, after any MonStats minions (this class has none).",
              "leader seed after = {%08x:%08x}." % rec["useed"]]))

    # ---- the members
    for m in rec["members"]:
        n = len(m["cells"])
        nout = sum(1 for c in m["cells"] if c[2] == "out")
        nblk = sum(1 for c in m["cells"] if c[2] == "block")
        header("MEMBER %d OF %d: RING WALK" % (m["i"], rec["k"]))
        ring = None
        if m["found"]:
            placed[m["found"]] = str(m["i"])
            ring = max(abs(m["found"][0] - lx), abs(m["found"][1] - ly))
        room(tested=m["cells"])
        panel([("3 ROOM DRAWS PER RING", "dim", 2),
               ("SEED BEFORE %s" % hx(m["seed0"]), "dim", 2),
               ("CELLS WALKED: %d" % n, "txt", 3),
               ("OUTSIDE THE BOX, SKIPPED: %d" % nout, "dim", 2),
               ("BLOCKED: %d" % nblk, "bad" if nblk else "dim", 2),
               (("TAKEN: (%d, %d) ON RING %d" % (m["found"][0], m["found"][1], ring)) if m["found"] else
                "NO CELL: THE MEMBER IS MISSING", "good" if m["found"] else "bad", 2),
               ("THE WALK MOVES BEFORE IT", "dim", 2), ("TESTS, FROM A RANDOM CELL", "dim", 2)])
        # the order strip
        sx = 508
        for i, c in enumerate(m["cells"][:28]):
            k.rect(sx + i * 15, 330, 13, 13, {"out": "dim", "block": "bad", "ok": "good"}[c[2]])
        k.text(508, 350, "WALK ORDER, LEFT TO RIGHT" + (" (FIRST 28)" if n > 28 else ""), "dim", 1)
        r_tail = "taken at (%d, %d)" % m["found"] if m["found"] else "no cell was taken"
        k.caption("Member %d: the walk round rings 3, 6 and 9 from the leader reaches %s in order, skips %d outside the box "
                  "untested and refuses %d blocked; %s (spawn H2)." % (m["i"], cells_n(n), nout, nblk, r_tail), CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Member %d: %s walked, %d outside the box, %d blocked; %s." % (m["i"], cells_n(n), nout, nblk, r_tail),
            calc=["F2, H2: MonSpawnTry near the leader (%d, %d), with the group's box, radius 3 (rings s = 3, 6, 9): each ring has 3 room draws, then a walk from a random cell that moves before it tests." % (lx, ly),
                  "H2: a cell outside the box rectangle is skipped with no test; the toy has one region, so the region-id test passes; a cell whose plus footprint gives a non-zero value under mask 0x%04X is refused." % mask,
                  "%d room draws; room seed {%08x:%08x} before, {%08x:%08x} after." % ((m["draws"],) + m["seed0"] + m["seed"])]))

    # ---- the end
    header("THE GROUP")
    room()
    got = [m for m in rec["members"] if m["found"]]
    panel([("%d OF %d MEMBERS PLACED" % (len(got), rec["k"]), "good" if len(got) == rec["k"] else "txt", 2),
           ("GROUP OF %d MONSTERS" % (1 + len(got)), "txt", 3),
           ("SEED AFTER %s" % hx(rs.t()), "dim", 2),
           ("%d ROOM DRAWS IN ALL" % rs.n, "dim", 2),
           ("NOT SHOWN: THE CREATION DRAW", "dim", 2), ("ON THE GAME SEED, EACH TIME", "dim", 2)])
    k.caption("The group stands: the leader and %d of %d members, after %d room draws (spawn F2, H1, H2). Each creation "
              "also steps the game seed once, which is not shown (spawn J)." % (len(got), rec["k"], rs.n), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The group: the leader and %d members, after %d room draws." % (len(got), rs.n),
        calc=["room draws: %d in all; room seed after = {%08x:%08x}." % ((rs.n,) + rs.t()),
              "leader (%d, %d)%s." % (lx, ly, "".join("; member %d (%d, %d)" % ((m["i"],) + m["found"]) for m in got))]))
    return frames, caps, k.pal, rec


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--seed": "0xC0FFEE", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) not in (1, 2) or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        seed = int(opts["--seed"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not 0 < seed <= 0xFFFFFFFF:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    mid = argv[1] if len(argv) == 2 else "swarm1"
    ci = class_info(argv[0], mid)
    if ci is None or ci["spawncol"] != 0 or ci["size"] != 2 or ci["minion"] >= 0:
        print("class %r is not usable here (it needs a footprint of 2, spawn collision 0 and no minions)" % mid,
              file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "pack-%s-%x-schematic" % (mid, seed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _rec = build(argv[0], mid, seed, opts["--theme"])
    K.write_illustration(out, "pack", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "monster group placement animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

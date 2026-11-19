"""Animate the four spawn tests on a toy room's subtiles (docs/specs/drlg/collision.md sections C, E, G4, H, I and the predicate
order; docs/specs/monsters/spawn.md H): NearWarpTest, LogicRegionIdAt, SpawnClassCellTest and CollisionTest on seven candidate
points of one toy room, each stopping at the first test that fails. Schematic only (ADR-0036): boxes, text and cells in our own
palette; the room is our own toy and holds no map art.

Usage:
  python3 -I tools/collision_anim.py <root> [--base N] [--theme dark|light] [--out DIR] [--schematic]

<root> is accepted for the export builder and read for nothing: the model needs no table. --base N (default 528) is the
monster class's MonStats BaseId, which SpawnClassCellTest keys on: 206, 228, 298, 334 and 528 have a cell test, any other
value passes (spec H1). --theme: dark or light palette values. --schematic is accepted for the export builder and changes
nothing. DIR defaults to workspace/render/anim/collision-schematic/ and must stay under workspace/. Outputs: frame-NNN.png,
collision.gif, index.html, steps.json, schematic.json.

The toy: a room of 40 by 30 subtiles (8 by 6 tiles) with a long wall, a small block, one warp point, one waypoint point and a
WarpDist of 100 (a squared distance, in subtiles; the same toy numbers as tools/pack_anim.py), and a box grid of two regions
(tiles 0 to 4 of the box's region 1, tiles 5 to 7 of region 2). Steps: the room; one step per candidate point, with the four
tests in the order of the spec's predicate order and the later tests marked not called after a failure; the summary. The tests
are the model's: tools/collision.py's World.collision_test on a world of this room's grid (the plus footprint of size 2 against
the mask 0x3C01), World.logic_id (G4), World.class_cell_base (H1) and near_waypoint (I1), with spawn_place.near_point for the
warp points. Not shown: the rectangle test, NearWarpTest's side effects (the room activation and the level-seed step of its
waypoint lookup), the draws that choose the candidates, the creation marks. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import collision  # noqa: E402
import schematic_kit as K  # noqa: E402
import spawn_place  # noqa: E402

W, H = 960, 500
CAP_Y = 424
CELL = 10
OX, OY = 14, 44
GX, GY = 100, 50                  # the toy room's first subtile; the grid is GW x GH subtiles
GW, GH = 40, 30
TX, TY = GX // 5, GY // 5         # the room's tile origin
ROOM = 1
MASK = 0x3C01                     # the default spawn mask (spawn H3)
SIZE = 2                          # the footprint: the plus of five cells
WARP = (GX + 14, GY + 5)          # the toy's one warp point, in subtiles
WAYPOINT = (TX + 6, TY + 1)       # the toy's type-11 point, in tiles (NearWarpTest scales it by 5)
WARP_DIST = 100                   # an illustrative WarpDist (a squared distance in subtiles)
BOX_ID = 1                        # the id of the logic box the monster is placed in
WALLS = ((24, 0, 1, 25), (8, 18, 3, 3))      # (x0, y0, w, h) in subtiles from (GX, GY), tile bit 0
# the candidates, offsets from (GX, GY): each stops at a different test (a note names what the toy was built to show)
POINTS = ((16, 8, "NEAR THE WARP POINT"), (32, 8, "NEAR THE WAYPOINT POINT"), (33, 20, "IN ANOTHER REGION"),
          (7, 15, "THE CLASS'S OFFSET CELL IS A WALL"), (9, 19, "THE POINT IS A WALL"), (23, 22, "A WALL TOUCHES THE PLUS"),
          (18, 24, "CLEAR"))
NAMES = {"NEARWARPTEST": "NearWarpTest", "LOGICREGIONIDAT": "LogicRegionIdAt", "SPAWNCLASSCELLTEST": "SpawnClassCellTest",
         "COLLISIONTEST": "CollisionTest"}
HELP = """<li>The room is 40 by 30 subtiles. Light cells are region 1 (the box's region), the tinted cells region 2; the bright cells are walls, the two marks are the warp point and the waypoint point.</li>
<li>For each candidate point the four tests run in the game's order and the first one that fails refuses the point; the tests after it are not called.</li>
<li>The yellow cell is the point, its four neighbours are the plus footprint of a size-2 monster, the blue outline is the cell the class's own test reads.</li>
<li>Every value is computed by our model for the toy room, not observed in the game.</li>"""


def hx(v):
    return "0x%04X" % v


class Toy:
    def __init__(self, base):
        self.base = base
        cells = [0] * (GW * GH)
        for wx, wy, ww, wh in WALLS:
            for y in range(wy, wy + wh):
                for x in range(wx, wx + ww):
                    cells[y * GW + x] = 0x0001
        self.cells = cells
        self.world = collision.World.one_room(ROOM, GX, GY, GW, GH, cells)
        # the logic record's box grid, one id per tile: region 1 in tiles 0 to 4, region 2 in tiles 5 to 7 (G4)
        self.lg = {"fl": 2, "first": None, "t": (TX, TY),
                   "grid": (None, None, [[BOX_ID if gx < 5 else 2 for gx in range(GW // 5)] for gy in range(GH // 5)])}

    def tests(self, x, y):
        """The four tests of one candidate point in the spec's order: [(name, ran, passed, detail)]; a test after a failure is
        not run. A test 'passes' when the point survives it."""
        out = []
        # NearWarpTest (I1): the warp points, then the type-11 point
        d2 = (x - WARP[0]) ** 2 + (y - WARP[1]) ** 2
        near = spawn_place.near_point([WARP[0]], [WARP[1]], WARP_DIST, x, y)
        assert near == (d2 < WARP_DIST)
        if near:
            out.append(("NEARWARPTEST", True, False, "WARP POINT: D2 %d < %d" % (d2, WARP_DIST), "the point is near a warp point"))
        else:
            wx, wy = WAYPOINT[0] * 5, WAYPOINT[1] * 5
            d2w = (x - wx) ** 2 + (y - wy) ** 2
            nw = collision.near_waypoint(WAYPOINT[0], WAYPOINT[1], WARP_DIST, x, y)
            assert nw == (d2w < WARP_DIST)
            out.append(("NEARWARPTEST", True, not nw,
                        ("WAYPOINT POINT: D2 %d < %d" % (d2w, WARP_DIST)) if nw else "D2 %d AND %d, BOTH >= %d" % (d2, d2w, WARP_DIST),
                        "the point is near the waypoint point" if nw else "no warp point or waypoint point is near"))
            if nw:
                return self.skip(out)
        if not out[-1][2]:
            return self.skip(out)
        # LogicRegionIdAt (G4) against the box's id
        r = self.world.room_at(ROOM, x, y)
        rid = self.world.logic_id(self.lg, x, y) if r else 0
        ok = rid == BOX_ID
        out.append(("LOGICREGIONIDAT", True, ok, "REGION %d, BOX %d" % (rid, BOX_ID),
                    "the point's region is the box's" if ok else "the point's region differs from the box's"))
        if not ok:
            return self.skip(out)
        # SpawnClassCellTest (H1), flag 1 as the pass makes it
        cc = self.world.class_cell_base(self.base, ROOM, x, y, 1)
        row = collision.CLASS_CELL.get(self.base)
        if self.base == 298:
            det, why = "BASEID 298 PASSES WITH FLAG 1", "the class passes with flag 1"
        elif row is None:
            det, why = "BASEID %d HAS NO CELL TEST" % self.base, "the class has no cell test"
        else:
            cx, cy = x + row[0], y + row[1]
            v = self.world.collision_test(ROOM, cx, cy, 2, row[2])
            det = "CELL (%+d,%+d) PLUS & %s = %s" % (row[0], row[1], hx(row[2]), hx(v))
            why = "the class's offset cell is clear" if cc else "the class's offset cell is blocked"
        out.append(("SPAWNCLASSCELLTEST", True, bool(cc), det, why))
        if not cc:
            return self.skip(out)
        # CollisionTest (E): the plus of size 2 against the mask
        v = self.world.collision_test(ROOM, x, y, SIZE, MASK)
        out.append(("COLLISIONTEST", True, v == 0, "PLUS & %s = %s" % (hx(MASK), hx(v)),
                    "the plus is clear: the point stands" if v == 0 else "the plus is blocked"))
        return self.skip(out)

    @staticmethod
    def skip(out):
        names = ("NEARWARPTEST", "LOGICREGIONIDAT", "SPAWNCLASSCELLTEST", "COLLISIONTEST")
        done = {o[0] for o in out}
        return out + [(n, False, None, "NOT CALLED", "not called: an earlier test failed") for n in names if n not in done]


def build(base, theme):
    toy = Toy(base)
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    results = [(x, y, note, toy.tests(GX + x, GY + y)) for x, y, note in POINTS]

    def grid(point=None, cc=None):
        for gy in range(GH):
            for gx in range(GW):
                v = toy.cells[gy * GW + gx]
                fill = "dim" if v else ("room" if gx // 5 < 5 else "roomdone")
                k.rect(OX + gx * CELL, OY + gy * CELL, CELL - 1, CELL - 1, fill)
        k.rect(OX + (WARP[0] - GX) * CELL, OY + (WARP[1] - GY) * CELL, CELL - 1, CELL - 1, "warp")
        k.rect(OX + (WAYPOINT[0] * 5 - GX) * CELL, OY + (WAYPOINT[1] * 5 - GY) * CELL, CELL - 1, CELL - 1, "door")
        if cc:
            k.outline(OX + cc[0] * CELL - 1, OY + cc[1] * CELL - 1, CELL + 1, CELL + 1, "blue", 2)
        if point:
            px, py = point
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                k.rect(OX + (px + dx) * CELL, OY + (py + dy) * CELL, CELL - 1, CELL - 1, "cur")
                k.outline(OX + (px + dx) * CELL, OY + (py + dy) * CELL, CELL - 1, CELL - 1, "acc", 1)
            k.rect(OX + px * CELL, OY + py * CELL, CELL - 1, CELL - 1, "acc")
        k.outline(OX - 2, OY - 2, GW * CELL + 3, GH * CELL + 3, "grey", 2)

    def put(cap, text, calc):
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))

    # ---- the room
    k.text(14, 12, "THE TOY ROOM: 40 BY 30 SUBTILES", "acc", 2, True)
    grid()
    k.legend(14, 360, [("room", "REGION 1 (THE BOX)"), ("roomdone", "REGION 2"), ("dim", "WALL"), ("warp", "WARP POINT"),
                       ("door", "WAYPOINT POINT")], sc=1)
    for j, s in enumerate(("A POINT IS REFUSED BY THE FIRST", "TEST THAT FAILS. THE ORDER:", "NEARWARPTEST, LOGICREGIONIDAT,",
                           "SPAWNCLASSCELLTEST, COLLISIONTEST.", "WARPDIST %d (A SQUARED DISTANCE)" % WARP_DIST,
                           "CLASS BASEID %d, SIZE %d, MASK %s" % (base, SIZE, hx(MASK)))):
        k.text(440, 60 + j * 28, s, "dim" if j < 4 else "txt", 2)
    put("A toy room of 40 by 30 subtiles with walls, a warp point, a waypoint point and two logic regions. Seven candidate points "
        "meet the four spawn tests, which run in a fixed order (collision, predicate order).",
        "A toy room and seven candidate points.",
        ["collision, predicate order: per try NearWarpTest (when avoidWarp), then LogicRegionIdAt (with a box), then the probe; per ring cell the "
         "rectangle test, LogicRegionIdAt, SpawnClassCellTest, CollisionTest.",
         "toy: WarpDist %d, one warp point, one waypoint point, box id %d, class BaseId %d, plus footprint, mask %s." % (
             WARP_DIST, BOX_ID, base, hx(MASK))])
    # ---- one step per candidate
    for i, (x, y, note, res) in enumerate(results):
        row = collision.CLASS_CELL.get(base)
        cc = (x + row[0], y + row[1]) if row else None
        k.text(14, 12, "POINT %d OF %d: (%d, %d) - %s" % (i + 1, len(results), x, y, note), "acc", 2, True)
        grid((x, y), cc if res[2][1] else None)
        first_fail = next((r for r in res if r[1] and not r[2]), None)
        for j, (name, ran, ok, det, why) in enumerate(res):
            yy = 56 + j * 66
            col = "dim" if not ran else ("good" if ok else "bad")
            k.box(440, yy, 500, 56, [(name, "txt"), ((det if ran else "A TEST EARLIER FAILED"), col)], "panel",
                  "good" if ran and ok else ("bad" if ran else "grey"), sc=2)
        verdict = ("THE POINT STANDS: ALL FOUR TESTS PASS" if first_fail is None else "REFUSED BY %s" % first_fail[0])
        k.text(440, 56 + 4 * 66 + 2, verdict, "good" if first_fail is None else "bad", 2, True)
        cap = ("The point (%d, %d) passes all four tests: CollisionTest reads the plus as clear (collision, predicate order)." % (x, y)
               if first_fail is None else
               "The point (%d, %d) is refused: %s fails, %s%s (collision, predicate order)." % (
                   x, y, NAMES[first_fail[0]], first_fail[4],
                   "" if first_fail[0] == "COLLISIONTEST" else ", so the tests after it are not called"))
        put(cap, "Point (%d, %d): %s." % (x, y, "all four tests pass" if first_fail is None else "refused by " + NAMES[first_fail[0]]),
            ["%s: %s." % (NAMES[n], d.lower() if ran else "not called") for n, ran, ok, d, w in res])
    # ---- the summary
    k.text(14, 12, "THE SEVEN POINTS: THE FIRST TEST THAT FAILS", "acc", 2, True)
    for j, (x, y, note, res) in enumerate(results):
        yy = 56 + j * 44
        ff = next((r for r in res if r[1] and not r[2]), None)
        k.box(14, yy, 150, 36, [("(%d, %d)" % (x, y), "txt")], "panel", "dim", sc=2)
        k.box(174, yy, 520, 36, [("STANDS" if ff is None else "FAILS AT " + ff[0], "good" if ff is None else "bad")], "panel",
              "good" if ff is None else "bad", sc=2)
        for m, r in enumerate(res):
            k.box(704 + m * 56, yy, 50, 36, ["+" if (r[1] and r[2]) else ("-" if r[1] else ".")],
                  "qd_set" if (r[1] and r[2]) else ("panel" if not r[1] else "qd_rare"), "grey", "good" if (r[1] and r[2]) else "dim", 2)
    k.text(704, 36, "N  L  C  T", "dim", 2)
    k.text(14, 372, "N NEARWARPTEST  L LOGICREGIONIDAT  C SPAWNCLASSCELLTEST  T COLLISIONTEST", "dim", 1)
    k.text(14, 388, "+ PASSES   - FAILS   . NOT CALLED", "dim", 1)
    put("Of the seven points one stands; each other point is refused by the first test that fails, and the tests after it are not "
        "called, so their side effects do not happen (collision, predicate order).",
        "One point stands; the others fail at one test each.",
        ["collision, predicate order: a test that fails skips the later ones, so a reimplementation must not call them.",
         "; ".join("(%d, %d) %s" % (x, y, "stands" if all(r[2] for r in res) else "fails at " + NAMES[next(r for r in res if r[1] and not r[2])[0]])
                   for x, y, note, res in results)])
    return frames, caps, k.pal, results


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--base": "528", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES or not opts["--base"].lstrip("-").isdigit():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "collision-schematic")
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _r = build(int(opts["--base"]), opts["--theme"])
    K.write_illustration(out, "collision", frames, caps, W, H, K.palette(opts["--theme"])[1],
                         "spawn tests animation", HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Plan 0038 batch H5e (drlg-mazes): counters around tools/drlg.py gen on the run:2026-10-16-sweep-mazes logs, and the
offline seed scan that chose the map seeds.

Usage:
  python3 -I tools/sweep_h5e.py logs [LOG ...]            # default: workspace/logs/sweep-mazes/sweep-mazes-s*.log
  python3 -I tools/sweep_h5e.py scan FIRST LAST [DIFFS]    # map seeds FIRST..LAST-1, difficulties "0,1,2"
  python3 -I tools/sweep_h5e.py stampdefs BASE TYPE ...    # every Def a border stamp of these LvlSub types can place
Unit tests of the pure helpers: python3 -I tools/test_sweep_h5e.py.

`logs` runs the unchanged GenModel of tools/drlg.py (its own checks, 0 mismatches required) with counters added by
wrapping three of its methods; it prints one `H5E` line per counter group:
  maze     maze windows whose room list, level-seed draws and seed after matched, per level id, with the tomb role
           (act +0x094 true tomb, +0x484 Kaa) and level 64's special sequence (Tight Spot def 509, Treasure 505)
  outdoor  outdoor windows run by the model per branch: BridgeFind on a non-square level, the cliff-cave scan order
           (rows or columns outer) with the grid shape, the rare branches (ring merge, waypoint not placed, roads with
           5 or 6 endpoints, a failed search, an exhausted pool, the prisons' scan)
  preset   PresetRoomLoadDs1 lists that matched with the Blood Moor centre monster added, and the client river
           objects per Def
`scan` runs the outdoor model alone (drlg.Act, act_links, Outdoor) on every outdoor level of every act for each map
seed and difficulty and counts the same branches, plus the cliff-cave scan and, on the Act I levels, flags `0x10` and
`0x20` set or clear, keyed by level id and grid shape, the Act I road endpoints split by source (town and Monastery
Gate nodes, seam openings, caves, east bridge; H5e reachability (c)) and, per level, the windows of the waypoint pass and
the fewest free interior cells it met (no 0x1B81 bit; H5e reachability (b)), and the H5e (a) vertex-merge condition
per window (a Vis/Warp -1 seam overlapping the level edge by exactly 8 tiles, or the level's size or a neighbour's
origin relative to the level's or extent, along the seam's edge, off the 8 grid; per level met / not met, each reason, and the smallest overlap
per seam); it reads no log. In `logs`, a rebuild whose previous placement
differs from the act's rect for the level is counted apart, by level (`gen maze input: rebuild ... differs`).

`stampdefs` reads the LvlSub border records of each TYPE (drlg.load_outdoor, drlg.od_sub_ds1) and prints, per type,
the set of Defs `BorderSubStamp` (0x0066F520) can place with base BASE: `BASE + ((W >> 8) & 0xFF) - 1` for every wall
cell with bit 0 in every variant of every group (srcX = (w + 1)(v + 1), v < variants), the wildcard 62 excluded; it is a
superset of what a run can stamp (H5e reachability (c): which caves or bridges a stamp could add).

Exit 1 when gen reports a mismatch. Stdlib only. Read-only.
"""
import collections
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
LOGS = os.path.join(ROOT, "workspace", "logs", "sweep-mazes")

RARE = ("ring merge", "waypoint not placed", "A1 road endpoints 5", "A1 road endpoints 6", "A1 road path not found",
        "A1 road search pool exhausted", "A5 prison by scan")
A1_LEVELS = (2, 3, 4, 5, 6, 7, 17)    # the Act I outdoor levels whose O.flags carry 0x10 (middle river) and 0x20 (cliff)
LAIR64_DEFS = (509, 505)     # Tight Spot (0x006F00E8) and the fixed Treasure entry (0x006F00D8), drlg/0006 § 6


def scan_order(calls):
    """The cliff-cave scan's loop order from its first two probe cells (x, y): 'rows' when x moves first (rows outer,
    0x00680200 with r & 1 = 0), 'columns' when y moves first (columns outer, bounds swapped), None with one probe."""
    if len(calls) < 2:
        return None
    return "columns" if calls[1][0] == calls[0][0] else "rows"


def endpoint_sources(adj, defg, cell, cw, ch):
    """The road endpoints A1PathEndpoints (0x00680D70) would collect, by source: (town nodes, Monastery Gate nodes, seam
    openings (Def 4-7, file index 3), caves (Def 24, 25, 51, 52), east bridge (Def 28, index 1, x = cw - 2)). The
    model's own list (drlg.Outdoor.a1_paths) is the reference; this split only labels it."""
    town = sum(1 for n in adj if n["nbr"] == 1)
    mon = sum(1 for n in adj if n["nbr"] == 26)
    op = cv = br = 0
    for x in range(cw):
        for y in range(ch):
            d, idx = defg[y][x], (cell[y][x] >> 16) & 0xF
            if 4 <= d <= 7 and idx == 3:
                op += 1
            elif d in (24, 25, 51, 52):
                cv += 1
            elif d == 28 and idx == 1 and x == cw - 2:
                br += 1
    return town, mon, op, cv, br


def free_interior(cell, cw, ch):
    """Cells (x, y) with 1 <= x <= cw - 2, 1 <= y <= ch - 2 and no 0x1B81 bit: the cells OutWaypointPlace (0x00674B70)
    can take after its shuffle."""
    return sum(1 for y in range(1, ch - 1) for x in range(1, cw - 1) if not cell[y][x] & 0x1B81)


def tomb_role(lid, tombs):
    """'true' for act +0x094, 'kaa' for act +0x484, 'plain' for the other tombs 66-72, None outside them."""
    if not 66 <= lid <= 72:
        return None
    return "true" if lid == tombs[0] else "kaa" if lid == tombs[1] else "plain"


class Hooks:
    """Counters around drlg.Outdoor and drlg.GenModel; the wrapped methods run unchanged."""

    def __init__(self, drlg):
        self.d = drlg
        self.c = collections.Counter()
        self.probe = None
        self.lo = {}
        O, G = drlg.Outdoor, drlg.GenModel
        cave, east, paths, wayp = O.a1_cave_try, O.a1_river_east_cave, O.a1_paths, O.waypoint
        check = G.maze_check
        h = self

        def cave_try(o, x, y):
            if h.probe is not None:
                h.probe.append((x, y))
            return cave(o, x, y)

        def river_east(o):
            h.probe = []
            try:
                return east(o)
            finally:
                order = scan_order(h.probe)
                if order:
                    h.c["outdoor cliff-cave scan, %s outer, level %d, %s (%dx%d)"
                        % (order, o.lid, "square" if o.cw == o.ch else "non-square", o.cw, o.ch)] += 1
                h.probe = None

        def a1_paths(o):
            if o.flags & 0x10:
                h.c["outdoor BridgeFind (flag 0x10), level %d, %s (%dx%d)"
                    % (o.lid, "square" if o.cw == o.ch else "non-square", o.cw, o.ch)] += 1
            t, m, op, cv, br = endpoint_sources(o.adj, o.defg, o.cell, o.cw, o.ch)
            h.c["A1 road endpoint sources: level %d, town %d, monastery %d, openings %d, caves %d, bridge %d (total %d)"
                % (o.lid, t, m, op, cv, br, t + m + op + cv + br)] += 1
            return paths(o)

        def waypoint(o):
            n = free_interior(o.cell, o.cw, o.ch)
            k = "waypoint pass free interior cells: level %d, %s (%dx%d)" % (
                o.lid, "square" if o.cw == o.ch else "non-square", o.cw, o.ch)
            h.c[k + " windows"] += 1
            h.lo[k] = min(h.lo.get(k, n), n)
            return wayp(o)

        def maze_check(g, path, L, d):
            f0 = g.fail
            r = check(g, path, L, d)
            M = getattr(L, "mz_model", None)
            ok = g.fail == f0 and M is not None
            tag = "maze windows matched" if ok else "maze windows with a mismatch"
            h.c["%s: level %d (difficulty %s)" % (tag, L.id, getattr(L, "mz_diff", "?"))] += 1
            if M is not None:
                role = tomb_role(L.id, M.L.tombs)
                if role:
                    n = len(M.L.rooms)
                    h.c["maze tomb %s: level %d, %d rooms, LvlMaze Rooms x%d" % (
                        role, L.id, n, {"true": 3, "kaa": 2}.get(role, 1))] += 1
                if L.id == 64:
                    defs = [R.d for R in M.L.rooms]
                    h.c["maze level 64: Tight Spot 509 %s, Treasure 505 %s" % (
                        509 in defs, 505 in defs)] += 1
            return r

        O.a1_cave_try, O.a1_river_east_cave, O.a1_paths, O.waypoint = cave_try, river_east, a1_paths, waypoint
        G.maze_check = maze_check


def seam_overlaps(rect, adj):
    """Per adjacency node (Vis with Warp -1, the ring's seams): (neighbour, side, overlap in tiles) along the level edge
    on that side, inclusive bounds as in the ring build (side 0 left and 2 right: y; 1 top and 3 bottom: x)."""
    out = []
    for n in adj:
        r, side = n["rect"], n["side"]
        if side in (0, 2):
            lo, hi = max(rect[1], r[1]), min(rect[1] + rect[3], r[1] + r[3]) - 1
        else:
            lo, hi = max(rect[0], r[0]), min(rect[0] + rect[2], r[0] + r[2]) - 1
        out.append((n["nbr"], side, hi - lo + 1))
    return out


def vertex_merge_condition(rect, adj):
    """H5e (a) scan condition (drlg/0008 H5e reachability (a)): the reasons a window could meet a vertex merge in
    OutVertsToCells: a seam whose overlap with the level edge is exactly 8 tiles, or a rect value off the 8 grid. The
    ring is moved to the level's origin before the division by 8 (0x00675080), so the grid test is on the level's
    width and height and, per seam, on the neighbour's origin relative to the level's and its extent along that edge
    (y and height on sides 0 and 2, x and width on 1 and 3; absolute origins such as Act I's y 1114 are off the grid
    and do not matter, nor is the other axis read by the ring). An empty list means the ring cannot merge."""
    why = []
    for nb, side, ov in seam_overlaps(rect, adj):
        if ov == 8:
            why.append("seam overlap 8 (neighbour %d, side %d)" % (nb, side))
    if rect[2] % 8 or rect[3] % 8:
        why.append("level size off the 8 grid")
    for n in adj:
        r = n["rect"]
        k = 1 if n["side"] in (0, 2) else 0      # the coordinate along the edge: y on the left and right, else x
        if (r[k] - rect[k]) % 8 or r[k + 2] % 8:
            why.append("neighbour %d off the level's 8 grid along side %d" % (n["nbr"], n["side"]))
    return why


def cmd_logs(paths):
    import drlg
    H = Hooks(drlg)
    paths = paths or sorted(glob.glob(os.path.join(LOGS, "sweep-mazes-s*.log")))
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    m = drlg.GenModel(data, False, False, drlg.PresetUnitData(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE))
    for p in paths:
        m.run(p)
        print("log %s" % os.path.relpath(p, ROOT))
    for k in sorted(H.c):
        print("H5E %s  %d" % (k, H.c[k]))
    for k in sorted(m.cov):
        if any(s in k for s in ("centre monster", "client river objects", "outdoor branch", "rebuild")):
            print("H5E gen %s  %d" % (k, m.cov[k]))
    print("H5E gen: %d checks, %d mismatches over %d logs" % (m.checks, m.fail, len(paths)))
    return 1 if m.fail else 0


def cmd_scan(argv):
    import drlg
    H = Hooks(drlg)
    a, b = int(argv[0]), int(argv[1])
    diffs = [int(x) for x in argv[2].split(",")] if len(argv) > 2 else [0, 1, 2]
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    drlg.load_outdoor(data.root, data.exe)
    out = [i for i in range(len(data.drlgtype)) if data.drlgtype[i] == 3 and i not in (39, 134)]
    windows, seeds_hit, errors = 0, collections.defaultdict(list), 0
    for s in range(a, b):
        for diff in diffs:
            for acti in range(5):
                A = drlg.Act(acti, s, diff)
                try:
                    drlg.act_links(A)
                except NotImplementedError:
                    continue
                for lid in out:
                    if drlg.LV[lid]["act"] != acti or lid not in A.rect:
                        continue
                    O = drlg.Outdoor(A, lid, drlg.Seed(A.base + lid))
                    why = vertex_merge_condition(O.rect, O.adj)
                    H.c["vertex-merge condition %s: level %d" % ("met" if why else "not met", lid)] += 1
                    for w in why:
                        H.c["vertex-merge condition reason: level %d, %s" % (lid, w)] += 1
                    for nb, side, ov in seam_overlaps(O.rect, O.adj):
                        H.lo["seam overlap (tiles), level %d side %d neighbour %d" % (lid, side, nb)] = min(
                            ov, H.lo.get("seam overlap (tiles), level %d side %d neighbour %d" % (lid, side, nb), ov))
                    if why and len(seeds_hit["vertex-merge condition"]) < 5:
                        seeds_hit["vertex-merge condition"].append((s, diff, lid))
                    try:
                        O.run()
                    except Exception as e:      # a model fatal or an unmodelled branch: counted, never hidden
                        errors += 1
                        print("H5E scan error: seed %d difficulty %d level %d: %r" % (s, diff, lid, e))
                        continue
                    windows += 1
                    shape = "%s (%dx%d)" % ("square" if O.cw == O.ch else "non-square", O.cw, O.ch)
                    for bit in (0x10, 0x20):          # H5e review follow-up (b): the flags by level and grid shape
                        if lid in A1_LEVELS:
                            H.c["outdoor flag 0x%02x %s: level %d, %s" % (bit, "set" if O.flags & bit else "clear", lid, shape)] += 1
                    for k in RARE:
                        if O.cov.get(k):
                            H.c["scan %s" % k] += 1
                            if len(seeds_hit[k]) < 5:
                                seeds_hit[k].append((s, diff, lid))
    print("H5E scan: map seeds %d..%d, difficulties %s, outdoor windows %d, model errors %d" % (a, b - 1, diffs, windows, errors))
    for k in RARE:
        print("H5E scan %s  %d  first %s" % (k, H.c["scan %s" % k], seeds_hit.get(k, [])))
    met = sum(v for k, v in H.c.items() if k.startswith("vertex-merge condition met"))
    print("H5E scan vertex-merge condition met  %d  first %s" % (met, seeds_hit.get("vertex-merge condition", [])))
    for k in sorted(H.c):
        if not k.startswith("scan "):
            print("H5E %s  %d" % (k, H.c[k]))
    for k in sorted(H.lo):
        print("H5E %s minimum  %d" % (k, H.lo[k]))
    return 1 if errors else 0


def cmd_stampdefs(argv):
    import drlg
    base, types = int(argv[0]), [int(x) for x in argv[1:]]
    data = drlg.Data(drlg.DEFAULT_DATA, drlg.DEFAULT_EXE)
    drlg.load_outdoor(data.root, data.exe)
    for t in types:
        defs, recs, cells = set(), 0, 0
        for i, rec in enumerate(drlg.LVLSUB):
            if rec["type"] != t:
                continue
            recs += 1
            S = drlg.od_sub_ds1(i)
            cols = S["cols"]
            for g in S["groups"]:
                for v in range(g[4]):
                    srcx = (g[2] + 1) * (v + 1)
                    for gy in range(g[3]):
                        for gx in range(g[2]):
                            si = (g[1] + gy) * cols + g[0] + gx + srcx
                            W = S["wall"][si] if S["wall"] and si < len(S["wall"]) else 0
                            if W & 1:
                                cells += 1
                                o = ((W >> 8) & 0xFF) - 1
                                if o != 62:
                                    defs.add(base + o)
        print("H5E stampdefs type %d base %d: records %d, wall cells %d, Defs %s" % (t, base, recs, cells, sorted(defs)))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "logs":
        return cmd_logs(argv[2:])
    if len(argv) >= 4 and argv[1] == "stampdefs":
        return cmd_stampdefs(argv[2:])
    if len(argv) >= 4 and argv[1] == "scan":
        return cmd_scan(argv[2:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

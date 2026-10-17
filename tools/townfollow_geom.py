"""Offline geometry check for the town-follow case, recipe (b) (plan 0038 batch H7a; drlg/0009 § 11.2 (b)).

Usage:
  python3 -I tools/townfollow_geom.py scan <log> [<log> ...] [--mask 0x3C01] [--window 100] [--show]
  python3 -I tools/townfollow_geom.py scan --list FILE ...

Question. § 11.2 (b) reads that a hostile monster's planned walk may cross a town room when the target room is not
in town: the planner tests only the target room (sub_006483A0), and the walk's room update (PathRoomUpdate
0x0064FAD0) has no town test. A harness case needs a monster standing outside a town and a target point outside it
whose route goes through a town room. This tool looks for such routes on the collision grids the logs hold.

Input. The CB lines of tools/gdb/pilot.py (COLL_MapBuild 0x0064C9FF: a room's sub-tile rect, its level id and its
cells at activation). Every log that holds CB lines of a town (level 1, 40, 75, 103, 109) is read; the cells of a
game are the union of its CB grids (a second GP line starts a new game).

Method. A cell is free under the move mask when `cell & mask` = 0 (default 0x3C01, the ground monster move mask of
PATH_MonTestMask 0x00648480; drlg/0005). A town free cell 8-adjacent to a free cell of another level is an
"opening" cell; the openings are grouped into 8-connected runs, each with the 8-connected component of town free
cells it belongs to (index, size). Any route between two cells outside the town that
passes through town cells leaves the outside at a cell a next to an opening and comes back at a cell b next to an
opening (the "doors"). So a shortest route through the town exists only if, for some doors a and b within the
window, the shortest distance allowing town cells is below (or equal to: "ties") the shortest distance over outside
cells only. Both distances are taken with two metrics: 4-connected unit steps, and 8-connected octile steps (10 and
14, corner cutting allowed: the most permissive), each restricted to the WINDOW square around a (the planner's
100-sub-tile window, § 11.2 (a)). Cells no CB line covers count as blocked; doors next to unknown cells are counted.

Output per game: the town and its neighbour levels, the opening runs (cells, extent), the doors, and the pair counts
(strictly shorter via town, ties, none). Deterministic; reads logs only. Stdlib only.
"""
import hashlib
import heapq
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import collision  # noqa: E402

TOWNS = (1, 40, 75, 103, 109)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def games(path):
    """Yield (game index, {cell: (value, lid)}) for every game of the log that has a town CB line."""
    cells, has_town, g = {}, False, 0
    with open(path, errors="replace") as f:
        for line in f:
            if line.startswith("GP "):
                if has_town:
                    yield g, cells
                cells, has_town = {}, False
                g += 1
            elif line.startswith("CB "):
                try:
                    d = json.loads(line[3:])
                except ValueError:
                    continue
                c = collision.unz(d["z"]).get("cells")
                if not c or not c[4]:
                    continue
                x0, y0, w, h = d["rect"]
                lid = d["lid"]
                if lid in TOWNS:
                    has_town = True
                vals = collision.u16cells(c[4])
                for j in range(h):
                    for i in range(w):
                        cells[(x0 + i, y0 + j)] = (vals[j * w + i], lid)
    if has_town:
        yield g, cells


def runs(cells_set):
    """8-connected components of a set of cells."""
    left, out = set(cells_set), []
    while left:
        s = left.pop()
        comp, st = [s], [s]
        while st:
            x, y = st.pop()
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n in left:
                    left.remove(n)
                    comp.append(n)
                    st.append(n)
        out.append(comp)
    return out


def dist(src, ok, window, eight):
    """Shortest distances from src over cells where ok(cell), within the window square around src."""
    sx, sy = src
    D = {src: 0}
    pq = [(0, src)]
    nb = N8 if eight else N4
    while pq:
        d, c = heapq.heappop(pq)
        if D.get(c, 1 << 60) < d:
            continue
        x, y = c
        for dx, dy in nb:
            n = (x + dx, y + dy)
            if abs(n[0] - sx) > window or abs(n[1] - sy) > window or not ok(n):
                continue
            nd = d + ((14 if dx and dy else 10) if eight else 1)
            if nd < D.get(n, 1 << 60):
                D[n] = nd
                heapq.heappush(pq, (nd, n))
    return D


def scan_game(cells, mask, window):
    free = {c for c, (v, _) in cells.items() if not v & mask}
    town_lids = sorted({l for _, l in cells.values() if l in TOWNS})
    res = []
    for tl in town_lids:
        tfree = {c for c in free if cells[c][1] == tl}
        tall = [c for c, (_, l) in cells.items() if l == tl]
        xs, ys = [c[0] for c in tall], [c[1] for c in tall]
        openings, doors, unknown_edge, nlids = set(), set(), set(), set()
        for (x, y) in tfree:
            for dx, dy in N8:
                n = (x + dx, y + dy)
                if n not in cells:
                    unknown_edge.add((x, y))
                elif cells[n][1] != tl and n in free:
                    openings.add((x, y))
                    doors.add(n)
                    nlids.add(cells[n][1])
        r = {"town": tl, "rect": [min(xs), min(ys), max(xs) + 1, max(ys) + 1], "town_free": len(tfree),
             "neighbours": sorted(nlids), "openings": [], "doors": len(doors),
             "town_free_next_to_unknown": len(unknown_edge)}
        tcomp = {}
        for k, comp in enumerate(runs(tfree)):
            for c in comp:
                tcomp[c] = (k, len(comp))
        for comp in sorted(runs(openings)):
            cx, cy = [c[0] for c in comp], [c[1] for c in comp]
            r["openings"].append({"cells": len(comp), "x": [min(cx), max(cx)], "y": [min(cy), max(cy)],
                                  "town component": sorted({tcomp[c] for c in comp})})
        doors_l = sorted(doors)
        for eight in (False, True):
            key = "8" if eight else "4"
            shorter = ties = pairs = 0
            best = None

            def ok_all(c):
                return c in free

            def ok_out(c):
                return c in free and cells[c][1] != tl

            D_all = {a: dist(a, ok_all, window, eight) for a in doors_l}
            for a in doors_l:
                da = D_all[a]
                do = dist(a, ok_out, window, eight)
                for b in doors_l:
                    if b <= a or abs(b[0] - a[0]) > window or abs(b[1] - a[1]) > window:
                        continue
                    if b not in da:
                        continue
                    pairs += 1
                    vo = do.get(b)
                    if vo is None or da[b] < vo:
                        shorter += 1
                        gain = None if vo is None else vo - da[b]
                        if best is None or (gain is None) or (best[0] is not None and gain > best[0]):
                            best = (gain, a, b, da[b], vo)
                    else:
                        # equal length: a shortest route (allowing town cells) that goes through a town cell
                        db = D_all[b]
                        if any(t in da and t in db and da[t] + db[t] == da[b] for t in tfree):
                            ties += 1
            r["pairs_" + key] = {"door pairs": pairs, "via town strictly shorter": shorter,
                                 "equal length through town": ties, "best": best and {"gain": best[0], "a": best[1], "b": best[2],
                                                                         "via town": best[3], "outside only": best[4]}}
        res.append(r)
    return res


def main(argv):
    if not argv or argv[0] != "scan":
        print(__doc__)
        return 2
    mask, window, show, logs = 0x3C01, 100, False, []
    a = argv[1:]
    k = 0
    while k < len(a):
        if a[k] == "--mask":
            mask = int(a[k + 1], 0)
            k += 2
        elif a[k] == "--window":
            window = int(a[k + 1])
            k += 2
        elif a[k] == "--list":
            logs += [ln.strip() for ln in open(a[k + 1]) if ln.strip()]
            k += 2
        elif a[k] == "--show":
            show = True
            k += 1
        else:
            logs.append(a[k])
            k += 1
    seen = {}
    total = {"games": 0, "layouts": 0, "shorter": 0}
    for path in logs:
        for g, cells in games(path):
            total["games"] += 1
            h = hashlib.sha256(json.dumps(sorted((c[0], c[1], v, l) for c, (v, l) in cells.items()
                                                 if l in TOWNS)).encode())
            # layouts: key on the town cells and the cells of the other levels within 3 cells of a town cell
            tcells = {c for c, (_, l) in cells.items() if l in TOWNS}
            near = sorted((c[0], c[1], cells[c][0], cells[c][1]) for c in cells if cells[c][1] not in TOWNS and
                          any((c[0] + dx, c[1] + dy) in tcells for dx in (-3, 0, 3) for dy in (-3, 0, 3)))
            h.update(json.dumps(near).encode())
            key = h.hexdigest()[:16]
            if key in seen:
                seen[key][1].append("%s#%d" % (os.path.relpath(path), g))
                continue
            res = scan_game(cells, mask, window)
            seen[key] = (res, ["%s#%d" % (os.path.relpath(path), g)])
            total["layouts"] += 1
            for r in res:
                if r["pairs_4"]["via town strictly shorter"] or r["pairs_8"]["via town strictly shorter"]:
                    total["shorter"] += 1
            print(json.dumps({"layout": key, "first": seen[key][1][0], "towns": res}), flush=True)
    print("SUMMARY " + json.dumps(dict(total, mask=hex(mask), window=window)))
    if show:
        for key, (res, where) in seen.items():
            print("%s %d games: %s" % (key, len(where), " ".join(where)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Plan 0064 (backlog drlg-outdoor-statements (a)): A1CliffMark (0x00680070) as read from the code, checked against the
logged outdoor windows, with a counter per branch.

Replaces tools/drlg.py's Outdoor.a1_cliff_mark with a transcription written from the disassembly (labels are the
instruction addresses), runs `drlg.py gen` over the given logs (the ODG check compares O.flags exactly, and the def and
cell grids that the vertex types feed), and prints which branches the logs took.

With --count-one-or-two it also counts the branches of A1PlaceOneOrTwo (0x006804E0) for its `s` = 1 calls (levels 3-7):
from the defs the model's act1 hands Outdoor.place_near, a call whose def is placed twice in a row took the `r & 3 == 0`
branch, else the else branch (and `Near(49)` after it when the `s` step's bit 0 is 1). The model is not changed.

With --control-no-vis-test it also swaps drlg.border_adj for a copy without LevelBorderAdj's `Vis != 0` test
(backlog item (d)), as a control: the kept run with it must score mismatches for the logs to separate the readings.

Usage: python3 -I tools/cliff_cover.py [--control-no-vis-test] [--count-one-or-two] <log>...
Evidence: docs/findings/drlg/0008-outdoor.md § Plan 0064 statements (a), (c) and (d).
"""
import collections, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drlg            # noqa: E402

CNT = collections.Counter()


def cliff_mark(O):
    head = O.ring                       # 0x0068007C: [O + 0x64]
    p = head                            # 0x00680092: walk to the vertex whose next is the head
    while p.next is not head:
        p = p.next
    v, done = head, False
    CNT["walks"] += 1
    while True:                         # 0x006800A3
        CNT["start tests"] += 1
        n0 = v.next
        a = v.x < n0.x and p.y > v.y and not v.flags & 1 and not p.flags & 1      # 0x006800A3..0x006800BC
        b = v.y > n0.y and p.x > v.x and not v.flags & 1 and not p.flags & 1      # 0x006800BE..0x006800DE
        w = v
        if a or b:
            CNT["run start: up then right (A)" if a else "run start: left then up (B)"] += 1
            if v is head:
                CNT["run starts at the ring head"] += 1
            last = None                 # 0x006800E4: [ebp-4] = 0, [ebp-8] = v
            while True:                 # 0x006800F0
                if w is head:
                    done = True         # 0x006800F5
                    CNT["run reaches the ring head (done)"] += 1
                n = w.next
                if w.y < n.y:
                    CNT["run ends: segment goes down"] += 1; break        # 0x00680101
                if w.x > n.x:
                    CNT["run ends: segment goes left"] += 1; break        # 0x00680107
                if w.flags & 1:
                    CNT["run ends: w seam"] += 1; break                   # 0x0068010C
                if n.flags & 1:
                    CNT["run ends: n seam"] += 1; break                   # 0x00680111
                nn = n.next
                if w.x < n.x and n.y < nn.y and not n.flags & 1:          # 0x00680115..0x0068012C (C)
                    last = w; CNT["last set: right then down (C)"] += 1
                elif n.y < w.y and n.x < nn.x and not n.flags & 1:        # 0x0068012E..0x0068013F (D)
                    last = w; CNT["last set: up then right (D)"] += 1
                w = n                   # 0x00680147
                if w is v:
                    CNT["run ends: back at its start"] += 1; break        # 0x0068014C
            if last is not None:        # 0x0068014E
                q = v
                while q is not last:
                    q.type = 1; q = q.next; CNT["vertices typed 1"] += 1  # 0x00680160
                q.type = 1; CNT["vertices typed 1"] += 1                  # 0x0068016A
                O.flags |= 0x20         # 0x00680170
                CNT["runs marked"] += 1
                O.hit("A1 cliff run", 1)
            else:
                CNT["runs with no corner (nothing marked)"] += 1
        v = w.next                      # 0x00680179
        if done:
            CNT["walk ends: done"] += 1; return                          # 0x0068017C
        p = w
        if v is O.ring:
            CNT["walk ends: back at the head"] += 1; return               # 0x00680189


drlg.Outdoor.a1_cliff_mark = cliff_mark


def border_adj_no_vis_test(A, lo, hi):
    """Control for LevelBorderAdj's `Vis != 0` test (0x006776D6): drlg.border_adj with that test removed, so an empty
    slot (Vis 0, Warp -1) also makes a node. The logs separate the readings if this scores mismatches."""
    for lv in range(lo, hi + 1):
        if lv not in drlg.LV or drlg.LV[lv]["drlg"] != 3:
            continue
        vis, warp = A.vis(lv), A.warp(lv)
        lst = A.adj.setdefault(lv, [])
        for k in range(8):
            if warp[k] == -1:
                nb = vis[k]
                CNT["control: nodes made"] += 1
                if not nb:
                    CNT["control: nodes for an empty slot"] += 1
                side = drlg.rect_adj_dir(A.rect.get(lv, [0, 0, 0, 0]), A.rect.get(nb, [0, 0, 0, 0]))
                drlg.adj_insert(lst, dict(nbr=nb, side=side, preset=drlg.LV[nb]["drlg"] == 2,
                                          rect=list(A.rect.get(nb, [0, 0, 0, 0]))))


ONE_OR_TWO_S1 = {3: 48, 4: 47, 5: 48, 6: 47, 7: 48}   # the def of each level's one_or_two(d, 1) call (drlg/0008 § 8)


def count_one_or_two():
    act1, place_near = drlg.Outdoor.act1, drlg.Outdoor.place_near

    def place_near_rec(O, d, idx=-1):
        seq = getattr(O, "_n64r_near", None)
        if seq is not None:
            seq.append(d)
        return place_near(O, d, idx)

    def act1_rec(O):
        O._n64r_near = [] if O.lid in ONE_OR_TWO_S1 else None
        rc = act1(O)
        seq, O._n64r_near = O._n64r_near, None
        if seq is not None:
            d = ONE_OR_TWO_S1[O.lid]
            i = seq.index(d)
            CNT["one_or_two s=1: calls"] += 1
            if seq[i + 1:i + 2] == [d]:
                CNT["one_or_two s=1: r & 3 == 0 (Near(d) twice)"] += 1
            else:
                CNT["one_or_two s=1: else branch (Near(d) once)"] += 1
                if seq[i + 1:i + 2] == [49]:
                    CNT["one_or_two s=1: else branch, Near(49)"] += 1
        return rc

    drlg.Outdoor.place_near, drlg.Outdoor.act1 = place_near_rec, act1_rec


def main(argv):
    if "--count-one-or-two" in argv:
        argv = [a for a in argv if a != "--count-one-or-two"]
        count_one_or_two()
    if "--control-no-vis-test" in argv:
        argv = [a for a in argv if a != "--control-no-vis-test"]
        drlg.border_adj = border_adj_no_vis_test
    rc = drlg.cmd_gen(argv[1:])
    for k in sorted(CNT):
        print("  cliff %-48s %d" % (k, CNT[k]))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

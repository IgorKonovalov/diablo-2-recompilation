"""The two position rules of monster placement that both the log checker (tools/monspawn.py, tools/collision.py) and the
pack animation (tools/pack_anim.py) call, so that the picture and the model cannot differ (spawn.md H1, H2): the ring
walk of MonSpawnTry and NearWarpTest's distance test, and the mutable room seed they draw on. Pure functions; stdlib
only, no game files.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from rng import step  # noqa: E402

MASK_BY_SPAWNCOL = {0: 0x3C01, 1: 0x01C0, 2: 0x3F11, 3: 0}     # jump table 0x005B2F04


class S:
    """A mutable seed."""
    def __init__(self, t):
        self.lo, self.hi = t

    def t(self):
        return self.lo, self.hi

    def step(self):
        self.lo, self.hi = step(self.lo, self.hi)
        return self.lo

    def rangeb(self, n):                       # RNG_Range / RNG_RangeB, and the inlined copies
        if n & 0x80000000 or n == 0:
            return 0
        return self.step() % n


def ring_search(rs, cx, cy, rad, accept):
    """The ring walk of MonSpawnTry (spawn.md H2), as a pure function of the room seed `rs` (an object with step() and
    rangeb(n)): rings s = 3, 6 .. 3 * rad (s = 0 for a negative radius) around (cx, cy), each with its three room draws
    and a walk of max(8 * s, 1) cells that moves before it tests. `accept(x, y)` is the caller's cell tests, called for
    every cell the walk reaches (it skips the ones outside the rectangle itself) and returning true to take the cell.
    Returns the taken (x, y), or None. tools/pack_anim.py calls the same function."""
    s, smax = (0, 0) if rad < 0 else (3, 3 * rad)
    while s <= smax:
        if rs.step() & 1:
            dx, dy, dirx, diry = s, rs.rangeb(s), 0, 1
        else:
            dx, dy, dirx, diry = rs.rangeb(s), s, 1, 0
        if rs.step() & 1:
            dx = -dx
        if rs.step() & 1:
            dy = -dy
        x, y = cx + dx, cy + dy
        l, r = cx - s, cx + s
        tp, bt = cy - s, cy + s
        cnt = 8 * s if 8 * s else 1
        while cnt > 0:
            if x == l and y == tp:
                dirx, diry = 1, 0
            if x == r:
                if y == tp:
                    dirx, diry = 0, 1
                if y == bt:
                    dirx, diry = -1, 0
            if x == l:
                if y == bt:
                    dirx, diry = 0, -1
                if y == tp and x == r and y == bt:
                    dirx, diry = 0, 0
            y += diry
            x += dirx
            cnt -= 1
            if accept(x, y):
                return x, y
        s += 3
    return None


def near_point(xs, ys, wd, x, y):
    """NearWarpTest's distance rule (spawn.md H1 note): true when (x, y) is within the squared distance `wd` (Levels
    WarpDist) of one of the points (xs[i], ys[i]), in subtiles. tools/pack_anim.py calls the same function."""
    return any((x - px) * (x - px) + (y - py) * (y - py) < wd for px, py in zip(xs, ys))

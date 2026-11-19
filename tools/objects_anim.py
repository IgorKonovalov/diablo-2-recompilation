"""Animate one room's object population on a toy level and room: the eight slots, the member pick and the spot search
(docs/specs/objects/README.md D1, E (handler 3), F1, F6; wiki objects, The eight slots and the member pick, Finding a
spot). Schematic only (ADR-0036): boxes and text in our own palette.

Usage:
  python3 -I tools/objects_anim.py <root> [--seed N] [--oseed N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. --seed: the room seed S is {seed, 666} (default 0xC0FFEE); --oseed: the object-region seed O is {oseed, 666}
(default 12345); both are illustrative inputs. --theme: the palette's dark or light values (default dark). --schematic
is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/objects-<seed hex>-<oseed hex>-schematic/ and must stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; objects.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

The toy: a level with three used slots, three object groups of two or three members, every member of PopulateFn 3 (the
scatter handler), and one 48 by 40 subtile room with a toy wall and pillar; every number is an illustrative input (no
table is read). Shown: the eight slot rolls on the room seed, each member pick (the PROB walk), the handler's count, and
each placer call's attempts on the object-region seed (two draws, the margin, the box test), with the spots accepted
marking the grid for the later ones. Not shown: the gate and the theme roll, the unit creation (the game-seed step of G),
the handlers other than 3, and the real grid (a toy wall and pillar stand in for it; cells outside the room read as free).

Model (ADR-0014 boundary): tools/objects.py is a checker of event logs with no function that runs a room forward; the
rules of the sections above are written out here with a trace, using the model's generator step (objects.step), and the
tests (tools/test_objects_anim.py) feed the toy's room-seed draws to the model's own slot-loop solver (objects.solve)
and recompute every placer call on its own, so any difference of a number or a seed fails. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import objects  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
HIGH = 666
RECT = (5080, 5600, 48, 40)                     # the toy room: x, y, width, height in subtiles
ROOMS = (9, 71)                                 # the toy level's roomsVisited and roomCount (the forced-slot test)
# the toy level: slot k -> (group, ObjPrb); the groups: ID, PROB, DENSITY per member (illustrative)
SLOTS = [(38, 70), (33, 70), (34, 90), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
GROUPS = {38: [(174, 34, 30), (175, 33, 40), (176, 33, 30)],
          33: [(177, 50, 40), (178, 40, 30)],
          34: [(179, 20, 30), (180, 30, 40)]}
SIZES = {174: (1, 1), 175: (2, 2), 176: (2, 2), 177: (3, 2), 178: (1, 1), 179: (2, 2), 180: (3, 3)}
# the toy collision grid: a wall and a pillar, as (x0, y0, x1, y1) in subtiles from the room's corner, inclusive
WALLS = [(20, 0, 23, 25), (8, 24, 15, 31)]
STEPS = ("SLOTS", "PICK", "COUNT", "SPOT")
SC = 8                                          # pixels per subtile on the room map
MX, MY = 556, 98                                # the room map's top left
HELP = """<li>The room seed S makes two draws for a passing slot and one for the rest: the slot roll, then the member pick. The object-region seed O makes every draw of the placement.</li>
<li>A slot passes when its roll is at most its chance; the pick adds the members' PROB values up and takes the first member whose running sum is above the second roll.</li>
<li>The handler turns the member's DENSITY into a count from the room's size and tries to place that many objects.</li>
<li>Each placement makes up to five attempts of two draws; an attempt is kept only inside the margin and with no marked cell in the box around it. There is no fallback.</li>
<li>Every number is an illustrative input or computed from one, not observed in the game.</li>"""


def rr(seed, n):
    """Range(seed, n) -> (value, seed after); n < 1: no draw."""
    if n < 1:
        return 0, seed
    seed = objects.step(seed)
    return seed[0] % n, seed


def whtest(blocked, x, y, w, h):
    """COLL_WHTest on the toy grid (F6): one cell when w and h are at most 1, else the inclusive rectangle."""
    if w <= 1 and h <= 1:
        return 1 if (x, y) in blocked else 0
    l, t = x - (w >> 1), y - (h >> 1)
    return 1 if any((cx, cy) in blocked for cx in range(l, l + w) for cy in range(t, t + h)) else 0


def run(seed, oseed):
    """The toy room's population: a trace of the slot rolls, the picks and the placements."""
    rx, ry, rw, rh = RECT
    S, O = (seed, HIGH), (oseed, HIGH)
    blocked = set()
    for x0, y0, x1, y1 in WALLS:
        for cx in range(rx + x0, rx + x1 + 1):
            for cy in range(ry + y0, ry + y1 + 1):
                blocked.add((cx, cy))
    walls = set(blocked)
    forced = ROOMS[1] > 0 and (ROOMS[0] << 7) // ROOMS[1] > 96
    tr = dict(S0=S, O0=O, walls=walls, slots=[], places=[], forced=forced, o_draws=0, s_draws=0)
    for k, (g, prb) in enumerate(SLOTS):
        S = objects.step(S)
        r = S[0] % 100
        tr["s_draws"] += 1
        sl = dict(k=k, g=g, prb=prb, r=r, rn=tr["s_draws"], passes=(g != 0 and r <= prb), pick=None)
        if sl["passes"]:
            S = objects.step(S)
            r2 = S[0] % 100
            tr["s_draws"] += 1
            sl["r2"], sl["r2n"] = r2, tr["s_draws"]
            total, pick = 0, None
            walk = []
            for i, (cls, prob, dens) in enumerate(GROUPS[g]):
                total += prob
                walk.append((cls, prob, dens, total))
                if pick is None and r2 < total:
                    pick = i
            sl["walk"], sl["pick"], sl["sum"] = walk, pick, total
            if pick is not None:
                cls, prob, dens, _t = walk[pick]
                sx, sy = SIZES[cls]
                cnt = (((rw * rh) >> 7) * dens) >> 8
                O = objects.step(O)
                p100 = O[0] % 100
                tr["o_draws"] += 1
                sl.update(cls=cls, dens=dens, cnt=cnt, p100=p100, p100n=tr["o_draws"], sx=sx, sy=sy)
                for j in range(cnt):
                    call = dict(slot=k, j=j + 1, cls=cls, sx=sx, sy=sy, attempts=[], spot=None)
                    for a in range(5):
                        vx, O = rr(O, rw - sx - 1)
                        vy, O = rr(O, rh - sy - 1)
                        tr["o_draws"] += 2
                        x, y = rx + vx, ry + vy
                        inside = x != 0 and y != 0 and rx + 1 <= x < rx + rw - 1 and ry + 1 <= y < ry + rh - 1
                        res = whtest(blocked, x, y, sx + 6, sy + 6) if inside else None
                        call["attempts"].append(dict(a=a + 1, vx=vx, vy=vy, x=x, y=y, inside=inside, res=res,
                                                     n=tr["o_draws"]))
                        if inside and res == 0:
                            call["spot"] = (x, y)
                            break
                    call["marks"] = set(blocked)                     # the grid the call tested against
                    if call["spot"]:
                        x, y = call["spot"]
                        if sx == 1 and sy == 1:
                            blocked.add((x, y))
                        else:
                            l, t = x - (sx >> 1), y - (sy >> 1)
                            for cx in range(l, l + sx):
                                for cy in range(t, t + sy):
                                    blocked.add((cx, cy))
                    tr["places"].append(call)
        tr["slots"].append(sl)
    tr["S"], tr["O"] = S, O
    tr["blocked"] = blocked
    return tr


def sd(t):
    return "%08X:%08X" % t


def build(seed, oseed, theme):
    tr = run(seed, oseed)
    rx, ry, rw, rh = RECT
    k = K.Kit(W, H, theme)
    frames, caps = [], []

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def stepper(cur):
        for i, n in enumerate(STEPS):
            k.box(20 + i * 232, 40, 222, 30, [n], "cur" if i == cur else "panel", "acc" if i == cur else "dim",
                  "txt" if i <= cur else "dim", 2, bold=(i == cur))

    def room(marks, walls, call=None, upto=0):
        """The room map: the toy wall, the marks of earlier objects, and (for a placer call) the attempts up to `upto`."""
        k.rect(MX - 6, MY - 6, rw * SC + 12, rh * SC + 12, "panel")
        k.outline(MX - 6, MY - 6, rw * SC + 12, rh * SC + 12, "dim")
        k.rect(MX, MY, rw * SC, rh * SC, "bg")
        for (cx, cy) in marks:
            px, py = MX + (cx - rx) * SC, MY + (cy - ry) * SC
            if 0 <= cx - rx < rw and 0 <= cy - ry < rh:
                k.rect(px, py, SC, SC, "grey" if (cx, cy) in walls else "blue")
        k.outline(MX + SC, MY + SC, (rw - 2) * SC, (rh - 2) * SC, "dim")          # the one-subtile margin
        if call:
            for at in call["attempts"][:upto]:
                bw, bh = call["sx"] + 6, call["sy"] + 6
                l, t = at["x"] - (bw >> 1), at["y"] - (bh >> 1)
                cur = at is call["attempts"][upto - 1]
                col = "bad" if (not at["inside"] or at["res"]) else "good"
                if cur or col == "good":
                    k.outline(MX + (l - rx) * SC, MY + (t - ry) * SC, bw * SC, bh * SC, col, 2 if cur else 1)
                k.rect(MX + (at["x"] - rx) * SC, MY + (at["y"] - ry) * SC, SC, SC, col)
                k.text(MX + (at["x"] - rx) * SC + 1, MY + (at["y"] - ry) * SC - 10, str(at["a"]), "txt", 1)

    # ---- inputs
    header("ONE ROOM'S OBJECTS: A TOY LEVEL AND ROOM")
    stepper(-1)
    k.text(20, 88, "THE LEVEL'S EIGHT SLOTS (TOY INPUTS)", "txt", 2, True)
    k.text(20, 114, "SLOT  GROUP  OBJPRB", "dim", 2)
    for i, (g, p) in enumerate(SLOTS):
        k.rect(20, 138 + i * 26, 300, 22, "panel")
        k.text(30, 142 + i * 26, "%d" % i, "txt", 2)
        k.text(100, 142 + i * 26, "%d" % g, "txt", 2)
        k.text(200, 142 + i * 26, "%d" % p if g else "-", "txt", 2)
    k.text(340, 114, "GROUPS: ID, PROB, DENSITY", "dim", 2)
    yy = 138
    for g, mem in GROUPS.items():
        k.text(340, yy, "GROUP %d" % g, "txt", 2, True)
        yy += 24
        for cls, prob, dens in mem:
            k.text(350, yy, "%d  %d  %d" % (cls, prob, dens), "txt", 2)
            yy += 22
    k.text(20, 372, "ROOM %d BY %d; S %08X:%d, O %08X:%d" % (rw, rh, tr["S0"][0], HIGH, tr["O0"][0], HIGH), "acc", 2, True)
    k.text(20, 398, "VISITED %d OF %d: %d * 128 / %d = %d, NOT ABOVE 96" % (
        ROOMS[0], ROOMS[1], ROOMS[0], ROOMS[1], (ROOMS[0] << 7) // ROOMS[1]), "dim", 2)
    room(tr["walls"], tr["walls"])
    k.caption("A toy level with three used slots and one toy room: the slot rolls, the member picks and the spot searches "
              "(objects D, E, F).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="One toy room is populated: the room seed is {%d:%d} and the object-region seed {%d:%d} (illustrative)." % (
            seed, HIGH, oseed, HIGH),
        calc=["Toy slots (illustrative), slot: group, ObjPrb: %s." % "; ".join("%d: %d, %d" % (i, g, p) for i, (g, p) in enumerate(SLOTS) if g),
              "Toy groups (illustrative), class, PROB, DENSITY: %s." % "; ".join(
                  "group %d: %s" % (g, ", ".join("%d/%d/%d" % m for m in mem)) for g, mem in GROUPS.items()),
              "objects/README.md D1: the forced-slot test needs roomsVisited * 128 / roomCount > 96; here %d * 128 / %d = %d, so it does not apply." % (
                  ROOMS[0], ROOMS[1], (ROOMS[0] << 7) // ROOMS[1])]))

    # ---- the eight slots
    header("THE EIGHT SLOTS: ONE ROOM-SEED ROLL EACH")
    stepper(0)
    k.text(20, 82, "SLOT GROUP PRB   DRAW  R   TEST", "dim", 2)
    for sl in tr["slots"]:
        y = 106 + sl["k"] * 38
        k.rect(20, y, 920, 34, "cur" if sl["passes"] else "panel")
        k.text(30, y + 10, "%d" % sl["k"], "txt", 2)
        k.text(80, y + 10, "%d" % sl["g"], "txt", 2)
        k.text(160, y + 10, "%d" % sl["prb"] if sl["g"] else "-", "txt", 2)
        k.text(250, y + 10, "S%d" % sl["rn"], "dim", 2)
        k.text(320, y + 10, "%d" % sl["r"], "txt", 2, True)
        if sl["g"] == 0:
            msg, col = "GROUP 0: NOTHING", "dim"
        elif sl["passes"]:
            msg, col = "%d <= %d: PASSES; S%d, R2 = %d" % (sl["r"], sl["prb"], sl["r2n"], sl["r2"]), "good"
            if sl["pick"] is None:
                msg += ", SUM %d: NONE" % sl["sum"]
            else:
                msg += ", MEMBER %d" % sl["pick"]
        else:
            msg, col = "%d > %d: FAILS" % (sl["r"], sl["prb"]), "bad"
        k.text(400, y + 10, msg, col, 2, sl["passes"])
    k.caption("Every slot costs one room-seed draw, even group 0; a passing slot costs a second draw for the member pick "
              "(objects D1).", CAP_Y, 76)
    frames.append(k.done())
    calc = []
    for sl in tr["slots"]:
        if sl["g"] == 0:
            calc.append("objects/README.md D1: slot %d, group 0: draw S%d = %d; g = 0, so the slot fails." % (sl["k"], sl["rn"], sl["r"]))
        elif sl["passes"]:
            calc.append("objects/README.md D1: slot %d, group %d, ObjPrb %d: draw S%d = %d, %d <= %d passes; second draw S%d = %d." % (
                sl["k"], sl["g"], sl["prb"], sl["rn"], sl["r"], sl["r"], sl["prb"], sl["r2n"], sl["r2"]))
        else:
            calc.append("objects/README.md D1: slot %d, group %d, ObjPrb %d: draw S%d = %d, %d > %d fails." % (
                sl["k"], sl["g"], sl["prb"], sl["rn"], sl["r"], sl["r"], sl["prb"]))
    npass = sum(1 for s in tr["slots"] if s["passes"])
    caps.append(dict(
        text="Eight slot rolls and %d pick rolls on the room seed: %d slot%s pass%s." % (
            npass, npass, "" if npass == 1 else "s", "es" if npass == 1 else ""),
        calc=calc))

    # ---- picks and placements, slot by slot
    for sl in tr["slots"]:
        if not sl["passes"]:
            continue
        header("SLOT %d: THE MEMBER PICK, GROUP %d" % (sl["k"], sl["g"]))
        stepper(1)
        k.text(20, 88, "R2 = %d (S%d)" % (sl["r2"], sl["r2n"]), "txt", 2, True)
        k.text(20, 114, "MEMBER  CLASS  PROB  RUNNING SUM", "dim", 2)
        for i, (cls, prob, dens, tot) in enumerate(sl["walk"]):
            y = 138 + i * 34
            k.rect(20, y, 520, 30, "cur" if i == sl["pick"] else "panel")
            k.text(30, y + 8, "%d" % i, "txt", 2)
            k.text(130, y + 8, "%d" % cls, "txt", 2)
            k.text(230, y + 8, "%d" % prob, "txt", 2)
            k.text(330, y + 8, "%d" % tot, "txt", 2, True)
            k.text(400, y + 8, "%d < %d" % (sl["r2"], tot) if sl["r2"] < tot else "%d >= %d" % (sl["r2"], tot),
                   "good" if i == sl["pick"] else "dim", 2)
        yb = 138 + len(sl["walk"]) * 34 + 14
        x0 = 20
        pos = 0
        for i, (cls, prob, dens, tot) in enumerate(sl["walk"]):
            k.rect(x0 + pos * 5, yb, prob * 5, 26, "good" if i == sl["pick"] else "grey")
            k.outline(x0 + pos * 5, yb, prob * 5, 26, "dim")
            pos = tot
        k.rect(x0 + min(499, sl["r2"] * 5), yb - 8, 3, 42, "txt")
        k.text(x0, yb + 40, "0", "dim", 2)
        k.text(x0 + 500 - K.text_w("99", 2), yb + 40, "99", "dim", 2)
        if sl["pick"] is None:
            k.text(20, yb + 74, "SUM %d <= R2 %d: NOTHING IS PLACED" % (sl["sum"], sl["r2"]), "bad", 2, True)
            cap = ("The walk's running sum never rises above the roll (%d <= %d), so nothing is placed; the PROB values are "
                   "percentages against 100 (objects D1)." % (sl["sum"], sl["r2"]))
            text = "Slot %d: the pick roll %d is not below the PROB sum %d, so nothing is placed." % (sl["k"], sl["r2"], sl["sum"])
            calc = ["objects/README.md D1: sum = %s = %d; no member has r2 < sum for r2 = %d; nothing is placed." % (
                " + ".join(str(m[1]) for m in sl["walk"]), sl["sum"], sl["r2"])]
        else:
            k.text(20, yb + 74, "CLASS %d, DENSITY %d, POPULATEFN 3" % (sl["cls"], sl["dens"]), "txt", 2, True)
            cap = ("The first member whose running sum is above the roll is picked: member %d, class %d (objects D1)." % (
                sl["pick"], sl["cls"]))
            text = "Slot %d: the pick roll %d picks member %d, class %d." % (sl["k"], sl["r2"], sl["pick"], sl["cls"])
            calc = ["objects/README.md D1: the running sums are %s; the first with r2 = %d < sum is member %d, class %d, DENSITY %d." % (
                ", ".join(str(m[3]) for m in sl["walk"]), sl["r2"], sl["pick"], sl["cls"], sl["dens"])]
        k.caption(cap, CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text=text, calc=calc))
        if sl["pick"] is None:
            continue
        # the count
        header("SLOT %d: HANDLER 3 COUNTS" % sl["k"])
        stepper(2)
        a = (rw * rh) >> 7
        rows = [("ROOM AREA >> 7 = (%d * %d) >> 7" % (rw, rh), "%d" % a),
                ("CNT = (%d * DENSITY %d) >> 8" % (a, sl["dens"]), "%d" % sl["cnt"]),
                ("P100 ON O (O%d), ALWAYS PASSES" % sl["p100n"], "%d" % sl["p100"])]
        y = 90
        for lab, val in rows:
            k.rect(20, y, 520, 32, "panel")
            k.outline(20, y, 520, 32, "dim")
            k.text(30, y + 9, lab, "txt", 2)
            k.text(530 - K.text_w(val, 2), y + 9, val, "acc", 2, True)
            y += 36
        k.text(20, y + 10, "%d PLACER CALL%s OF CLASS %d, SIZE %d BY %d" % (sl["cnt"], "" if sl["cnt"] == 1 else "S", sl["cls"], sl["sx"], sl["sy"]),
               "txt", 2, True)
        k.text(20, y + 40, "EACH: 5 ATTEMPTS AT MOST", "dim", 2)
        room(set(), set())
        k.caption("The count is ((area >> 7) * DENSITY) >> 8; one roll against 100 always passes; then that many placer "
                  "calls (objects E).", CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Slot %d: the count is %d, and the always-passing roll on the object-region seed is %d." % (sl["k"], sl["cnt"], sl["p100"]),
            calc=["objects/README.md E: cnt = ((w * h) >> 7) * DENSITY >> 8 = ((%d * %d) >> 7) * %d >> 8 = %d * %d >> 8 = %d." % (
                rw, rh, sl["dens"], a, sl["dens"], sl["cnt"]),
                  "objects/README.md E, handler 3: P100(O) = %d (draw O%d), never above 100; then cnt calls of OBJ_PlaceRandom." % (sl["p100"], sl["p100n"])]))
        # the placer calls
        for call in [c for c in tr["places"] if c["slot"] == sl["k"]]:
            n = len(call["attempts"])
            for upto in range(1, n + 1):
                at = call["attempts"][upto - 1]
                header("SLOT %d, CALL %d OF %d: ATTEMPT %d" % (sl["k"], call["j"], sl["cnt"], at["a"]))
                stepper(3)
                y = 88
                for b in call["attempts"][:upto]:
                    cur = b is at
                    k.rect(20, y, 520, 50, "cur" if cur else "panel")
                    k.text(28, y + 5, "ATTEMPT %d: O%d = %d, O%d = %d" % (b["a"], b["n"] - 1, b["vx"], b["n"], b["vy"]), "txt", 2, cur)
                    k.text(28, y + 28, "SPOT (%d, %d)" % (b["x"], b["y"]), "dim" if not cur else "txt", 2)
                    if not b["inside"]:
                        k.text(250, y + 28, "OUT OF THE MARGIN", "bad", 2, cur)
                    elif b["res"]:
                        k.text(250, y + 28, "BOX %d BY %d MARKED" % (call["sx"] + 6, call["sy"] + 6), "bad", 2, cur)
                    else:
                        k.text(250, y + 28, "BOX %d BY %d FREE" % (call["sx"] + 6, call["sy"] + 6), "good", 2, cur)
                    y += 54
                if upto == n and not call["spot"]:
                    k.text(20, y + 6, "5 ATTEMPTS, NO SPOT: NOTHING IS MADE", "bad", 2, True)
                elif upto == n:
                    k.text(20, y + 6, "ACCEPTED: THE OBJECT MARKS ITS CELLS", "good", 2, True)
                k.text(20, 404, "GREY WALL, BLUE MARK, GREEN KEPT, RED NOT", "dim", 2)
                room(call["marks"], tr["walls"], call, upto)
                if not at["inside"]:
                    cap = "Attempt %d lands outside the one-subtile margin, so it is dropped without a box test (objects F1)." % at["a"]
                elif at["res"]:
                    cap = ("Attempt %d: the box of the object's size plus 6 holds a marked cell, so it is rejected (objects F1, F6)."
                           % at["a"])
                else:
                    cap = "Attempt %d: the margin holds and the box is free, so the object is made there (objects F1, F6)." % at["a"]
                if upto == n and not call["spot"]:
                    cap = "Five attempts failed and there is no fallback: the object is not made (objects F1)."
                k.caption(cap, CAP_Y, 76)
                frames.append(k.done())
                calc = ["objects/README.md F1: x = rect.x + R(O, w - sx - 1) = %d + R(O, %d) = %d + %d (O%d); y = rect.y + R(O, h - sy - 1) = %d + R(O, %d) = %d + %d (O%d)." % (
                    rx, rw - call["sx"] - 1, rx, at["vx"], at["n"] - 1, ry, rh - call["sy"] - 1, ry, at["vy"], at["n"])]
                if not at["inside"]:
                    calc.append("objects/README.md F1: the margin needs %d <= x < %d and %d <= y < %d; (%d, %d) is outside, so no box test is made." % (
                        rx + 1, rx + rw - 1, ry + 1, ry + rh - 1, at["x"], at["y"]))
                else:
                    calc.append("objects/README.md F1: (%d, %d) is inside the margin; COLL_WHTest(room, x, y, %d, %d, mask) = %s on the toy grid (illustrative)%s." % (
                        at["x"], at["y"], call["sx"] + 6, call["sy"] + 6, "nonzero" if at["res"] else "0",
                        ": rejected" if at["res"] else ": accepted, the object is created there"))
                if upto == n and not call["spot"]:
                    calc.append("objects/README.md F1: five attempts made, no fallback: no object is created.")
                caps.append(dict(
                    text="Slot %d, call %d, attempt %d: spot (%d, %d) %s." % (
                        sl["k"], call["j"], at["a"], at["x"], at["y"],
                        "is outside the margin" if not at["inside"] else "is rejected" if at["res"] else "is accepted"),
                    calc=calc))

    # ---- summary
    header("THE ROOM'S DRAWS, IN ORDER")
    stepper(3)
    npl = sum(1 for c in tr["places"] if c["spot"])
    k.text(20, 90, "ROOM SEED S: %d DRAWS" % tr["s_draws"], "txt", 2, True)
    k.text(40, 118, "8 SLOT ROLLS AND %d PICKS" % sum(1 for s in tr["slots"] if s["passes"]), "dim", 2)
    k.text(20, 160, "OBJECT-REGION SEED O: %d DRAWS" % tr["o_draws"], "txt", 2, True)
    k.text(40, 188, "%d P100, %d ATTEMPTS OF 2" % (sum(1 for s in tr["slots"] if s["pick"] is not None),
                                                   sum(len(c["attempts"]) for c in tr["places"])), "dim", 2)
    k.text(20, 230, "%d OF %d PLACER CALLS FOUND A SPOT" % (npl, len(tr["places"])), "good" if npl == len(tr["places"]) else "bad", 2, True)
    k.text(20, 270, "S ENDS AT %s" % sd(tr["S"]), "dim", 2)
    k.text(20, 296, "O ENDS AT %s" % sd(tr["O"]), "dim", 2)
    k.text(20, 322, "GAME SEED: 1 STEP PER OBJECT, NOT SHOWN", "dim", 2)
    room(tr["blocked"], tr["walls"])
    k.caption("The room seed drew once per slot and once per pick; the object-region seed drew the always-passing roll and "
              "two draws per attempt (objects D1, E, F1).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The room seed drew %d times and the object-region seed %d times; %d of %d placer calls found a spot." % (
            tr["s_draws"], tr["o_draws"], npl, len(tr["places"])),
        calc=["room seed after = {%d:%d}; object-region seed after = {%d:%d}." % (tr["S"] + tr["O"])]))
    return frames, caps, k.pal, tr


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--seed": "0xc0ffee", "--oseed": "12345", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            if i + 1 >= len(argv):
                print(__doc__.strip(), file=sys.stderr)
                return 2
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        seed, oseed = int(opts["--seed"], 0), int(opts["--oseed"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < seed <= 0xFFFFFFFF and 0 < oseed <= 0xFFFFFFFF):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "objects-%x-%x-schematic" % (seed, oseed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _tr = build(seed, oseed, opts["--theme"])
    K.write_illustration(out, "objects", frames, caps, W, H, K.palette(opts["--theme"])[1], "object population animation",
                         HELP, targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Animate a toy missile's life: its creation numbers, its per-frame step and its hit on a toy monster (docs/specs/skills/
missiles.md B1, D2-D4, E1; wiki skills, missiles). Schematic only (ADR-0036): boxes and text in our own palette.

Usage:
  python3 -I tools/missile_anim.py <root> [--seed N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. --seed: the owner's seed is {seed, 666} (default 0xC0FFEE; illustrative). --theme: the palette's dark or light values
(default dark). --schematic is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/missile-<seed hex>-schematic/ and must stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; missile.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

The toy: one missile of an illustrative row (every column a toy input, none read from a table) cast at level 10 by a toy
owner. Shown: the creation numbers of B1 (velocity, range, frames left, the activate mark), the frames of do function 1
(D2-D3 with the velocity step of D4: the fifth-step acceleration, the cap, the position step, frames left less 1), the
first frame that tests collisions, and the hit of E1 on a toy monster (the last-hit record, the to-hit roll on the
owner's seed, the result). Not shown: the missile's own seed (B1's creation step, the hit's damage draws of F, the
knockback roll of E3), the town tests of D2, the direction table (the toy direction is an input), the cells a step
crosses (the toy tests the cell the frame ends in), the defender's draws.

Model (ADR-0014 boundary): tools/skills.py is a checker of event logs with no function that runs a missile forward; the
rules of the sections above are written out here with a trace, using the model's generator step and signed helpers
(skills.step, skills.tdiv), and the tests (tools/test_missile_anim.py) feed every frame's velocity state and position to
the model's own frame check (skills.Checker.mf) as if logged, so any difference of a number fails. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import schematic_kit as K  # noqa: E402
import skills  # noqa: E402

W, H = 960, 500
CAP_Y = 436
HIGH = 666
# the toy row: Missiles columns as inputs, and the cast
ROW = dict(Vel=24, VelLev=8, Range=8, LevRange=1, Activate=12, Accel=1024, MaxVel=32, CollideType=3, CollideKill=1,
           Explosion=0, NextHit=0, LastCollide=0, Pierce=0, ToHit=1)
LVL = 10
DIR = (3547, 2048)            # the toy direction vector (4096 is 1.0): about 30 degrees
START = (100, 100)            # the toy start subtile
HIT_CHANCE = 70               # the to-hit chance of the owner on the toy monster, an input (to-hit § C gives it)
MASK = 0x0184                 # g_MissileCollideTypes[3].mask (missiles.md D, the collide types table)
STEPS = ("CREATE", "FRAMES", "COLLIDE", "HIT")
HELP = """<li>The toy missile is made with the creation rules of B1: its velocity, range, frames left and activate mark come from the row and the level.</li>
<li>Each frame the do function steps the velocity (every fifth step it adds the acceleration up to the cap), moves the position by the step and takes one off the frames left.</li>
<li>Only once the frames left reach the activate mark does the missile test its cell for a unit; a unit found there is hit.</li>
<li>The hit takes the owner's next draw as a to-hit roll; below the chance it is a hit, otherwise the missile is freed at that unit.</li>
<li>Every number is an illustrative input or computed from one, not observed in the game.</li>"""


def run(seed):
    """The toy missile's life, as a trace of dicts for the frames and the tests."""
    r = ROW
    v = ((r["VelLev"] * LVL) // 8 + r["Vel"]) << 8           # u8 columns, the product signed, divided toward zero
    v0 = v
    v = skills.tdiv(v * 75, 100) if v != 0 else 0
    rng_ = r["LevRange"] * LVL + r["Range"]
    cr = dict(v0=v0, v=v, range=rng_, left=rng_, activate=rng_ - r["Activate"], accel=r["Accel"],
              maxv=r["MaxVel"] << 8)
    st = dict(v=v, a=cr["accel"], cnt=0, mx=cr["maxv"], x=START[0] << 16, y=START[1] << 16)
    left = rng_
    frames = []
    cell_of = lambda x, y: (x >> 16, y >> 16)               # noqa: E731
    # run the toy once without the monster to place it on the cell of the frame that ends at 14 (or the first one
    # past the activate mark with a different cell from the one before it)
    probe = dict(st)
    cells = []
    pl = left
    while pl > 0:
        v_, a_, c_ = probe["v"], probe["a"], probe["cnt"]
        if a_:
            c_ += 1
            if c_ > 4:
                v_ += a_
                if v_ > probe["mx"]:
                    v_, a_ = probe["mx"], 0
                elif v_ < 0:
                    v_ = 0
                c_ = 0
        s_ = (v_ * 0x400) >> 6
        probe.update(v=v_, a=a_, cnt=c_, x=probe["x"] + ((DIR[0] * s_) >> 12), y=probe["y"] + ((DIR[1] * s_) >> 12))
        pl -= 1
        cells.append(cell_of(probe["x"], probe["y"]))
    n_hit = len(cells) - 4                                   # the 14th frame of 18
    mon = cells[n_hit - 1]
    tr = dict(cr=cr, mon=mon, frames=[], seed=(seed, HIGH))
    f = 0
    while True:
        f += 1
        d0 = dict(st)
        if st["a"]:
            st["cnt"] += 1
            if st["cnt"] > 4:
                st["v"] += st["a"]
                if st["v"] > st["mx"]:
                    st["v"], st["a"] = st["mx"], 0
                elif st["v"] < 0:
                    st["v"] = 0
                st["cnt"] = 0
        s = (st["v"] * 0x400) >> 6
        sx, sy = (DIR[0] * s) >> 12, (DIR[1] * s) >> 12
        st["x"] += sx
        st["y"] += sy
        left -= 1
        cell = cell_of(st["x"], st["y"])
        fr = dict(n=f, d0=d0, d1=dict(st), s=s, sx=sx, sy=sy, left=left, cell=cell, tests=left <= cr["activate"],
                  unit=(left <= cr["activate"] and cell == mon), fifth=d0["a"] != 0 and st["cnt"] == 0 and st["a"] != 0,
                  capped=d0["a"] != 0 and st["a"] == 0)
        tr["frames"].append(fr)
        if fr["unit"] or left <= 0:
            break
    hit = tr["frames"][-1]
    tr["hit"] = hit
    sd = (seed, HIGH)
    sd = skills.step(sd)
    roll = sd[0] % 100
    tr["roll"] = dict(r=roll, c=HIT_CHANCE, hit=roll < HIT_CHANCE, seed=sd)
    return tr


def pos_s(p):
    """A 16.16 position as subtiles with two decimals."""
    return "%d.%02d" % (p >> 16, ((p & 0xFFFF) * 100) >> 16)


def build(seed, theme):
    tr = run(seed)
    cr, fr_all = tr["cr"], tr["frames"]
    hit, rl = tr["hit"], tr["roll"]
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    MX, MY, SC = 600, 100, 12                                # the mini map's origin and pixels per subtile
    shown_cells = []

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def stepper(cur):
        for i, n in enumerate(STEPS):
            k.box(20 + i * 232, 40, 222, 30, [n], "cur" if i == cur else "panel", "acc" if i == cur else "dim",
                  "txt" if i <= cur else "dim", 2, bold=(i == cur))

    def minimap(upto, cur=None):
        """The toy field: one dot per frame end so far (the newest highlighted), the monster's cell."""
        k.rect(MX - 10, MY - 10, 340, 200, "panel")
        k.outline(MX - 10, MY - 10, 340, 200, "dim")
        mx_, my_ = tr["mon"]
        k.rect(MX + (mx_ - START[0]) * SC - 3, MY + (my_ - START[1]) * SC - 3, SC + 6, SC + 6, "bad")
        k.text(MX - 2, MY + 172, "MONSTER", "bad", 1)
        k.rect(MX - 3, MY - 3, 7, 7, "txt")
        for j in range(upto):
            cx, cy = fr_all[j]["cell"]
            k.rect(MX + (cx - START[0]) * SC + 2, MY + (cy - START[1]) * SC + 2, SC - 4, SC - 4,
                   "acc" if j == (cur if cur is not None else upto - 1) else "dim")

    def rows(y, items, w=540):
        for lab, val in items:
            assert K.text_w(lab, 2) + K.text_w(val, 2) + 40 <= w, (lab, val)     # a row's two texts never meet
            k.rect(20, y, w, 32, "panel")
            k.outline(20, y, w, 32, "dim")
            k.text(30, y + 9, lab, "txt", 2)
            k.text(20 + w - 10 - K.text_w(val, 2), y + 9, val, "acc", 2, True)
            y += 36
        return y

    # ---- inputs
    header("A TOY MISSILE: CREATION, FRAMES, HIT")
    stepper(-1)
    k.text(20, 90, "THE ROW (TOY INPUTS, NOT TABLE VALUES)", "txt", 2, True)
    for i, ln in enumerate(("VEL %d, VELLEV %d, RANGE %d, LEVRANGE %d" % (ROW["Vel"], ROW["VelLev"], ROW["Range"], ROW["LevRange"]),
                            "ACTIVATE %d, ACCEL %d, MAXVEL %d" % (ROW["Activate"], ROW["Accel"], ROW["MaxVel"]),
                            "COLLIDETYPE %d, COLLIDEKILL %d, EXPLOSION 0, TOHIT %d" % (ROW["CollideType"], ROW["CollideKill"],
                                                                                     ROW["ToHit"]),
                            "THE SKILL LEVEL IS %d" % LVL)):
        k.text(40, 120 + i * 28, ln, "txt", 2)
    k.text(20, 250, "THE OWNER", "txt", 2, True)
    k.text(40, 280, "SEED %08X : %08X (ILLUSTRATIVE)" % (seed, HIGH), "acc", 2, True)
    k.text(40, 308, "CHANCE TO HIT THE MONSTER: %d PERCENT" % HIT_CHANCE, "txt", 2)
    k.text(20, 350, "THE DIRECTION IS A TOY VECTOR (%d, %d)" % DIR, "dim", 2)
    k.text(20, 376, "THE MONSTER STANDS ON A CELL THE PATH CROSSES", "dim", 2)
    k.caption("A toy missile is made, steps frame by frame, and hits a toy monster: creation (B1), the frame (D2 to D4), "
              "the hit (E1).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="A toy missile of level %d is created, steps frame by frame and hits a toy monster; the owner's seed is {%d:%d} (illustrative)." % (
            LVL, seed, HIGH),
        calc=["Toy row (illustrative): Vel %d, VelLev %d, Range %d, LevRange %d, Activate %d, Accel %d, MaxVel %d, CollideType %d, CollideKill %d, Explosion 0, ToHit %d." % (
            ROW["Vel"], ROW["VelLev"], ROW["Range"], ROW["LevRange"], ROW["Activate"], ROW["Accel"], ROW["MaxVel"],
            ROW["CollideType"], ROW["CollideKill"], ROW["ToHit"]),
              "Toy direction vector (illustrative, 4096 is 1.0): (%d, %d); start subtile (%d, %d); to-hit chance %d percent." % (
                  DIR[0], DIR[1], START[0], START[1], HIT_CHANCE)]))

    # ---- creation: velocity
    header("CREATE: THE VELOCITY")
    stepper(0)
    y = rows(90, [("(VELLEV * LVL) / 8 + VEL = (%d * %d) / 8 + %d" % (ROW["VelLev"], LVL, ROW["Vel"]),
                   "%d" % ((ROW["VelLev"] * LVL) // 8 + ROW["Vel"])),
                  ("SHIFTED LEFT 8 BITS", "%d" % cr["v0"]),
                  ("TIMES 75 / 100 (V IS NOT 0)", "%d" % cr["v"])], 900)
    k.text(20, y + 10, "THE PATH'S ACCEL %d, ITS CAP MAXVEL << 8 = %d" % (cr["accel"], cr["maxv"]), "txt", 2, True)
    k.caption("Creation sets the velocity to ((VelLev * level) / 8 + Vel) << 8, then 75 / 100 of it: %d (creation B1)." % cr["v"],
              CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The velocity is %d, the row's formula for level %d, then 75 percent." % (cr["v"], LVL),
        calc=["missiles.md B1: v = ((VelLev * lvl) / 8 + Vel) << 8 = ((%d * %d) / 8 + %d) << 8 = %d." % (
            ROW["VelLev"], LVL, ROW["Vel"], cr["v0"]),
              "missiles.md B1: v is not 0, so v = v * 75 / 100 = %d." % cr["v"],
              "missiles.md B1: the path's acceleration is Accel = %d and its maximum is MaxVel << 8 = %d." % (cr["accel"], cr["maxv"])]))

    # ---- creation: range
    header("CREATE: RANGE, FRAMES LEFT, THE ACTIVATE MARK")
    stepper(0)
    y = rows(90, [("RANGE = LEVRANGE * LVL + RANGE = %d * %d + %d" % (ROW["LevRange"], LVL, ROW["Range"]), "%d" % cr["range"]),
                  ("FRAMES LEFT = RANGE", "%d" % cr["left"]),
                  ("ACTIVATE MARK = RANGE - ACTIVATE = %d - %d" % (cr["range"], ROW["Activate"]), "%d" % cr["activate"])], 900)
    k.text(20, y + 10, "COLLISIONS ARE TESTED ONLY WHILE FRAMES LEFT <= %d" % cr["activate"], "txt", 2, True)
    k.caption("The range is LevRange * level + Range; the frames left start there, and the activate mark is the range less "
              "Activate (creation B1, each frame D3).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The range is %d frames, so %d frames are left; collisions start at the mark %d." % (cr["range"], cr["left"], cr["activate"]),
        calc=["missiles.md B1: range = LevRange * lvl + Range = %d * %d + %d = %d (no sub-loop, no override); left = range = %d." % (
            ROW["LevRange"], LVL, ROW["Range"], cr["range"], cr["left"]),
              "missiles.md B1: activate = range - Activate = %d - %d = %d." % (cr["range"], ROW["Activate"], cr["activate"])]))

    # ---- frame 1, in detail
    f1 = fr_all[0]
    header("FRAME 1: THE DO FUNCTION")
    stepper(1)
    st0, st1 = f1["d0"], f1["d1"]
    y = rows(90, [("ACCEL SET: COUNT %d -> %d, NOT ABOVE 4" % (st0["cnt"], st1["cnt"]), "V %d" % st1["v"]),
                  ("S = (%d * 1024) >> 6" % st1["v"], "%d" % f1["s"]),
                  ("STEP X = (%d * %d) >> 12" % (DIR[0], f1["s"]), "%d" % f1["sx"]),
                  ("STEP Y = (%d * %d) >> 12" % (DIR[1], f1["s"]), "%d" % f1["sy"]),
                  ("FRAMES LEFT %d - 1" % cr["left"], "%d" % f1["left"])], 560)
    minimap(1)
    k.text(20, y + 8, "POSITION %s, %s SUBTILES" % (pos_s(st1["x"]), pos_s(st1["y"])), "txt", 2, True)
    k.caption("Each frame the velocity is stepped, the position moves by the step on both axes and the frames left fall by "
              "1 (do function 1, D3 and D4).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Frame 1: the velocity stays %d, the position moves by (%d, %d) and %d frames are left." % (st1["v"], f1["sx"], f1["sy"], f1["left"]),
        calc=["missiles.md D2: n is the row's do function, 1; the toy missile is not in a town, so the do function runs.",
              "missiles.md D4: accel is %d, so count = %d; count is not above 4, so v stays %d." % (st0["a"], st1["cnt"], st1["v"]),
              "missiles.md D4: s = (v * 0x400) >> 6 = %d; step.x = (dir.x * s) >> 12 = %d, step.y = (dir.y * s) >> 12 = %d." % (
                  f1["s"], f1["sx"], f1["sy"]),
              "missiles.md D3: the position moves by the step on both 16.16 axes: (%s, %s) subtiles; left = %d - 1 = %d." % (
                  pos_s(st1["x"]), pos_s(st1["y"]), cr["left"], f1["left"])]))

    # ---- the frame table up to the cap
    capf = [f for f in fr_all if f["capped"]][0]
    fifth = [f for f in fr_all if f["fifth"]]
    header("FRAMES 1 TO %d: THE VELOCITY STEPS UP, THEN CAPS" % capf["n"])
    stepper(1)
    k.text(20, 86, "FRAME", "dim", 2)
    k.text(110, 86, "COUNT", "dim", 2)
    k.text(210, 86, "VELOCITY", "dim", 2)
    k.text(350, 86, "NOTE", "dim", 2)
    for i, f in enumerate(fr_all[:capf["n"]]):
        yy = 112 + i * 26
        d1 = f["d1"]
        note = ""
        if f["capped"]:
            note = "CAPPED, ACCEL 0"
        elif f["fifth"]:
            note = "FIFTH STEP: +%d" % ROW["Accel"]
        k.rect(20, yy, 540, 22, "cur" if (f["fifth"] or f["capped"]) else "panel")
        k.text(26, yy + 4, "%d" % f["n"], "txt", 2)
        k.text(116, yy + 4, "%d" % d1["cnt"], "txt", 2)
        k.text(216, yy + 4, "%d" % d1["v"], "txt", 2, f["fifth"] or f["capped"])
        if note:
            k.text(350, yy + 4, note, "acc", 2)
    minimap(capf["n"])
    k.caption("Every fifth step adds Accel to the velocity; a sum above the cap sets the velocity to it and stops the "
              "acceleration (D4).", CAP_Y, 76)
    frames.append(k.done())
    c1 = fifth[0]
    caps.append(dict(
        text="Frame %d adds the acceleration (velocity %d); frame %d goes past the cap and sets it to %d." % (
            c1["n"], c1["d1"]["v"], capf["n"], capf["d1"]["v"]),
        calc=["missiles.md D4: count += 1; when count > 4, v += accel and count = 0 (frames %s: v = %s)." % (
            ", ".join(str(f["n"]) for f in fifth), ", ".join(str(f["d1"]["v"]) for f in fifth)),
              "missiles.md D4: v = %d + %d = %d is above the cap %d, so v = %d and accel = 0; later frames keep v and make no count." % (
                  capf["d0"]["v"], capf["d0"]["a"], capf["d0"]["v"] + capf["d0"]["a"], cr["maxv"], capf["d1"]["v"])]))

    # ---- the first collision frame
    t0 = [f for f in fr_all if f["tests"]][0]
    header("FRAME %d: FRAMES LEFT REACH THE ACTIVATE MARK" % t0["n"])
    stepper(2)
    y = rows(90, [("FRAMES LEFT AFTER THE STEP", "%d" % t0["left"]),
                  ("ACTIVATE MARK", "%d" % cr["activate"]),
                  ("LEFT > ACTIVATE?", "NO: THE CELL IS TESTED")], 560)
    free = not t0["unit"]
    k.text(20, y + 8, "THE CELL (%d, %d)" % t0["cell"], "txt", 2, True)
    k.text(20, y + 36, "FREE, THE CELL WORD IS 0: KEEP" if free else "HOLDS THE MONSTER", "txt", 2, True)
    k.text(20, y + 74, "THE WORD IS READ EVERY FRAME;", "dim", 2)
    k.text(20, y + 100, "FROM NOW ON, NOT 0 STARTS A UNIT SEARCH", "dim", 2)
    minimap(t0["n"])
    k.caption("From the activate mark on, a non-zero word of the missile's own cell starts the unit search; a word of 0 "
              "keeps it (D3).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Frame %d leaves %d frames, at the activate mark %d, so a non-zero cell word would start the unit search%s." % (
            t0["n"], t0["left"], cr["activate"], "; the word is 0 and the missile is kept" if free else ""),
        calc=["missiles.md D3: left = %d - 1 = %d; mode (CollideType) = %d is not 0 and not 6; c = PathCellCollision = %s; "
              "left > activate is %d > %d, false." % (t0["left"] + 1, t0["left"], ROW["CollideType"],
                                                       "0, so the call returns 1 (keep)" if free else "nonzero", t0["left"], cr["activate"])]))

    # ---- the hit frame
    if not hit["unit"]:
        raise SystemExit("toy missile never meets the monster")
    if hit["n"] != t0["n"]:
        header("FRAME %d: A UNIT ON THE CELL" % hit["n"])
        stepper(2)
        y = rows(90, [("FRAMES LEFT %d <= ACTIVATE %d" % (hit["left"], cr["activate"]), "TESTED"),
                      ("CELL WORD (%d, %d)" % hit["cell"], "NOT 0, BITS 0, 2 CLEAR"),
                      ("CollisionTest, MASK 0X%04X" % MASK, "NOT 0"),
                      ("FindUnitAtCell", "THE MONSTER")], 560)
        k.text(20, y + 8, "HITUNIT(MISSILE, MONSTER, END 0)", "txt", 2, True)
        minimap(hit["n"])
        k.caption("A cell with a unit of the collide type's filter calls the hit with that unit (D3, E1).", CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="Frame %d: the cell (%d, %d) holds the monster, so the hit function is called with it." % (hit["n"], hit["cell"][0], hit["cell"][1]),
            calc=["missiles.md D3: c = PathCellCollision is not 0 and has neither bit 0 nor bit 2; left %d is not above activate %d; "
                  "the collide type's filter exists; for the step's cells, CollisionTest(room, x, y, size, 0x%04X) is not 0 there, "
                  "FindUnitAtCell returns the monster: HitUnit(m, unit, 0)." % (hit["left"], cr["activate"], MASK)]))

    # ---- E1: the filters and the roll
    header("THE HIT: THE FILTERS, THEN THE TO-HIT ROLL")
    stepper(3)
    y = rows(90, [("c = EXPLOSION ? 0 : 2 = 2; p = 3", "c = 2"),
                  ("LASTHIT = THE MONSTER, BEFORE FILTERS", "SET"),
                  ("NEXTHIT, LASTCOLLIDE: NOT SET", "PASS"),
                  ("TYPE FILTER, HOSTILE TEST", "PASS (TOY)"),
                  ("PIERCE 0; COLLIDEKILL 1: c | 1", "c = 3"),
                  ("ROW HAS TOHIT: ROLL ON OWNER SEED", "NEXT")], 560)
    k.caption("The hit runs the filters in E1's order, with the last-hit record before them, then the to-hit roll on the "
              "owner's seed (E1).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The hit records the monster, passes the filters and, the row having ToHit, rolls to hit on the owner's seed.",
        calc=["missiles.md E1: c = (Explosion ? 0 : 2) = 2, p = 3; m.data.lastHit = unit before the filters; NextHit and LastCollide are 0; "
              "the type filter and the hostility test pass for the toy monster (illustrative).",
              "missiles.md E1: Pierce is 0, so p stays 3; CollideKill is 1, so c |= 1: c = 3. The row has ToHit: COMBAT_ToHitRoll(owner, unit, stat 19, 1) runs."]))

    # ---- the roll
    header("THE HIT: THE OWNER'S ROLL")
    stepper(3)
    k.box(40, 86, 400, 90, [("RANGE(100) ON THE OWNER'S SEED", "dim"), (str(rl["r"]), "acc")], "panel", "dim", "txt", 2, bold=True)
    k.text(470, 96, "R = %d  %s  C = %d" % (rl["r"], "<" if rl["hit"] else ">=", rl["c"]), "txt", 3, True)
    k.text(470, 140, "A HIT" if rl["hit"] else "A MISS", "good" if rl["hit"] else "bad", 3, True)
    k.bar(40, 200, 880, 18, rl["c"], 100, "good", "grey")
    k.rect(40 + min(878, rl["r"] * 880 // 100) - 1, 192, 3, 34, "txt")
    k.text(40, 228, "0", "dim", 2)
    k.text(40 + 880 - K.text_w("99", 2), 228, "99", "dim", 2)
    k.text(40, 270, "SEED AFTER THE DRAW: %08X : %08X" % rl["seed"], "dim", 2)
    k.caption("The roll is the owner's next draw, low mod 100; below the chance is a hit (E1; to-hit C gives the chance)." if rl["hit"]
              else "The roll is the owner's next draw, low mod 100; at or above the chance is a miss, and the missile is freed at that unit (E1).",
              CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The owner's roll is %d against %d: %s." % (rl["r"], rl["c"], "a hit" if rl["hit"] else "a miss"),
        calc=["missiles.md E1: the roll is the owner's next draw, low mod 100: %d (seed after = {%d:%d})." % (rl["r"], rl["seed"][0], rl["seed"][1]),
              "missiles.md E1: r %s c = %d: %s." % ("<" if rl["hit"] else ">=", rl["c"],
                                                    "a hit" if rl["hit"] else "a miss, JustHitState and the hit event run, the result is 2: the missile is freed")]))

    # ---- the result
    header("THE HIT: THE RESULT")
    stepper(3)
    if rl["hit"]:
        y = rows(90, [("p & 2: JUSTHIT, THE HIT EVENT", "RUN"),
                      ("ROW HAS NO HIT FUNCTION", "c STAYS 3"),
                      ("C & 2: DAMAGE (F), APPLY (E3)", "NOT SHOWN"),
                      ("c & 1 AND p & 1: UNMARK, FREE", "RESULT 2")], 560)
        k.text(20, y + 10, "THE MISSILE ENDS AT THE MONSTER", "good", 2, True)
        k.caption("On a hit with no hit function the damage is built and applied, and a CollideKill missile ends there with "
                  "result 2 (E1).", CAP_Y, 76)
        txt = "The roll hits: the damage is built and applied, and the CollideKill missile is freed."
        calc = ["missiles.md E1: p & 2: JustHitState and the hit event run; no hit function, so c = 3 stays; c & 2: MISSILE_BuildDamage then "
                "MissileApplyAndAc (their draws are not shown).",
                "missiles.md E1: c & 1 and p & 1: the missile's 0x40 mark is removed (only a Collision row marks it) and the result is 2: the missile is freed."]
    else:
        y = rows(90, [("PIERCE 0: NO CHARGE SPENT", "-"),
                      ("JUSTHIT, THE HIT-BY-MISSILE EVENT", "RUN"),
                      ("ROW HAS NO ALWAYSEXPLODE", "RETURN 2")], 560)
        k.text(20, y + 10, "NO DAMAGE IS BUILT; THE MISSILE IS FREED", "bad", 2, True)
        k.caption("A missed roll runs the just-hit state and the event, builds no damage, and returns 2: the missile is freed "
                  "at that unit (E1).", CAP_Y, 76)
        txt = "The roll misses: no damage is built and the missile is freed at the monster."
        calc = ["missiles.md E1: a failed roll runs JustHitState and the hit-by-missile event; the row has no hit function, so it returns 2 with "
                "no build; the missile is freed at that unit (E1, a missed to-hit)."]
    frames.append(k.done())
    caps.append(dict(text=txt, calc=calc))

    # ---- summary
    header("THE MISSILE'S LIFE, IN FRAMES")
    stepper(3)
    k.text(20, 90, "CREATED: V %d, RANGE %d, ACTIVATE MARK %d" % (cr["v"], cr["range"], cr["activate"]), "txt", 2, True)
    k.text(20, 122, "FRAMES 1 TO %d: THE DO FUNCTION; THE VELOCITY CAPS AT FRAME %d" % (hit["n"], capf["n"]), "txt", 2, True)
    k.text(20, 154, "FRAMES %d ON: THE CELL IS TESTED" % t0["n"], "txt", 2, True)
    k.text(20, 186, "FRAME %d: THE MONSTER, ROLL %d AGAINST %d: %s" % (hit["n"], rl["r"], rl["c"], "HIT" if rl["hit"] else "MISS"),
           "good" if rl["hit"] else "bad", 2, True)
    k.text(20, 232, "FRAMES LEFT FELL BY 1 PER FRAME: %d AT THE END" % hit["left"], "dim", 2)
    k.text(20, 258, "THE OWNER'S SEED DREW ONCE: %08X : %08X" % rl["seed"], "dim", 2)
    minimap(hit["n"])
    k.caption("The toy missile moved %d frames, was tested from frame %d and ended at the monster (D3, E1)." % (hit["n"], t0["n"]),
              CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The toy missile lived %d frames, tested its cell from frame %d and met the monster at frame %d; the owner's seed drew once." % (
            hit["n"], t0["n"], hit["n"]),
        calc=["summary: v = %d at creation, the cap %d at frame %d; left = %d at the hit (the range %d less %d frames)." % (
            cr["v"], cr["maxv"], capf["n"], hit["left"], cr["range"], hit["n"]),
              "owner seed after = {%d:%d}." % rl["seed"]]))
    return frames, caps, k.pal, tr


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--seed": "0xc0ffee", "--theme": "dark", "--out": None}
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
        seed = int(opts["--seed"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not 0 < seed <= 0xFFFFFFFF:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim", "missile-%x-schematic" % seed)
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _tr = build(seed, opts["--theme"])
    K.write_illustration(out, "missile", frames, caps, W, H, K.palette(opts["--theme"])[1], "missile animation", HELP,
                         targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

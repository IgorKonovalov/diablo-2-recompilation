"""Animate one melee hit of a toy attacker on a toy defender (docs/specs/combat/to-hit.md A-C, damage.md A-B,
delivery.md A-B; wiki combat, Draw order and chaining): the draws it makes, in order, on the attacker's seed and the
defender's seed. Schematic only (ADR-0036): boxes and text in our own palette.

Usage:
  python3 -I tools/combat_anim.py <root> [--seed N] [--dseed N] [--theme dark|light] [--out DIR] [--schematic]

<root> is the data tree every illustration tool takes first (workspace/merged); this tool reads no game file and ignores
it. --seed: the attacker's seed is {seed, 666} (default 0xC0FFEE); --dseed: the defender's seed is {dseed, 666}
(default 12345); both are illustrative inputs. --theme: the palette's dark or light values (default dark). --schematic
is accepted for the export builder and changes nothing. DIR defaults to
workspace/render/anim/combat-<seed hex>-<dseed hex>-schematic/ and must stay under workspace/. Outputs:
  frame-NNN.png  one frame per step; combat.gif the frames as an animated GIF; index.html the step-through page;
  steps.json the captions and calculations; schematic.json the marker's file list (ADR-0036).

The toy: a player attacker holding a one-handed weapon and a monster defender, every number an illustrative input (none
is read from a table). The attacker's chances are set so that every draw of a normal player attack on a monster shows:
the to-hit draw, the monster's block draw, the build's physical roll, the deadly strike chain, the build's always-drawn
RangeB(1), then on a hit the open wounds and crushing blow draws; the defender's avoidance chances are 0, which draws
nothing (to-hit C3). Not shown: elemental damage and drains, leech, stun and cold draws (they draw only under their own
conditions, none held by the toy), the reductions (no draw; the toy has none), the hit class and the durability and
get-hit boundary draws.

Model (ADR-0014 boundary): tools/combat.py is a checker of event logs, with no function that runs a hit forward, so the
rules of the sections above are written out here with a trace; the arithmetic helpers (the generator's step, range and
the signed MulDiv, the truncating division) and the defence formula (Checker.get_defense) are the model's. The
tests (tools/test_combat_items_anim.py) feed the toy's numbers to the model's own to-hit, defence, damage-build,
open-wounds and crushing-blow checks (Checker.tohit, defence, build, openwounds, crushing) as if logged, so any
difference of a number or a seed fails. Stdlib only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_common  # noqa: E402
import combat  # noqa: E402
import schematic_kit as K  # noqa: E402

W, H = 960, 500
CAP_Y = 436
HIGH = 666
# the toy's inputs; stat ids as in the specs' tables of runtime state
ATT = {12: 30, 0: 80, 2: 40, 19: 150, 21: 5, 22: 11, 25: 40, 135: 92, 136: 60, 141: 20}
DEF = {12: 20, 31: 180, 2: 80, 20: 20, 6: 300 * 256, 7: 300 * 256, 100: 1}
TOY_TOHIT_FACTOR = 20            # the toy class's CharStats ToHitFactor
TOY_WEAPON = dict(sb=100, db=0)  # the toy weapon's StrBonus and DexBonus
STEPS = ("TO-HIT", "BLOCK", "BUILD", "DELIVERY")
HELP = """<li>Two seeds: the attacker's (left column of draws) and the defender's (right). Each draw is one step of its own seed.</li>
<li>To-hit: the attacker's chance c from attack rating and defence, then one draw below 100; below c is a hit. The monster's block follows only on a hit, on the defender's seed.</li>
<li>Build: the attacker's damage is built whatever the to-hit gave: the physical roll, the deadly strike test, and one draw that is always made. A blocked or missed swing delivers nothing.</li>
<li>Delivery: on a hit, open wounds then crushing blow, each drawn only when the attacker has the stat; then the life changes.</li>
<li>Every number is an illustrative input or computed from one, not observed in the game.</li>"""


def unit(stats, cls=0, typ=0):
    return {"t": typ, "c": cls, "st": {str(k): v for k, v in stats.items()}, "m": 1, "u": 1}


def run(seed, dseed):
    """The toy hit, step by step: a trace of dicts (name, numbers, the seed after each draw) for the frames."""
    a, d = unit(ATT), unit(DEF, 7, 1)
    ck = combat.Checker(None)
    st = combat.stat
    tr = dict(a=a, d=d, draws=[])
    sa, sd = (seed, HIGH), (dseed, HIGH)

    def draw(who, label, n):
        nonlocal sa, sd
        if who == "A":
            v, sa = combat.rng_range(sa, n)
            tr["draws"].append((who, label, n, v, sa))
        else:
            v, sd = combat.rng_range(sd, n)
            tr["draws"].append((who, label, n, v, sd))
        return v
    # ---- A: the chance to hit
    dlvl, alvl = st(d, 12), st(a, 12)
    defense = ck.get_defense(d) + st(d, 33)
    ar0 = (st(a, 2) - 7) * 5 + st(a, 19) + TOY_TOHIT_FACTOR
    pct = 0                                           # no weapon mastery, stat 119 and arPct are 0 for the toy
    ar = ar0 + combat.muldiv(ar0, pct, 100)
    c1 = 100 if ar + defense == 0 else combat.tdiv(100 * ar, ar + defense)
    c2 = combat.tdiv(c1 * alvl * 2, alvl + dlvl)
    c = 5 if c2 <= 5 else (95 if c2 >= 95 else c2)
    tr["th"] = dict(alvl=alvl, dlvl=dlvl, defense=defense, def_base=st(d, 31), def_dex=st(d, 2), ar0=ar0, ar=ar, c1=c1,
                    c2=c2, c=c, dex=st(a, 2), factor=TOY_TOHIT_FACTOR, s19=st(a, 19))
    r = draw("A", "to-hit", 100)
    hit = r < c
    tr["th"].update(r=r, hit=hit)
    res = 1 if hit else 0
    # ---- C: the defence rolls, on a hit
    blocked = False
    b = min(st(d, 20), 75)
    tr["df"] = dict(b=b, ran=hit, r=None, blocked=False)
    if hit:
        if b >= 1:
            rb = draw("D", "block", 100)
            blocked = rb < b
            tr["df"].update(r=rb, blocked=blocked)
        if blocked:
            res = 0x10
    tr["res"] = res
    # ---- the build runs whatever the hit test gave (damage A2 note)
    mn, mx = st(a, 21) << 8, st(a, 22) << 8
    add = st(a, 111) << 8
    mn, mx = mn + add, mx + add
    if mn < 1:
        mn = 256
    if mx <= mn:
        mx = mn + 256
    ed = st(a, 25) + combat.tdiv(st(a, 0) * TOY_WEAPON["sb"], 100) + combat.tdiv(st(a, 2) * TOY_WEAPON["db"], 100)
    ed = max(ed, -90)
    lo = mn + combat.muldiv(mn, ed + st(a, 18), 100)
    hi = mx + combat.muldiv(mx, ed + st(a, 17), 100)
    x = draw("A", "physical", hi - lo) if hi > lo else 0
    phys = max(0 + lo + x, 0)
    tr["ph"] = dict(mn=mn, mx=mx, ed=ed, lo=lo, hi=hi, x=x, phys=phys, ed_base=st(a, 25),
                    ed_str=combat.tdiv(st(a, 0) * TOY_WEAPON["sb"], 100))
    crit = dict(ran=False, r=None, chance=st(a, 141), won=False)
    if st(a, 141) > 0:                                # the toy has no mastery crit and no stat 337
        rc = draw("A", "deadly strike", 100)
        crit.update(ran=True, r=rc, won=rc < st(a, 141))
    final = phys * 2 if crit["won"] else phys
    tr["cr"] = dict(crit, phys=phys, final=final)
    rb1 = draw("A", "burning step", 1)
    tr["rb"] = dict(r=rb1, burn=combat.tdiv(max(316 + rb1, 0), 128))
    tr["pkt"] = dict(phys=final)
    # ---- delivery (a hit that was not blocked)
    life = st(d, 6)
    dl = dict(ran=bool(res & 1), life0=life, ow=None, cb=None)
    if res & 1:
        c_ow = st(a, 135)
        ow = dict(chance=c_ow, ran=False, r=None, won=False)
        if c_ow > 0:
            ro = draw("A", "open wounds", 100)
            ow.update(ran=True, r=ro, won=ro < c_ow)
            if ow["won"]:
                L = max(st(a, 12), 1)
                band = 0 if L < 2 else (L - 1) * 9 if L <= 15 else 126 + (L - 15) * 18 if L <= 30 else \
                    396 + (L - 30) * 27 if L <= 45 else 801 + (L - 45) * 36 if L <= 60 else 1341 + (L - 60) * 45
                dmg = band + 40
                ow.update(L=L, band=band, dmg=dmg)
        dl["ow"] = ow
        c_cb = st(a, 136)
        cb = dict(chance=c_cb, ran=False, r=None, won=False, life_before=life)
        if c_cb > 0:
            rc2 = draw("A", "crushing blow", 100)
            cb.update(ran=True, r=rc2, won=rc2 < c_cb)
            if cb["won"]:
                k = 4                                 # a normal monster, one player: no player-count term
                share = combat.tdiv(life, k)
                life = max(life - share, 0)
                cb.update(k=k, share=share, life_after=life)
        dl["cb"] = cb
        total = final
        take = min(final, life)
        hp = life - total
        life = 0 if hp < 256 else hp
        dl.update(total=total, take=take, life_end=life)
    tr["dl"] = dl
    tr["sa"], tr["sd"] = sa, sd
    return tr


def pts(v):
    """Life or damage in 1/256 units as points with two decimals (256 units are one point)."""
    return "%d.%02d" % (v // 256, (v % 256) * 100 // 256)


def build(seed, dseed, theme):
    tr = run(seed, dseed)
    th, df, ph, cr, rb, dl = tr["th"], tr["df"], tr["ph"], tr["cr"], tr["rb"], tr["dl"]
    k = K.Kit(W, H, theme)
    frames, caps = [], []
    nA = sum(1 for x in tr["draws"] if x[0] == "A")
    nD = sum(1 for x in tr["draws"] if x[0] == "D")
    shown = []                                        # the draws shown so far, for the two columns

    def header(s):
        k.text(20, 12, s, "acc", 2, True)

    def stepper(cur):
        for i, n in enumerate(STEPS):
            k.box(20 + i * 232, 40, 222, 30, [n], "cur" if i == cur else "panel", "acc" if i == cur else "dim",
                  "txt" if i <= cur else "dim", 2, bold=(i == cur))

    def upto(label):
        """How many draws are made up to and with the one named label."""
        return [i for i, d_ in enumerate(tr["draws"]) if d_[1] == label][0] + 1

    def columns(upto, y0=300, last=5):
        """The draws so far (the newest `last` of each seed), one column per seed, newest highlighted."""
        k.text(20, y0, "ATTACKER SEED DRAWS", "dim", 2)
        k.text(500, y0, "DEFENDER SEED DRAWS", "dim", 2)
        ya = yd = y0 + 26
        for j, (who, label, n, v, _s) in enumerate(tr["draws"][:upto]):
            if sum(1 for q in tr["draws"][j + 1:upto] if q[0] == who) >= last:
                continue
            cur = j == upto - 1
            x = 20 if who == "A" else 500
            y = ya if who == "A" else yd
            k.rect(x, y, 440, 22, "cur" if cur else "panel")
            k.text(x + 6, y + 4, "%d %s: RANGE(%d) = %d" % (j + 1, label.upper(), n, v), "txt" if cur else "dim", 2, cur)
            if who == "A":
                ya += 26
            else:
                yd += 26

    # ---- inputs
    header("ONE MELEE HIT: A TOY ATTACKER AND A TOY MONSTER")
    stepper(-1)
    k.text(20, 90, "ATTACKER: A PLAYER, ONE-HANDED WEAPON", "txt", 2, True)
    for i, ln in enumerate(("LEVEL %d, STRENGTH %d, DEXTERITY %d" % (ATT[12], ATT[0], ATT[2]),
                            "ATTACK RATING BONUS %d, DAMAGE %d TO %d, +%d PERCENT" % (ATT[19], ATT[21], ATT[22], ATT[25]),
                            "OPEN WOUNDS %d, CRUSHING BLOW %d, DEADLY STRIKE %d PERCENT" % (ATT[135], ATT[136], ATT[141]),
                            "SEED %08X : %08X" % (seed, HIGH))):
        k.text(40, 120 + i * 28, ln, "txt" if i < 3 else "acc", 2, i == 3)
    k.text(20, 248, "DEFENDER: A MONSTER", "txt", 2, True)
    for i, ln in enumerate(("LEVEL %d, DEFENCE %d, BLOCK %d PERCENT, LIFE %d" % (DEF[12], DEF[31] + DEF[2] // 4, DEF[20],
                                                                                 DEF[6] // 256),
                            "SEED %08X : %08X" % (dseed, HIGH))):
        k.text(40, 278 + i * 28, ln, "txt" if i == 0 else "acc", 2, i == 1)
    k.text(20, 350, "ALL NUMBERS ARE TOY INPUTS, NOT TABLE VALUES", "dim", 2)
    k.text(20, 376, "THE DEFENDER HAS NO DODGE, AVOID, RESISTANCE OR REDUCTION", "dim", 2)
    k.caption("One swing of a toy player at a toy monster, with its draws on each seed in order: to-hit, block, "
              "build, delivery.", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="A toy player attacks a toy monster once; the attacker's seed is {%d:%d} and the defender's {%d:%d} (illustrative)." % (
            seed, HIGH, dseed, HIGH),
        calc=["Attacker stats (illustrative): level %d, strength %d, dexterity %d, stat 19 %d, damage %d to %d, stat 25 %d, "
              "stat 135 %d, stat 136 %d, stat 141 %d." % (ATT[12], ATT[0], ATT[2], ATT[19], ATT[21], ATT[22], ATT[25],
                                                          ATT[135], ATT[136], ATT[141]),
              "Defender stats (illustrative): level %d, stat 31 %d, stat 2 %d, block stat 20 %d, life %d; stats 338, 340 and 348 "
              "are 0, so no avoidance draw." % (DEF[12], DEF[31], DEF[2], DEF[20], DEF[6] // 256)]))

    # ---- to-hit
    header("TO-HIT: THE CHANCE C")
    stepper(0)
    y = 86
    rows = [("DEFENCE = %d + %d / 4" % (th["def_base"], th["def_dex"]), "%d" % th["defense"]),
            ("AR = (%d - 7) * 5 + %d + %d" % (th["dex"], th["s19"], th["factor"]), "%d" % th["ar"]),
            ("C = 100 * %d / (%d + %d)" % (th["ar"], th["ar"], th["defense"]), "%d" % th["c1"]),
            ("C = %d * %d * 2 / (%d + %d)" % (th["c1"], th["alvl"], th["alvl"], th["dlvl"]), "%d" % th["c2"]),
            ("CLAMPED TO 5..95", "%d" % th["c"])]
    for lab, val in rows:
        k.rect(40, y, 880, 36, "panel")
        k.outline(40, y, 880, 36, "dim")
        k.text(52, y + 11, lab, "txt", 2)
        k.text(910 - K.text_w(val, 2), y + 11, val, "acc", 2, True)
        y += 42
    k.text(40, y + 12, "CHANCE TO HIT C = %d PERCENT" % th["c"], "txt", 3, True)
    k.text(40, y + 52, "LEVELS: ATTACKER %d, DEFENDER %d" % (th["alvl"], th["dlvl"]), "dim", 2)
    k.caption("The chance is 100 * AR / (AR + defence), scaled by the two levels and kept to 5..95: here %d percent "
              "(to-hit A)." % th["c"], CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The chance to hit is %d percent: attack rating %d against defence %d, levels %d and %d." % (
            th["c"], th["ar"], th["defense"], th["alvl"], th["dlvl"]),
        calc=["to-hit.md A1, B1: DEF = stat 31 + stat 2 / 4 = %d + %d / 4 = %d (no percent terms)." % (th["def_base"], th["def_dex"], th["defense"]),
              "to-hit.md A2: AR = (stat 2 - 7) * 5 + stat 19 + the class's ToHitFactor = (%d - 7) * 5 + %d + %d = %d; pct = 0, so A3 keeps "
              "AR = %d." % (th["dex"], th["s19"], th["factor"], th["ar0"], th["ar"]),
              "to-hit.md A5: c = 100 * AR / (AR + DEF) = %d; c = c * alvl * 2 / (alvl + dlvl) = %d; clamped to 5..95: %d." % (
                  th["c1"], th["c2"], th["c"])]))

    # ---- the to-hit draw
    shown = 1
    header("TO-HIT: DRAW 1, ON THE ATTACKER'S SEED")
    stepper(0)
    k.box(40, 86, 400, 90, [("RANGE(100)", "dim"), (str(th["r"]), "acc")], "panel", "dim", "txt", 3, bold=True)
    k.text(470, 96, "R = %d  %s  C = %d" % (th["r"], "<" if th["hit"] else ">=", th["c"]), "txt", 3, True)
    k.text(470, 140, "A HIT" if th["hit"] else "A MISS", "good" if th["hit"] else "bad", 3, True)
    k.bar(40, 200, 880, 18, th["c"], 100, "good", "grey")
    k.rect(40 + min(878, th["r"] * 880 // 100) - 1, 192, 3, 34, "txt")
    k.text(40, 228, "0", "dim", 2)
    k.text(40 + 880 - K.text_w("99", 2), 228, "99", "dim", 2)
    columns(1, 270)
    k.caption("The to-hit draw is %d of 0..99; below %d is a hit: %s (to-hit A6)." % (
        th["r"], th["c"], "a hit, so the monster's defence rolls follow" if th["hit"] else
        "a miss, so no defence roll is made, but the damage is still built"), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The to-hit draw is %d, %s %d: %s." % (th["r"], "below" if th["hit"] else "not below", th["c"],
                                                  "a hit" if th["hit"] else "a miss"),
        calc=["to-hit.md A6: r = Range(att.seed, 100) = %d (draw 1 on the attacker's seed); seed = {%d:%d}." % (
            th["r"], tr["draws"][0][4][0], tr["draws"][0][4][1]),
              "to-hit.md A6: r %s c = %d: %s." % ("<" if th["hit"] else ">=", th["c"], "hit" if th["hit"] else "miss")]))

    # ---- block
    header("BLOCK: THE DEFENDER'S SEED, ON A HIT ONLY")
    stepper(1)
    di = [d_ for d_ in tr["draws"] if d_[0] == "D"]
    if df["ran"]:
        k.text(40, 86, "BLOCK CHANCE B = STAT 20 = %d, CAPPED AT 75: %d" % (DEF[20], df["b"]), "txt", 2, True)
        k.box(40, 120, 400, 90, [("RANGE(100)", "dim"), (str(df["r"]), "acc")], "panel", "dim", "txt", 3, bold=True)
        k.text(470, 130, "R = %d  %s  B = %d" % (df["r"], "<" if df["blocked"] else ">=", df["b"]), "txt", 3, True)
        k.text(470, 174, "BLOCKED: NO HIT" if df["blocked"] else "NOT BLOCKED: THE HIT STANDS",
               "bad" if df["blocked"] else "good", 2, True)
        k.text(40, 230, "THEN THE AVOIDANCE ROLLS: NONE, THE CHANCES ARE 0 (NO DRAW)", "dim", 2)
    else:
        k.text(40, 96, "A MISS: NO BLOCK ROLL, NO DRAW ON THE DEFENDER'S SEED", "txt", 2, True)
    columns(len(tr["draws"][:2]) if df["ran"] else 1, 270)
    k.caption(("The monster's block chance is %d percent; the draw is %d, so the hit is %s (to-hit C2, C3)." % (
        df["b"], df["r"], "blocked and does nothing" if df["blocked"] else "not blocked") if df["ran"] else
        "The swing missed, so the defender's seed is not drawn at all (to-hit C1)."), CAP_Y, 76)
    frames.append(k.done())
    if df["ran"]:
        caps.append(dict(
            text="Block: the draw is %d against a chance of %d, so the hit is %s." % (
                df["r"], df["b"], "blocked" if df["blocked"] else "not blocked"),
            calc=["to-hit.md C2: b = BlockChance(monster) = min(stat 20, 75) = %d (the toy monster has NoShldBlock set); b >= 1, so r = Range(def.seed, 100) = %d on the "
                  "defender's seed (draw 1 on it); seed = {%d:%d}." % (df["b"], df["r"], di[0][4][0], di[0][4][1]),
                  "to-hit.md C2: r %s b: %s." % ("<" if df["blocked"] else ">=", "blocked, result 0x10, the hit bit is cleared"
                                       if df["blocked"] else "not blocked"),
                  "to-hit.md C3: stats 340, 348 and 338 are 0 for the toy, so no evade, weapon block or dodge draw."]))
    else:
        caps.append(dict(text="The swing missed, so no defence roll is made.",
                         calc=["to-hit.md C1: the defence rolls run only when the to-hit result has bit 0x1; the defender's seed is not drawn."]))

    # ---- the build: physical
    nb = len(tr["draws"])
    header("BUILD: THE PHYSICAL ROLL, WHATEVER THE TO-HIT GAVE")
    stepper(2)
    rows = [("WEAPON DAMAGE (1/256 UNITS)", "%d TO %d" % (ph["mn"], ph["mx"])),
            ("ED = %d + %d * %d / 100 + %d * %d / 100" % (ph["ed_base"], ATT[0], TOY_WEAPON["sb"], ATT[2], TOY_WEAPON["db"]), "%d" % ph["ed"]),
            ("LO = %d + %d * %d / 100, HI = %d + %d * %d / 100" % (ph["mn"], ph["mn"], ph["ed"], ph["mx"], ph["mx"], ph["ed"]),
             "%d, %d" % (ph["lo"], ph["hi"])),
            ("PHYSICAL = LO + RANGEB(%d)" % (ph["hi"] - ph["lo"]), "%d + %d = %d" % (ph["lo"], ph["x"], ph["phys"]))]
    y = 86
    for lab, val in rows:
        k.rect(40, y, 880, 36, "panel")
        k.outline(40, y, 880, 36, "dim")
        k.text(52, y + 11, lab, "txt", 2)
        k.text(910 - K.text_w(val, 2), y + 11, val, "acc", 2, True)
        y += 42
    k.text(40, y + 8, "= %s POINTS OF PHYSICAL DAMAGE (256 UNITS ARE 1 POINT)" % pts(ph["phys"]), "txt", 2, True)
    columns(upto("physical"), 300)
    k.caption("The attacker builds its damage on a miss too. The roll is the low end plus a draw over the span: %d units, "
              "%s points (damage B1)." % (ph["phys"], pts(ph["phys"])), CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The physical roll: %d units, %s points, from a draw of %d over a span of %d." % (
            ph["phys"], pts(ph["phys"]), ph["x"], ph["hi"] - ph["lo"]),
        calc=["damage.md B1: one-handed: min = stat 21 << 8 = %d, max = stat 22 << 8 = %d." % (ph["mn"], ph["mx"]),
              "damage.md B1: ed = stat 25 + StrBonus * stat 0 / 100 + DexBonus * stat 2 / 100 + mastery = %d + %d + 0 + 0 = %d." % (
                  ph["ed_base"], ph["ed_str"], ph["ed"]),
              "damage.md B1: lo = %d, hi = %d; v = lo + RangeB(att.seed, hi - lo) = %d + %d = %d." % (
                  ph["lo"], ph["hi"], ph["lo"], ph["x"], ph["phys"])]))

    # ---- the build: critical chain and the always-drawn step
    header("BUILD: DEADLY STRIKE, THEN THE DRAW MADE EVERY TIME")
    stepper(2)
    if cr["ran"]:
        k.text(40, 86, "STAT 141 = %d PERCENT: RANGE(100) = %d" % (cr["chance"], cr["r"]), "txt", 2, True)
        k.text(40, 116, "%d %s %d: %s" % (cr["r"], "<" if cr["won"] else ">=", cr["chance"],
                                         "PHYSICAL DOUBLED: %d" % cr["final"] if cr["won"] else "NOT DOUBLED"),
               "good" if cr["won"] else "txt", 2, True)
    else:
        k.text(40, 86, "NO DEADLY STRIKE CHANCE: NO DRAW", "dim", 2)
    k.text(40, 156, "THE ELEMENTS AND POISON: NO DAMAGE RANGE, NO DRAW", "dim", 2)
    k.text(40, 186, "RANGEB(1) IS DRAWN EVERY TIME: RESULT %d" % rb["r"], "txt", 2, True)
    k.text(40, 216, "FINAL PHYSICAL %s POINTS" % pts(cr["final"]), "txt", 2, True)
    columns(upto("burning step"), 260)
    k.caption(("Deadly strike: draw %d against %d percent, %s. " % (cr["r"], cr["chance"], "so the physical damage "
               "doubles" if cr["won"] else "so it does not double") if cr["ran"] else "") +
              "The build always draws RangeB(1) once (damage A, steps 3 and 7).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="Deadly strike draw %d against %d percent: %s; the build then draws RangeB(1) once." % (
            cr["r"], cr["chance"], "physical damage doubles" if cr["won"] else "no doubling"),
        calc=["damage.md A step 3: the chain is the weapon mastery's crit (none for the toy), stat 337 (0, no draw), stat 141 = %d: r = Range(att.seed, "
              "100) = %d: %s." % (cr["chance"], cr["r"], "r < chance, physical doubled to %d" % cr["final"] if cr["won"] else
                                  "r >= chance, no doubling"),
              "damage.md A steps 4 and 6: the four elements and poison have no range (stats 48 to 55, 57, 58 are 0): no draw.",
              "damage.md A step 7: b = RangeB(att.seed, 1) = %d, always one step of the seed." % rb["r"]]))

    # ---- the result word and the delivery
    if dl["ran"]:
        ow, cb = dl["ow"], dl["cb"]
        header("DELIVERY: OPEN WOUNDS, THEN CRUSHING BLOW")
        stepper(3)
        y = 86
        k.rect(40, y, 880, 64, "panel")
        k.outline(40, y, 880, 64, "dim")
        k.text(52, y + 8, "OPEN WOUNDS: STAT 135 = %d PERCENT" % ow["chance"], "txt", 2, True)
        if ow["ran"]:
            s2 = "RANGE(100) = %d: %s" % (ow["r"], "WOUNDED" if ow["won"] else "NOT WOUNDED")
            if ow["won"]:
                s2 += ", STAT 74 = -%d FOR 200 FRAMES" % ow["dmg"]
        else:
            s2 = "NO CHANCE, NO DRAW"
        k.text(52, y + 34, s2, "good" if ow["won"] else "txt", 2, True)
        y += 74
        k.rect(40, y, 880, 90, "panel")
        k.outline(40, y, 880, 90, "dim")
        k.text(52, y + 8, "CRUSHING BLOW: STAT 136 = %d PERCENT" % cb["chance"], "txt", 2, True)
        if cb["ran"]:
            k.text(52, y + 34, "RANGE(100) = %d: %s" % (cb["r"], "CRUSHED" if cb["won"] else "NO CRUSHING BLOW"),
                   "good" if cb["won"] else "txt", 2, True)
            if cb["won"]:
                k.text(52, y + 60, "TAKES %s / %d = %s: LIFE %s POINTS" % (pts(cb["life_before"]), cb["k"], pts(cb["share"]),
                                                                           pts(cb["life_after"])), "txt", 2, True)
        else:
            k.text(52, y + 34, "NO CHANCE, NO DRAW", "dim", 2)
        columns(len(tr["draws"]), 290, 3)
        k.caption("On a hit, open wounds then crushing blow, each drawing on the attacker's seed only when its chance is above "
                  "0 (delivery B3, E1, E2).", CAP_Y, 76)
        frames.append(k.done())
        calc = ["delivery.md B3: the handlers of event 5 run newest first: open wounds (E2), then crushing blow (E1); each reads life before this hit's damage."]
        if ow["ran"]:
            calc.append("delivery.md E2: r = Range(att.seed, 100) = %d against stat 135 = %d: %s%s." % (
                ow["r"], ow["chance"], "applied" if ow["won"] else "not applied",
                "; L = max(stat 12, 1) = %d, dmg = Band(L) + 40 = %d + 40 = %d, state 62 for 200 frames, stat 74 = %d" % (
                    ow["L"], ow["band"], ow["dmg"], -ow["dmg"]) if ow["won"] else ""))
        if cb["ran"]:
            calc.append("delivery.md E1: r = Range(att.seed, 100) = %d against stat 136 = %d: %s%s." % (
                cb["r"], cb["chance"], "applied" if cb["won"] else "not applied",
                "; k = 4 for a normal monster with one player, cb = life / k = %d / %d = %d, life %d" % (
                    cb["life_before"], cb["k"], cb["share"], cb["life_after"]) if cb["won"] else ""))
        caps.append(dict(
            text="Delivery: open wounds draw %s, crushing blow draw %s." % (
                "%d (%s)" % (ow["r"], "applied" if ow["won"] else "not applied") if ow["ran"] else "none",
                "%d (%s)" % (cb["r"], "applied" if cb["won"] else "not applied") if cb["ran"] else "none"),
            calc=calc))
        # life
        header("DELIVERY: THE LIFE CHANGES")
        stepper(3)
        k.text(40, 90, "LIFE BEFORE THE HIT: %s POINTS" % pts(dl["life0"]), "txt", 2, True)
        if cb["won"]:
            k.text(40, 124, "AFTER CRUSHING BLOW: %s POINTS" % pts(cb["life_after"]), "txt", 2, True)
        k.text(40, 158, "THE PACKET'S TOTAL: %s POINTS" % pts(dl["total"]), "txt", 2, True)
        k.text(40, 192, "LIFE = LIFE - TOTAL, 0 BELOW 1 POINT", "dim", 2)
        k.box(40, 230, 880, 70, [("LIFE %s POINTS" % pts(dl["life_end"]), "good")], "cur", "good", "txt", 3, bold=True)
        k.caption("The life change is the life less the packet's total, taken after the stat events, and 0 when the "
                  "result is below one point (delivery B4).", CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(
            text="The monster's life goes from %s to %s points." % (pts(dl["life0"]), pts(dl["life_end"])),
            calc=["delivery.md B3, B4: the stat events saw the life before this hit's damage; then hp = %d - total = %d - %d = %d%s." % (
                cb["life_after"] if cb["won"] else dl["life0"], cb["life_after"] if cb["won"] else dl["life0"],
                dl["total"], (cb["life_after"] if cb["won"] else dl["life0"]) - dl["total"],
                ", set to 0 below 256" if dl["life_end"] == 0 else ""),
                  "total = physical %d (the toy has no other damage and no reduction), life = %d units, %s points." % (
                      dl["total"], dl["life_end"], pts(dl["life_end"]))]))
    else:
        header("DELIVERY: NOTHING IS DELIVERED")
        stepper(3)
        k.text(40, 96, "THE SWING %s" % ("WAS BLOCKED" if tr["res"] == 0x10 else "MISSED"), "bad", 3, True)
        k.text(40, 146, "NO RESULT BIT 0x1: NO OPEN WOUNDS, NO CRUSHING BLOW, NO LIFE CHANGE", "txt", 2, True)
        columns(len(tr["draws"]), 200)
        k.caption("Only a hit with bit 0x1 reaches the delivery, so the stat events draw nothing and the life is unchanged "
                  "(delivery A2, B3).", CAP_Y, 76)
        frames.append(k.done())
        caps.append(dict(text="Nothing is delivered: the swing %s." % ("was blocked" if tr["res"] == 0x10 else "missed"),
                         calc=["delivery.md A2: ApplyDamage runs only when the queued packet's result has bit 0x1."]))
    # ---- the order of the draws
    header("THE DRAWS, IN ORDER")
    k.text(20, 46, "ATTACKER SEED: %d DRAWS" % nA, "txt", 2, True)
    k.text(500, 46, "DEFENDER SEED: %d DRAW%s" % (nD, "" if nD == 1 else "S"), "txt", 2, True)
    ya = yd = 80
    for j, (who, label, n, v, _s) in enumerate(tr["draws"]):
        x = 20 if who == "A" else 500
        y = ya if who == "A" else yd
        k.rect(x, y, 440, 30, "panel")
        k.outline(x, y, 440, 30, "dim")
        k.text(x + 8, y + 8, "%d %s: RANGE(%d) = %d" % (j + 1, label.upper(), n, v), "txt", 2)
        if who == "A":
            ya += 36
        else:
            yd += 36
    k.text(500, yd + 10, "NOT DRAWN: DODGE, AVOID,", "dim", 2)
    k.text(500, yd + 36, "EVADE, WEAPON BLOCK", "dim", 2)
    k.caption("The swing's draws in order: to-hit, block, the build, then the stat events on a hit (to-hit C, damage A, "
              "delivery B).", CAP_Y, 76)
    frames.append(k.done())
    caps.append(dict(
        text="The attacker's seed drew %d times and the defender's %d time%s; the attacker's seed ends at {%d:%d}." % (
            nA, nD, "" if nD == 1 else "s", tr["sa"][0], tr["sa"][1]),
        calc=["order: %s." % ", ".join("%d %s (%s)" % (j + 1, d_[1], "attacker" if d_[0] == "A" else "defender")
                                       for j, d_ in enumerate(tr["draws"])),
              "attacker seed after = {%d:%d}; defender seed after = {%d:%d}." % (
                  tr["sa"][0], tr["sa"][1], tr["sd"][0], tr["sd"][1])]))
    return frames, caps, k.pal, tr


def main(argv):
    argv = list(argv)
    if "--schematic" in argv:
        argv.remove("--schematic")
    targs = list(argv[1:])
    if "--out" in targs:
        del targs[targs.index("--out"):targs.index("--out") + 2]
    opts = {"--seed": "0xc0ffee", "--dseed": "12345", "--theme": "dark", "--out": None}
    for o in opts:
        if o in argv:
            i = argv.index(o)
            opts[o] = argv[i + 1]
            del argv[i:i + 2]
    if len(argv) != 1 or opts["--theme"] not in K.THEMES:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        seed, dseed = int(opts["--seed"], 0), int(opts["--dseed"], 0)
    except ValueError:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if not (0 < seed <= 0xFFFFFFFF and 0 < dseed <= 0xFFFFFFFF):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    out = opts["--out"] or os.path.join(HERE, "..", "workspace", "render", "anim",
                                        "combat-%x-%x-schematic" % (seed, dseed))
    out = anim_common.safe_out(out)
    os.makedirs(out, exist_ok=True)
    frames, caps, _pal, _tr = build(seed, dseed, opts["--theme"])
    K.write_illustration(out, "combat", frames, caps, W, H, K.palette(opts["--theme"])[1], "melee hit animation", HELP,
                         targs)
    print("%d frames -> %s" % (len(frames), out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

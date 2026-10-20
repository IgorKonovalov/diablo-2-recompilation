"""Scripted harness sessions for plan 0037 Phase 2 (combat formulas): one game per session on one slot, logged by
tools/gdb/combat.gdb, driven by tools/d2pilot.py (Teleport on Shift + left, Attack on the right button for the
melee characters; Nova for the immune-monster session).

Usage:
  python3 -I tools/combat_sessions.py list
  python3 -I tools/combat_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]
  python3 -I tools/combat_sessions.py check [SESSION ...]   # dry check, no game: plan 0047's cases (default) or these

Each SESSION names a row of SESSIONS below: the save (built from tools/d2s_recipes/<recipe>.json with tools/d2s.py
build into --saves), the difficulty steps file, the map seed, and the tools/d2pilot.py commands run in order (each
with a time limit). The log goes to workspace/logs/combat/<RUN>-<SESSION>.log. The slot is stopped after each session
(tools/slots.py stop N) and its saves directory returned to the TAG aside, so every session starts from the built
save. A step is (pilot args, timeout[, level]) (skipped when the player already stands in that level) or ("keys",
[key, ...], seconds) (tools/xdrive.py key presses, e.g. "r", the run/walk toggle). Nothing here feeds a model.

`check` (plan 0047 Phase 1) runs tools/session_check.py on every case of CASES_0047 and lists the cases that cannot be
staged (UNSTAGED_0047) with the reason: each save is built from its recipe into a temporary directory (sha256 against
tools/test_d2s.py), the stats a case needs are summed over the built save's equipped items, the steps file and every
d2pilot.py option are checked. No game, no slot.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]

MELEE = ["--melee-button", "3", "--melee-hold", "2.5", "--radius", "9", "--max-res", "1000", "--mana-col", "4",
         "--drink", "0.5", "--give-up", "8"]
SWEEP = ["farm", "--sweep"] + MELEE
NOVA = ["--nova-key", "F2", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6"]
CLASSIC_WP = ["--wp-tab-x0", "120", "--wp-tab-w", "78"]


def andariel(extra=(), first=(), guard=False):
    """With guard (resume lane), two more descend steps, each skipped once the player is in level 37."""
    if not guard:
        return [(SWEEP + ["--wp", "1,9", "--descend", "18", "--time", "20"] + list(first) + list(extra), 260),
                (SWEEP + ["--descend", "18", "--time", "20"] + list(extra), 220),
                (["hunt", "--mon-cls", "156", "--time", "240"] + MELEE + list(extra), 270)]
    down = SWEEP + ["--descend", "18", "--time", "20"] + list(extra)
    return [(SWEEP + ["--wp", "1,9", "--descend", "18", "--time", "20"] + list(first) + list(extra), 260, 37),
            (down, 220, 37), (down, 220, 37), (down, 220, 37),
            (["hunt", "--mon-cls", "156", "--time", "300"] + MELEE + list(extra), 330)]


def andariel_nova():
    """Nova clears the way and hits Andariel; the mercenary meleeing her gives the hireling boss percent."""
    return [(["farm", "--sweep", "--wp", "1,9", "--descend", "18", "--descend-time", "300", "--time", "15",
              "--max-res", "1000"] + NOVA, 380),
            (["farm", "--sweep", "--descend", "18", "--descend-time", "300", "--time", "15", "--max-res", "1000"]
             + NOVA, 360),
            (["hunt", "--mon-cls", "156", "--time", "240"] + NOVA, 270)]


def andariel_es():
    """Resume lane: CombatSorH (poison and all resistances raised, a mercenary in unique gear) takes the warps
    without sweeping, so the mercenary reaches Andariel alive, then Nova and the mercenary on her."""
    es = NOVA + ["--merc-drink", "0.5"]
    down = ["farm", "--descend", "18", "--descend-time", "300", "--time", "1", "--max-res", "1000"]
    # a descend step is skipped once the player stands in Catacombs Level 4 (level 37), so a failed first search
    # costs one retry instead of leaving the hunt a level short
    return [(down[:1] + ["--wp", "1,9"] + down[1:] + es, 380, 37), (down + es, 360, 37), (down + es, 360, 37),
            (down + es, 360, 37), (["hunt", "--mon-cls", "156", "--time", "300"] + es, 330)]


SESSIONS = {
    "sor-n-highlands": ("CombatSor", "enter-normal", 3715, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "sor-nm-highlands": ("CombatSor", "enter-nightmare", 3725, [(SWEEP + ["--wp", "5,2", "--players", "4", "--time", "270"], 340)]),
    "sor-h-andariel-nova": ("CombatSor", "enter-hell", 3737, andariel_nova()),
    "sor-h-andariel-nova2": ("CombatSor", "enter-hell", 3738, andariel_nova()),
    "sor-h-andariel-nova3": ("CombatSor", "enter-hell", 3739, andariel_nova()),
    "sor-nm-andariel-nova": ("CombatSor", "enter-nightmare", 3727, andariel_nova()),
    # no mercenary, /players 8: monsters live longer, so more attacks per kill on both sides
    "solo-n-p8": ("CombatSolo", "enter-normal", 3713, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "270"], 340)]),
    "solo-n2-p8": ("CombatSolo", "enter-normal", 3714, [(SWEEP + ["--wp", "1,3", "--players", "8", "--time", "270"], 340)]),
    "solo-nm-p8": ("CombatSolo", "enter-nightmare", 3723, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "270"], 340)]),
    "solo-nm2-p8": ("CombatSolo", "enter-nightmare", 3724, [(SWEEP + ["--wp", "1,3", "--players", "8", "--time", "270"], 340)]),
    "solo-h-p3": ("CombatSolo", "enter-hell", 3734, [(SWEEP + ["--wp", "1,2", "--players", "3", "--time", "270"], 340)]),
    "solo-h2-p3": ("CombatSolo", "enter-hell", 3735, [(SWEEP + ["--wp", "1,3", "--players", "3", "--time", "270"], 340)]),
    "solo-h3": ("CombatSolo", "enter-hell", 3736, [(SWEEP + ["--wp", "1,4", "--time", "270"], 340)]),
    # resume lane (plan 0037 Phase 2 review ruling (c)): CombatOW melees with open wounds 85 % and crushing blow 40 %;
    # /players 8 keeps Andariel and Eldritch alive for many hits
    "ow-n-andariel-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel2-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel3-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel4-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel5-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel6-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-n-andariel7-p8": ("CombatOW", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True)),
    "ow-nm-andariel-p8": ("CombatOW", "enter-nightmare", 3727, andariel(first=["--players", "8"], guard=True)),
    "ow-n-highlands-p8": ("CombatOW", "enter-normal", 3783, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands2-p8": ("CombatOW", "enter-normal", 3785, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands3-p8": ("CombatOW", "enter-normal", 3786, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-n-highlands4-p8": ("CombatOW", "enter-normal", 3787, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "ow-nm-highlands-p8": ("CombatOW", "enter-nightmare", 3784, [(SWEEP + ["--wp", "5,2", "--players", "8", "--time", "270"], 340)]),
    "sorh-h-andariel": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel2": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel3": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel4": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel5": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel6": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel7": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel8": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel9": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel10": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel11": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    "sorh-h-andariel12": ("CombatSorH", "enter-hell", 3738, andariel_es()),
    # name: (save, steps, seed, [(pilot args, timeout s)])
    "sor-n-plains": ("CombatSor", "enter-normal", 3711, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-n-andariel": ("CombatSor", "enter-normal", 3712, andariel()),
    "sor-nm-plains": ("CombatSor", "enter-nightmare", 3721, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-nm-andariel": ("CombatSor", "enter-nightmare", 3722, andariel()),
    "sor-h-plains": ("CombatSor", "enter-hell", 3731, [(SWEEP + ["--wp", "1,2", "--time", "260"], 330)]),
    "sor-h-andariel": ("CombatSor", "enter-hell", 3732, andariel()),
    "sor-h-highlands": ("CombatSor", "enter-hell", 3733, [(SWEEP + ["--wp", "5,2", "--time", "260"], 330)]),
    "sor-n-p8": ("CombatSor", "enter-normal", 3741, [(SWEEP + ["--wp", "1,2", "--players", "8", "--time", "260"], 340)]),
    "sor-n-p2": ("CombatSor", "enter-normal", 3742, [(SWEEP + ["--wp", "1,3", "--players", "2", "--time", "200"], 270)]),
    "nova-h-immune": ("CombatSor", "enter-hell", 3751,
                      [(["farm", "--sweep", "--wp", "5,2", "--time", "200", "--max-res", "1000"] + NOVA, 270)]),
    "cls-nm-plains": ("CombatCls", "enter-nightmare", 3761,
                      [(SWEEP + ["--wp", "1,2", "--time", "240"] + CLASSIC_WP, 310)]),
    "cls-h-plains": ("CombatCls", "enter-hell", 3762, [(SWEEP + ["--wp", "1,2", "--time", "240"] + CLASSIC_WP, 310)]),
    "bar-n-plains": ("CombatBar", "enter-normal", 3771,
                     [(["farm", "--wp", "1,2", "--time", "1"], 60),
                      (["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--hops", "120",
                        "--drink", "0.5"], 300)]),
}

# ---- plan 0047 Phase 1: the shortfalls of run:2026-10-16-combat (sessions written and dry-checked, not run)
FARM = ["farm"] + MELEE                       # bosses: the unique and champion flags first (no --sweep)
WALKM = ["explore", "--walk", "--melee", "--melee-hold", "1.2", "--radius", "9", "--drink", "0.5"]
WALK = ["explore", "--walk", "--drink", "0.5"]
for k, wp in enumerate(("1,2", "1,3", "1,4", "1,5", "5,2", "5,3")):
    # crushing blow on champions (type flag 0x04 without 0x08): CombatOW's 40 % in Nightmare, /players 8
    SESSIONS["ow-nm-champs%d" % (k + 1)] = ("CombatOW", "enter-nightmare", 4701 + k,
                                            [(SWEEP + ["--wp", wp, "--players", "8", "--time", "270"], 340)])
    # plan 0047 Phase 2: --sweep (bosses and champions first, then the level), since without it farm ended once the
    # first unique was down (ow-nm-champs1: 134 s, 21 monsters seen, no champion)
for name, wp, seed in (("darkwood", "1,4", 4711), ("lostcity", "2,6", 4712), ("marsh", "1,5", 4713),
                       ("oasis", "2,5", 4714), ("catacombs", "1,9", 4715)):
    # the cold and lightning caps: CombatSorH's resistances (The Ward, Rockstopper, Mara's) above 75 in Normal, where
    # no difficulty penalty applies; cold attackers in the Dark Wood and the Lost City, lightning in the Black Marsh,
    # the Far Oasis and the Catacombs
    SESSIONS["sorh-n-" + name] = ("CombatSorH", "enter-normal", seed,
                                  [(SWEEP + ["--wp", wp, "--players", "8", "--time", "270"], 340)])
for name, wp, seed in (("upperk", "3,7", 4716), ("travincal", "3,8", 4717), ("spider", "3,2", 4718),
                       ("cityd", "4,2", 4719)):
    # plan 0047 Phase 2: the Dark Wood's cold rows (fallen2, quillrat2) and the Black Marsh's lightning row (goatman2)
    # have an empty El1Pct, so they never add the element; levels whose MonStats rows add it (El1Pct > 0): cold in
    # Upper Kurast (cantor2 55) and Travincal (cantor3 65, vampire2 65), lightning in the Spider Forest (batdemon2 70)
    # and the City of the Damned (bighead5 100, batdemon5 85)
    SESSIONS["sorh-n-" + name] = ("CombatSorH", "enter-normal", seed,
                                  [(SWEEP + ["--wp", wp, "--players", "8", "--time", "270"], 340)])
for name, wp, seed in (("travincal2", "3,8", 4791), ("travincal3", "3,8", 4792), ("catacombs2", "1,9", 4793),
                       ("catacombs3", "1,9", 4794)):
    # plan 0047 Phase 2: Levels picks NumMon (3) of a level's rows per game, so only levels whose every row adds the
    # element give hits on every seed: Travincal (cantor3, cantor3, vampire2: cold) and the Catacombs Level 2
    # (bighead2 among 3 rows of 3: lightning); the Lost City drew sandleaper3, zombie5, slinger6 on seed 4712, and
    # wp 3,2 is the Spider Forest (76), not the Spider Cave (84) whose row batdemon2 was meant
    SESSIONS["sorh-n-" + name] = ("CombatSorH", "enter-normal", seed,
                                  [(SWEEP + ["--wp", wp, "--players", "8", "--time", "270"], 340)])
for k in range(6):                            # 4-6: plan 0047 Phase 2, ruling 3 (d) (up to six seeds)
    # magic immunity: CombatSorH's Ginther's Rift (magic damage) on the Lost City's Plague Bearers (zombie5, Hell
    # ResMa 100), Hell
    SESSIONS["sorh-h-lostcity%d" % (k + 1)] = ("CombatSorH", "enter-hell", 4721 + k,
                                               [(SWEEP + ["--wp", "2,6", "--time", "270"], 340)])
for name, wp, seed in (("plains", "1,2", 4731), ("darkwood", "1,4", 4732), ("marsh", "1,5", 4733)):
    # fields driven negative by DR and MDR (the negative total) and percent absorb on a negative field (Dwarf Star
    # fire 15 %, Raven Frost cold 20 %): CombatDR against Normal Act I monsters, one player
    SESSIONS["dr-n-" + name] = ("CombatDR", "enter-normal", seed, [(SWEEP + ["--wp", wp, "--time", "270"], 340)])
for name, steps, wp, seed in (("n-plains", "enter-normal", "1,2", 4741), ("n-darkwood", "enter-normal", "1,4", 4742),
                              ("n-marsh", "enter-normal", "1,5", 4743), ("nm-marsh", "enter-nightmare", "1,5", 4744)):
    # flat absorb (fire 15 Hellmouth, cold 11 Spirit Ward, lightning 20 + 20 Blackhorn's Face and Thudergod's Vigor);
    # Nightmare for fields larger than the absorb
    SESSIONS["abs-" + name] = ("CombatAbs", steps, seed, [(SWEEP + ["--wp", wp, "--time", "270"], 340)])
for name, steps, seed in (("n-plains", "enter-normal", 4751), ("nm-plains", "enter-nightmare", 4752)):
    # freeze (stat 134: Frostwind's 4), the stat event 14 handler and COMBAT_ApplyFreeze
    SESSIONS["frz-" + name] = ("CombatFrz", steps, seed, [(SWEEP + ["--wp", "1,2", "--time", "270"], 340)])
# dodge (melee) and avoid (missiles) standing, evade moving (mode 3 running, then mode 2 walking after the run/walk
# toggle), and the walking player's block (mode 2 keeps the full chance): CombatAma, Normal, /players 8
SESSIONS["ama-n-stand"] = ("CombatAma", "enter-normal", 4761,
                           [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90),
                            (WALKM + ["--hops", "120"], 400)])
SESSIONS["ama-n-run"] = ("CombatAma", "enter-normal", 4762,
                         [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90), (WALK + ["--hops", "150"], 400)])
SESSIONS["ama-n-walk"] = ("CombatAma", "enter-normal", 4763,
                          [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90), ("keys", ["r"], 1.0),
                           (WALK + ["--hops", "150"], 500)])
SESSIONS["ama-n-walk2"] = ("CombatAma", "enter-normal", 4764,
                           [(["farm", "--wp", "1,3", "--players", "8", "--time", "1"], 90), ("keys", ["r"], 1.0),
                            (WALK + ["--hops", "150"], 500)])
# plan 0047 Phase 2: dodge and avoid roll only for a player outside modes 2 and 3 (COMBAT_AvoidRoll), and the
# walking explore of ama-n-stand kept her moving (3 dodge and 8 avoid rolls); these sessions walk into a pack
# (explore without --melee), then stand still ("wait") while the pack attacks
for k, wp in enumerate(("1,2", "1,3", "1,4")):
    SESSIONS["ama-n-idle%d" % (k + 1)] = ("CombatAma", "enter-normal", 4765 + k,
                                          [(["farm", "--wp", wp, "--players", "8", "--time", "1"], 90),
                                           (WALK + ["--hops", "25"], 200), ("wait", 90),
                                           (WALK + ["--hops", "15"], 150), ("wait", 90),
                                           (WALK + ["--hops", "15"], 150), ("wait", 90)])
# plan 0047 Phase 2: CombatAma (level 85, dexterity 400, defence above 1 000) was hit at the to-hit floor (c = 5 in
# every logged roll of ama-n-stand, ama-n-walk and ama-n-idle1), and every defence roll needs a hit first; CombatAmaD
# (level 5, dexterity 15, no shield, no armour: no block roll ahead of dodge) and CombatAmaW (level 5, dexterity 60,
# Pelta Lunata only, level 2: the walking block; Steelclash's level 17 left it unusable, block 0 in the first
# amaw-n-walk, kept as workspace/logs/combat/dev-p47h-amaw-n-walk-steelclash.log) give Normal monsters a chance well
# above the floor
for k, wp in enumerate(("1,2", "1,3", "1,4")):
    SESSIONS["amad-n-idle%d" % (k + 1)] = ("CombatAmaD", "enter-normal", 4795 + k,
                                           [(["farm", "--wp", wp, "--players", "8", "--time", "1"], 90),
                                            (WALK + ["--hops", "25"], 200), ("wait", 90),
                                            (WALK + ["--hops", "15"], 150), ("wait", 90),
                                            (WALK + ["--hops", "15"], 150), ("wait", 90)])
SESSIONS["amad-n-run"] = ("CombatAmaD", "enter-normal", 4798,
                          [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90), (WALK + ["--hops", "150"], 400)])
# ruling 3 (a)'s one more walking session: the walk toggle held, Stony Field's archers and shamans (ranged)
SESSIONS["amaw-n-walk"] = ("CombatAmaW", "enter-normal", 4799,
                           [(["farm", "--wp", "1,3", "--players", "8", "--time", "1"], 90), ("keys", ["r"], 1.0),
                            (WALK + ["--hops", "150"], 500)])
# weapon block: two claws (CombatAss) and one claw with an empty left hand (CombatAssO), standing in melee; the
# skill check 0x0064F380 (WBS) is a value oracle and tells which weapon class it wants
SESSIONS["ass-n-plains"] = ("CombatAss", "enter-normal", 4771,
                            [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90), (WALKM + ["--hops", "120"], 400)])
SESSIONS["ass-n-plains2"] = ("CombatAss", "enter-normal", 4772,
                             [(["farm", "--wp", "1,3", "--players", "8", "--time", "1"], 90), (WALKM + ["--hops", "120"], 400)])
SESSIONS["ass-n-plains3"] = ("CombatAss", "enter-normal", 4774,          # plan 0047 Phase 2: weapon block at 29
                             [(["farm", "--wp", "1,4", "--players", "8", "--time", "1"], 90), (WALKM + ["--hops", "120"], 400)])
SESSIONS["asso-n-plains"] = ("CombatAssO", "enter-normal", 4773,
                             [(["farm", "--wp", "1,2", "--players", "8", "--time", "1"], 90), (WALKM + ["--hops", "120"], 400)])
# the set-aside Fleshripper session re-staged (the plan 0037 resume lane's log was lost with its scratch):
# CombatOWF is commit 5871b00's CombatOW recipe (Fleshripper, Dracul's Grasp) renamed, at the first session's seed
SESSIONS["owf-n-andariel-p8"] = ("CombatOWF", "enter-normal", 3712, andariel(first=["--players", "8"], guard=True))

# stat ids the cases read (tbl:ItemStatCost.txt:ID): resistances 39 fire, 41 lightning, 43 cold, 37 magic; DR 34,
# MDR 35; absorb percent 142 fire, 144 lightning, 148 cold; flat 143, 145, 149; 134 freeze, 136 crushing blow,
# 52/53 magic damage
CASES_0047 = {
    "C1 crushing blow on champions": ("CombatOW in Nightmare, bosses first (the champion flag), /players 8",
                                      ["ow-nm-champs%d" % k for k in range(1, 7)], [136], ()),
    "C2 cold cap (cold resistance above 75)": ("CombatSorH in Normal (no penalty), cold attackers",
                                               ["sorh-n-darkwood", "sorh-n-lostcity", "sorh-n-upperk", "sorh-n-travincal",
                                                "sorh-n-travincal2", "sorh-n-travincal3"],
                                               [43, 41], ()),
    "C3 lightning cap": ("CombatSorH in Normal, lightning attackers",
                         ["sorh-n-marsh", "sorh-n-oasis", "sorh-n-catacombs", "sorh-n-spider", "sorh-n-cityd",
                          "sorh-n-catacombs2", "sorh-n-catacombs3"],
                         [41], ()),
    "C5 magic immunity": ("CombatSorH's magic damage on Hell Plague Bearers (ResMa(H) 100)",
                          ["sorh-h-lostcity%d" % k for k in range(1, 7)], [52, 53], ()),
    "C6 negative absorbed amount": ("CombatDR: MDR above the field, then percent absorb on the negative field",
                                    ["dr-n-plains", "dr-n-darkwood"], [35, 142, 148], ()),
    "C7 negative total, life unchanged": ("CombatDR: DR and MDR above every field of weak Normal hits",
                                         ["dr-n-plains", "dr-n-darkwood", "dr-n-marsh"], [34, 35], ()),
    "C8 evade": ("CombatAma moving (running, then walking)", ["ama-n-run", "ama-n-walk", "ama-n-walk2", "amad-n-run"], [],
                 ("Evade",)),
    "C9 weapon block": ("CombatAss with two claws, CombatAssO with one (the weapon class the skill check wants)",
                        ["ass-n-plains", "ass-n-plains2", "ass-n-plains3", "asso-n-plains"], [], ("Weapon Block",)),
    "C10 dodge": ("CombatAma standing in melee", ["ama-n-stand", "ama-n-idle1", "ama-n-idle2", "ama-n-idle3", "amad-n-idle1",
                                                    "amad-n-idle2", "amad-n-idle3"], [],
                  ("Dodge",)),
    "C11 avoid": ("CombatAma standing against missiles (fallen shamans, archers)",
                  ["ama-n-stand", "ama-n-idle1", "ama-n-idle2", "ama-n-idle3", "amad-n-idle1", "amad-n-idle2",
                          "amad-n-idle3"], [], ("Avoid",)),
    "C12 freeze": ("CombatFrz's Frostwind (freeze 4) in melee", ["frz-n-plains", "frz-nm-plains"], [134], ()),
    "C13 flat absorb": ("CombatAbs against fire, cold and lightning attackers",
                        ["abs-n-plains", "abs-n-darkwood", "abs-n-marsh", "abs-nm-marsh"], [143, 145, 149], ()),
    "C14 a walking player's block": ("CombatAma after the run/walk toggle (mode 2), with a shield",
                                     ["ama-n-walk", "ama-n-walk2", "amaw-n-walk"], [20], ()),
    "C15 the set-aside Fleshripper session (backlog 2026-10-17 resume-lane follow (a))":
        ("the log was lost; the session is staged again on the same recipe and seed", ["owf-n-andariel-p8"], [], ()),
}
UNSTAGED_0047 = {
    "C4 magic cap": "no stock source of player magic resistance (stat 37) reaches the 75 cap: no unique, set item, "
                    "affix, runeword, gem, skill or state writes it; the only writer is the crafted Safety Shield "
                    "recipe (cubemain.txt, res-mag 5-10), which tools/d2s.py cannot build with its recipe mods "
                    "(tools/combat_sessions.py check prints this list; the table search is in the plan 0047 log)",
}


def check(names):
    """Dry check (plan 0047 Phase 1): every case's sessions, or the named sessions as one case."""
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import session_check

    def of(n):
        save, steps, seed, cmds = SESSIONS[n]
        return save, steps, [c[0] for c in cmds if c[0] not in ("keys", "wait")]
    if names:
        cases = {"named": ("sessions named on the command line", names, [], ())}
        return session_check.run(cases, {}, of, "combat_sessions")
    return session_check.run(CASES_0047, UNSTAGED_0047, of, "combat_sessions")


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def level_of(path):
    """The level id of the player's last PLR line in a log (None without one)."""
    lid = None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                if line.startswith("PLR "):
                    lid = line.split('"lid":', 1)[1].split(",", 1)[0]
    except OSError:
        return None
    return int(lid) if lid is not None else None


def run_session(name, slot, tag, saves, run):
    save, steps, seed, cmds = SESSIONS[name]
    log = os.path.join("workspace", "logs", "combat", "%s-%s.log" % (run, name))
    out = open(os.path.join(ROOT, "workspace", "logs", "combat", "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
    sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
    drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                 "tools/gdb/combat.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after", "1500",
                                 "--install", tag, os.path.join(saves, save + ".d2s"), "--log", log],
                           cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                           start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 150:
        time.sleep(3)
        try:
            if "PLR " in open(os.path.join(ROOT, log), errors="replace").read():
                break
        except OSError:
            pass
    time.sleep(3)
    os.makedirs(os.path.join(ROOT, "workspace", "logs", "combat", "%s-%s-shots" % (run, name)), exist_ok=True)
    for step in cmds:
        if step[0] == "wait":                 # ("wait", seconds): the game runs, nothing is pressed (plan 0047)
            time.sleep(step[1])
            continue
        if step[0] == "keys":                 # ("keys", [key, ...], seconds): key presses on the slot's display
            for key in step[1]:
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", key], 30)
                time.sleep(step[2])
            continue
        args, timeout = step[0], step[1]
        if len(step) > 2 and level_of(os.path.join(ROOT, log)) == step[2]:
            continue
        sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + args[1:] +
           ["--shots", "workspace/logs/combat/%s-%s-shots" % (run, name)], timeout, out)
    sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
    try:
        drv.wait(30)
    except subprocess.TimeoutExpired:
        pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run", "check"):
        print(__doc__)
        return 2
    if argv[0] == "check":
        bad = [n for n in argv[1:] if n not in SESSIONS]
        if bad:
            print("unknown session(s) %s" % " ".join(bad))
            return 2
        return check(argv[1:])
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-16s %-10s %-16s %d %d step(s)" % (k, v[0], v[1], v[2], len(v[3])))
        return 0
    a = argv[1:]
    opt = {}
    names = []
    k = 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--saves", "--run"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        else:
            names.append(a[k])
            k += 1
    for n in names:
        if n not in SESSIONS:
            print("unknown session %s" % n)
            return 2
    for n in names:
        run_session(n, int(opt["slot"]), opt["tag"], opt["saves"], opt["run"])
    sh(PY + ["tools/saves.py", "--slot", opt["slot"], "restore", opt["tag"]], 60)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

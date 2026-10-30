"""Scripted harness sessions for plan 0046 Phase 2 (the catalogue sample): the sessions of tools/skills_sessions.py's
machinery, with the sessions below added. Same logger (tools/gdb/skills.gdb), same runner.

Usage:
  python3 -I tools/skills_catalogue_sessions.py list
  python3 -I tools/skills_catalogue_sessions.py build --saves DIR
  python3 -I tools/skills_catalogue_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

Families with no tier-A member: the monster skills (8a rows 156-189, 8b rows 190-289, 8c rows 290-338) and the item
callers (batch 10). Monster casters act on their own while the Sorceress (Teleport and Nova, as skills_sessions)
explores; the item family is the Barbarian `SkillsChain` (suffix 443 'of Chain Lightning', att-skill 53, on both
weapons, both rings and the amulet) walking and attacking.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skills_sessions as S  # noqa: E402

S.SAVES["SkillsChain"] = ("skills-chain", "smpbar")
S.SAVES["SkillsSor"] = S.SAVES["SkillsSor"]
for _k in list(S.SAVES):
    if _k not in ("SkillsSor", "SkillsChain"):
        del S.SAVES[_k]
S.SESSIONS.clear()

wp, cast_explore, SOR_KEYS = S.wp, S.cast_explore, S.SOR_KEYS
SESSIONS = S.SESSIONS


def sor(name, steps, seed, wpt, hops=200, t=1500, env=None):
    SESSIONS[name] = ("SkillsSor", steps, seed, [wp(wpt), ("pilot", cast_explore(SOR_KEYS, hops), t)], env or {})


# 8a: act 1 fallen shamans (160 ShamanFire, 181 Resurrect), act 3 fetish shamans (178 FetishInferno)
sor("cat-a1-1", "enter-normal", 5101, "1,3")
sor("cat-a1-2", "enter-normal", 5102, "1,4")
sor("cat-a1-3", "enter-normal", 5109, "1,2")
sor("cat-a1-4", "enter-normal", 5110, "1,2")
sor("cat-a3-1", "enter-normal", 5103, "3,4")
sor("cat-a3-2", "enter-normal", 5104, "3,3")
# 8b / 8c: act 5 imps (282 Imp Inferno, 299 Imp Fire Missile, 322 ImpBolt, 330 Imp Teleport), act 5 others
sor("cat-a5-1", "enter-normal", 5105, "5,2")
sor("cat-a5-2", "enter-normal", 5106, "5,3")
sor("cat-a5-3", "enter-nightmare", 5107, "5,2")
sor("cat-a5-4", "enter-nightmare", 5108, "5,3")
# the item family: the Chain Lightning charm-less item cast (att-skill 53) from the weapons, rings and amulet
for k, w in enumerate(("1,2", "1,3", "1,4")):
    SESSIONS["cat-chain-%d" % (k + 1)] = ("SkillsChain", "enter-normal", 5111 + k,
                                          [wp(w), ("pilot", cast_explore(["F1"], 200, walk=True), 1500)], {})


# --- the Baal Tentacle cast (plan 0046 Phase 1 batch 8c, do 140; Baal, 'baalcrab', is the only stock user of row 315):
# plan 0038 H6d's route to Baal (tools/h6d_sessions.py baal(): Worldstone Keep 2 waypoint by `farm --wp 5,9`, the two Baal Temple Down
# warps, the five waves, the Worldstone Chamber portal, the hunt for class 544) on this module's character and logger.
# An "until" step (tools/skills_sessions.py, added for this run) repeats a pilot command until the player's level is
# the one given (as h6d_sessions).
NOVA = ["--nova-key", "F1", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6",
        "--max-res", "1000"]


DOWN = ["farm", "--sweep", "--descend", "86,87", "--descend-time", "240", "--time", "5"] + NOVA
SESSIONS["cat-baal-1"] = ("SkillsSor", "enter-normal", 5121, [
    ("pilot", ["farm", "--wp", "5,9", "--time", "1"], 120),
    ("until", (130, DOWN, 300, 5), 0),
    ("until", (131, DOWN, 300, 5), 0),
    ("pilot", ["farm", "--sweep", "--time", "420", "--chase", "30"] + NOVA, 460),
    ("until", (132, ["objop", "--obj-cls", "563", "--times", "1", "--done", "RRESEED", "--time", "120"] + NOVA, 150, 3), 0),
    ("pilot", ["hunt", "--mon-cls", "544", "--time", "420"] + NOVA, 450)], {"SKILLS_WIN": "4"})


if __name__ == "__main__":
    sys.exit(S.main(sys.argv[1:]))

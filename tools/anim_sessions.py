"""Scripted harness sessions for plan 0050 Phase 2 (animation and frame timing): the character recipes (tool-built,
stock rate items, ADR-0013 § Neutral) and one game per session on one slot, logged by tools/gdb/anim.gdb, driven by
tools/d2pilot.py.

Usage:
  python3 -I tools/anim_sessions.py recipes                     # write tools/d2s_recipes/anim-<cls>-t<k>.json
  python3 -I tools/anim_sessions.py rates                       # each recipe's rate stats and the lengths they give
  python3 -I tools/anim_sessions.py list
  python3 -I tools/anim_sessions.py build --saves DIR           # every recipe into DIR (tools/d2s.py build)
  python3 -I tools/anim_sessions.py run --slot N --tag TAG --saves DIR --run RUN SESSION [SESSION ...]

The recipes: one per class and rate tier (t0, t1, t2), every rate item a stock magic affix (magicsuffix rows, the
record index d2s.py takes) or a plain base item:
  IAS  weapon suffixes of Alacrity (20) / of Quickness (40), gloves of Readiness (10)
  FCR  rings and amulet of the Apprentice (10 each), circlet of the Magus (20)
  FHR  body armour and belt of Stability (24 each)
  FBR  shield of Blocking (15) / of Deflecting (30)
  FRW  boots of Haste (20) / of Speed (30)
Each class carries two weapon sets (weapon swap, W): set 1 a one-handed weapon with a shield, set 2 another weapon
type. The sessions play Act I Normal at clvl 25 (near the monsters' levels, so their hits land) with Dexterity 100 (a
block chance near 20 %), life 1500; the gh- variants (recipes anim-<cls>-t<k>-gh, saves under DIR/gh/) have life
40, so that the monsters' hits reach GetHitRoll's bands. The belt holds rejuvenation potions, drunk below 70 % life. Hotkeys: F1 Attack, F2 the class's cast skill, F3 Kick, F4 Throw (a throwing weapon in set 1) or the second
cast skill, F5 the class's sequence skill (if any).

A session (SESSIONS row): the save, the difficulty steps file, the game seed and the steps; ("pilot", [args], t) runs
one tools/d2pilot.py command, ("keys", [key, ...], s) presses keys s seconds apart, ("wait", s), ("hold", key, s)
presses the hotkey and holds the right button s seconds beside the player (back-to-back actions, plan 0050 P1b-1). The log goes to
workspace/logs/anim/<RUN>-<SESSION>.log; the slot is stopped after each session (tools/slots.py stop N) and its saves
directory returned to the TAG aside. Nothing here feeds a model: the pilot only decides where to click.
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = [sys.executable, "-I"]
LOGDIR = os.path.join("workspace", "logs", "anim")
EXCEL = os.path.join("workspace", "merged", "data", "global", "excel")
BASE = os.path.join("workspace", "runtime", "saves-backup", "p0005")
RDIR = os.path.join(HERE, "d2s_recipes")

# magicsuffix record indices (d2s.py: the index in the file without the Expansion row)
# (the rows whose levelreq a clvl 25 character meets: Alacrity 6, Quickness 18, Readiness 15, Apprentice 3, Magus 21,
# Stability 13, Blocking 1, Deflecting 8, Haste 9, Speed 16)
ALACRITY_W, QUICKNESS_W, READINESS_G = 16, 18, 674
APPRENTICE, MAGUS = 173, 174
STABILITY = 263
BLOCKING, DEFLECTING = 171, 172
HASTE, SPEED = 112, 113

# class: (save class, base save, set 1 weapon, set 1 left hand, set 2 weapon, set 2 left, cast, cast2, seq, extra skills)
CLASSES = {
    "ama": ("Amazon", "smpama", "jav", "buc", "sbw", "aqv", "Inner Sight", "Magic Arrow", "Jab", {}),
    "sor": ("Sorceress", "smpsor", "crs", "buc", "lst", None, "Fire Bolt", "Charged Bolt", "Lightning", {}),
    "nec": ("Necromancer", "smpnec", "wnd", "buc", "scy", None, "Teeth", "Amplify Damage", None, {}),
    "pal": ("Paladin", "smppal", "crs", "buc", "spr", None, "Holy Bolt", "Holy Shield", "Sacrifice", {}),
    "bar": ("Barbarian", "smpbar", "tax", "buc", "2hs", None, "Howl", "Shout", "Double Swing", {}),
    "dru": ("Druid", "smpdru", "crs", "buc", "mau", None, "Firestorm", "Molten Boulder", "Arctic Blast", {}),
    "ass": ("Assassin", "smpasn", "ktr", "buc", "tkf", None, "Psychic Hammer", "Fire Trauma", "Fists of Fire", {}),
}
THROWN = {"jav", "tax", "tkf"}


def magic(code, suffix, equip):
    it = {"code": code, "equip": equip}
    if suffix:
        it["suffix"] = suffix
    return it


def recipe(cls, tier, gh=False):
    name, base, w1, l1, w2, l2, cast, cast2, seq, extra = CLASSES[cls]
    ias_w = (None, ALACRITY_W, QUICKNESS_W)[tier]
    items = []
    # thrown weapons and bows take no IAS suffix of their own here (stackable items carry a quantity; bows are not mele)
    items.append(dict(magic(w1, ias_w if w1 not in THROWN else None, "rarm"), **({"quantity": 60} if w1 in THROWN else {})))
    items.append(magic(l1, (None, BLOCKING, DEFLECTING)[tier], "larm"))
    w2s = None if w2 in ("sbw", "tkf") else ias_w
    if w2 == "sbw" and tier:
        w2s = (None, ALACRITY_W, ALACRITY_W)[tier]
    items.append(dict(magic(w2, w2s, "rarm2"), **({"quantity": 60} if w2 in THROWN else {})))
    if l2:
        items.append(dict({"code": l2, "equip": "larm2"}, **({"quantity": 150} if l2 == "aqv" else {})))
    elif w2 in THROWN:
        items.append({"code": "buc", "equip": "larm2"})
    if tier >= 1:
        items += [magic("rin", APPRENTICE, "rrin"), magic("rin", APPRENTICE, "lrin"),
                  magic("qui", STABILITY, "tors"), magic("lbt" if tier == 1 else "vbt", (None, HASTE, SPEED)[tier], "feet")]
    if tier == 2:
        items += [magic("amu", APPRENTICE, "neck"), magic("ci0", MAGUS, "head"), magic("lgl", READINESS_G, "glov"),
                  magic("mbl", STABILITY, "belt")]
    else:
        items.append({"code": "mbl", "equip": "belt"})
    skills = {cast: 1, cast2: 1}
    if seq:
        skills[seq] = 1
    skills.update(extra)
    hot = ["Attack", cast, "Kick", "Throw" if w1 in THROWN else cast2] + ([seq] if seq else [])
    return {
        "game": "expansion", "class": name, "seed": 5000 + 10 * list(CLASSES).index(cls) + tier,
        "name": "Anim%s%d" % (cls.capitalize(), tier), "progression": 15, "difficulty": [131, 131, 131],
        "waypoints": {"normal": "all", "nightmare": "all", "hell": "all"}, "quests": "all",
        "stats": {"strength": 150, "energy": 200, "dexterity": 100, "vitality": 25, "hitpoints": 40 if gh else 1500,
                  "maxhp": 40 if gh else 1500,
                  "mana": 600, "maxmana": 600, "stamina": 120 if tier == 1 else 400,
                  "maxstamina": 120 if tier == 1 else 400, "level": 25, "experience": 2050449},
        "skills": skills, "mouse": {"left": "Attack", "right": cast, "swap_left": "Attack", "swap_right": cast},
        "hotkeys": hot, "belt_fill": ["rvl", "rvl", "rvl", "mp5"], "items": items,
    }


def mon_recipe():
    """the monster-session Sorceress: Teleport (left), Frost Nova F1 (chill: the slowing state), Nova F2, Frozen Orb
    F3 (P1b-12: a delay skill), Lightning F4; life 900 so that Act V Normal and Act II-III fields are survivable."""
    r = recipe("sor", 0)
    r["name"] = "AnimSorMon"
    r["seed"] = 5090
    r["stats"].update({"hitpoints": 900, "maxhp": 900, "vitality": 200, "dexterity": 100, "level": 80,
                       "experience": 742730244, "mana": 1500, "maxmana": 1500})
    r["skills"] = {"Teleport": 1, "Frost Nova": 5, "Nova": 10, "Frozen Orb": 1, "Lightning": 1, "Fire Bolt": 1,
                   "Charged Bolt": 1}
    r["mouse"] = {"left": "Teleport", "right": "Nova", "swap_left": "Teleport", "swap_right": "Nova"}
    r["hotkeys"] = ["Frost Nova", "Nova", "Frozen Orb", "Lightning"]
    return r


# batch 5 (the second lane run): the get-hit variant gh2 and the special recipes of the P1b cases
GH2_SET1 = {"ama": ("wnd", "buc"), "sor": ("tax", "buc"), "nec": ("tax", "buc"), "pal": ("tax", "buc"),
            "bar": ("tax", "buc"), "dru": ("whm", "buc"), "ass": ("tax", "buc")}
GH2_SET2 = {"dru": ("2hs", None)}


def gh2_recipe(cls, tier, life=120, tag="H", seed0=5400):
    """life 120 (Act III Normal hits of about 8-20 reach every GetHitRoll band), set 1 a throwing axe with a buckler
    (Throw by every class but the Amazon, P1b-3), the Amazon's a wand with a buckler (her block with a wand, P1b-8),
    the Druid's a war hammer (one-handed hammer) and in set 2 a two-handed sword (his get-hits, P1b-8)."""
    r = recipe(cls, tier)
    r["name"] = "Anim%s%s%d" % (cls.capitalize(), tag, tier)
    r["seed"] = seed0 + 10 * list(CLASSES).index(cls) + tier
    r["stats"].update({"hitpoints": life, "maxhp": life})
    w1, l1 = GH2_SET1[cls]
    ias_w = (None, ALACRITY_W, QUICKNESS_W)[tier]
    items = [it for it in r["items"] if it["equip"] not in ("rarm", "larm")]
    items.insert(0, magic(l1, (None, BLOCKING, DEFLECTING)[tier], "larm"))
    items.insert(0, dict(magic(w1, None if w1 in THROWN else ias_w, "rarm"), **({"quantity": 60} if w1 in THROWN else {})))
    if cls in GH2_SET2:
        w2, l2 = GH2_SET2[cls]
        items = [it for it in items if it["equip"] not in ("rarm2", "larm2")]
        items.append(magic(w2, ias_w, "rarm2"))
    r["items"] = items
    r["hotkeys"][3] = "Throw" if w1 in THROWN else CLASSES[cls][7]
    return r


def special_recipes():
    """P1b-2 (Burst of Speed, a fast claw), P1b-4/P1b-15 (Charge, Leap Attack at two item-IAS values), P1b-5 (Double
    Swing and Frenzy with two weapons of different speed), P1b-6/P1b-7 (werewolf and werebear: attacks with no weapon
    and with a hammer, the form casts)."""
    out = {}
    r = recipe("ass", 2)                                 # P1b-2: t2 items, Burst of Speed 20, katars of Quickness
    r.update({"name": "AnimAssBos", "seed": 5480})
    r["skills"] = {"Quickness": 20, "Psychic Hammer": 1, "Fire Trauma": 1, "Fists of Fire": 1}
    r["mouse"] = {"left": "Attack", "right": "Quickness", "swap_left": "Attack", "swap_right": "Quickness"}
    r["hotkeys"] = ["Attack", "Quickness", "Kick", "Psychic Hammer", "Fists of Fire"]
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("ktr", QUICKNESS_W, "rarm"), magic("ktr", QUICKNESS_W, "larm"), magic("clw", None, "rarm2")]
    out["anim-ass-bos"] = ("AnimAssBos", r, "smpasn")
    r = recipe("bar", 0)                                 # P1b-5, P1b-4: two weapons of different speed
    r.update({"name": "AnimBarDw", "seed": 5481})
    r["skills"] = {"Double Swing": 1, "Frenzy": 1, "Leap Attack": 1, "Leap": 1, "Howl": 1}
    r["mouse"] = {"left": "Attack", "right": "Frenzy", "swap_left": "Attack", "swap_right": "Frenzy"}
    r["hotkeys"] = ["Attack", "Double Swing", "Frenzy", "Leap Attack", "Kick"]
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("hax", None, "rarm"), magic("scm", None, "larm"),
        magic("hax", QUICKNESS_W, "rarm2"), magic("flc", ALACRITY_W, "larm2")]
    out["anim-bar-dw"] = ("AnimBarDw", r, "smpbar")
    r = recipe("pal", 0)                                 # P1b-4, P1b-15: Charge at two item-IAS values
    r.update({"name": "AnimPalChg", "seed": 5482})
    r["skills"] = {"Charge": 5, "Holy Bolt": 1, "Sacrifice": 1}
    r["mouse"] = {"left": "Attack", "right": "Charge", "swap_left": "Attack", "swap_right": "Charge"}
    r["hotkeys"] = ["Attack", "Charge", "Kick", "Holy Bolt", "Sacrifice"]
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("crs", None, "rarm"), magic("buc", None, "larm"),
        magic("crs", QUICKNESS_W, "rarm2"), magic("buc", None, "larm2")]
    out["anim-pal-chg"] = ("AnimPalChg", r, "smppal")
    r = recipe("dru", 1)                                 # P1b-6, P1b-7: no weapon in set 1, a war hammer in set 2
    r.update({"name": "AnimDruForm", "seed": 5483})
    r["skills"] = {"Wearwolf": 1, "Wearbear": 1, "Shape Shifting": 1, "Firestorm": 1}
    r["mouse"] = {"left": "Attack", "right": "Wearwolf", "swap_left": "Attack", "swap_right": "Wearwolf"}
    r["hotkeys"] = ["Attack", "Wearwolf", "Wearbear", "Kick", "Firestorm"]
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("buc", None, "larm"), magic("whm", ALACRITY_W, "rarm2"), magic("buc", None, "larm2")]
    out["anim-dru-form"] = ("AnimDruForm", r, "smpdru")
    r = recipe("dru", 2)                                 # P1b-6, P1b-7 again: a spear (2ht) and a short staff (stf), FCR 50
    r.update({"name": "AnimDruForm2", "seed": 5485})
    r["skills"] = {"Wearwolf": 1, "Wearbear": 1, "Shape Shifting": 1, "Firestorm": 1}
    r["mouse"] = {"left": "Attack", "right": "Wearwolf", "swap_left": "Attack", "swap_right": "Wearwolf"}
    r["hotkeys"] = ["Attack", "Wearwolf", "Wearbear", "Kick", "Firestorm"]
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("spr", None, "rarm"), magic("sst", None, "rarm2")]
    out["anim-dru-form2"] = ("AnimDruForm2", r, "smpdru")
    r = gh2_recipe("dru", 1)                             # P1b-8: the two-handed sword in set 1 (p8-dru-2h's swap missed)
    r.update({"name": "AnimDruH2s", "seed": 5486})
    r["items"] = [it for it in r["items"] if it["equip"] not in ("rarm", "larm", "rarm2", "larm2")] + [
        magic("2hs", ALACRITY_W, "rarm"), magic("whm", ALACRITY_W, "rarm2"), magic("buc", BLOCKING, "larm2")]
    out["anim-dru-2hs"] = ("AnimDruH2s", r, "smpdru")
    r = mon_recipe()                                     # P1b-10: Blood Raven in Hell (MonProp bloodraven, knock)
    r.update({"name": "AnimSorBr", "seed": 5484})
    r["stats"].update({"hitpoints": 2500, "maxhp": 2500, "vitality": 400})
    r["skills"] = {"Teleport": 1, "Nova": 20, "Frost Nova": 5, "Static Field": 1}
    r["mouse"] = {"left": "Teleport", "right": "Nova", "swap_left": "Teleport", "swap_right": "Nova"}
    r["hotkeys"] = ["Nova", "Frost Nova", "Static Field"]
    out["anim-sor-br"] = ("AnimSorBr", r, "smpsor")
    return out


def cmd_recipes():
    for cls in CLASSES:
        for tier in (0, 1, 2):
            p = os.path.join(RDIR, "anim-%s-t%d-gh.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(recipe(cls, tier, gh=True), f, indent=1)
                f.write("\n")
    for cls in CLASSES:
        for tier in (0, 1, 2):
            p = os.path.join(RDIR, "anim-%s-t%d-gh2.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(gh2_recipe(cls, tier), f, indent=1)
                f.write("\n")
            p = os.path.join(RDIR, "anim-%s-t%d-gh3.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(gh2_recipe(cls, tier, 60, "L", 5500), f, indent=1)
                f.write("\n")
            p = os.path.join(RDIR, "anim-%s-t%d-gh4.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(gh2_recipe(cls, tier, 80, "M", 5600), f, indent=1)
                f.write("\n")
            p = os.path.join(RDIR, "anim-%s-t%d-bk.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(gh2_recipe(cls, tier, 1500, "B", 5800), f, indent=1)
                f.write("\n")
    for rec, (_, r, _) in special_recipes().items():
        with open(os.path.join(RDIR, rec + ".json"), "w") as f:
            json.dump(r, f, indent=1)
            f.write("\n")
    p = os.path.join(RDIR, "anim-sor-mon.json")
    with open(p, "w") as f:
        json.dump(mon_recipe(), f, indent=1)
        f.write("\n")
    print(p)
    for cls in CLASSES:
        for tier in (0, 1, 2):
            r = recipe(cls, tier)
            p = os.path.join(RDIR, "anim-%s-t%d.json" % (cls, tier))
            with open(p, "w") as f:
                json.dump(r, f, indent=1)
                f.write("\n")
            print(p)
    return 0


SAVES = {"Anim%s%d" % (c.capitalize(), t): ("anim-%s-t%d" % (c, t), CLASSES[c][1]) for c in CLASSES for t in (0, 1, 2)}
SAVES["AnimSorMon"] = ("anim-sor-mon", "smpsor")
SAVES.update({"gh/Anim%s%d" % (c.capitalize(), t): ("anim-%s-t%d-gh" % (c, t), CLASSES[c][1]) for c in CLASSES
              for t in (0, 1, 2)})

SAVES.update({"gh2/Anim%sH%d" % (c.capitalize(), t): ("anim-%s-t%d-gh2" % (c, t), CLASSES[c][1]) for c in CLASSES
              for t in (0, 1, 2)})
SAVES.update({"gh3/Anim%sL%d" % (c.capitalize(), t): ("anim-%s-t%d-gh3" % (c, t), CLASSES[c][1]) for c in CLASSES
              for t in (0, 1, 2)})
SAVES.update({"gh4/Anim%sM%d" % (c.capitalize(), t): ("anim-%s-t%d-gh4" % (c, t), CLASSES[c][1]) for c in CLASSES
              for t in (0, 1, 2)})
SAVES.update({"bk/Anim%sB%d" % (c.capitalize(), t): ("anim-%s-t%d-bk" % (c, t), CLASSES[c][1]) for c in CLASSES
              for t in (0, 1, 2)})
SAVES.update({"sp/" + name: (rec, base) for rec, (name, _, base) in special_recipes().items()})

FIELDS = ("1,2", "1,3", "1,4", "1,5")


def wp(w):
    return ("pilot", ["farm", "--wp", w, "--time", "1"], 90)


def fight(keys, hops, radius=10, extra=()):
    """explore on foot, the right button cast or swung at the nearest live monster, the hotkeys taken in turn."""
    return ("pilot", ["explore", "--walk", "--melee", "--melee-button", "3", "--curse-keys", ",".join(keys),
                      "--keys-cycle", "--give-up", "10", "--radius", str(radius), "--melee-hold", "0.3",
                      "--drink", "0.7", "--mana-col", "4", "--hops", str(hops)] + list(extra), 60 + 12 * hops)


def class_session(cls, tier, seed, field, hops=24):
    seq = CLASSES[cls][8]
    keys1 = ["F1", "F1", "F2", "F3", "F1", "F4"] + (["F5", "F5"] if seq else [])
    keys2 = ["F1", "F1", "F2", "F1", "F3"] + (["F5"] if seq else [])
    holds = [("hold", "F1", 4.0), ("hold", "F2", 4.0)] + ([("hold", "F5", 3.0)] if seq else [])
    return ("Anim%s%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), fight(keys1, hops, extra=("--loot", "6"))] + holds +
            [fight(keys1, hops // 2), ("hold", "F3", 3.0), ("hold", "F4", 3.0),
             ("keys", ["w"], 1.0), ("keys", ["r"], 0.5), fight(keys2, hops, extra=("--loot", "6"))] + holds[:2] +
            [("keys", ["r"], 0.5), ("keys", ["w"], 1.0), fight(keys1, hops // 2)])


def gh_session(cls, tier, seed, field, hops=16):
    """the fragile character's session: fights only, drinking below 80 % life."""
    keys = ["F1", "F1", "F2", "F1", "F3"]
    f = fight(keys, hops)
    f = (f[0], [("0.8" if a == "0.7" else a) for a in f[1]], f[2])
    return ("Anim%s%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), f, ("keys", ["w"], 1.0), f])


SESSIONS = {"dev-smoke": ("AnimSor0", "enter-normal", 5900, [wp("1,2"), fight(["F1", "F2", "F3", "F4"], 6),
                                                             ("hold", "F1", 3.0), ("hold", "F5", 3.0),
                                                             ("keys", ["w"], 1.0), ("keys", ["r"], 0.5),
                                                             fight(["F1", "F2", "F5"], 6)])}
for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        SESSIONS["%s-t%d" % (cls, tier)] = class_session(cls, tier, 5100 + 10 * k + tier, FIELDS[(k + tier) % 4])
        # the get-hit variant: life 40 (the bands of GetHitRoll reached by Act I Normal hits); gh-ama-t0 and
        # gh-sor-t0 (run:2026-10-27-anim, the first batch) played the class_session steps; from the second batch on
        # the gh- sessions play gh_session (no held skills: the held button kept the pilot from drinking)
        if (cls, tier) in (("ama", 0), ("sor", 0)):
            row = class_session(cls, tier, 5100 + 10 * k + tier, FIELDS[(k + tier) % 4])
        else:
            row = gh_session(cls, tier, 5300 + 10 * k + tier, FIELDS[(k + tier + 1) % 4])
        SESSIONS["gh-%s-t%d" % (cls, tier)] = ("gh/" + row[0],) + row[1:]


def mon_session(seed, field, hops=40):
    """Teleport hops (Shift + left) and the right button cast at the nearest live monster, the hotkeys in turn:
    monsters of every class met, chilled walkers (Frost Nova), Frozen Orb held (P1b-12)."""
    tele = ("pilot", ["explore", "--melee", "--melee-button", "3", "--curse-keys", "F1,F2,F1,F4", "--keys-cycle",
                      "--give-up", "8", "--radius", "12", "--melee-hold", "0.3", "--drink", "0.5", "--mana-col", "4",
                      "--hops", str(hops)], 60 + 12 * hops)
    return ("AnimSorMon", "enter-normal", seed, [wp(field), tele, ("hold", "F3", 6.0), ("hold", "F4", 4.0),
                                                 ("hold", "F3", 6.0), tele])


for k, f in enumerate(("5,2", "5,3", "2,2", "3,2", "1,4", "5,4")):
    SESSIONS["mon-%d" % (k + 1)] = mon_session(5200 + k, f)


def gh2_session(cls, tier, seed, field, hops=20):
    """batch 5's get-hit session: Act III Normal, fights only (Attack, Throw or the second cast, the cast, Kick), the
    pilot drinking below 80 % life inside its click bursts too (d2pilot --drink-in-burst); the weapon swap half way."""
    keys = ["F1", "F4", "F2", "F1", "F4", "F3"]
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.8" if a == "0.7" else a) for a in f[1]], f[2])
    return ("gh2/Anim%sH%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), f, ("keys", ["w"], 1.0), f])


for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        SESSIONS["gh2-%s-t%d" % (cls, tier)] = gh2_session(cls, tier, 5400 + 10 * k + tier, ("3,2", "3,3")[(k + tier) % 2])


def gh3_session(cls, tier, seed, field, hops=24):
    """gh2-sor-t1 (life 120 in Act III) died after 7 get-hits, its potions spent at hops 1-8 (a full orb reads 0.75):
    life 60 in Act I Normal (hits of 3-7 in the 3/8 and 3/4 bands), drinking below 0.5 of the orb, in bursts too."""
    keys = ["F1", "F4", "F2", "F1", "F4", "F3"]
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.5" if a == "0.7" else a) for a in f[1]], f[2])
    return ("gh3/Anim%sL%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), f, ("keys", ["w"], 1.0), f])


for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        SESSIONS["gh3-%s-t%d" % (cls, tier)] = gh3_session(cls, tier, 5500 + 10 * k + tier, ("1,3", "1,4")[(k + tier) % 2])


def gh4_session(cls, tier, seed, field, hops=24):
    """the Act I monsters (levels near 5) seldom hit a clvl 25 character (dev5-gh3-sor-t2: 2 of 33 attacks): life 80
    in Act II Normal (Dry Hills, Far Oasis), drinking below 0.5 of the orb, in bursts too."""
    keys = ["F1", "F4", "F2", "F1", "F4", "F3"]
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.5" if a == "0.7" else a) for a in f[1]], f[2])
    return ("gh4/Anim%sM%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), f, ("keys", ["w"], 1.0), f])


for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        SESSIONS["gh4-%s-t%d" % (cls, tier)] = gh4_session(cls, tier, 5600 + 10 * k + tier, ("2,3", "2,5")[(k + tier) % 2])


def gh4n_session(cls, tier, seed, field, hops=24):
    """gh4 in Far Oasis died within a burst (gh4-nec-t1, the belt full: 80 life gone in under a second): the same
    saves in Act I Nightmare (Cold Plains, Stony Field), no lightning scarabs."""
    row = gh4_session(cls, tier, seed, field, hops)
    return (row[0], "enter-nightmare") + row[2:]


for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        SESSIONS["gh4n-%s-t%d" % (cls, tier)] = gh4n_session(cls, tier, 5700 + 10 * k + tier, ("1,2", "1,3")[(k + tier) % 2])


def bk_session(cls, tier, seed, field="2,5", hops=24):
    """blocks and throws (P1b-3, P1b-8's wand block): the gh2 weapons (a throwing axe, the Amazon's wand, the Druid's
    hammer and two-handed sword) on a life-1500 character in Far Oasis (gh4-sor-t2 met 126 attacks there in a minute)."""
    keys = ["F1", "F4", "F2", "F1", "F4", "F3"]
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.5" if a == "0.7" else a) for a in f[1]], f[2])
    return ("bk/Anim%sB%d" % (cls.capitalize(), tier), "enter-normal", seed,
            [wp(field), f, ("keys", ["w"], 1.0), f])


for k, cls in enumerate(CLASSES):
    for tier in (0, 1, 2):
        # bk-ama-t2 (the first) ran 24 hops per half (about 12 minutes); the others 10, for the session cap
        SESSIONS["bk-%s-t%d" % (cls, tier)] = bk_session(cls, tier, 5800 + 10 * k + tier,
                                                         hops=24 if (cls, tier) == ("ama", 2) else 10)


def p8_session(save, seed, swap_first, field="3,2", hops=24):
    """P1b-8: the Druid's get-hits with the war hammer (set 1) or, swapped first, the two-handed sword (set 2), on the
    life-120 gh2 save in Spider Forest (gh2-sor-t1: 7 get-hits before its death)."""
    keys = ["F1", "F2", "F1", "F3"]
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.5" if a == "0.7" else a) for a in f[1]], f[2])
    return (save, "enter-normal", seed, [wp(field)] + ([("keys", ["w"], 1.0)] if swap_first else []) + [f, f])


SESSIONS["p8-dru-1h"] = p8_session("gh2/AnimDruH2", 5490, False)
SESSIONS["p8-dru-2h"] = p8_session("gh2/AnimDruH1", 5491, True)


def sp_session(save, seed, field, keys, hops=24, holds=()):
    f = fight(keys, hops, extra=("--drink-in-burst",))
    f = (f[0], [("0.5" if a == "0.7" else a) for a in f[1]], f[2])
    return ("sp/" + save, "enter-normal", seed,
            [wp(field), f] + list(holds) + [("keys", ["w"], 1.0), f] + list(holds))


SESSIONS["sp-ass-bos"] = sp_session("AnimAssBos", 5480, "1,3", ["F2", "F1", "F1", "F1", "F1", "F5", "F1", "F1"])
SESSIONS["sp-bar-dw"] = sp_session("AnimBarDw", 5481, "1,4", ["F1", "F2", "F3", "F3", "F4", "F1", "F3", "F2"],
                                   holds=[("hold", "F3", 4.0), ("hold", "F2", 3.0)])
SESSIONS["sp-pal-chg"] = sp_session("AnimPalChg", 5482, "1,2", ["F2", "F1", "F2", "F1", "F2", "F4"])
BRNOVA = ["--nova-key", "F1", "--radius", "9", "--mana-col", "4", "--drink", "0.5", "--nova-hold", "1.6",
          "--max-res", "1000"]
# Blood Raven (class 267) in the Graveyard preset (LvlPrest Def 108) of the Burial Grounds, next to Cold Plains;
# map seed 4807 reached it in plan 0038's raven2 (monsters/experiments, H4a)
SESSIONS["br-hell"] = ("sp/AnimSorBr", "enter-hell", 4807,
                       [wp("1,2"), ("pilot", ["explore", "--hops", "300", "--to-pdef", "108", "--pdef-any", "--persist",
                                              "25"] + BRNOVA, 400),
                        ("pilot", ["hunt", "--mon-cls", "267", "--time", "240"] + BRNOVA, 280)])
SESSIONS["br-hell2"] = SESSIONS["br-hell"]          # the same steps again (br-hell: 7 knockback results)
SESSIONS["sp-dru-form2"] = sp_session("AnimDruForm2", 5485, "1,4", ["F2", "F1", "F1", "F1", "F3", "F1", "F1", "F1",
                                                                    "F3", "F5", "F3", "F1", "F1"])
SESSIONS["p8-dru-2hs"] = p8_session("sp/AnimDruH2s", 5492, False)
SESSIONS["sp-dru-form"] = sp_session("AnimDruForm", 5483, "1,5", ["F2", "F1", "F1", "F1", "F3", "F1", "F1", "F1",
                                                                  "F3", "F5", "F3", "F1", "F1"])


def sh(args, timeout=None, log=None):
    print("$ " + " ".join(args), flush=True)
    try:
        return subprocess.run(args, cwd=ROOT, timeout=timeout, stdout=log, stderr=subprocess.STDOUT).returncode
    except subprocess.TimeoutExpired:
        print("  (timeout after %s s)" % timeout, flush=True)
        return None


def build(saves, only=None):
    for d in ("gh", "gh2", "gh3", "gh4", "bk", "sp"):
        os.makedirs(os.path.join(saves, d), exist_ok=True)
    for name, (rec, base) in SAVES.items():
        if only and not any(name.startswith(o) for o in only):
            continue
        rc = sh(PY + ["tools/d2s.py", "build", EXCEL, os.path.join("tools", "d2s_recipes", rec + ".json"),
                      os.path.join(BASE, base + ".d2s"), os.path.join(saves, name + ".d2s")], 60)
        if rc:
            return rc
    return 0


def run_session(name, slot, tag, saves, run):
    save, steps, seed, todo = SESSIONS[name][:4]
    env = SESSIONS[name][4] if len(SESSIONS[name]) > 4 else {}
    log = os.path.join(LOGDIR, "%s-%s.log" % (run, name))
    os.makedirs(os.path.join(ROOT, LOGDIR), exist_ok=True)
    out = open(os.path.join(ROOT, LOGDIR, "%s-%s.pilot.txt" % (run, name)), "a")
    print("=== %s: %s, %s, seed %d -> %s" % (name, save, steps, seed, log), flush=True)
    for k in [k for k in os.environ if k.startswith("ANIM_")]:
        del os.environ[k]
    os.environ.update(env)
    drv = None
    for attempt in range(3):
        sh(PY + ["tools/saves.py", "--slot", str(slot), "restore", tag], 60)
        sh(PY + ["tools/saves.py", "--slot", str(slot), "aside", tag], 60)
        if attempt and os.path.exists(os.path.join(ROOT, log)):
            os.replace(os.path.join(ROOT, log), os.path.join(ROOT, log + ".failed%d" % attempt))
        drv = subprocess.Popen(PY + ["tools/d2run.py", "--slot", str(slot), "--seed", str(seed), "--gdb",
                                     "tools/gdb/anim.gdb", "--steps", "tools/gdb/%s.steps" % steps, "--after",
                                     "2400", "--install", tag, os.path.join(saves, save + ".d2s"), "--log", log],
                               cwd=ROOT, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               start_new_session=True)
        t0, ok = time.time(), False
        while time.time() - t0 < 150:
            time.sleep(3)
            try:
                if "PLR " in open(os.path.join(ROOT, log), errors="replace").read():
                    ok = True
                    break
            except OSError:
                pass
        if ok:
            break
        print("  no PLR line after 150 s: relaunch", flush=True)
        sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
        try:
            drv.wait(30)
        except subprocess.TimeoutExpired:
            pass
    t0 = time.time()
    while time.time() - t0 < 300:
        try:
            with open(os.path.join(ROOT, log), "rb") as fh:
                fh.seek(max(0, os.path.getsize(os.path.join(ROOT, log)) - 20000))
                tail = fh.read().decode("latin1")
            frs = [int(x) for x in re.findall(r'"fr":(\d+)', tail)]
            if frs and max(frs) >= 75:
                break
        except OSError:
            pass
        time.sleep(2)
    time.sleep(2)
    shots = os.path.join(LOGDIR, "%s-%s-shots" % (run, name))
    os.makedirs(os.path.join(ROOT, shots), exist_ok=True)
    for step in todo:
        if step[0] == "pilot":
            args, timeout = step[1], step[2]
            sh(PY + ["tools/d2pilot.py", args[0], log, "--slot", str(slot)] + args[1:] + ["--shots", shots],
               timeout, out)
        elif step[0] == "wait":
            time.sleep(step[1])
        elif step[0] == "hold":       # a skill held on the right button beside the player (back-to-back actions)
            sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", step[1]], 30)
            time.sleep(0.3)
            sh(PY + ["tools/xdrive.py", "--slot", str(slot), "--window", "Diablo II", "rhold", "440", "262",
                     str(step[2])], 30 + step[2])
        elif step[0] == "keys":
            for k in step[1]:
                sh(PY + ["tools/xdrive.py", "--slot", str(slot), "key", k], 30)
                time.sleep(step[2])
    sh(PY + ["tools/xdrive.py", "--slot", str(slot), "--window", "Diablo II", "shot",
             os.path.join(shots, "end.png")], 30)
    sh(PY + ["tools/slots.py", "stop", str(slot)], 60)
    if drv is not None:
        try:
            drv.wait(30)
        except subprocess.TimeoutExpired:
            pass
    out.close()


def main(argv):
    if not argv or argv[0] not in ("list", "run", "build", "recipes"):
        print(__doc__)
        return 2
    if argv[0] == "recipes":
        return cmd_recipes()
    if argv[0] == "list":
        for k, v in SESSIONS.items():
            print("%-12s %-10s %-14s %d %r" % (k, v[0], v[1], v[2], v[3]))
        return 0
    a = argv[1:]
    opt, names, k = {}, [], 0
    while k < len(a):
        if a[k] in ("--slot", "--tag", "--saves", "--run"):
            opt[a[k][2:]] = a[k + 1]
            k += 2
        else:
            names.append(a[k])
            k += 1
    if argv[0] == "build":
        return build(opt["saves"], names)
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

#!/usr/bin/env python3
"""Plan 0069 Phase 1a (`lane/n69a`): where the monster AI bestiary tour finds each catalogue entry, which map seed each
act runs on, and which calls of each entry's think the AI logger can compare.

    python3 -I tools/ai_tour.py entries                       # the tour's entries: batches, inventory rows, statements
    python3 -I tools/ai_tour.py place [ENTRY ...]             # per entry: records, pool levels, presets, other sources
    python3 -I tools/ai_tour.py seeds --group G [--first N] [--count K] [--top T]   # score map seeds for a seed group
    python3 -I tools/ai_tour.py pools                         # each case's pool aims against monpool.py on its seed
    python3 -I tools/ai_tour.py rows                          # every inventory row of the tour: its case(s) or its move
    python3 -I tools/ai_tour.py routes                        # each case's warps against Levels Vis/Warp
    python3 -I tools/ai_tour.py audit [ENTRY ...]             # the boundary audit of each entry's think, init and alt
    python3 -I tools/ai_tour.py cases                         # the case table (what tools/ai_sessions.py runs)
    python3 -I tools/ai_tour.py conv [ADDR ...]               # the convention of the boundaries CONV lacks

Inputs: the excel directory workspace/merged/data/global/excel (the .bin records the game loads, the .txt for names),
the DS1 files under workspace/merged/data/global/tiles, the pinned game.exe (workspace/runtime/game/game.exe, checked
by sha256), docs/plans/0066-inventory/monsters-ai-catalogue.md (the rows and their batches) and tools/gdb/ai.py (the
boundary list `BND`, the windows `THINK_LO`) with tools/gdb/ai-retsites.txt.

Placement sources, each printed with its kind:
  pool     a Levels `mon` (Normal) or `nmon` (Nightmare, Hell) slot names a record of the entry (monsters/pool: the pool
           keeps `NumMon` of them, so a level holds the class only on a seed whose pool picked it; `seeds`, `pools`);
  preset   a DS1 places a record (type-1 unit through MonPreset, tools/ds1.py `_units`), a superunique
           whose class is a record (MonPreset kind 2), or a MonPlace row the preset spawn turns into a record (MonPlace
           § Interpretation notes: 4 navi, 5 bloodraven, 8 maggotqueen1, 10/11 tentaclehead1); the levels are the
           record's LevelId, or for a maze or outdoor record the levels of the level types whose files cover its DT1s
           (the scoring of tools/ds1.py `units`); a DS1 LvlPrest does not name is listed with Def -1 and no level;
  spawn    a MonStats `spawn` or `minion1`/`minion2` cell of a placed record names it (a chain: maggot egg, larva,
           tentacles);
  code     a creator the findings name (CODE below, with its anchor);
  none     no source found: the entry's rows are moved (MOVES below).
Nothing here is a game claim: the tool says where the tour looks. Stdlib only, and the tools it imports. Read-only.
"""
import collections
import hashlib
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXCEL = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
MERGED = os.path.join(ROOT, "workspace", "merged")
EXE = os.path.join(ROOT, "workspace", "runtime", "game", "game.exe")
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
INVENTORY = os.path.join(ROOT, "docs", "plans", "0066-inventory", "monsters-ai-catalogue.md")
BATCHES = ("H1a", "H1b", "H1c", "H1d", "H1g", "H1h", "H1p")   # H1p: the rows this tool moved out (MOVES)
TOWNS = {1: "Rogue Encampment", 40: "Lut Gholein", 75: "Kurast Docks", 103: "Pandemonium Fortress", 109: "Harrogath"}

# ------------------------------------------------------------------------------------------------- creators by code
# Entries placed by code the data does not show: entry -> (levels, anchor and reading). Every one is a lead for where to
# look, not a claim of this tool.
CODE = {
    "R58": ((2,), "drlg/0004 § preset units: the Blood Moor centre preset (Def 4-7, level 2) adds MonStats 266 navi; "
                  "quests/0001 x-navi met it there (map seed 45)"),
    "R60": ((3, 4, 5, 6, 27), "monsters/spawn § K: the wanderer list holds 270 rogue2, Act I only "
                              "(fn:sub_0054EF50_WandererSpawn@0x0054EF50), in levels whose MonWndr is set"),
    "R77": ((57, 79), "objects/0001: OBJ_TrapEvent's trap monsters 330 trap-lightning (type 1, level 57 reached) and "
                      "326 trap-firebolt (types 2, 6; remapped below level 40) at an operated trapped object"),
    "R80": ((113, 79), "objects/0001: OBJTRAP_PoisonCloud makes 329 trap-poisoncloud (type 3; level 113 reached)"),
    "R92": ((57, 79), "objects/0001: OBJTRAP_Nova makes 369 trap-nova (type 4 at level 40 or above)"),
    "R129": ((110, 111), "monsters/0002 spawn 42: evilhut (528) preset units in the kept Act V logs; DS1 "
                         "expansion/siege/monsterspawner*.ds1 (not named by LvlPrest)"),
    "R1": ((4,), "the kept rev 4 case a1-stony logged its 4 decisions (map seed 5803): a rerun with logger rev 7"),
    "R78": ((78,), "the kept rev 6 case a3-flayer-p8 logged 147 decisions (map seed 5602): a rerun with rev 7"),
    "R79": ((78,), "the kept rev 6 case s-barb-flayer logged 17 decisions (map seed 5401): a rerun with rev 7"),
    "S11": ((29,), "the kept rev 6 case s-necro-curse logged 27 decisions (map seed 5802): a rerun with rev 7"),
    "S5": tuple([tuple(TOWNS)]) + ("catalogue S5a: row 61's MonAiInit(ctl, 5) for an unowned hireling: the town "
                                   "hirelings before they are hired",),
    "S6": tuple([tuple(TOWNS)]) + ("catalogue S6a: row 61's MonAiInit(ctl, 6), as state 5",),
    "S15": ((110, 112, 129), "catalogue S15a: do 131 (Overseer Whip) turns a base-453 minion into 461 suicideminion1 "
                             "with MonAiInit(.., 15): an overseer and minions in one pool"),
    "S16": ((111, 117, 110), "catalogue S16a: ImpAttach (do 129) gives an imp (base 492) and a host of base 435 or "
                             "441 state 143 and MonAiInit(.., 16): imps and siege beasts in one pool"),
    "R128": ((124,), "MonPlace § Interpretation notes, Scope: A5Q3_NihlathakBossSpawn calls PresetMonSpawn "
                     "(0x0058A70D); DS1_Parse rewrites the preset nihlathak 514 to an object (tools/ds1.py ACT4_REWRITES)"),
    "NOTES": ((3, 6, 27, 46), "inventory row 517: row 7's second aip(3) draw, with R7"),
}

# Entries no source places: entry -> the reason its rows are moved, and where to. Each is (class, batch, reason).
NO_CREATOR = ("no stock placement found by `tools/ai_tour.py place`: no Levels mon/nmon/umon slot, no DS1 unit "
              "(every .ds1 file scanned, LvlPrest-named or not), no MonPlace or superunique row, no MonStats "
              "spawn/minion cell and no Skills summon names %s, and no finding names a creator; a code creator, if one "
              "exists, is not followed (the class-id immediates are not read). Route: a static creator scan, then a "
              "recipe")
MOVES = {
    "R46": ("b", NO_CREATOR % "230-233 (firebeast..poisonorb; `enabled` blank, archaeology/0002 § 2)"),
    "R47": ("b", NO_CREATOR % "234 flyingscimitar (only the object region's default class, monsters/0001 pool 23)"),
    "R62": ("b", NO_CREATOR % "272 rogue3 (MonPreset Act 1 names it, no DS1 places it)"),
    "R75": ("b", NO_CREATOR % "313-317 quillbear1..5 (unreached, archaeology/0002 § 2)"),
    "R76": ("b", NO_CREATOR % "321-325 evilhole1..5 and 711 demonhole (its one spawner, 0x005E9DD0, has no reference, "
                              "ai/0016 § 7)"),
    "R81": ("b", NO_CREATOR % "331 act2guard2 (quests/0001 lists it as a quest NPC id; no placement read)"),
    "R82": ("b", NO_CREATOR % "332 invisospawner"),
    "R83": ("b", NO_CREATOR % "334-337 suckernest1..4 (`enabled` blank; MonPlace 21 place_mosquitonest places nothing, "
                              "MonPlace § Interpretation notes)"),
    "R87": ("b", NO_CREATOR % "354 trap-melee (MonPreset Act 3 names it, no DS1 places it; not one of "
                              "g_ObjTrapFns' trap monsters, objects/0001)"),
    "R113": ("b", NO_CREATOR % "435 barricadetower (S16a's host of base 435 has no placement either)"),
    "R121": ("b", NO_CREATOR % "484-491 minionspawner1..8 and 710 demonspawner"),
}

# ------------------------------------------------------------------------------------------------------ the cases
# A route step: ("stage", "TAB,ROW", secs) waypoint and Nova sweep; ("descend", "ROWS", level, secs) the LvlWarp rows to a
# level, then a sweep there; ("border", hops) explore --any-level out of the level into its neighbours (Nova on);
# ("hunt", class, secs) kill one class, Nova radius 1 so it thinks for a while; ("town", "TAB,ROW", hops) waypoint to a
# town and walk there (no Nova); ("stay", hops) walk in the start town; ("loot", hops) explore and operate containers
# (needs the objects logger's lines, tools/gdb/objects.py); ("rerun", CASE) the steps of a kept case of
# tools/ai_sessions.py.
# pool: {level: entries the seed's pool must hold there}; aims: the entries the case looks for (pool ones included).
G1, G2, G3, G4, G5, N5 = "n1", "n2", "n3", "n4", "n5", "nm5"
TOUR = {
    # ---- Act I (seed group n1)
    "t-a1-town": dict(group=G1, route=[("town", "1,1", 0), ("border", 40)],
                      pool={}, aims=("R32", "S5", "S6", "R58")),
    "t-a1-cold": dict(group=G1, route=[("stage", "1,2", 180), ("border", 40), ("hunt", 267, 60)],
                      pool={3: ("R7", "R36", "R10")}, aims=("R7", "R36", "R10", "R59", "R60", "NOTES")),
    "t-a1-stony": dict(group=G1, route=[("stage", "1,3", 200)], pool={4: ("R43",)}, aims=("R43", "R60")),
    "t-a1-darkwood": dict(group=G1, route=[("stage", "1,4", 200)], pool={5: ("R14", "R36", "R10")},
                          aims=("R14", "R36", "R10", "R60")),
    "t-a1-marsh": dict(group=G1, route=[("stage", "1,5", 200)], pool={6: ("R7", "R43")}, aims=("R7", "R43", "NOTES")),
    "t-a1-barracks": dict(group=G1, route=[("stage", "1,6", 150), ("border", 40), ("hunt", 402, 60)],
                          pool={27: ("R14", "R10")}, aims=("R14", "R10", "R98", "R7")),
    "t-a1-catacombs": dict(group=G1, route=[("stage", "1,9", 200)], pool={35: ("R4", "R26")}, aims=("R4", "R26")),
    # the kept cases that logged the H1h rows 1, 78, 79 and state 11, rerun on their own map seeds with logger rev 7
    "t-h1h-a1-stony": dict(group="5803", route=[("rerun", "a1-stony")], pool={}, aims=("R1",)),
    "t-h1h-a3-flayer-p8": dict(group="5602", route=[("rerun", "a3-flayer-p8")], pool={}, aims=("R78",)),
    "t-h1h-s-barb-flayer": dict(group="5401", route=[("rerun", "s-barb-flayer")], pool={}, aims=("R79",)),
    "t-h1h-s-necro-curse": dict(group="5802", route=[("rerun", "s-necro-curse")], pool={}, aims=("S11",)),
    # ---- Act II (n2)
    "t-a2-town": dict(group=G2, route=[("town", "2,1", 40)], pool={}, aims=("R32", "R41", "R42", "S5", "S6")),
    "t-a2-dryhills": dict(group=G2, route=[("stage", "2,3", 200)], pool={42: ("R17", "R18", "R23", "R95")},
                          aims=("R17", "R18", "R23", "R95")),
    "t-a2-oasis": dict(group=G2, route=[("stage", "2,5", 150), ("descend", "47", 62, 40), ("descend", "49", 63, 40),
                                        ("descend", "49", 64, 40), ("hunt", 284, 60)],
                       pool={43: ("R15", "R23", "R43")},
                       aims=("R15", "R23", "R43", "R38", "R40", "R66")),
    "t-a2-lostcity": dict(group=G2, route=[("stage", "2,6", 150), ("border", 40)],
                          pool={44: ("R8", "R17", "R18", "R95"), 45: ("R16",)}, aims=("R8", "R17", "R18", "R95", "R16")),
    "t-a2-canyon": dict(group=G2, route=[("stage", "2,9", 150), ("descend", "38", 66, 60)],
                        pool={46: ("R7", "R15", "R18", "R95")}, aims=("R7", "R15", "R18", "R95", "R45", "R94")),
    "t-a2-palace": dict(group=G2, route=[("stage", "2,7", 200)], pool={52: ("R8", "R11", "R39")},
                        aims=("R8", "R11", "R39")),
    "t-a2-arcane": dict(group=G2, route=[("stage", "2,8", 150), ("hunt", 250, 90)], pool={},
                        aims=("R93", "R53")),
    "t-a2-halls": dict(group=G2, route=[("stage", "2,4", 120), ("loot", 60)], pool={57: ("R95",)},
                       aims=("R95", "R77", "R92")),
    # ---- Act III (n3)
    "t-a3-town": dict(group=G3, route=[("town", "3,1", 40)], pool={}, aims=("R32", "R41", "S5", "S6")),
    "t-a3-spider": dict(group=G3, route=[("stage", "3,2", 200)], pool={76: ("R24", "R27", "R11")},
                        aims=("R24", "R27", "R11", "R56", "R57")),
    "t-a3-marsh": dict(group=G3, route=[("stage", "3,3", 200)], pool={77: ("R25", "R27", "R52", "R65")},
                       aims=("R25", "R27", "R52", "R65", "R56", "R57")),
    "t-a3-flayer": dict(group=G3, route=[("stage", "3,4", 200)], pool={78: ("R23", "R52", "R65")},
                        aims=("R23", "R52", "R65", "R56", "R57")),
    "t-a3-lower": dict(group=G3, route=[("stage", "3,5", 150), ("loot", 60)], pool={79: ("R11", "R17", "R23", "R48")},
                       aims=("R11", "R17", "R23", "R48", "R77", "R80", "R92")),
    "t-a3-bazaar": dict(group=G3, route=[("stage", "3,6", 200)], pool={80: ("R27", "R48", "R49")},
                        aims=("R27", "R48", "R49")),
    "t-a3-upper": dict(group=G3, route=[("stage", "3,7", 200)], pool={81: ("R23", "R27", "R48", "R49")},
                       aims=("R23", "R27", "R48", "R49")),
    "t-a3-travincal": dict(group=G3, route=[("stage", "3,8", 150), ("hunt", 345, 90)], pool={83: ("R49",)},
                           aims=("R49", "R85")),
    "t-a3-durance": dict(group=G3, route=[("stage", "3,9", 100), ("descend", "67,68", 102, 30), ("hunt", 242, 90)],
                         pool={101: ("R39",)}, aims=("R39", "R50", "R85")),
    # ---- Act IV (n4)
    "t-a4-town": dict(group=G4, route=[("stay", 30)], pool={}, aims=("R32", "R54")),
    "t-a4-steppes": dict(group=G4, route=[("border", 60), ("hunt", 256, 90)], pool={104: ("R72",)},
                         aims=("R72", "R55")),
    "t-a4-cotd": dict(group=G4, route=[("stage", "4,2", 240)], pool={106: ("R4", "R68", "R70", "R71", "R73")},
                      aims=("R4", "R68", "R70", "R71", "R73")),
    "t-a4-river": dict(group=G4, route=[("stage", "4,3", 200), ("hunt", 409, 60)],
                       pool={107: ("R39", "R68", "R70", "R71", "R73")},
                       aims=("R39", "R68", "R70", "R71", "R73", "R33", "R98", "R100")),
    "t-a4-chaos": dict(group=G4, route=[("stage", "4,3", 30), ("border", 60)], pool={108: ("R74", "R70")},
                       aims=("R74", "R70")),
    # ---- Act V (n5)
    "t-a5-town": dict(group=G5, route=[("town", "5,1", 40)], pool={}, aims=("R32", "S5", "S6")),
    "t-a5-foothills": dict(group=G5, route=[("town", "5,1", 0), ("border", 80)],
                           pool={110: ("R116", "R120", "R122")},
                           aims=("R116", "R120", "R122", "R123", "R126", "R129", "S15", "S16")),
    "t-a5-highlands": dict(group=G5, route=[("stage", "5,2", 200)], pool={111: ("R115", "R122")},
                           aims=("R115", "R122", "S16", "R129", "R123", "R126")),
    "t-a5-plateau": dict(group=G5, route=[("stage", "5,3", 200)], pool={112: ("R116", "R120")},
                         aims=("R116", "R120", "S15", "R123", "R126")),
    "t-a5-crystal": dict(group=G5, route=[("stage", "5,4", 150), ("loot", 60)], pool={113: ("R124", "R118")},
                         aims=("R124", "R118", "R80")),
    "t-a5-glacial": dict(group=G5, route=[("stage", "5,5", 200)], pool={115: ("R114", "R124")},
                         aims=("R114", "R124")),
    "t-a5-tundra": dict(group=G5, route=[("stage", "5,7", 200)], pool={117: ("R115", "R122")},
                        aims=("R115", "R122", "S16", "R123", "R126")),
    "t-a5-halls": dict(group=G5, route=[("stage", "5,6", 150), ("descend", "77", 124, 40), ("hunt", 526, 90)],
                       pool={123: ("R137", "R114")}, aims=("R137", "R114", "R128")),
    "t-a5-wsk1": dict(group=G5, route=[("stage", "5,9", 100), ("descend", "81", 128, 120)],
                      pool={128: ("R119", "R137")}, aims=("R119", "R137", "R136", "S15")),
    "t-a5-wsk": dict(group=G5, route=[("stage", "5,9", 150), ("descend", "82", 130, 60)],
                     pool={129: ("R116", "R117"), 130: ("R137",)},
                     aims=("R116", "R117", "R137", "S15", "R136")),
    # ---- Nightmare, Act V (nm5): row 142's records are in nmon slots only
    "nm-a5-crystal": dict(group=N5, diff="nightmare", route=[("stage", "5,4", 200)], pool={113: ("R142",)},
                          aims=("R142",)),
    "nm-a5-wsk": dict(group=N5, diff="nightmare", route=[("stage", "5,9", 150), ("descend", "82", 130, 60)],
                      pool={129: ("R142", "R25"), 130: ("R74",)}, aims=("R142", "R25", "R74")),
}

# The map seed of each seed group: the best of `seeds --group G --first 6901 --count 3000` (most entries held, then most
# pairs, then the lowest seed; plan 0069 Phase 1a, kept as workspace/logs/n69a/seeds.txt); the H1h reruns keep their
# kept case's seed (the group name is that seed).
SEEDS = {G1: 7159, G2: 8723, G3: 7842, G4: 7055, G5: 6908, N5: 6927}


def seed_of(group):
    if group in SEEDS:
        return SEEDS[group]
    return int(group) if group.isdigit() else None


def diff_of(case):
    return TOUR[case].get("diff", "normal")


def act_of(case):
    g = TOUR[case]["group"]
    return int(g[-1]) if not g.isdigit() else None


# --------------------------------------------------------------------------------------------------------- tables
def _tables():
    import ai_survey
    import excel_bin as eb
    d = ai_survey.Data(EXCEL)
    h, rows, _, _ = eb.load_table(EXCEL, "levels")
    lv = {}
    for r in rows:
        x = dict(zip(h, r))
        lv[int(x["Id"])] = x
    return d, lv


def waypoints(lv):
    """level id -> (tab, row) of the waypoint list: tab = act + 1, row = the rank of its Waypoint index in its act,
    from 1 (the town)."""
    by_act = collections.defaultdict(list)
    for lid, x in lv.items():
        if x["Waypoint"] not in ("", "255"):
            by_act[int(x["Act"])].append((int(x["Waypoint"]), lid))
    out = {}
    for a, v in by_act.items():
        for k, (_, lid) in enumerate(sorted(v)):
            out[lid] = (a + 1, k + 1)
    return out


def warps(lv, lid):
    """[(destination level, LvlWarp row)] of a level's Vis/Warp pairs (a warp, not a border)."""
    x = lv[lid]
    out = []
    for k in range(8):
        v, w = int(x["Vis%d" % k] or 0), int(x["Warp%d" % k] or -1)
        if v and w >= 0:
            out.append((v, w))
    return out


def pool_levels(d, lv, entry, col):
    recs = set(d.users[entry_row(entry)])
    idx = {x: i for i, x in enumerate(d.ids)}
    out = []
    for lid, x in sorted(lv.items()):
        if any(x.get("%s%d" % (col, k)) and idx.get(x["%s%d" % (col, k)]) in recs for k in range(1, 11)):
            out.append(lid)
    return out


def entry_row(entry):
    return int(entry[1:]) if entry[0] == "R" else None


_PRESETS = None


def presets():
    """class id -> sorted [(Def, LevelId, file, levels)] from every LvlPrest-named DS1; MonPlace rows resolved."""
    global _PRESETS
    if _PRESETS is not None:
        return _PRESETS
    import ds1
    t = ds1._tables(MERGED)
    tiles = os.path.join(MERGED, "data", "global", "tiles")
    present = {os.path.relpath(p, tiles).replace(os.sep, "/").lower(): p for p in ds1.ds1_files(tiles)}
    levels, by_type, ltfiles = ds1._classify(t)
    nm, ns = t["n_monstats"], t["n_superuniques"]
    su_class = [r["Class"] for r in _su_recs()]
    place = {4: 266, 5: 267, 8: 284, 10: 261, 11: 261}           # MonPlace row -> class (MonPlace.md)
    parsed = {}

    def get(n):
        if n not in parsed:
            f, _, _ = ds1._status(open(present[n], "rb").read())
            parsed[n] = f
        return parsed[n]
    out = collections.defaultdict(set)
    for r in t["lvlprest"]:
        names = [r["File%d" % i].replace("\\", "/").lower() for i in range(1, 7)]
        names = [n for n in names if n not in ("", "0") and n in present]
        if r["LevelId"]:
            lids = (r["LevelId"],)
        else:
            need = set()
            for n in names:
                if get(n):
                    need |= {k for k in map(ds1._dt1_key, get(n)["files"]) if k}
            mask, score = r["Dt1Mask"], {}
            bits = [b for b in range(32) if mask >> b & 1]
            for ti, files in enumerate(ltfiles):
                if bits and all(files[b] not in ("", "0") for b in bits):
                    score[ti] = len(need & {files[b] for b in bits})
            top = max(score.values(), default=0)
            tis = {ti for ti, sc in score.items() if sc == top and top}
            lids = tuple(sorted(lid for lid, (_, dd) in levels.items() if dd["LevelType"] in tis and dd["DrlgType"] != 2))
        for n in names:
            f = get(n)
            if f is None:
                continue
            for u in ds1._units(f, t, None):
                if u["type"] != 1 or u["id"] is None or u["id"] < 0:
                    continue
                c = u["id"]
                if nm <= c < nm + ns:
                    c = su_class[c - nm]
                elif c >= nm + ns:
                    c = place.get(c - nm - ns)
                    if c is None:
                        continue
                out[c].add((r["Def"], r["LevelId"], n.split("/")[-1], lids))
    named = {n for r in t["lvlprest"] for n in (r["File%d" % i].replace("\\", "/").lower() for i in range(1, 7))}
    for rel in sorted(present):                 # the DS1s LvlPrest does not name (Def -1, no levels): what else is there
        if rel in named:
            continue
        f = get(rel)
        if f is None:
            continue
        for u in ds1._units(f, t, None):
            if u["type"] != 1 or u["id"] is None or u["id"] < 0:
                continue
            c = u["id"]
            if nm <= c < nm + ns:
                c = su_class[c - nm]
            elif c >= nm + ns:
                c = place.get(c - nm - ns)
                if c is None:
                    continue
            out[c].add((-1, 0, rel + " (not named by LvlPrest)", ()))
    _PRESETS = {c: sorted(v) for c, v in out.items()}
    return _PRESETS


def _su_recs():
    import excel_bin as eb
    import excel_layouts as L
    refs = eb.Refs(EXCEL)
    fields = [f for f in L.LAYOUTS["superuniques"]["fields"] if "col" in f or "name" in f]
    recs, _ = eb.read_bin(eb.find_file(EXCEL, "superuniques", ".bin"))
    return [{f.get("name", f.get("col")): eb.decode_field(b, f, refs) for f in fields} for b in recs]


def spawn_chain(d):
    """class -> [(parent class, column)] from MonStats spawn / minion1 / minion2 (.txt Id names)."""
    idx = {x: i for i, x in enumerate(d.ids)}
    out = collections.defaultdict(list)
    for i, t in enumerate(d.ms.txt):
        for col in ("spawn", "minion1", "minion2"):
            v = t.get(col, "")
            if v and v in idx:
                out[idx[v]].append((i, col))
    return out


# ------------------------------------------------------------------------------------------------------ inventory
def inventory():
    """The inventory rows of the tour's batches: [(row number, line, entry, class, batch, count)]."""
    out = []
    for ln in open(INVENTORY):
        if not ln.startswith("| ") or ln.startswith("| #"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if not c[0].isdigit():
            continue
        batch, cnt = c[-2], c[-1]
        if batch not in BATCHES:
            continue
        sec = c[2]
        entry = "NOTES" if sec.startswith("Reimplementation") else sec.split(".")[0]
        out.append((int(c[0]), int(c[1]), entry, c[5], batch, int(cnt) if cnt.isdigit() else 0))
    return out


def entries():
    """entry -> (batches, rows, statements)."""
    e = collections.OrderedDict()
    for n, line, entry, cls, batch, cnt in inventory():
        b, rows, s = e.setdefault(entry, (set(), [], [0]))
        b.add(batch)
        rows.append(n)
        s[0] += cnt
    return {k: (sorted(b), rows, s[0]) for k, (b, rows, s) in e.items()}


def cases_of(entry):
    return [c for c, t in TOUR.items() if entry in t["aims"]]


# ----------------------------------------------------------------------------------------------------- commands
def cmd_entries():
    e = entries()
    tot = collections.Counter()
    for k, (b, rows, s) in e.items():
        print("ENTRY %-6s batches %-9s rows %-3d statements %-3d inventory %s" % (k, ",".join(b), len(rows), s,
                                                                                  ",".join(map(str, rows))))
    for n, line, entry, cls, batch, cnt in inventory():
        tot[batch] += cnt
    print("SUMMARY entries %d rows %d statements %d %s" % (len(e), len(inventory()), sum(tot.values()),
                                                         " ".join("%s=%d" % kv for kv in sorted(tot.items()))))
    return 0


def cmd_place(want):
    d, lv = _tables()
    wp = waypoints(lv)
    pre = presets()
    chain = spawn_chain(d)
    for k in entries():
        if want and k not in want:
            continue
        print("ENTRY %s" % k)
        if k == "NOTES" or k[0] == "S":
            print("  code %s" % (CODE[k][1] if k in CODE else "-"))
        else:
            row = entry_row(k)
            recs = d.users[row]
            print("  records %s" % d.row_text(row))
            print("  marks %s (ai_survey.py: P a Levels mon/nmon/umon slot, U a superunique, S a Skills summon or "
                  "PetType class, H a hireling)" % ("".join(sorted(d.ai_marks(row))) or "none"))
            for col, tag in (("mon", "Normal"), ("nmon", "Nightmare/Hell")):
                ls = pool_levels(d, lv, k, col)
                if ls:
                    print("  pool %s: %s" % (tag, " ".join("%d%s" % (x, "(wp %d,%d)" % wp[x] if x in wp else "")
                                                           for x in ls)))
            for c in recs:
                for dfn, lid, f, lids in pre.get(c, ()):
                    print("  preset %d %s: Def %d %s levels %s" % (c, d.ids[c], dfn, f, ",".join(map(str, lids)) or "-"))
                for par, col in chain.get(c, ()):
                    print("  spawn %d %s: %s of %d %s" % (c, d.ids[c], col, par, d.ids[par]))
            if k in CODE:
                print("  code levels %s: %s" % (",".join(map(str, CODE[k][0])), CODE[k][1]))
        if k in MOVES:
            print("  none -> move to (%s): %s" % MOVES[k])
        print("  cases %s" % (" ".join(cases_of(k)) or "-"))
    return 0


def _pool_sets(seed, diff):
    import monpool
    t = _pool_tables()
    s = monpool.first_draw_low(seed, 1)
    return {lid: {c for c, _, _ in reg["ents"]} for lid, reg, _ in monpool.build_all(t, s.low, diff, 1)}


_PT = None


def _pool_tables():
    global _PT
    if _PT is None:
        import monpool
        _PT = monpool.Tables(EXCEL)
    return _PT


def score(group, seed, d):
    """(met, wanted, unmet) of the group's pool-aimed entries on a seed: an entry is met when one (case, level) of the
    group that lists it holds one of its records in the level's pool."""
    diff = {"normal": 0, "nightmare": 1, "hell": 2}
    want, got, pairs = set(), set(), 0
    pools = {}
    for c, t in TOUR.items():
        if t["group"] != group:
            continue
        dd = diff[t.get("diff", "normal")]
        if dd not in pools:
            pools[dd] = _pool_sets(seed, dd)
        for lid, es in t["pool"].items():
            for e in es:
                want.add(e)
                if pools[dd].get(lid, set()) & set(d.users[entry_row(e)]):
                    got.add(e)
                    pairs += 1
    return len(got), len(want), sorted(want - got), pairs


def cmd_seeds(group, first, count, top):
    d, _ = _tables()
    res = []
    for s in range(first, first + count):
        m, p, u, pairs = score(group, s, d)
        res.append((-m, -pairs, s, p, u))
    res.sort()               # most entries held, then most (case, level, entry) pairs held, then the lowest seed
    for m, pairs, s, p, u in res[:top]:
        print("SEED group %s seed %d met %d of %d pairs %d unmet %s" % (group, s, -m, p, -pairs, " ".join(u) or "-"))
    best = res[0]
    print("SUMMARY seeds group %s range %d..%d best %d met %d of %d pairs %d" % (
        group, first, first + count - 1, best[2], -best[0], best[3], -best[1]))
    return 0


def cmd_pools():
    """Per case and level, the pool monpool.py predicts on the case's seed and the aimed entries it holds; an entry is a
    miss when no (case, level) of its group holds it."""
    d, _ = _tables()
    diff = {"normal": 0, "nightmare": 1, "hell": 2}
    want, got = collections.defaultdict(set), collections.defaultdict(set)
    bad = 0
    for c, t in TOUR.items():
        g = t["group"]
        if not t["pool"]:
            continue
        s = seed_of(g)
        if s is None:
            print("CASE %s group %s: no seed" % (c, g))
            bad += 1
            continue
        pools = _pool_sets(s, diff[t.get("diff", "normal")])
        for lid, es in t["pool"].items():
            pool = sorted(pools.get(lid, set()))
            held = [e for e in es if set(pool) & set(d.users[entry_row(e)])]
            for e in es:
                want[g].add(e)
            got[g] |= set(held)
            print("POOL %-18s %-9s seed %d level %3d pool [%s] aims %s holds %s" % (
                c, t.get("diff", "normal"), s, lid, " ".join("%d %s" % (x, d.ids[x]) for x in pool), ",".join(es),
                ",".join(held) or "-"))
    for g in sorted(want):
        miss = sorted(want[g] - got[g])
        bad += len(miss)
        print("GROUP %-5s seed %s entries %d held %d miss %s" % (g, seed_of(g), len(want[g]), len(got[g]),
                                                                 " ".join(miss) or "-"))
    print("SUMMARY pools miss %d" % bad)
    return 1 if bad else 0


def cmd_rows():
    bad = 0
    tot = collections.Counter()
    for n, line, entry, cls, batch, cnt in inventory():
        cs = cases_of(entry)
        if entry in MOVES:
            how = "move (%s)" % MOVES[entry][0]
            tot["moved"] += cnt
        elif cs:
            how = "cases " + " ".join(cs)
            tot["cased"] += cnt
        else:
            how = "NONE"
            bad += 1
        print("ROW %3d line %4d %-6s %-6s %-4s count %d %s" % (n, line, entry, cls, batch, cnt, how))
    print("SUMMARY rows statements cased %d moved %d unplaced %d" % (tot["cased"], tot["moved"], bad))
    return 1 if bad else 0


def cmd_routes():
    _, lv = _tables()
    wp = waypoints(lv)
    bad = 0
    for c, t in TOUR.items():
        at = None
        for st in t["route"]:
            if st[0] in ("stage", "town"):
                tab, row = map(int, st[1].split(","))
                lid = [k for k, v in wp.items() if v == (tab, row)]
                at = lid[0] if lid else None
                print("ROUTE %-18s %s %s -> level %s" % (c, st[0], st[1], at))
            elif st[0] == "descend":
                to = st[2]
                ws = [w for v, w in warps(lv, at)] if at else []
                rows = [w for v, w in warps(lv, at) if v == to] if at else []
                ok = bool(rows) and set(map(int, st[1].split(","))) == set(rows)
                bad += not ok
                print("ROUTE %-18s descend %s -> %d from %s: Levels warps to it %s %s" % (
                    c, st[1], to, at, ",".join(map(str, rows)) or "-", "ok" if ok else "BAD (all warps %s)" % ws))
                at = to
            else:
                print("ROUTE %-18s %s" % (c, " ".join(map(str, st))))
    print("SUMMARY routes bad %d" % bad)
    return 1 if bad else 0


def cmd_cases():
    for c, t in TOUR.items():
        print("CASE %-20s %-9s group %-5s seed %s pool %s aims %s" % (
            c, t.get("diff", "normal"), t["group"], seed_of(t["group"]),
            ";".join("%d:%s" % (k, ",".join(v)) for k, v in t["pool"].items()) or "-", ",".join(t["aims"])))
    print("SUMMARY cases %d" % len(TOUR))
    return 0


# ---------------------------------------------------------------------------------------------- the boundary audit
def _logger():
    src = open(os.path.join(HERE, "gdb", "ai.py")).read()
    m = re.search(r"BND = \((.*?)\n    \)", src, re.S)
    bnd = set(int(x, 16) for x in re.findall(r"0x[0-9A-F]{8}", m.group(1)))
    m = re.search(r"THINK_LO = \((.*?)\)\n", src, re.S)
    win = [tuple(int(x, 16) for x in p) for p in re.findall(r"\((0x[0-9A-F]{8}), (0x[0-9A-F]{8})\)", m.group(1))]
    rets = set()
    for ln in open(os.path.join(HERE, "gdb", "ai-retsites.txt")):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            rets.add(int(ln, 16))
    return bnd, win, rets


def _symbols():
    import csv
    out = {}
    with open(os.path.join(ROOT, "re", "symbols.csv")) as fh:
        for r in csv.DictReader(fh):
            out[int(r["address"], 16)] = r["name"]
    return out


def _check_exe():
    with open(EXE, "rb") as fh:
        if hashlib.sha256(fh.read()).hexdigest() != PINNED:
            raise SystemExit("%s is not the pinned game.exe" % EXE)


def _calls(lo, hi):
    """Direct and indirect calls in [lo, hi) of the pinned image, from objdump (Intel syntax): [(site, ret, callee or
    None, text)]."""
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, EXE], capture_output=True, text=True, check=True).stdout
    ins = []
    for ln in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)$", ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2).strip()))
    res = []
    for k, (a, txt) in enumerate(ins):
        if not txt.startswith("call"):
            continue
        nxt = ins[k + 1][0] if k + 1 < len(ins) else hi
        m = re.match(r"call\s+(?:0x)?([0-9a-f]+)$", txt)
        res.append((a, nxt, int(m.group(1), 16) if m else None, txt))
    return res


def _row_words():
    """entry -> (think, init, alt) from the pinned image's AI tables."""
    import ai_survey
    with open(EXE, "rb") as fh:
        data = fh.read()
    rows = ai_survey.table_from_image(data, ai_survey.AI_TABLE, 148)
    sts = ai_survey.table_from_image(data, ai_survey.AI_STATES, ai_survey.AI_STATE_ROWS)
    out = {}
    for i, r in enumerate(rows):
        out["R%d" % i] = (r[2], r[1], r[3])
    for i, r in enumerate(sts):
        out["S%d" % i] = (r[2], r[1], r[3])
    return out


# The rev 7 words of the plan (§ The logger), by entry: what the logger must add for the entry's forks.
REV7 = {
    "R1": "the return-address window of the think 0x005B0CD0 (outside THINK_LO)",
    "R43": "a line at MonAiInit's init call (the init's draws)",
    "S11": "a line at MonAiInit's init call (the init 0x005E80E0)",
    "R68": "the calls inside AiVileMotherSpawn 0x005F9E30 (AI_NESTED for that function only)",
    "R70": "the MonStats run and walk speed words",
    "R78": "the region word +0x2D4 that AiTrapArrowKind reads",
    "R79": "the region word +0x2D4 that AiTrapArrowKind reads",
    "R118": "the return of StatListFindFlag 0x00625760",
    "R54": "the return of AiNearestPlayer",
    "R32": "the return of AiNearestPlayer; the script and home words",
    "R10": "MonPlayerBonus's block",
    "R48": "the owner record (MonsterOwnerRef 0x0058F090)",
    "R73": "the words the block reads that the AID line lacks",
}


def function_ends(starts):
    s = sorted(starts)
    return {a: (s[k + 1] if k + 1 < len(s) else a + 0x400) for k, a in enumerate(s)}


def cmd_audit(want):
    _check_exe()
    bnd, win, rets = _logger()
    sym = _symbols()
    words = _row_words()
    import ai_model_check as M
    conv = {v[0]: k for k, v in M.CONV.items()}
    modelled = {k for k in M.MODELS}
    starts = set(sym) | {w for t in words.values() for w in t if w}
    ends = function_ends(starts)
    for lo, hi in win:                     # a callee window of THINK_LO ends where the logger's window ends
        if hi - lo < 0x1000 and lo in ends:
            ends[lo] = min(ends[lo], hi)

    def in_win(a):
        return any(lo <= a < hi for lo, hi in win)
    import ai_resume
    run_fns = set(ai_resume.EXEC)

    def runs(a):
        return a in run_fns or any(lo <= a < hi for lo, hi in ai_resume.EXEC_WINDOWS)

    def classify(k, site, ret, callee):
        name = sym.get(callee, "?") if callee else "indirect"
        if callee in bnd:
            if not in_win(site):
                return "rev7", "a boundary called outside the logger's windows (THINK_LO)"
            if ret not in rets:
                return "rev7", "a boundary with no return site in ai-retsites.txt (an AIB line, no AIR)"
            return "compared", "CONV %s" % conv[callee] if callee in conv else "CONV missing"
        if k in REV7 and callee and ("%08x" % callee in REV7[k].lower() or name.split("_")[-1] in REV7[k]):
            return "rev7", REV7[k]
        if callee and runs(callee):
            return "run", "not a boundary: executed by the model (tools/ai_resume.py EXEC, a draw or a getter, or "\
                          "a helper in the logged windows, whose own calls are listed under it)"
        return "fork", "not a boundary and not executed: the model forks on what it returns or writes"
    tot = collections.Counter()
    seen = set()
    for k in entries():
        if want and k not in want:
            continue
        if k == "NOTES":
            continue
        th, init, alt = words[k]
        print("ENTRY %s think %08x init %s alt %s model %s" % (
            k, th, "%08x" % init if init else "-", "%08x" % alt if alt else "-",
            "yes" if k in modelled or (k == "R1" and "R100" in modelled) else "no"))
        if not in_win(th):
            print("  WINDOW the think %08x is outside THINK_LO: no call of it is logged (rev 7: %s)" % (
                th, REV7.get(k, "a window over it")))
        per = collections.Counter()
        todo = [(p, f) for p, f in (("think", th), ("init", init), ("alt", alt)) if f]
        done = set()
        while todo:
            part, fn = todo.pop(0)
            if fn in done:
                continue
            done.add(fn)
            for site, ret, callee, txt in _calls(fn, ends[fn]):
                cls, why = classify(k, site, ret, callee)
                if part != "think" and part not in ("init", "alt") and cls == "compared" and not in_win(site):
                    cls = "rev7"
                if not in_win(fn) and callee in bnd:
                    cls, why = "rev7", "the think is outside the windows: %s" % REV7.get(k, "a window over it")
                per[cls] += 1
                tot[cls] += 1
                if cls == "compared" and callee not in conv:
                    seen.add(callee)
                print("  CALL %-15s %08x -> %s %s: %s (%s)" % (part, site, "%08x" % callee if callee else "--------",
                                                                 sym.get(callee, "?") if callee else "indirect", cls, why))
                if callee and cls == "run" and any(lo <= callee < hi for lo, hi in ai_resume.EXEC_WINDOWS) \
                        and callee not in done and callee in ends:
                    todo.append(("helper %08x" % callee, callee))
        if k in REV7:
            print("  REV7 %s" % REV7[k])
        print("  COUNT %s compared %d rev7 %d run %d fork %d%s" % (
            k, per["compared"], per["rev7"], per["run"], per["fork"],
            "  NO-COMPARED-CALL" if not per["compared"] else ""))
    print("CONV-MISSING %s" % " ".join("%08x:%s" % (a, sym.get(a, "?")) for a in sorted(seen)))
    print("SUMMARY audit calls compared %d rev7 %d run %d fork %d conv-missing %d" % (
        tot["compared"], tot["rev7"], tot["run"], tot["fork"], len(seen)))
    return 0


def _insns(lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, EXE], capture_output=True, text=True, check=True).stdout
    res = []
    for ln in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(.*)$", ln)
        if m:
            res.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(2).strip())))
    return res


REGS = {"ecx": ("ecx", "cx", "cl", "ch"), "edx": ("edx", "dx", "dl", "dh")}


def caller_reads(bnd, win):
    """callee -> [(site, ecx set, edx set, pushes)] over every call from the logger's windows to a boundary: the
    instructions between the previous call (at most 24 back) and the site, read for writes of ECX and EDX and for
    pushes (the arguments the caller sets up)."""
    out = collections.defaultdict(list)
    for lo, hi in win:
        ins = _insns(lo, hi)
        last = -1
        for k, (a, t) in enumerate(ins):
            if not t.startswith("call"):
                continue
            m = re.match(r"call (?:0x)?([0-9a-f]+)$", t)
            if m and int(m.group(1), 16) in bnd:
                seg = [x for _, x in ins[max(last + 1, k - 24):k]]
                wr = {}
                for r in ("ecx", "edx"):
                    pat = re.compile(r"\b(%s)\b" % "|".join(REGS[r]))
                    wr[r] = any(x.split(" ")[0] in ("mov", "lea", "xor", "pop", "movzx", "movsx", "or", "and")
                                and pat.fullmatch(x.partition(" ")[2].split(",")[0].strip()) for x in seg)
                out[int(m.group(1), 16)].append((a, wr["ecx"], wr["edx"], sum(x.startswith("push ") for x in seg)))
            last = k
    return out


def conv_read(sites):
    """(ecx, edx, stack count) by the majority of the call sites: a register set at more than half of them is an
    argument; the stack count is the most common push count."""
    n = len(sites)
    ec = sum(s[1] for s in sites) * 2 > n
    ed = sum(s[2] for s in sites) * 2 > n
    st = collections.Counter(s[3] for s in sites).most_common(1)[0][0]
    return ec, ed, st


def cmd_conv(want):
    """The calling convention of the boundary functions, read at their call sites in the logger's windows (caller_reads).
    The read is checked first against ai_model_check.py's CONV (the S1b entries, whose words matched the logged calls):
    a CONV register named there must be set by the caller, and a CONV stack list must not be longer than the pushes.
    Then a line per boundary the audit finds compared but CONV lacks."""
    _check_exe()
    bnd, win, rets = _logger()
    sym = _symbols()
    import ai_model_check as M
    reads = caller_reads(bnd, win)
    agree = disagree = 0
    for name, (a, ecx, edx, names) in sorted(M.CONV.items(), key=lambda kv: kv[1][0]):
        if name in M.CONV_REV3:
            continue
        if a not in reads:
            print("CHECK %-20s %08x no call site in the windows" % (name, a))
            continue
        ec, ed, st = conv_read(reads[a])
        bad = []
        if ecx is not None and not ec:
            bad.append("ecx named, not set")
        if edx is not None and not ed:
            bad.append("edx named, not set")
        if len(names) > st:
            bad.append("%d stack names, %d pushes" % (len(names), st))
        agree += not bad
        disagree += bool(bad)
        print("CHECK %-20s %08x sites %d read ecx %s edx %s pushes %d: %s" % (
            name, a, len(reads[a]), "set" if ec else "-", "set" if ed else "-", st, "; ".join(bad) or "agrees"))
    print("CHECK-SUMMARY CONV entries %d agree %d disagree %d" % (agree + disagree, agree, disagree))
    have = {v[0] for v in M.CONV.values()}
    todo = sorted(want) if want else sorted(a for a in bnd if a not in have and a in reads)
    for a in todo:
        ec, ed, st = conv_read(reads[a])
        print("CONV %08x %-40s sites %d ecx %-3s edx %-3s stack %d  per site %s" % (
            a, sym.get(a, "?"), len(reads[a]), "arg" if ec else "-", "arg" if ed else "-", st,
            " ".join("%x:%d%d%d" % (s[0], s[1], s[2], s[3]) for s in reads[a][:6])))
    return 0


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("entries")
    p = sub.add_parser("place")
    p.add_argument("entry", nargs="*")
    p = sub.add_parser("seeds")
    p.add_argument("--group", required=True)
    p.add_argument("--first", type=int, default=6901)
    p.add_argument("--count", type=int, default=400)
    p.add_argument("--top", type=int, default=5)
    sub.add_parser("pools")
    sub.add_parser("rows")
    sub.add_parser("routes")
    sub.add_parser("cases")
    p = sub.add_parser("audit")
    p.add_argument("entry", nargs="*")
    p = sub.add_parser("conv")
    p.add_argument("addr", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "conv":
        return cmd_conv({int(x, 16) for x in a.addr})
    if a.cmd == "entries":
        return cmd_entries()
    if a.cmd == "place":
        return cmd_place(set(a.entry))
    if a.cmd == "seeds":
        return cmd_seeds(a.group, a.first, a.count, a.top)
    if a.cmd == "pools":
        return cmd_pools()
    if a.cmd == "rows":
        return cmd_rows()
    if a.cmd == "routes":
        return cmd_routes()
    if a.cmd == "cases":
        return cmd_cases()
    return cmd_audit(set(a.entry))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

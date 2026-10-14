"""Survey the monster-pool data of levels.bin and monstats.bin (plan 0012 Phase 0).

Usage:
  python3 -I tools/mon_survey.py levels   <excel-dir> [--list]
  python3 -I tools/mon_survey.py monstats <excel-dir>
  python3 -I tools/mon_survey.py spawn    <excel-dir>
  python3 -I tools/mon_survey.py collision <excel-dir>
  python3 -I tools/mon_survey.py umod     <excel-dir>
  python3 -I tools/mon_survey.py superuniques <excel-dir>
  python3 -I tools/mon_survey.py stats    <excel-dir> <class|record|all> <normal|nightmare|hell|0|1|2|all> [--print]

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are
decoded from the .bin files with the layouts in tools/excel_layouts.py (what the game loads), the
.txt is read only to tell blank cells from zeros.

levels    per pool column set (mon, nmon, umon: slots 1..10 of the 25-slot arrays) and per
          difficulty under the column-set mapping given below, counts the levels whose pool is
          empty, holds more entries than NumMon, repeats a class, or names a class whose monstats
          `enabled` bit is 0. A pool entry is looked up as a monstats record position (the stored
          distinct-Id ordinal; data/0001 section 8); entries that would differ if looked up by
          distinct Id (ordinal 723 after the duplicate cr_lancer8) are counted separately.
          Difficulty mapping (an assumption of the survey, not a claim about the code):
          normal -> mon, nightmare -> nmon, hell -> nmon. Also: slots 11..25 not 0xFFFF, the (N)/(H)
          blanks of the per-difficulty columns, and the critter columns. --list prints every level.
monstats  distributions of the pool-related columns (enabled, Level*, Rarity, isSpawn, MinGrp/MaxGrp,
          PartyMin/PartyMax, minion1/2, spawn, and the type flags).
spawn     the population-pass inputs (plan 0014 Phase 0), per difficulty (same mapping as levels):
          levels with MonDen 0; the MonDen values; over the "pool classes" (distinct classes named in
          the difficulty's column set by a level whose MonDen is non-zero) the MinGrp/MaxGrp and
          PartyMin/PartyMax ranges and how many have minion1, minion2, spawn, placespawn, spawn with
          placespawn; the same over the umon classes (normal only); the MonUMin/MonUMax pairs of the
          levels with MonDen non-zero. Then MonWndr and MonSpcWalk (one column for all difficulties).
umod      MonUMod (plan 0018 Phase 0), one line per record: id, name, enabled, version, xfer, champion,
          fPick, exclude1/exclude2 (montype names), cpick and upick per difficulty, fInit, constants.
          Then, per difficulty, the champion weights (cpick) and the unique weights (upick) of the
          records with a non-zero weight, their sums, and the sums over the records that pass
          enabled = 1 and version = 0 (classic) or any version (expansion). This filter is an
          assumption of the survey, not a claim about the code. Then the (mod, exclude) pairs that occur.
superuniques  SuperUniques generation columns (plan 0018 Phase 0): per record the class, Mod1..Mod3
          as MonUMod names, MinGrp/MaxGrp, AutoPos, EClass, Stacks, Replaceable, Utrans*; then the
          value distributions, the class's monstats minion1, and which records MonPreset names.
collision the MonStats2 footprint and collision columns (plan 0017 Phase 0): SizeX, SizeY, spawnCol,
          objCol, deadCol, inert, unflatDead (blank cells shown as blank), the (SizeX, SizeY) and
          (SizeX, spawnCol) pairs and the classes with spawnCol 1, 2 and 3, over the pool classes of
          `spawn` (normal; nightmare = hell), the umon classes, "pool" = the union of the three (the
          362 pool classes of plan 0014 Phase 0), and every MonStats class ("all"). A class reaches its MonStats2 row through MonStatsEx.
stats     the stat inputs of one monster class (plan 0025 Phase 0). The class is a MonStats Id (first
          row with that Id) or a record index. For each difficulty asked: the flags, every per-difficulty
          stat cell (Level, minHP/maxHP, AC, Exp, A1/A2/S1 damage and to-hit, resistances, Drain,
          coldeffect, ToBlock, El1..El3 Pct/MinD/MaxD/Dur; "(blank)" = empty .txt cell, which decodes
          as 0), the one-value columns (MonProp, SkillDamage, Crit, DamageRegen, El modes and types),
          the skills, the class's MonProp slots of that difficulty, the MonLvl row at the class's own
          MonStats level of that difficulty (classic and L- columns; no Levels MonLvlEx override is
          applied, which is an omission of the survey, not a claim) and the DifficultyLevels row.
          With class `all` every record is formatted (printed only with --print), then the summary:
          blank patterns per stat group and difficulty, the records with no core stats, flag counts,
          min > max checks, resistance ranges, the MonProp users.

The last line is a `SURVEY mon_<cmd> key=value ...` summary of integer counts. Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402

NONE = 0xFFFF
DIFFS = [("normal", "mon"), ("nightmare", "nmon"), ("hell", "nmon")]


def decode(excel_dir, table):
    lay = LAYOUTS[table]
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (table, size)
    out = []
    for rec in recs:
        d = {}
        for f in lay["fields"]:
            d[f.get("name") or f["col"]] = decode_field(rec, f)
        out.append(d)
    return out


def txt_rows(excel_dir, table):
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    return [dict(zip(header, r)) for r in rows]


def pool(lv, prefix, slots=range(1, 11)):
    return [lv["%s%d" % (prefix, k)] for k in slots if lv["%s%d" % (prefix, k)] != NONE]


def cmd_levels(excel_dir, list_all=False):
    levels = decode(excel_dir, "levels")
    ltxt = txt_rows(excel_dir, "levels")
    mons = decode(excel_dir, "monstats")
    mtxt = txt_rows(excel_dir, "monstats")
    ids = [r["Id"] for r in mtxt]
    distinct = list(dict.fromkeys(ids))
    summary = collections.OrderedDict()
    summary["levels"] = len(levels)

    def enabled(o):
        return mons[o]["enabled"] if 0 <= o < len(mons) else None

    print("Pool column sets (slots 1..10), over %d levels" % len(levels))
    print("set   empty  over_nummon  dup_class  names_disabled  disabled_entries  entries  pos_vs_id"
          "  rarity0_entries  isspawn0_entries")
    for prefix in ("mon", "nmon", "umon"):
        empty = over = dup = dis = dis_e = ent = posid = rar0 = spw0 = 0
        for lv in levels:
            p = pool(lv, prefix)
            ent += len(p)
            empty += not p
            over += len(p) > lv["NumMon"]
            dup += len(set(p)) != len(p)
            bad = [o for o in p if enabled(o) == 0]
            dis += bool(bad)
            dis_e += len(bad)
            posid += sum(1 for o in p if o < len(ids) and ids[o] != distinct[o])
            rar0 += sum(1 for o in p if mons[o]["Rarity"] == 0)
            spw0 += sum(1 for o in p if mons[o]["isSpawn"] == 0)
        print("%-5s %5d  %11d  %9d  %14d  %16d  %7d  %9d  %15d  %16d"
              % (prefix, empty, over, dup, dis, dis_e, ent, posid, rar0, spw0))
        for k, v in (("empty", empty), ("over_nummon", over), ("dup", dup), ("disabled", dis),
                     ("disabled_entries", dis_e), ("entries", ent), ("pos_vs_id", posid),
                     ("rarity0_entries", rar0), ("isspawn0_entries", spw0)):
            summary["%s_%s" % (prefix, k)] = v
    hi = sum(1 for lv in levels for pre in ("mon", "nmon", "umon")
             for k in range(11, 26) if lv["%s%d" % (pre, k)] != NONE)
    summary["slots_11_25_used"] = hi
    print("slots 11..25 holding a value other than 0xFFFF: %d" % hi)

    print("\nPer difficulty (mapping: normal->mon, nightmare->nmon, hell->nmon)")
    print("difficulty  MonDen=0  empty  empty_with_MonDen  over_nummon  names_disabled")
    for di, (dname, prefix) in enumerate(DIFFS):
        den = "MonDen" + ["", "(N)", "(H)"][di]
        zero = empty = empty_den = over = dis = 0
        for lv in levels:
            p = pool(lv, prefix)
            zero += lv[den] == 0
            empty += not p
            empty_den += (not p) and lv[den] != 0
            over += len(p) > lv["NumMon"]
            dis += any(enabled(o) == 0 for o in p)
        print("%-10s  %8d  %5d  %17d  %11d  %14d" % (dname, zero, empty, empty_den, over, dis))
        for k, v in (("monden0", zero), ("empty", empty), ("empty_with_monden", empty_den),
                     ("over_nummon", over), ("disabled", dis)):
            summary["%s_%s" % (dname, k)] = v

    empty_names = [r["Name"] for lv, r in zip(levels, ltxt) if not pool(lv, "mon") and not pool(lv, "nmon")]
    print("levels with mon and nmon both empty: %d: %s" % (len(empty_names), ", ".join(empty_names)))
    nm0 = sum(1 for lv in levels if lv["NumMon"] == 0)
    nm0_empty = sum(1 for lv in levels if lv["NumMon"] == 0 and not pool(lv, "mon") and not pool(lv, "nmon"))
    print("NumMon 0: %d levels, %d of them with mon and nmon empty" % (nm0, nm0_empty))
    summary.update(nummon0=nm0, nummon0_empty=nm0_empty)
    print("\nNumMon distribution: %s" % dict(sorted(collections.Counter(lv["NumMon"] for lv in levels).items())))
    print("NumMon blank in .txt: %d" % sum(1 for r in ltxt if r["NumMon"] == ""))
    print("\nBlank cells in the per-difficulty columns (.txt):")
    for base in ("MonDen", "MonUMin", "MonUMax", "MonLvl1Ex"):
        if base == "MonLvl1Ex":
            cols = ["MonLvl1Ex", "MonLvl2Ex", "MonLvl3Ex"]
        else:
            cols = [base, base + "(N)", base + "(H)"]
        blank = [sum(1 for r in ltxt if r[c] == "") for c in cols]
        mixed = sum(1 for r in ltxt if len({r[c] == "" for c in cols}) > 1)
        print("  %-28s blank %s, rows mixing blank and set %d" % ("/".join(cols), blank, mixed))
        summary["blank_%s" % base.lower()] = sum(blank)
        summary["mixed_%s" % base.lower()] = mixed
    blank_lvl = sum(1 for r in ltxt for c in ("MonLvl1", "MonLvl2", "MonLvl3") if r[c] == "")
    print("  MonLvl1..3 blank cells: %d" % blank_lvl)

    print("\nCritters (cmon1..4 / cpct1..4 / camt1..4):")
    crit = sum(1 for lv in levels if pool(lv, "cmon", range(1, 5)))
    cpct_without = sum(1 for lv in levels for k in range(1, 5)
                       if lv["cmon%d" % k] == NONE and lv["cpct%d" % k] != 0)
    cmon_zero_pct = sum(1 for lv in levels for k in range(1, 5)
                        if lv["cmon%d" % k] != NONE and lv["cpct%d" % k] == 0)
    camt = sum(1 for lv in levels for k in range(1, 5) if lv["camt%d" % k] != 0)
    pct = collections.Counter(lv["cpct%d" % k] for lv in levels for k in range(1, 5) if lv["cmon%d" % k] != NONE)
    print("  levels with a critter: %d; cpct set without cmon: %d; cmon with cpct 0: %d; camt non-zero: %d"
          % (crit, cpct_without, cmon_zero_pct, camt))
    print("  cpct values for named critters: %s" % dict(sorted(pct.items())))
    crit_dis = sum(1 for lv in levels for o in pool(lv, "cmon", range(1, 5)) if enabled(o) == 0)
    print("  critter entries naming a class with enabled 0: %d" % crit_dis)
    summary.update(critter_levels=crit, critter_cpct_no_cmon=cpct_without, critter_cmon_pct0=cmon_zero_pct,
                   critter_camt_nonzero=camt, critter_disabled=crit_dis)

    if list_all:
        print("\nid  name                          NumMon  mon  nmon  umon  disabled(mon/nmon/umon)")
        for lv, r in zip(levels, ltxt):
            p = [pool(lv, x) for x in ("mon", "nmon", "umon")]
            d = [sum(1 for o in q if enabled(o) == 0) for q in p]
            print("%3d %-30s %6d  %3d  %4d  %4d  %s" % (lv["Id"], r["Name"][:30], lv["NumMon"],
                                                      len(p[0]), len(p[1]), len(p[2]), "/".join(map(str, d))))
    print("SURVEY mon_levels " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


def cmd_monstats(excel_dir):
    mons = decode(excel_dir, "monstats")
    mtxt = txt_rows(excel_dir, "monstats")
    summary = collections.OrderedDict(records=len(mons))
    flags = ["enabled", "isSpawn", "noRatio", "killable", "npc", "boss", "primeevil", "SetBoss", "BossXfer",
             "inTown", "neverCount", "petIgnore", "genericSpawn", "zoo", "placespawn", "isMelee", "rangedtype"]
    print("flag bits set (of %d records):" % len(mons))
    for f in flags:
        n = sum(m[f] for m in mons)
        print("  %-13s %4d" % (f, n))
        summary["bit_" + f.lower()] = n
    lv = [(m["Level"], m["Level(N)"], m["Level(H)"]) for m in mons]
    mono = sum(1 for a, b, c in lv if a <= b <= c)
    print("\nLevel/Level(N)/Level(H): ranges %s / %s / %s; non-decreasing in %d records; all zero in %d"
          % ((min(x[0] for x in lv), max(x[0] for x in lv)), (min(x[1] for x in lv), max(x[1] for x in lv)),
             (min(x[2] for x in lv), max(x[2] for x in lv)), mono, sum(1 for x in lv if x == (0, 0, 0))))
    summary.update(level_nondecreasing=mono, level_allzero=sum(1 for x in lv if x == (0, 0, 0)))
    en = [m for m in mons if m["enabled"]]
    print("Rarity (enabled records): %s" % dict(sorted(collections.Counter(m["Rarity"] for m in en).items())))
    print("Rarity (disabled records): %s" % dict(sorted(collections.Counter(m["Rarity"] for m in mons
                                                                            if not m["enabled"]).items())))
    summary["enabled_rarity0"] = sum(1 for m in en if m["Rarity"] == 0)
    grp_bad = sum(1 for m in mons if m["MinGrp"] > m["MaxGrp"])
    party_bad = sum(1 for m in mons if m["PartyMin"] > m["PartyMax"])
    print("MinGrp > MaxGrp: %d; PartyMin > PartyMax: %d" % (grp_bad, party_bad))
    print("MinGrp/MaxGrp pairs: %s" % dict(sorted(collections.Counter((m["MinGrp"], m["MaxGrp"]) for m in mons).items())))
    print("PartyMin/PartyMax pairs: %s" % dict(sorted(collections.Counter((m["PartyMin"], m["PartyMax"])
                                                                         for m in mons).items())))
    summary.update(mingrp_gt_maxgrp=grp_bad, partymin_gt_partymax=party_bad)
    for c in ("minion1", "minion2", "spawn"):
        refs = [m[c] for m in mons if m[c] != NONE]
        dis = sum(1 for o in refs if not mons[o]["enabled"])
        print("%s: %d set, %d pointing at a record with enabled 0" % (c, len(refs), dis))
        summary["%s_set" % c] = len(refs)
        summary["%s_disabled" % c] = dis
    party_nominion = sum(1 for m in mons if m["PartyMax"] and m["minion1"] == NONE)
    minion_noparty = sum(1 for m in mons if m["minion1"] != NONE and not m["PartyMax"])
    print("PartyMax > 0 without minion1: %d; minion1 set with PartyMax 0: %d" % (party_nominion, minion_noparty))
    summary.update(party_without_minion=party_nominion, minion_without_party=minion_noparty)
    print("SURVEY mon_monstats " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


def _rng(vals):
    return "%d..%d" % (min(vals), max(vals)) if vals else "-"


def _class_stats(mons, classes):
    """Counts over a set of monstats ordinals -> OrderedDict of ints, plus printable ranges."""
    ms = [mons[o] for o in sorted(classes)]
    st = collections.OrderedDict()
    st["classes"] = len(ms)
    for c in ("MinGrp", "MaxGrp", "PartyMin", "PartyMax"):
        v = [m[c] for m in ms]
        st[c.lower() + "_min"] = min(v) if v else 0
        st[c.lower() + "_max"] = max(v) if v else 0
    st["party_nonzero"] = sum(1 for m in ms if m["PartyMax"])
    st["minion1"] = sum(1 for m in ms if m["minion1"] != NONE)
    st["minion2"] = sum(1 for m in ms if m["minion2"] != NONE)
    st["spawn"] = sum(1 for m in ms if m["spawn"] != NONE)
    st["placespawn"] = sum(1 for m in ms if m["placespawn"])
    st["spawn_placespawn"] = sum(1 for m in ms if m["spawn"] != NONE and m["placespawn"])
    st["setboss"] = sum(1 for m in ms if m["SetBoss"])
    st["bossxfer"] = sum(1 for m in ms if m["BossXfer"])
    st["ismelee"] = sum(1 for m in ms if m["isMelee"])
    st["npc"] = sum(1 for m in ms if m["npc"])
    st["intown"] = sum(1 for m in ms if m["inTown"])
    st["align_nonzero"] = sum(1 for m in ms if m["Align"])
    return st


def cmd_spawn(excel_dir):
    levels = decode(excel_dir, "levels")
    ltxt = txt_rows(excel_dir, "levels")
    mons = decode(excel_dir, "monstats")
    ids = [r["Id"] for r in txt_rows(excel_dir, "monstats")]
    names = [r["Name"] for r in ltxt]
    summary = collections.OrderedDict()
    for di, (dname, prefix) in enumerate(DIFFS):
        sfx = ["", "(N)", "(H)"][di]
        den, umin, umax = "MonDen" + sfx, "MonUMin" + sfx, "MonUMax" + sfx
        print("== %s (pool %s, %s, %s/%s)" % (dname, prefix, den, umin, umax))
        zero = [i for i, lv in enumerate(levels) if lv[den] == 0]
        print("MonDen 0: %d levels: %s" % (len(zero), ", ".join(names[i] for i in zero)))
        live = [lv for lv in levels if lv[den] != 0]
        dens = collections.Counter(lv[den] for lv in live)
        print("MonDen non-zero: %d levels, values %s, distribution %s"
              % (len(live), _rng(list(dens)), dict(sorted(dens.items()))))
        classes = {o for lv in live for o in pool(lv, prefix, range(1, 26))}
        st = _class_stats(mons, classes)
        print("pool classes (levels with MonDen != 0): %d; MinGrp %d..%d, MaxGrp %d..%d, PartyMin %d..%d, "
              "PartyMax %d..%d" % (st["classes"], st["mingrp_min"], st["mingrp_max"], st["maxgrp_min"],
                                   st["maxgrp_max"], st["partymin_min"], st["partymin_max"],
                                   st["partymax_min"], st["partymax_max"]))
        print("  MinGrp/MaxGrp pairs: %s" % dict(sorted(collections.Counter(
            (mons[o]["MinGrp"], mons[o]["MaxGrp"]) for o in classes).items())))
        print("  PartyMin/PartyMax pairs: %s" % dict(sorted(collections.Counter(
            (mons[o]["PartyMin"], mons[o]["PartyMax"]) for o in classes).items())))
        print("  with PartyMax>0 %d, minion1 %d, minion2 %d, spawn %d, placespawn %d, spawn+placespawn %d"
              % (st["party_nonzero"], st["minion1"], st["minion2"], st["spawn"], st["placespawn"],
                 st["spawn_placespawn"]))
        print("  flags: SetBoss %d, BossXfer %d, isMelee %d, npc %d, inTown %d, Align>0 %d"
              % (st["setboss"], st["bossxfer"], st["ismelee"], st["npc"], st["intown"], st["align_nonzero"]))
        sp = sorted(o for o in classes if mons[o]["spawn"] != NONE)
        print("  spawn classes: %s" % ", ".join("%s->%s%s" % (ids[o], ids[mons[o]["spawn"]],
                                                              "(placespawn)" if mons[o]["placespawn"] else "")
                                                for o in sp))
        pairs = collections.Counter((lv[umin], lv[umax]) for lv in live)
        print("MonUMin/MonUMax pairs (levels with MonDen != 0): %s; min > max: %d"
              % (dict(sorted(pairs.items())), sum(n for (a, b), n in pairs.items() if a > b)))
        summary["%s_monden0" % dname] = len(zero)
        summary["%s_monden_min" % dname] = min(dens) if dens else 0
        summary["%s_monden_max" % dname] = max(dens) if dens else 0
        for k, v in st.items():
            summary["%s_%s" % (dname, k)] = v
        summary["%s_umpairs" % dname] = len(pairs)
        summary["%s_umin_gt_umax" % dname] = sum(n for (a, b), n in pairs.items() if a > b)
        print()
    live = [lv for lv in levels if lv["MonDen"] != 0]
    uclasses = {o for lv in live for o in pool(lv, "umon", range(1, 26))}
    st = _class_stats(mons, uclasses)
    print("== umon classes (normal; levels with MonDen != 0): %d; MinGrp %d..%d, MaxGrp %d..%d, PartyMin %d..%d, "
          "PartyMax %d..%d; minion1 %d, spawn %d, placespawn %d"
          % (st["classes"], st["mingrp_min"], st["mingrp_max"], st["maxgrp_min"], st["maxgrp_max"],
             st["partymin_min"], st["partymin_max"], st["partymax_min"], st["partymax_max"],
             st["minion1"], st["spawn"], st["placespawn"]))
    for k in ("classes", "minion1", "spawn", "placespawn"):
        summary["umon_" + k] = st[k]
    print()
    for c in ("MonWndr", "MonSpcWalk"):
        dist = collections.Counter(lv[c] for lv in levels)
        blank = sum(1 for r in ltxt if r[c] == "")
        nz = [names[i] for i, lv in enumerate(levels) if lv[c]]
        print("%s (all difficulties): %s; blank %d; non-zero on %d levels (%d with MonDen 0)"
              % (c, dict(sorted(dist.items())), blank, len(nz),
                 sum(1 for lv in levels if lv[c] and lv["MonDen"] == 0)))
        print("  %s" % ", ".join(nz))
        summary[c.lower() + "_nonzero"] = len(nz)
    print("SURVEY mon_spawn " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


COLL_COLS = ("SizeX", "SizeY", "spawnCol", "objCol", "deadCol", "inert", "unflatDead")


def cmd_collision(excel_dir):
    """MonStats2 footprint and collision columns over the pool classes (plan 0017 Phase 0)."""
    levels = decode(excel_dir, "levels")
    mons = decode(excel_dir, "monstats")
    m2 = decode(excel_dir, "monstats2")
    ids = [r["Id"] for r in txt_rows(excel_dir, "monstats")]
    m2txt = txt_rows(excel_dir, "monstats2")
    assert len(m2txt) == len(m2), (len(m2txt), len(m2))
    summary = collections.OrderedDict()

    def rec(o):
        return m2[mons[o]["MonStatsEx"]]

    def cell(o, c):
        r = rec(o)
        return "blank" if m2txt[mons[o]["MonStatsEx"]][c] == "" else r[c]

    def report(tag, classes):
        classes = sorted(classes)
        print("== %s: %d classes, %d distinct MonStats2 rows" % (
            tag, len(classes), len({mons[o]["MonStatsEx"] for o in classes})))
        for c in COLL_COLS:
            dist = collections.Counter(cell(o, c) for o in classes)
            print("  %-10s %s" % (c, ", ".join("%s=%d" % kv for kv in sorted(dist.items(), key=lambda kv: str(kv[0])))))
        pairs = collections.Counter((rec(o)["SizeX"], rec(o)["SizeY"]) for o in classes)
        print("  (SizeX, SizeY) %s; SizeX != SizeY: %d" % (
            dict(sorted(pairs.items())), sum(n for (x, y), n in pairs.items() if x != y)))
        sc = collections.Counter((rec(o)["SizeX"], cell(o, "spawnCol")) for o in classes)
        print("  (SizeX, spawnCol) %s" % ", ".join("%s=%d" % kv for kv in sorted(sc.items(), key=str)))
        for v in (1, 2, 3):
            hit = [o for o in classes if rec(o)["spawnCol"] == v]
            print("  spawnCol %d: %d classes%s" % (v, len(hit), (": " + ", ".join(
                "%s(SizeX %d)" % (ids[o], rec(o)["SizeX"]) for o in hit)) if hit else ""))
            summary["%s_spawncol%d" % (tag, v)] = len(hit)
        summary["%s_classes" % tag] = len(classes)
        for x in range(4):
            summary["%s_sizex%d" % (tag, x)] = sum(1 for o in classes if rec(o)["SizeX"] == x)
        summary["%s_sizex_ne_sizey" % tag] = sum(n for (x, y), n in pairs.items() if x != y)
        summary["%s_objcol" % tag] = sum(1 for o in classes if rec(o)["objCol"])
        summary["%s_deadcol" % tag] = sum(1 for o in classes if rec(o)["deadCol"])
        print()

    every = set()
    for di, (dname, prefix) in enumerate(DIFFS):
        den = "MonDen" + ["", "(N)", "(H)"][di]
        classes = {o for lv in levels if lv[den] != 0 for o in pool(lv, prefix, range(1, 26))}
        every |= classes
        if dname != "hell":     # hell reads the nmon columns too (same set as nightmare)
            report(dname, classes)
    uclasses = {o for lv in levels if lv["MonDen"] != 0 for o in pool(lv, "umon", range(1, 26))}
    report("umon", uclasses)
    report("pool", every | uclasses)    # the 362 pool classes of docs/tables/MonStats.md, Spawn columns
    report("all", range(len(mons)))
    allm2 = collections.Counter(r["spawnCol"] for r in m2)
    print("MonStats2 rows (609, every row): spawnCol %s, SizeX %s" % (
        dict(sorted(allm2.items())), dict(sorted(collections.Counter(r["SizeX"] for r in m2).items()))))
    print("SURVEY mon_collision " + " ".join("%s=%d" % kv for kv in summary.items()))


DIFF3 = [("normal", ""), ("nightmare", " (N)"), ("hell", " (H)")]


def cmd_umod(excel_dir):
    um = decode(excel_dir, "monumod")
    utxt = txt_rows(excel_dir, "monumod")
    mt = [r["type"] for r in txt_rows(excel_dir, "montype")]
    names = [r["uniquemod"] for r in utxt]
    summary = collections.OrderedDict(records=len(um))

    def mtn(i):
        return "-" if i == 0 else mt[i]

    print("MonUMod, %d records (decoded from monumod.bin)" % len(um))
    print("%3s %-22s %3s %4s %4s %4s %5s %-10s %-10s %-11s %-11s %5s %5s  %s"
          % ("id", "uniquemod", "en", "ver", "xfer", "chmp", "fPick", "exclude1", "exclude2",
             "cpick N/NM/H", "upick N/NM/H", "fInit", "const", "*constant desc"))
    for i, (r, t) in enumerate(zip(um, utxt)):
        print("%3d %-22s %3d %4d %4d %4d %5d %-10s %-10s %-11s %-11s %5d %5d  %s"
              % (r["id"], names[i], r["enabled"], r["version"], r["xfer"], r["champion"], r["fPick"],
                 mtn(r["exclude1"]), mtn(r["exclude2"]),
                 "/".join(str(r["cpick" + d]) for _, d in DIFF3),
                 "/".join(str(r["upick" + d]) for _, d in DIFF3), r["fInit"], r["constants"],
                 t["*constant desc"]))
    summary["id_eq_index"] = sum(1 for i, r in enumerate(um) if r["id"] == i)
    summary["enabled0"] = sum(1 for r in um if r["enabled"] == 0)
    summary["version100"] = sum(1 for r in um if r["version"] == 100)
    summary["xfer1"] = sum(1 for r in um if r["xfer"])
    summary["champion1"] = sum(1 for r in um if r["champion"])
    summary["fpick_nonzero"] = sum(1 for r in um if r["fPick"])
    summary["finit_nonzero"] = sum(1 for r in um if r["fInit"])
    summary["constants_listed"] = sum(1 for t in utxt if t["constants"] != "")
    print("\nPick weights per difficulty (records with a non-zero weight; [*] = enabled 0, [x] = version 100)")
    for kind in ("cpick", "upick"):
        for dname, d in DIFF3:
            col = kind + d
            nz = [(i, r[col]) for i, r in enumerate(um) if r[col]]
            mark = lambda i: ("*" if um[i]["enabled"] == 0 else "") + ("x" if um[i]["version"] == 100 else "")
            cl = sum(w for i, w in nz if um[i]["enabled"] and um[i]["version"] == 0)
            ex = sum(w for i, w in nz if um[i]["enabled"])
            print("%-15s %-9s n=%2d sum=%3d classic=%3d expansion=%3d: %s"
                  % (col, dname, len(nz), sum(w for _, w in nz), cl, ex,
                     ", ".join("%s(%d)%s=%d" % (names[i], i, mark(i), w) for i, w in nz)))
            key = "%s_%s" % (kind, dname)
            summary[key + "_n"] = len(nz)
            summary[key + "_sum"] = sum(w for _, w in nz)
            summary[key + "_classic"] = cl
            summary[key + "_expansion"] = ex
    pairs = [(i, c, r[c]) for i, r in enumerate(um) for c in ("exclude1", "exclude2") if r[c]]
    print("\nexclude pairs (mod, column, montype): %s" % (
        ", ".join("%s(%d) %s=%s(%d)" % (names[i], i, c, mt[v], v) for i, c, v in pairs) or "none"))
    summary["exclude_pairs"] = len(pairs)
    fp = [(i, r["fPick"]) for i, r in enumerate(um) if r["fPick"]]
    print("fPick non-zero: %s" % ", ".join("%s(%d)=%d" % (names[i], i, v) for i, v in fp))
    print("SURVEY mon_umod " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


def cmd_superuniques(excel_dir):
    su = decode(excel_dir, "superuniques")
    stxt = [t for t in txt_rows(excel_dir, "superuniques") if t["Superunique"] != "Expansion"]
    mons = decode(excel_dir, "monstats")
    mids = [r["Id"] for r in txt_rows(excel_dir, "monstats")]
    umn = [r["uniquemod"] for r in txt_rows(excel_dir, "monumod")]
    preset = decode(excel_dir, "monpreset")
    named = collections.Counter(p["Place"] for p in preset if p["PlaceKind"] == 2)
    summary = collections.OrderedDict(records=len(su))
    cols = ["AutoPos", "EClass", "Stacks", "Replaceable"]
    print("SuperUniques, %d records (decoded from superuniques.bin)" % len(su))
    print("%3s %-26s %-14s %-38s %-7s %-4s %-4s %-4s %-4s %-8s %-14s %s"
          % ("rec", "Superunique", "Class", "Mod1/Mod2/Mod3", "Grp", "Auto", "ECls", "Stck", "Repl",
             "Utrans", "minion1", "MonPreset"))
    for i, (r, t) in enumerate(zip(su, stxt)):
        mods = "/".join("%s(%d)" % (umn[r[m]], r[m]) if r[m] else "-" for m in ("Mod1", "Mod2", "Mod3"))
        m1 = mons[r["Class"]]["minion1"]
        print("%3d %-26s %-14s %-38s %-7s %-4d %-4d %-4d %-4d %-8s %-14s %d"
              % (i, t["Superunique"], mids[r["Class"]], mods, "%d..%d" % (r["MinGrp"], r["MaxGrp"]),
                 r["AutoPos"], r["EClass"], r["Stacks"], r["Replaceable"],
                 "%d/%d/%d" % (r["Utrans"], r["Utrans(N)"], r["Utrans(H)"]),
                 mids[m1] if m1 != NONE and m1 < len(mids) else "-", named[i]))
    print()
    for c in ["Mod1", "Mod2", "Mod3"]:
        dist = collections.Counter(umn[r[c]] if r[c] else "-" for r in su)
        print("%s: %s" % (c, dict(sorted(dist.items(), key=lambda kv: -kv[1]))))
        summary[c.lower() + "_set"] = sum(1 for r in su if r[c])
    nmods = collections.Counter(sum(1 for c in ("Mod1", "Mod2", "Mod3") if r[c]) for r in su)
    print("fixed mods per record: %s" % dict(sorted(nmods.items())))
    order = sum(1 for r in su if not (r["Mod1"] or not r["Mod2"]) or (r["Mod3"] and not r["Mod2"]))
    print("records with a gap (ModN set after a blank Mod): %d" % order)
    summary["mod_gap"] = order
    grp = collections.Counter((r["MinGrp"], r["MaxGrp"]) for r in su)
    print("MinGrp..MaxGrp: %s" % dict(sorted(grp.items())))
    summary["min_gt_max"] = sum(1 for r in su if r["MinGrp"] > r["MaxGrp"])
    summary["grp_zero"] = sum(1 for r in su if r["MaxGrp"] == 0)
    summary["minion1_none"] = sum(1 for r in su if mons[r["Class"]]["minion1"] == NONE)
    print("min > max: %d; MaxGrp 0: %d; class with no minion1: %d"
          % (summary["min_gt_max"], summary["grp_zero"], summary["minion1_none"]))
    for c in cols:
        on = [stxt[i]["Superunique"] for i, r in enumerate(su) if r[c]]
        print("%s = 1 on %d: %s" % (c, len(on), ", ".join(on)))
        summary[c.lower()] = len(on)
    ut = collections.Counter(r["Utrans"] for r in su)
    summary["utrans_differ"] = sum(1 for r in su if not (r["Utrans"] == r["Utrans(N)"] == r["Utrans(H)"]))
    print("Utrans: %d distinct, %d records where the three differ" % (len(ut), summary["utrans_differ"]))
    summary["monpreset_named"] = len(named)
    print("records named by MonPreset (kind 2): %d of %d" % (len(named), len(su)))
    print("SURVEY mon_superuniques " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


# ---------------------------------------------------------------- stats (plan 0025 Phase 0)

DIFF_NAMES = ["normal", "nightmare", "hell"]
# per-difficulty stat columns: base name -> the three .txt/layout column names
_STAT_TRI = {
    "Level": ["Level", "Level(N)", "Level(H)"],
    "minHP": ["minHP", "MinHP(N)", "MinHP(H)"],
    "maxHP": ["maxHP", "MaxHP(N)", "MaxHP(H)"],
}
for _b in ["AC", "Exp", "A1TH", "A2TH", "S1TH", "A1MinD", "A1MaxD", "A2MinD", "A2MaxD", "S1MinD", "S1MaxD",
           "ResDm", "ResMa", "ResFi", "ResLi", "ResCo", "ResPo", "Drain", "coldeffect", "ToBlock"] \
        + ["El%d%s" % (e, c) for e in (1, 2, 3) for c in ("Pct", "MinD", "MaxD", "Dur")]:
    _STAT_TRI[_b] = [_b, _b + "(N)", _b + "(H)"]
# groups of the per-difficulty stat columns (for the blank patterns)
STAT_GROUPS = collections.OrderedDict([
    ("level", ["Level"]),
    ("hp", ["minHP", "maxHP"]),
    ("ac_exp", ["AC", "Exp"]),
    ("a1", ["A1MinD", "A1MaxD", "A1TH"]),
    ("a2", ["A2MinD", "A2MaxD", "A2TH"]),
    ("s1", ["S1MinD", "S1MaxD", "S1TH"]),
    ("res", ["ResDm", "ResMa", "ResFi", "ResLi", "ResCo", "ResPo"]),
    ("misc", ["Drain", "coldeffect", "ToBlock"]),
] + [("el%d" % e, ["El%d%s" % (e, c) for c in ("Pct", "MinD", "MaxD", "Dur")]) for e in (1, 2, 3)])
# difficulty-independent columns shown beside them
STAT_ONE = ["MonProp", "SkillDamage", "Crit", "DamageRegen", "El1Mode", "El1Type", "El2Mode", "El2Type",
            "El3Mode", "El3Type"]
STAT_FLAGS = ["enabled", "killable", "npc", "inTown", "interact", "boss", "primeevil", "noRatio", "SetBoss",
              "BossXfer", "isMelee", "lUndead", "hUndead", "demon", "NoShldBlock", "noAura", "neverCount"]
MONLVL_COLS = ["AC", "TH", "HP", "DM", "XP"]


def _stats_load(excel_dir):
    t = dict(mons=decode(excel_dir, "monstats"), mtxt=txt_rows(excel_dir, "monstats"),
             lvl=decode(excel_dir, "monlvl"), prop=decode(excel_dir, "monprop"),
             ptxt=txt_rows(excel_dir, "monprop"), dl=decode(excel_dir, "difficultylevels"),
             dltxt=txt_rows(excel_dir, "difficultylevels"))
    t["props"] = [r["code"] for r in txt_rows(excel_dir, "properties")]
    t["skills"] = [r["skill"] for r in txt_rows(excel_dir, "skills")]
    t["elem"] = [r["Code"] for r in txt_rows(excel_dir, "elemtypes")]
    t["modes"] = [r["code"] for r in txt_rows(excel_dir, "monmode")]
    return t


def _cell(t, i, col):
    """(decoded value, .txt cell) of monstats record i; the cell is '' when blank."""
    return t["mons"][i][col], t["mtxt"][i].get(col, "")


def _show(v, cell):
    return "%d" % v if cell != "" else "(blank)"


def _stats_block(t, i, d, out):
    m, tx = t["mons"][i], t["mtxt"][i]
    flags = [f for f in STAT_FLAGS if m[f]]
    out.append("monstats record %d  Id %s  hcIdx %s  difficulty %d (%s)"
               % (i, tx["Id"], tx["hcIdx"], d, DIFF_NAMES[d]))
    out.append("  flags set: %s" % (" ".join(flags) if flags else "-"))
    out.append("  per-difficulty columns (column = decoded value; (blank) = empty .txt cell):")
    for g, bases in STAT_GROUPS.items():
        out.append("    %-7s %s" % (g, "  ".join("%s=%s" % (_STAT_TRI[b][d], _show(*_cell(t, i, _STAT_TRI[b][d])))
                                                 for b in bases)))
    one = []
    for c in STAT_ONE:
        v, cell = _cell(t, i, c)
        name = cell if cell != "" else "(blank)"
        one.append("%s=%s[%d]" % (c, name, v) if c in ("MonProp", "SkillDamage") or c.startswith("El")
                   else "%s=%s" % (c, _show(v, cell)))
    out.append("  one value for all difficulties: %s" % "  ".join(one))
    sk = ["%s/lvl %d" % (tx["Skill%d" % k], m["Sk%dlvl" % k]) for k in range(1, 9) if tx["Skill%d" % k]]
    out.append("  skills: %s" % (", ".join(sk) if sk else "-"))
    # MonProp row, this difficulty's six slots
    p = m["MonProp"]
    if 0 <= p < len(t["prop"]) and t["mtxt"][i]["MonProp"] != "":
        r, s = t["prop"][p], ["", " (N)", " (H)"][d]
        slots = ["%s par=%d chance=%d min=%d max=%d" % (t["props"][r["prop%d%s" % (k, s)]], r["par%d%s" % (k, s)],
                                                       r["chance%d%s" % (k, s)], r["min%d%s" % (k, s)],
                                                       r["max%d%s" % (k, s)])
                 for k in range(1, 7) if r["prop%d%s" % (k, s)] >= 0]
        out.append("  MonProp row %d (%s): %s" % (p, t["ptxt"][p]["Id"], "; ".join(slots) if slots else "no slot set"))
    else:
        out.append("  MonProp: none")
    # MonLvl row at the MonStats level of this difficulty (no Levels MonLvlEx override applied here)
    lv = m[_STAT_TRI["Level"][d]]
    row = t["lvl"][min(lv, len(t["lvl"]) - 1)]
    sfx = ["", "(N)", "(H)"][d]
    out.append("  MonLvl row %d (MonStats %s; capped at %d): classic %s | L- %s"
               % (min(lv, len(t["lvl"]) - 1), _STAT_TRI["Level"][d], len(t["lvl"]) - 1,
                  " ".join("%s=%d" % (c, row[c + sfx]) for c in MONLVL_COLS),
                  " ".join("%s=%d" % (c, row["L-" + c + sfx]) for c in MONLVL_COLS)))
    dl = t["dl"][d]
    out.append("  DifficultyLevels row %d (%s): %s" % (d, t["dltxt"][d]["Name"],
                                                     " ".join("%s=%d" % kv for kv in dl.items())))


def _find_class(t, key):
    if key.isdigit():
        i = int(key)
        return [i] if 0 <= i < len(t["mons"]) else []
    return [i for i, r in enumerate(t["mtxt"]) if r["Id"] == key][:1]


def cmd_stats(excel_dir, key, diff, print_all=False):
    t = _stats_load(excel_dir)
    n = len(t["mons"])
    if diff in DIFF_NAMES:
        diffs = [DIFF_NAMES.index(diff)]
    elif diff in ("0", "1", "2"):
        diffs = [int(diff)]
    elif diff == "all":
        diffs = [0, 1, 2]
    else:
        print("difficulty must be normal|nightmare|hell|0|1|2|all")
        return 2
    recs = list(range(n)) if key == "all" else _find_class(t, key)
    if not recs:
        print("no monstats record %r" % key)
        return 2
    blocks = 0
    for i in recs:
        for d in diffs:
            out = []
            _stats_block(t, i, d, out)
            blocks += 1
            if key != "all" or print_all:
                print("\n".join(out))
                print()
    summary = collections.OrderedDict(records=len(recs), blocks=blocks)
    if key != "all":
        print("SURVEY mon_stats " + " ".join("%s=%d" % kv for kv in summary.items()))
        return 0
    _stats_summary(t, summary)
    print("SURVEY mon_stats " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


def _stats_summary(t, summary):
    """Blank patterns and value checks over every monstats record (key 'all')."""
    mons, mtxt = t["mons"], t["mtxt"]
    n = len(mons)
    blank = lambda i, c: mtxt[i][c] == ""  # noqa: E731
    print("Per-difficulty stat column groups over %d monstats records: records with every cell of the group "
          "blank / some blank / none blank" % n)
    print("%-7s %-9s %6s %6s %6s" % ("group", "diff", "all", "some", "none"))
    for g, bases in STAT_GROUPS.items():
        for d in range(3):
            cols = [_STAT_TRI[b][d] for b in bases]
            k = [sum(blank(i, c) for c in cols) for i in range(n)]
            a = sum(1 for x in k if x == len(cols))
            s = sum(1 for x in k if 0 < x < len(cols))
            print("%-7s %-9s %6d %6d %6d" % (g, DIFF_NAMES[d], a, s, n - a - s))
            summary["%s_%s_blank" % (g, DIFF_NAMES[d])] = a
            summary["%s_%s_partial" % (g, DIFF_NAMES[d])] = s
    # the hit-point / level blank pattern: which records are blank in Level and minHP for all three difficulties
    core = ["Level", "minHP", "maxHP", "AC", "Exp"]
    nostat = [i for i in range(n) if all(blank(i, _STAT_TRI[b][d]) for b in core for d in range(3))]
    summary["no_core_stats"] = len(nostat)
    print("\nrecords blank in Level, minHP, maxHP, AC and Exp in all three difficulties: %d" % len(nostat))
    for f in ["enabled", "npc", "inTown", "boss", "primeevil", "killable", "noRatio", "interact"]:
        c = sum(1 for i in nostat if mons[i][f])
        print("  of them with %s: %d" % (f, c))
        summary["no_core_stats_" + f.lower()] = c
    print("  Ids: %s" % ", ".join(mtxt[i]["Id"] for i in nostat))
    mixed = [i for i in range(n) if i not in nostat
             and any(blank(i, _STAT_TRI[b][d]) for b in core for d in range(3))]
    summary["core_partial"] = len(mixed)
    print("records with some but not all of those 15 cells blank: %d" % len(mixed))
    for i in mixed:
        bl = [_STAT_TRI[b][d] for b in core for d in range(3) if blank(i, _STAT_TRI[b][d])]
        print("  %d %s: blank %s" % (i, mtxt[i]["Id"], " ".join(bl)))
    # stat rows by flag
    print("\nflag counts over all records / over the records not in the %d above" % len(nostat) + ":")
    withstat = [i for i in range(n) if i not in nostat]
    for f in STAT_FLAGS:
        a = sum(1 for i in range(n) if mons[i][f])
        b = sum(1 for i in withstat if mons[i][f])
        print("  %-12s %4d  %4d" % (f, a, b))
        summary["flag_%s" % f.lower()] = a
        summary["flag_%s_stat" % f.lower()] = b
    for flag in ("boss", "primeevil", "npc"):
        ids = [mtxt[i]["Id"] for i in range(n) if mons[i][flag]]
        print("%s records: %s" % (flag, ", ".join(ids)))
    # value checks
    bad_hp = sum(1 for i in range(n) for d in range(3)
                 if mons[i][_STAT_TRI["minHP"][d]] > mons[i][_STAT_TRI["maxHP"][d]])
    lvl_over = sum(1 for i in range(n) for d in range(3) if mons[i][_STAT_TRI["Level"][d]] > len(t["lvl"]) - 1)
    lvl_dec = sum(1 for i in range(n) if not (mons[i]["Level"] <= mons[i]["Level(N)"] <= mons[i]["Level(H)"]))
    summary.update(minhp_gt_maxhp=bad_hp, level_over_monlvl=lvl_over, level_not_rising=lvl_dec)
    print("\nminHP > maxHP (record x difficulty): %d; Level above the last MonLvl row: %d; "
          "Level, Level(N), Level(H) not non-decreasing: %d" % (bad_hp, lvl_over, lvl_dec))
    dmg_bad = sum(1 for i in range(n) for d in range(3) for a in ("A1", "A2", "S1")
                  if mons[i][_STAT_TRI[a + "MinD"][d]] > mons[i][_STAT_TRI[a + "MaxD"][d]])
    el_bad = sum(1 for i in range(n) for d in range(3) for e in (1, 2, 3)
                 if mons[i][_STAT_TRI["El%dMinD" % e][d]] > mons[i][_STAT_TRI["El%dMaxD" % e][d]])
    summary.update(dmg_min_gt_max=dmg_bad, el_min_gt_max=el_bad)
    print("A1/A2/S1 MinD > MaxD: %d; El MinD > MaxD: %d (record x difficulty x slot)" % (dmg_bad, el_bad))
    # elements: type set without a mode, or pct set without a type
    el_type_nomode = sum(1 for i in range(n) for e in (1, 2, 3)
                         if mtxt[i]["El%dType" % e] != "" and mtxt[i]["El%dMode" % e] == "")
    el_val_notype = sum(1 for i in range(n) for e in (1, 2, 3)
                        if mtxt[i]["El%dType" % e] == ""
                        and any(mtxt[i][_STAT_TRI["El%d%s" % (e, c)][d]] not in ("", "0")
                                for c in ("Pct", "MinD", "MaxD", "Dur") for d in range(3)))
    summary.update(el_type_without_mode=el_type_nomode, el_values_without_type=el_val_notype)
    print("El type without mode: %d; El values set without a type: %d" % (el_type_nomode, el_val_notype))
    for i in range(n):
        for d in range(3):
            tri = lambda b: _STAT_TRI[b][d]  # noqa: E731
            if mons[i][tri("minHP")] > mons[i][tri("maxHP")]:
                print("  %d %s %s: %s %d > %s %d" % (i, mtxt[i]["Id"], DIFF_NAMES[d], tri("minHP"),
                                                     mons[i][tri("minHP")], tri("maxHP"), mons[i][tri("maxHP")]))
            for e in (1, 2, 3):
                lo, hi = tri("El%dMinD" % e), tri("El%dMaxD" % e)
                if mons[i][lo] > mons[i][hi]:
                    print("  %d %s %s: %s %d > %s %d" % (i, mtxt[i]["Id"], DIFF_NAMES[d], lo, mons[i][lo],
                                                         hi, mons[i][hi]))
        for e in (1, 2, 3):
            if mtxt[i]["El%dType" % e] == "" and any(
                    mtxt[i][_STAT_TRI["El%d%s" % (e, c)][d]] not in ("", "0")
                    for c in ("Pct", "MinD", "MaxD", "Dur") for d in range(3)):
                print("  %d %s: El%d values with El%dType blank (El%dMode %r)"
                      % (i, mtxt[i]["Id"], e, e, e, mtxt[i]["El%dMode" % e]))
    # resistance ranges per difficulty
    for b in ("ResDm", "ResMa", "ResFi", "ResLi", "ResCo", "ResPo"):
        rng = []
        for d in range(3):
            v = [mons[i][_STAT_TRI[b][d]] for i in range(n)]
            rng.append("%s %s, >=100 on %d" % (DIFF_NAMES[d], _rng(v), sum(1 for x in v if x >= 100)))
            summary["%s_ge100_%s" % (b.lower(), DIFF_NAMES[d])] = sum(1 for x in v if x >= 100)
        print("%s: %s" % (b, "; ".join(rng)))
    # MonProp users
    users = [(i, mtxt[i]["Id"], mtxt[i]["MonProp"]) for i in range(n) if mtxt[i]["MonProp"] != ""]
    summary["monprop_users"] = len(users)
    print("\nMonStats records naming a MonProp row: %d" % len(users))
    for i, mid, p in users:
        print("  %d %s -> %s" % (i, mid, p))
    used = {p for _, _, p in users}
    unused = [r["Id"] for r in t["ptxt"] if r["Id"] not in used]
    summary["monprop_rows_unused"] = len(unused)
    print("MonProp rows no MonStats record names: %d %s" % (len(unused), ", ".join(unused)))
    # DifficultyLevels
    print("\nDifficultyLevels rows: %s" % ", ".join(r["Name"] for r in t["dltxt"]))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, excel_dir = argv[0], argv[1]
    if cmd == "levels":
        return cmd_levels(excel_dir, "--list" in argv)
    if cmd == "monstats":
        return cmd_monstats(excel_dir)
    if cmd == "spawn":
        return cmd_spawn(excel_dir)
    if cmd == "collision":
        return cmd_collision(excel_dir)
    if cmd == "umod":
        return cmd_umod(excel_dir)
    if cmd == "superuniques":
        return cmd_superuniques(excel_dir)
    if cmd == "stats":
        if len(argv) < 4:
            print(__doc__)
            return 2
        return cmd_stats(excel_dir, argv[2], argv[3], "--print" in argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

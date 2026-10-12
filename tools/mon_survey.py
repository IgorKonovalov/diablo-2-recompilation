"""Survey the monster-pool data of levels.bin and monstats.bin (plan 0012 Phase 0).

Usage:
  python3 -I tools/mon_survey.py levels   <excel-dir> [--list]
  python3 -I tools/mon_survey.py monstats <excel-dir>
  python3 -I tools/mon_survey.py spawn    <excel-dir>

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
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

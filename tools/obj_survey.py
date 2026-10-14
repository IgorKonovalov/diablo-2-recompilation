"""Survey the object tables: Levels object groups, ObjGroup, Objects and Shrines (plan 0023 Phase 0).

Usage:
  python3 -I tools/obj_survey.py levels  <excel-dir> [--all]
  python3 -I tools/obj_survey.py groups  <excel-dir>
  python3 -I tools/obj_survey.py objects <excel-dir>
  python3 -I tools/obj_survey.py shrines <excel-dir>

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are
decoded from the .bin files with the layouts in tools/excel_layouts.py (what the game loads); the .txt
is read only for the editor names that are not compiled (ObjGroup GroupName, Objects
"description - not loaded").

levels   one block per Levels record: Id, LevelName, then each slot k = 0..7 with ObjGrp<k> (ObjGroup record index, its GroupName),
         ObjPrb<k>, and the group's members: ID<k> (Objects record index and Name), DENSITY<k>, PROB<k>,
         plus the group's SHRINES and WELLS flags. A slot with ObjGrp 0 and ObjPrb 0 prints as "-".
         A record whose eight slots are all zero prints on one line ("no object groups"; --all prints its
         eight "-" slots too). Levels has one ObjGrp/ObjPrb set per row and no per-difficulty columns: the same slots apply
         in every difficulty (a statement about the table, not about the code).
groups   one line per ObjGroup record: index, GroupName, member count (ID != 0 or PROB != 0), sum of
         PROB, SHRINES, WELLS, and the Levels Ids that name it in any slot. Then the groups no level names.
objects  value distributions of the populate- and operate-related Objects columns (InitFn, PopulateFn,
         OperateFn, ClientFn, SubClass bits, SpawnMax, TrapProb, Lockable, IsDoor, HasCollision0,
         SizeX x SizeY, Xspace/Yspace, PreOperate, Trans, AutoMap, Mode0..7, Selectable0..7) and, per
         PopulateFn value, the Objects records that carry it.
shrines  one line per Shrines record: Code, Arg0, Arg1, Duration, reset, rarity, effectclass, LevelMin,
         and the editor name from the .txt.

The last line is a `SURVEY obj_<cmd> key=value ...` summary of integer counts. Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402


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


def txt_col(excel_dir, table, col):
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    i = header.index(col)
    return [r[i] if i < len(r) else "" for r in rows]


def members(g):
    """(slot, object id, density, prob) for the slots of an ObjGroup record that are in use."""
    return [(k, g["ID%d" % k], g["DENSITY%d" % k], g["PROB%d" % k])
            for k in range(8) if g["ID%d" % k] or g["PROB%d" % k]]


def summary(tag, d):
    print("SURVEY obj_%s " % tag + " ".join("%s=%d" % kv for kv in d.items()))


def cmd_levels(excel_dir, show_all=False):
    levels, groups, objs = decode(excel_dir, "levels"), decode(excel_dir, "objgroup"), decode(excel_dir, "objects")
    gname = txt_col(excel_dir, "objgroup", "GroupName")
    n_lv = n_slots = n_bad = 0
    for lv in levels:
        slots = [(k, lv["ObjGrp%d" % k], lv["ObjPrb%d" % k]) for k in range(8)]
        used = [s for s in slots if s[1] or s[2]]
        n_lv += 1 if used else 0
        if not used and not show_all:
            print("level %3d %s: no object groups" % (lv["Id"], lv["LevelName"]))
            continue
        print("level %3d %s" % (lv["Id"], lv["LevelName"]))
        for k, gi, prb in slots:
            if not gi and not prb:
                print("  slot %d  -" % k)
                continue
            n_slots += 1
            if gi >= len(groups):
                n_bad += 1
                print("  slot %d  ObjGrp %d (out of range) ObjPrb %d" % (k, gi, prb))
                continue
            g = groups[gi]
            print("  slot %d  ObjGrp %3d %-36s ObjPrb %3d  SHRINES %d WELLS %d"
                  % (k, gi, repr(gname[gi]), prb, g["SHRINES"], g["WELLS"]))
            for j, oid, den, p in members(g):
                name = objs[oid]["Name"] if oid < len(objs) else "?"
                print("      ID%d %3d %-24s DENSITY %3d PROB %3d" % (j, oid, name, den, p))
    summary("levels", collections.OrderedDict(levels=len(levels), levels_with_groups=n_lv, slots_used=n_slots,
                                              slots_out_of_range=n_bad))
    return 0


def cmd_groups(excel_dir):
    levels, groups = decode(excel_dir, "levels"), decode(excel_dir, "objgroup")
    gname = txt_col(excel_dir, "objgroup", "GroupName")
    users = collections.defaultdict(list)
    for lv in levels:
        for k in range(8):
            if lv["ObjGrp%d" % k] or lv["ObjPrb%d" % k]:
                users[lv["ObjGrp%d" % k]].append(lv["Id"])
    hist = collections.Counter()
    for i, g in enumerate(groups):
        m = members(g)
        hist[len(m)] += 1
        print("group %3d %-44s members %d probsum %3d SHRINES %d WELLS %d levels %s"
              % (i, repr(gname[i]), len(m), sum(p for _, _, _, p in m), g["SHRINES"], g["WELLS"],
                 ",".join(str(x) for x in sorted(set(users.get(i, [])))) or "-"))
    unused = [i for i in range(len(groups)) if i not in users]
    print("groups named by no level: %d: %s" % (len(unused), " ".join(map(str, unused))))
    d = collections.OrderedDict(groups=len(groups), groups_used=len(users), groups_unused=len(unused),
                                shrines=sum(g["SHRINES"] for g in groups), wells=sum(g["WELLS"] for g in groups))
    for n in sorted(hist):
        d["members_%d" % n] = hist[n]
    d["probsum_over_100"] = sum(1 for g in groups if sum(p for _, _, _, p in members(g)) > 100)
    summary("groups", d)
    return 0


def _dist(objs, col):
    c = collections.Counter(o[col] for o in objs)
    return ", ".join("%s:%d" % kv for kv in sorted(c.items()))


def cmd_objects(excel_dir):
    objs = decode(excel_dir, "objects")
    for col in ("InitFn", "PopulateFn", "OperateFn", "ClientFn", "SubClass", "SpawnMax", "TrapProb", "Lockable",
                "IsDoor", "HasCollision0", "Xspace", "Yspace", "PreOperate", "Trans", "AutoMap", "OperateRange",
                "Restore", "RestoreVirgins", "MonsterOK", "Act"):
        print("%-14s %s" % (col, _dist(objs, col)))
    bits = collections.Counter()
    for o in objs:
        for b in range(8):
            if o["SubClass"] & (1 << b):
                bits[b] += 1
    print("SubClass bits  %s" % ", ".join("bit%d(0x%02X):%d" % (b, 1 << b, bits[b]) for b in sorted(bits)))
    sizes = collections.Counter((o["SizeX"], o["SizeY"]) for o in objs)
    print("SizeX x SizeY  %s" % ", ".join("%dx%d:%d" % (x, y, n) for (x, y), n in sorted(sizes.items())))
    for col in ("Mode", "Selectable"):
        print("%-14s %s" % (col + "0..7", " ".join("%d:%d" % (k, sum(1 for o in objs if o["%s%d" % (col, k)]))
                                                    for k in range(8))))
    by_pop = collections.defaultdict(list)
    for i, o in enumerate(objs):
        by_pop[o["PopulateFn"]].append(i)
    for v in sorted(by_pop):
        if v:
            ids = by_pop[v]
            names = sorted(set(objs[i]["Name"] for i in ids))
            print("PopulateFn %d (%d records): ids %s; names %s" % (v, len(ids), " ".join(map(str, ids)),
                                                                    ", ".join(names)))
    d = collections.OrderedDict(records=len(objs))
    for col in ("InitFn", "PopulateFn", "OperateFn", "ClientFn"):
        d[col + "_distinct"] = len(set(o[col] for o in objs))
        d[col + "_max"] = max(o[col] for o in objs)
    d["populate_nonzero"] = sum(1 for o in objs if o["PopulateFn"])
    d["doors"] = sum(1 for o in objs if o["IsDoor"])
    d["lockable"] = sum(1 for o in objs if o["Lockable"])
    d["trapprob_nonzero"] = sum(1 for o in objs if o["TrapProb"])
    summary("objects", d)
    return 0


def cmd_shrines(excel_dir):
    sh = decode(excel_dir, "shrines")
    names = txt_col(excel_dir, "shrines", "Shrine name")
    for i, s in enumerate(sh):
        print("shrine %2d Code %2d Arg0 %4d Arg1 %4d Duration %4d reset %d rarity %d effectclass %d LevelMin %2d  %s"
              % (i, s["Code"], s["Arg0"], s["Arg1"], s["Duration in frames"], s["reset time in minutes"],
                 s["rarity"], s["effectclass"], s["LevelMin"], names[i]))
    d = collections.OrderedDict(records=len(sh), code_is_index=sum(1 for i, s in enumerate(sh) if s["Code"] == i))
    for r in sorted(set(s["rarity"] for s in sh)):
        d["rarity_%d" % r] = sum(1 for s in sh if s["rarity"] == r)
    d["raritysum"] = sum(s["rarity"] for s in sh)
    summary("shrines", d)
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, excel_dir = argv[0], argv[1]
    if cmd == "levels":
        return cmd_levels(excel_dir, "--all" in argv)
    if cmd == "groups":
        return cmd_groups(excel_dir)
    if cmd == "objects":
        return cmd_objects(excel_dir)
    if cmd == "shrines":
        return cmd_shrines(excel_dir)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

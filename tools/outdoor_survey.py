"""Survey the data the outdoor (DrlgType 3) generators read, per generator act (plan 0026 Phase 0).

Usage:
  python3 -I tools/outdoor_survey.py <root> [--quiet] [--act N]

<root> is a merged data tree (e.g. workspace/merged): the excel .bin files are decoded from
<root>/data/global/excel with the layouts in tools/excel_layouts.py (what the game loads), and the DS1
headers are read from <root>/data/global/tiles. The levels.txt / lvlprest.txt / lvltypes.txt /
lvlsub.txt `Name` columns are read only to label and group rows. --act N (1..5) prints one generator
act only (the SURVEY line still counts all five); --quiet drops the per-record listings.

The generator act of an outdoor level is its Levels `Act`, except level 134, which
sub_00675360_OutdoorLevelBuild sends to the Act II generator (drlg/0003, [I]).

Per generator act:

1. Outdoor levels: id, name, Levels Act, LevelType, SizeX x SizeY per difficulty (N/NM/H), the cell grid
   (size / 8, the division in OutdoorLevelBuild), OffsetX/Y, Depend, the Vis links set, SubType/SubTheme/
   SubWaypoint/SubShrine. Then the act's level types: LvlTypes Act/Expansion, named File count, and the
   other levels (by DrlgType) that use the same type.
2. Preset families the act's generator can place, by a data-only rule (a sorting rule of the survey, not
   a claim about the generator): the LvlPrest records with LevelId 0, at least one named file, outside
   every maze rotation range (base < Def < base+16, MAZE_DEF_BASE, drlg/0003), whose Dt1Mask is non-zero,
   selects only named files of the LvlTypes row of one of the act's outdoor level types, and selects at
   least one DT1 that the record's DS1s list. A family is the record Name with its variant tokens
   removed (numbers, "6A"-style numbers, N/S/E/W letter sets, "16X16" sizes). Per family: Def runs,
   records, the matched level types (and whether a maze level uses one of them), the DS1 directories,
   Files sum / named files, SizeX x SizeY, the DS1 header sizes, and the records whose named DS1 size
   differs from the record's non-zero size.
3. LvlSub per outdoor level: the records of SubType with Prob/Trials/Max at SubTheme (the
   sub_006706A0_LvlSubRoll draw count is the SubType block size, 0 when SubType or SubTheme is -1,
   drlg/0003 [I]); the SubWaypoint and SubShrine records (theme 0); whether every Dt1Mask bit of those
   records names a non-"0" file of the level's LvlTypes row.

Then, once:

4. LvlSub records: DS1 header (size, tag_type), group count and sizes, against BordType / GridSize /
   Prob / Dt1Mask / Expansion; which levels name each Type.

The last line is `SURVEY outdoor key=value ...` (integer counts). Stdlib only. Read-only.
"""
import collections
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402
import ds1  # noqa: E402

# sub_006738C0_MazePresetFile rotation bases (drlg/0003); the same table as tools/drlg.py and maze_survey.py
MAZE_DEF_BASE = {3: 0x34, 4: 0x6C, 7: 0xA7, 8: 0xCD, 10: 0x101, 13: 0x12D, 17: 0x19D, 18: 0x1E1, 22: 0x2F1,
                 24: 0x298, 25: 0x2C0, 28: 0x344, 33: 0x3EA, 34: 0x422, 35: 0x41C}
GEN_ACT_OVERRIDE = {134: 1}      # sub_00675360_OutdoorLevelBuild: level 0x86 takes the Act II layout (drlg/0003)
DIFF = ("", "(N)", "(H)")
VARIANT = re.compile(r"^(\d+[A-Za-z]?|[NSEW]{1,4}|\d+[xX]\d+)$")


def decode(excel_dir, table):
    lay = LAYOUTS[table]
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (table, size)
    return [{f.get("name") or f["col"]: decode_field(r, f) for f in lay["fields"]} for r in recs]


def txt_col(excel_dir, table, col):
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    i = header.index(col)
    return [r[i].strip() for r in rows]


def nfile(s):
    return (s or "").replace("\\", "/")


def named(s):
    return s not in ("", "0", None)


def runs(xs):
    out = []
    for x in sorted(set(xs)):
        if out and out[-1][1] == x - 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return ", ".join("%d" % a if a == b else "%d-%d" % (a, b) for a, b in out) or "-"


def family(name):
    """'Act 3 - Clearing Webby NW' -> 'Act 3 - Clearing Webby' (a sorting label only)."""
    head, sep, rest = name.partition(" - ")
    if not sep:
        head, rest = "", name
    toks = [t for t in rest.split() if not VARIANT.match(t)]
    return (head + " - " if sep else "") + " ".join(toks or rest.split())


def sizes(counter):
    return ", ".join("%dx%d%s" % (k[0], k[1], " (%d)" % v if v > 1 else "")
                     for k, v in sorted(counter.items()))


class Tiles:
    """DS1 headers under <root>/data/global/tiles, by lower-case relative path."""

    def __init__(self, root):
        self.base = os.path.join(root, "data", "global", "tiles")
        self.paths = {}
        for d, _, names in os.walk(self.base):
            for n in names:
                p = os.path.join(d, n)
                self.paths[os.path.relpath(p, self.base).replace(os.sep, "/").lower()] = p
        self.cache = {}

    def header(self, rel):
        """(size_x, size_y, tag_type, DT1 keys) from the header alone (a short file still has one)."""
        rel = nfile(rel).lower()
        if rel in self.cache:
            return self.cache[rel]
        p = self.paths.get(rel)
        if p is None:
            self.cache[rel] = None
            return None
        data = open(p, "rb").read()
        v, sx, sy = struct.unpack_from("<3i", data, 0)
        off, tag = 12, 0
        if v >= 8:
            off += 4
        if v >= 10:
            tag = struct.unpack_from("<i", data, off)[0]
            off += 4
        keys = set()
        if v >= 3:
            n = struct.unpack_from("<i", data, off)[0]
            off += 4
            for _ in range(n):
                e = data.index(b"\0", off)
                low = data[off:e].decode("latin-1").replace("\\", "/").lower()
                off = e + 1
                k = low.find("data/global/tiles/")
                if k >= 0:
                    keys.add(os.path.splitext(low[k + 18:])[0] + ".dt1")
        self.cache[rel] = (sx, sy, tag, keys)
        return self.cache[rel]

    def parse(self, rel):
        p = self.paths.get(nfile(rel).lower())
        try:
            return ds1.parse(open(p, "rb").read()) if p else None
        except ds1.Ds1Error:
            return None


def main(argv):
    if len(argv) < 1:
        print(__doc__)
        return 2
    root, quiet = argv[0], "--quiet" in argv[1:]
    only = None
    if "--act" in argv[1:]:
        only = int(argv[argv.index("--act") + 1]) - 1
    E = os.path.join(root, "data", "global", "excel")
    tiles = Tiles(root)
    S = collections.OrderedDict()
    lv, ld = decode(E, "levels"), decode(E, "leveldefs")
    pr, lt, ls = decode(E, "lvlprest"), decode(E, "lvltypes"), decode(E, "lvlsub")
    lname, pname = txt_col(E, "levels", "Name"), txt_col(E, "lvlprest", "Name")
    tname, sname = txt_col(E, "lvltypes", "Name"), txt_col(E, "lvlsub", "Name")
    assert all(r["Id"] == i for i, r in enumerate(lv)), "levels Id != row index"
    nlev = len(lv)
    outdoor = [i for i in range(nlev) if ld[i]["DrlgType"] == 3]
    gact = {i: GEN_ACT_OVERRIDE.get(i, lv[i]["Act"]) for i in outdoor}
    ltfiles = [[nfile(r["File %d" % (b + 1)]).lower() for b in range(32)] for r in lt]
    users = collections.defaultdict(list)          # level type -> [(level, DrlgType)]
    for i in range(1, nlev):
        users[ld[i]["LevelType"]].append((i, ld[i]["DrlgType"]))
    sub_block = collections.defaultdict(list)       # LvlSub Type -> record indices (file order)
    for k, r in enumerate(ls):
        sub_block[r["Type"]].append(k)

    S["levels"] = nlev
    S["outdoor_levels"] = len(outdoor)
    S["outdoor_level_types"] = len({ld[i]["LevelType"] for i in outdoor})
    S["gen_act_override"] = sum(1 for i in outdoor if gact[i] != lv[i]["Act"])
    S["size_diff_varies"] = S["size_not_mult8"] = S["size_negative"] = 0
    S["offset_set"] = S["depend_set"] = 0
    S["fam_records"] = S["fam_families"] = S["fam_size_zero"] = S["fam_ds1_size_mismatch"] = 0
    S["fam_files_ne_named"] = S["fam_records_maze_type"] = 0
    S["sub_dt1mask_bad"] = 0

    def in_rotation(d):
        return any(b < d < b + 16 for b in MAZE_DEF_BASE.values())

    # ---- record -> generator acts (survey rule)
    rec_acts = collections.defaultdict(set)
    rec_types = collections.defaultdict(set)
    act_types = collections.defaultdict(set)
    for i in outdoor:
        act_types[gact[i]].add(ld[i]["LevelType"])
    for r in pr:
        files = [r["File%d" % s] for s in range(1, 7) if named(r["File%d" % s])]
        if r["LevelId"] or not files or in_rotation(r["Def"]) or not r["Dt1Mask"]:
            continue
        need = set()
        for f in files:
            h = tiles.header(f)
            if h:
                need |= h[3]
        bits = [b for b in range(32) if r["Dt1Mask"] >> b & 1]
        for a, ts in act_types.items():
            for t in ts:
                if all(named(ltfiles[t][b]) for b in bits) and need & {ltfiles[t][b] for b in bits}:
                    rec_acts[r["Def"]].add(a)
                    rec_types[r["Def"]].add(t)
    S["records_in_no_act"] = sum(1 for r in pr if not r["LevelId"] and r["Def"] not in rec_acts)
    S["records_in_two_acts"] = sum(1 for v in rec_acts.values() if len(v) > 1)

    for a in range(5):
        lvls = [i for i in outdoor if gact[i] == a]
        S["act%d_levels" % (a + 1)] = len(lvls)
        show = only is None or only == a
        if show:
            print("=" * 100)
            print("== Generator act %d (OutdoorAct%d): %d outdoor levels" % (a + 1, a + 1, len(lvls)))
            print("\n-- 1. Outdoor levels")
            print("  id  name                         Act ltype  SizeX N/NM/H   SizeY N/NM/H   cells    "
                  "Offset      Depend Vis  SubType/Theme/Wp/Shrine")
        for i in lvls:
            d = ld[i]
            xs = [d["SizeX" + s] for s in DIFF]
            ys = [d["SizeY" + s] for s in DIFF]
            if len(set(xs)) > 1 or len(set(ys)) > 1:
                S["size_diff_varies"] += 1
            if any(v < 0 for v in xs + ys):
                S["size_negative"] += 1
            elif any(v % 8 for v in xs + ys):
                S["size_not_mult8"] += 1
            S["offset_set"] += (d["OffsetX"], d["OffsetY"]) != (-1, -1)
            S["depend_set"] += d["Depend"] != 0
            cells = "%dx%d" % (int(xs[0] / 8), int(ys[0] / 8)) if xs[0] > 0 and ys[0] > 0 else "-"
            vis = [d["Vis%d" % k] for k in range(8) if d["Vis%d" % k]]
            if show:
                print("  %3d %-28s %d  %3d   %-14s %-14s %-8s %5d,%-5d %6d %-4d %d/%d/%d/%d%s"
                      % (i, lname[i][:28], lv[i]["Act"] + 1, d["LevelType"], "/".join(map(str, xs)),
                         "/".join(map(str, ys)), cells, d["OffsetX"], d["OffsetY"], d["Depend"], len(vis),
                         d["SubType"], d["SubTheme"], d["SubWaypoint"], d["SubShrine"],
                         "  (generator act override)" if gact[i] != lv[i]["Act"] else ""))
        if show:
            print("  level types of the act's outdoor levels:")
            for t in sorted(act_types[a]):
                nf = sum(1 for f in ltfiles[t] if named(f))
                others = [(j, dt) for j, dt in users[t] if dt != 3]
                print("    %2d %-22s LvlTypes Act %d Expansion %d, %d named files; outdoor levels %s; other levels: %s"
                      % (t, tname[t], lt[t]["Act"], lt[t]["Expansion"], nf,
                         ",".join(str(j) for j, dt in users[t] if dt == 3),
                         ", ".join("%d (DrlgType %d)" % o for o in others) or "none"))

        # ---- 2. families
        fams = collections.OrderedDict()
        for r in pr:
            if a in rec_acts.get(r["Def"], ()):
                fams.setdefault(family(pname[r["Def"]]), []).append(r)
        S["act%d_records" % (a + 1)] = sum(len(v) for v in fams.values())
        S["act%d_families" % (a + 1)] = len(fams)
        S["fam_records"] += S["act%d_records" % (a + 1)]
        S["fam_families"] += len(fams)
        if show:
            print("\n-- 2. Preset families (survey rule): %d records in %d families"
                  % (S["act%d_records" % (a + 1)], len(fams)))
            print("  %-46s %-14s %3s %-8s %-7s %-12s %-26s %s"
                  % ("family", "Def", "rec", "types", "Files", "dirs", "record SizeX x SizeY", "DS1 sizes / notes"))
        for fam, recs in fams.items():
            fsum = sum(r["Files"] for r in recs)
            nn = sum(sum(1 for s in range(1, 7) if named(r["File%d" % s])) for r in recs)
            ne = sum(1 for r in recs if r["Files"] != sum(1 for s in range(1, 7) if named(r["File%d" % s])))
            S["fam_files_ne_named"] += ne
            rsz = collections.Counter((r["SizeX"], r["SizeY"]) for r in recs)
            dsz, mism, zero = collections.Counter(), [], 0
            dirs = set()
            for r in recs:
                if not (r["SizeX"] and r["SizeY"]):
                    zero += 1
                for s in range(1, 7):
                    f = r["File%d" % s]
                    if not named(f):
                        continue
                    dirs.add(os.path.dirname(nfile(f)) or ".")
                    h = tiles.header(f)
                    dsz[(h[0], h[1])] += 1
                    if r["SizeX"] and r["SizeY"] and (h[0], h[1]) != (r["SizeX"], r["SizeY"]):
                        mism.append("%d/%s %dx%d" % (r["Def"], os.path.basename(nfile(f)), h[0], h[1]))
            S["fam_size_zero"] += zero
            S["fam_ds1_size_mismatch"] += len(mism)
            types = sorted({t for r in recs for t in rec_types[r["Def"]]})
            maze_t = [t for t in types if any(dt == 1 for _, dt in users[t])]
            S["fam_records_maze_type"] += len(recs) if maze_t else 0
            if show:
                notes = []
                if zero:
                    notes.append("%d record(s) of size 0" % zero)
                if mism:
                    notes.append("DS1 != record size: " + "; ".join(mism))
                if ne:
                    notes.append("Files != named in %d" % ne)
                if maze_t:
                    notes.append("type %s also a maze level type" % ",".join(map(str, maze_t)))
                print("  %-46s %-14s %3d %-8s %-7s %-12s %-26s %s%s"
                      % (fam[:46], runs(r["Def"] for r in recs), len(recs), ",".join(map(str, types)),
                         "%d/%d" % (fsum, nn), ",".join(sorted(dirs))[:40], sizes(rsz), sizes(dsz),
                         ("; " + "; ".join(notes)) if notes else ""))
                if not quiet and len(recs) > 1:
                    for r in recs:
                        print("      %4d %-40s Files %d %2dx%-2d %s" % (
                            r["Def"], pname[r["Def"]][:40], r["Files"], r["SizeX"], r["SizeY"],
                            " ".join(os.path.basename(nfile(r["File%d" % s])) for s in range(1, 7)
                                     if named(r["File%d" % s]))))

        # ---- 3. LvlSub per level
        if show:
            print("\n-- 3. LvlSub per outdoor level (Prob/Trials/Max at the level's SubTheme; theme 0 for Wp/Shrine)")
        for i in lvls:
            d = ld[i]
            lt_row = ltfiles[d["LevelType"]]
            out = []
            for col, theme in (("SubType", d["SubTheme"]), ("SubWaypoint", 0), ("SubShrine", 0)):
                ty = d[col]
                if ty < 0:
                    out.append("    %-11s -1" % col)
                    continue
                if col == "SubType" and theme < 0:
                    out.append("    %-11s %d, SubTheme -1: no roll" % (col, ty))
                    continue
                recs = sub_block[ty]
                bad = [k for k in recs
                       if any(ls[k]["Dt1Mask"] >> b & 1 and not named(lt_row[b]) for b in range(32))]
                S["sub_dt1mask_bad"] += len(bad)
                lines = ["%s (P%d T%d M%d, Dt1Mask 0x%X)" % (
                    sname[k], ls[k]["Prob%d" % theme], ls[k]["Trials%d" % theme], ls[k]["Max%d" % theme],
                    ls[k]["Dt1Mask"]) for k in recs]
                extra = ", %d draw(s) per out room (LvlSubRoll)" % len(recs) if col == "SubType" else ""
                out.append("    %-11s Type %d, theme %d%s%s: %s" % (
                    col, ty, theme, extra, "; Dt1Mask names a '0' LvlTypes file in %d" % len(bad) if bad else "",
                    "; ".join(lines)))
            if show:
                print("  %3d %s" % (i, lname[i]))
                for ln in out:
                    print(ln)

    # ---- 4. LvlSub records (counted always, printed without --act)
    show = only is None
    if show:
        print("=" * 100)
        print("== 4. LvlSub records (%d): DS1 header, groups, columns" % len(ls))
    named_by = collections.defaultdict(set)
    for i in range(1, nlev):
        for col in ("SubType", "SubWaypoint", "SubShrine"):
            if ld[i][col] >= 0:
                named_by[ld[i][col]].add(i)
    tags = collections.Counter()
    for k, r in enumerate(ls):
        h = tiles.header(r["File"])
        f = tiles.parse(r["File"])
        g = ("%d groups %s" % (len(f["groups"]), sizes(collections.Counter((x["w"], x["h"]) for x in f["groups"])))
             if f else "groups: DS1 does not parse to the end (header only)")
        tags[(h[2], r["BordType"] != -1, all(r["Prob%d" % t] == 0 for t in range(5)))] += 1
        if show:
            print("  %2d Type %2d %-18s %-44s %3dx%-3d tag %d  BordType %2d GridSize %d Dt1Mask 0x%-6X Exp %d  %s"
                  % (k, r["Type"], sname[k][:18], nfile(r["File"])[:44], h[0], h[1], h[2], r["BordType"],
                     r["GridSize"], r["Dt1Mask"], r["Expansion"], g))
    for ty in sorted(sub_block) if show else ():
        if ty == min(sub_block):
            print("  per Type: records, levels naming it (SubType/SubWaypoint/SubShrine)")
        print("    Type %2d: %d record(s); levels %s" % (ty, len(sub_block[ty]), runs(named_by[ty]) if named_by[ty] else "none"))
    if show:
        print("  (DS1 tag_type, BordType != -1, Prob all 0) -> records: %s"
              % ", ".join("%s=%d" % (k, v) for k, v in sorted(tags.items())))
    S["sub_records"] = len(ls)
    S["sub_types"] = len(sub_block)
    S["sub_types_unnamed"] = sum(1 for ty in sub_block if not named_by[ty])
    S["sub_tag2"] = sum(v for k, v in tags.items() if k[0] == 2)
    S["sub_tag2_bord_prob0"] = tags[(2, True, True)]
    S["sub_tag1_nobord_prob"] = tags[(1, False, False)]
    S["sub_parse_short"] = sum(1 for r in ls if tiles.parse(r["File"]) is None)
    exp_lv = {ty for ty in sub_block if named_by[ty] and min(named_by[ty]) >= 109}
    S["sub_exp_rows"] = sum(1 for r in ls if r["Expansion"])
    S["sub_exp_rows_in_exp_types"] = sum(1 for r in ls if r["Expansion"] and (r["Type"] in exp_lv or not named_by[r["Type"]]))

    print("SURVEY outdoor " + " ".join("%s=%d" % kv for kv in S.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

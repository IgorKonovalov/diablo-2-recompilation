"""Survey of Hireling.txt and HireDesc.txt (plan 0033 Phase 0).

Usage:
  python3 -I tools/hireling_survey.py rows    <excel-dir> [act] [difficulty] [version]
  python3 -I tools/hireling_survey.py summary <excel-dir>

rows     one line per hireling record (filtered by Act 1..5, Difficulty 1..3, Version 0|100 when given): record index,
         Hireling, SubType, Version, Id, Class (and its monstats Id), Act, Difficulty, Level, Gold, Exp/Lvl, HireDesc,
         the name string range (NameFirst .. NameLast as string-table indices and the count), and the skills with
         their Mode, Chance/ChancePerLvl and Level/LvlPerLvl.
summary  counts only.

Both end with `SURVEY hireling key=value ...`; tools/gate.py --full compares the summary line with its baseline.
Records are read from hireling.bin with the layout of tools/excel_layouts.py (what the game loads); names are looked
up in the string tables next to the excel directory (tools/tbl.py). Definitions (data only, docs/tables/Hireling.md):
a "group" is the rows that share (Version, Id); a group's "level rows" are its rows in file order. Stdlib only.
Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

PER_ID = ["Class", "Act", "Difficulty", "Seller", "Gold", "Exp/Lvl", "HireDesc", "NameFirst", "NameLast",
          "DefaultChance", "Skill1", "Skill2", "Skill3"]


class Data:
    def __init__(self, excel_dir):
        header, rows, recs, _ = eb.load_table(excel_dir, "hireling")
        fields = {f["col"]: f for f in L.LAYOUTS["hireling"]["fields"] if "col" in f}
        self.txt = [dict(zip(header, r)) for r in rows]
        self.rec = [{c: eb.decode_field(b, f) for c, f in fields.items()} for b in recs]
        refs = eb.Refs(excel_dir)
        self.skills = refs.column("skills", "skill")
        self.monstats = refs.column("monstats", "Id")
        self.hiredesc = refs.column("hiredesc", "Code")
        self.strings = refs.strings()

    def names(self, r):
        a, b = self.strings.index(r["NameFirst"]), self.strings.index(r["NameLast"])
        return a, b

    def skill(self, i):
        return self.skills[i] if 0 <= i < len(self.skills) else "-"


def cmd_rows(d, argv):
    want = [int(a) if a else None for a in (argv + [""] * 3)[:3]]
    n = 0
    for k, (r, t) in enumerate(zip(d.rec, d.txt)):
        if any(w is not None and r[c] != w for w, c in zip(want, ("Act", "Difficulty", "Version"))):
            continue
        n += 1
        a, b = d.names(r)
        sk = "; ".join("%s m%d c%d+%d l%d+%d" % (d.skill(r["Skill%d" % i]), r["Mode%d" % i], r["Chance%d" % i],
                                                  r["ChancePerLvl%d" % i], r["Level%d" % i], r["LvlPerLvl%d" % i])
                       for i in range(1, 7) if r["Skill%d" % i] != -1)
        print("%3d %-16s %-16s v%-3d id %2d cls %3d(%s) act %d diff %d lvl %2d gold %5d exp/lvl %3d desc %-4s "
              "names %d..%d (%d) | %s" % (
                  k, t["Hireling"], t["SubType"], r["Version"], r["Id"], r["Class"],
                  d.monstats[r["Class"]] if 0 <= r["Class"] < len(d.monstats) else "-", r["Act"], r["Difficulty"],
                  r["Level"], r["Gold"], r["Exp/Lvl"], d.hiredesc[r["HireDesc"]] or "-", a, b, b - a + 1, sk))
    print("SURVEY hireling rows=%d" % n)
    return 0


def cmd_summary(d):
    kv = collections.OrderedDict()
    kv["rows"] = len(d.rec)
    for v in (0, 100):
        kv["v%d_rows" % v] = sum(1 for r in d.rec if r["Version"] == v)
    groups = collections.OrderedDict()
    for r in d.rec:
        groups.setdefault((r["Version"], r["Id"]), []).append(r)
    kv["groups"] = len(groups)
    kv["ids"] = len({i for _, i in groups})
    kv["ids_same_in_both_versions"] = sum(
        1 for i in {i for _, i in groups}
        if (0, i) in groups and (100, i) in groups
        and all(groups[(0, i)][0][c] == groups[(100, i)][0][c] for c in PER_ID))
    kv["group_field_varies"] = sum(1 for g in groups.values() for c in PER_ID if len({r[c] for r in g}) > 1)
    kv["group_level_not_ascending"] = sum(1 for g in groups.values()
                                          if [r["Level"] for r in g] != sorted({r["Level"] for r in g}))
    for v in (0, 100):
        for act in range(1, 6):
            for diff in (1, 2, 3):
                kv["v%d_a%d_d%d" % (v, act, diff)] = sum(1 for r in d.rec if (r["Version"], r["Act"], r["Difficulty"])
                                                         == (v, act, diff))
    kv["classes"] = len({r["Class"] for r in d.rec})
    kv["class_monstats_bad"] = sum(1 for r in d.rec if not 0 <= r["Class"] < len(d.monstats))
    kv["seller_monstats_bad"] = sum(1 for r in d.rec if not 0 <= r["Seller"] < len(d.monstats))
    kv["names_bad"] = sum(1 for r in d.rec if d.names(r)[1] < d.names(r)[0] or 5382 in d.names(r))
    kv["name_ranges"] = len({d.names(r) for r in d.rec})
    kv["hiredesc_none"] = sum(1 for r in d.rec if r["HireDesc"] == 0)
    kv["skills_set"] = sum(1 for r in d.rec for i in range(1, 7) if r["Skill%d" % i] != -1)
    kv["skill_slots_used"] = max(i for r in d.rec for i in range(1, 7) if r["Skill%d" % i] != -1)
    kv["unk_nonzero"] = sum(1 for r in d.rec if r.get("unk_114") or r.get("unk_116"))
    print("# version act difficulty: rows (ids)")
    for v in (0, 100):
        for act in range(1, 6):
            line = []
            for diff in (1, 2, 3):
                rs = [r for r in d.rec if (r["Version"], r["Act"], r["Difficulty"]) == (v, act, diff)]
                line.append("%2d (%s)" % (len(rs), ",".join(str(i) for i in sorted({r["Id"] for r in rs})) or "-"))
            print("  v%-3d act %d: %s" % (v, act, " | ".join(line)))
    for k, v in kv.items():
        if not k.startswith(("v0_a", "v100_a")):
            print("%-28s %d" % (k, v))
    print("SURVEY hireling " + " ".join("%s=%d" % x for x in kv.items()))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    d = Data(argv[1])
    if argv[0] == "rows":
        return cmd_rows(d, argv[2:])
    if argv[0] == "summary":
        return cmd_summary(d)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

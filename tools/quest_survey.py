"""Survey of the quest-related data: MonStats quest TCs and Misc quest items (plan 0032 Phase 0).

Usage:
  python3 -I tools/quest_survey.py tcs     <excel-dir>
  python3 -I tools/quest_survey.py items   <excel-dir>
  python3 -I tools/quest_survey.py summary <excel-dir>

tcs      one block per monstats record with TCQuestId != 0 or a TreasureClass4 cell: record index, Id, TCQuestId (the
         quest word the B6 test reads, save/0002), TCQuestCP, and per difficulty TreasureClass1 and TreasureClass4 (the
         quest TC) with the quest TC's Picks, NoDrop and items.
items    every weapons/armor/misc row with a non-zero `quest` or `questdiffcheck`: code, name, quest, questdiffcheck,
         compactsave (a simple item with questdiffcheck stores stat 356, d2s.md).
summary  counts only.

Every command ends with `SURVEY quest key=value ...`; tools/gate.py --full compares the summary line with its baseline.
MonStats fields are read from monstats.bin with the layout of tools/excel_layouts.py; a TC field holds the
treasureclassex row index + 161 (docs/tables/MonStats.md), 0 for a blank cell. TreasureClassEx and the item tables are
read from their .txt files. Stdlib only. Read-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

DIFFS = [("", "normal"), ("(N)", "nightmare"), ("(H)", "hell")]
TC_BIAS = 161


class Data:
    def __init__(self, excel_dir):
        _, _, recs, _ = eb.load_table(excel_dir, "monstats")
        fields = {f["col"]: f for f in L.LAYOUTS["monstats"]["fields"] if "col" in f}
        want = ["TCQuestId", "TCQuestCP"] + ["TreasureClass%d%s" % (n, d) for d, _ in DIFFS for n in (1, 4)]
        self.mon = [{c: eb.decode_field(b, fields[c]) for c in want} for b in recs]
        refs = eb.Refs(excel_dir)
        self.mon_ids = refs.column("monstats", "Id")
        h, rows = eb.read_txt(eb.find_file(excel_dir, "treasureclassex", ".txt"))
        self.tcrows = [dict(zip(h, r)) for r in rows]
        self.items = []
        for t in ("weapons", "armor", "misc"):
            h, rows = eb.read_txt(eb.find_file(excel_dir, t, ".txt"))
            for r in rows:
                row = dict(zip(h, r))
                if row.get("quest", "") not in ("", "0") or row.get("questdiffcheck", "") not in ("", "0"):
                    self.items.append((t, row))

    def quest_classes(self):
        return [(i, m) for i, m in enumerate(self.mon)
                if m["TCQuestId"] or any(m["TreasureClass4%s" % d] for d, _ in DIFFS)]

    def tc(self, v):
        """(name, row dict or None) of a stored TC field value."""
        if v == 0:
            return "-", None
        if v < TC_BIAS:
            return "<built-in %d>" % v, None
        row = self.tcrows[v - TC_BIAS] if v - TC_BIAS < len(self.tcrows) else None
        return (row["Treasure Class"] if row else "<bad %d>" % v), row


def tc_items(row):
    out = []
    for k in range(1, 11):
        it, p = row.get("Item%d" % k, ""), row.get("Prob%d" % k, "")
        if it:
            out.append("%s:%s" % (it, p))
    return " ".join(out)


def cmd_tcs(d):
    for i, m in d.quest_classes():
        print("monstats %3d %-10s TCQuestId %2d TCQuestCP %d" % (i, d.mon_ids[i], m["TCQuestId"], m["TCQuestCP"]))
        for suf, name in DIFFS:
            tc1, _ = d.tc(m["TreasureClass1%s" % suf])
            tc4, row = d.tc(m["TreasureClass4%s" % suf])
            print("  %-9s TC1 %-16s TC4 %-16s" % (name, tc1, tc4), end="")
            if row:
                print(" Picks %s NoDrop %s  %s" % (row.get("Picks", ""), row.get("NoDrop", ""), tc_items(row)))
            else:
                print()


def cmd_items(d):
    for t, r in d.items:
        print("%-7s %-4s %-36s quest %-3s questdiffcheck %-2s compactsave %-2s" % (
            t, r["code"], r["name"], r.get("quest", ""), r.get("questdiffcheck", ""), r.get("compactsave", "")))


def summary_line(d):
    qc = d.quest_classes()
    tc4 = [d.tc(m["TreasureClass4%s" % s]) for _, m in qc for s, _ in DIFFS]
    kv = [("quest_tc_classes", len(qc)),
          ("quest_tc_with_id", sum(1 for _, m in qc if m["TCQuestId"])),
          ("quest_ids_distinct", len({m["TCQuestId"] for _, m in qc})),
          ("quest_cp_nonzero", sum(1 for _, m in qc if m["TCQuestCP"])),
          ("tc4_cells", sum(1 for name, _ in tc4 if name != "-")),
          ("tc4_resolved", sum(1 for _, row in tc4 if row)),
          ("tc4_differs_tc1", sum(1 for _, m in qc for s, _ in DIFFS
                                  if m["TreasureClass4%s" % s] != m["TreasureClass1%s" % s])),
          ("quest_items", len(d.items)),
          ("quest_items_qdc", sum(1 for _, r in d.items if r.get("questdiffcheck") == "1")),
          ("quest_items_simple_qdc", sum(1 for _, r in d.items
                                         if r.get("questdiffcheck") == "1" and r.get("compactsave") == "1"))]
    return "SURVEY quest " + " ".join("%s=%s" % p for p in kv)


def main(argv):
    if len(argv) != 2 or argv[0] not in ("tcs", "items", "summary"):
        print(__doc__)
        return 2
    d = Data(argv[1])
    if argv[0] == "tcs":
        cmd_tcs(d)
    elif argv[0] == "items":
        cmd_items(d)
    print(summary_line(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Plan 0046 Phase 2: per-family event counts of skills logs (tools/gdb/skills.py SST0/SDO0 lines).

Usage: python3 -I tools/skills_catalogue_tally.py [--excel DIR] LOG [LOG ...]

For each log and in all: SrvDo and SrvStart events by (unit type, skill id) with the Skills.txt name, srvstfunc and
srvdofunc, the family the row belongs to (plan 0046 Phase 1 batches: general rows 0-5 and the class rows are tiers
the other plans reach; monster rows 156-338 by 8a 156-189, 8b 190-289, 8c 290-338; item casts = SDO0 with the item
argument set), and the chained-pair-relevant counts left to tools/skills.py check. Stdlib only, read-only.
"""
import csv
import json
import os
import sys
from collections import Counter

DEFAULT_EXCEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "merged",
                             "data", "global", "excel")


def family(uid_t, sid, item):
    if uid_t == 1 and 156 <= sid <= 189:
        return "8a"
    if uid_t == 1 and 190 <= sid <= 289:
        return "8b"
    if uid_t == 1 and 290 <= sid <= 338:
        return "8c"
    if item:
        return "item"
    return "-"


def main(argv):
    excel = DEFAULT_EXCEL
    if "--excel" in argv:
        k = argv.index("--excel")
        excel = argv[k + 1]
        del argv[k:k + 2]
    rows = list(csv.reader(open(os.path.join(excel, "skills.txt"), encoding="latin1"), delimiter="\t"))
    ix = {n: i for i, n in enumerate(rows[0])}
    sk = {}
    for r in rows[1:]:
        try:
            sk[int(r[ix["Id"]])] = (r[ix["skill"]], r[ix["srvstfunc"]], r[ix["srvdofunc"]])
        except (ValueError, IndexError):
            pass
    total = Counter()
    for path in argv:
        c = Counter()
        for line in open(path, errors="replace"):
            if line[:4] in ("SDO0", "SST0"):
                d = json.loads(line[5:])
                a = d["a"]
                c[(line[:3], d["u"]["t"], a[0], bool(len(a) > 3 and a[3]))] += 1
        print("== %s" % os.path.basename(path))
        for (tag, t, sid, item), n in sorted(c.items(), key=lambda x: (x[0][1], x[0][2], x[0][0])):
            nm = sk.get(sid, ("?", "", ""))
            print("  %s unit-type %d row %3d %-22s st %-3s do %-3s %-4s %s" % (tag, t, sid, nm[0], nm[1], nm[2],
                                                                           family(t, sid, item),
                                                                           ("item " if item else "") + str(n)))
        total.update(c)
    print("== all")
    fam = Counter()
    for (tag, t, sid, item), n in total.items():
        if tag == "SDO":
            fam[(family(t, sid, item), t, sid)] += n
    for k, n in sorted(fam.items()):
        if k[0] != "-":
            print("  family %-4s unit-type %d row %3d %-22s do events %d" % (k[0], k[1], k[2], sk.get(k[2], ("?",))[0], n))
    print("TALLY logs=%d" % len(argv))


if __name__ == "__main__":
    main(sys.argv[1:])

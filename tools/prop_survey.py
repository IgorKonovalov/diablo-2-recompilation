"""Survey the item property tables (properties, itemstatcost) and the property codes the item tables use,
plan 0024 Phase 0 (drop-path split corrected by Phase 1).

Usage:
  python3 -I tools/prop_survey.py columns <excel-dir> <properties|itemstatcost>
  python3 -I tools/prop_survey.py codes   <excel-dir>
  python3 -I tools/prop_survey.py funcs   <excel-dir>
  python3 -I tools/prop_survey.py stats   <excel-dir>
  python3 -I tools/prop_survey.py summary <excel-dir>

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel).

properties and itemstatcost are decoded from their .bin files with the layouts in tools/excel_layouts.py
(what the game loads); their .txt is read for the key names (record i = .txt data row i once the
`Expansion` marker is dropped) and to tell a blank cell from a zero. The property blocks of the source
tables are read from their .txt (their .bin blocks are not all mapped: uniqueitems and sets are
partial layouts, gems, runes and qualityitems have none). A block is used when its code cell is not blank
and names a properties row; a code is matched exactly, then case-insensitively (`Light` in setitems compiles
to the `light` row), and a code that matches no row (a commented-out `*enr`, which compiles to -1) is
listed as unresolved and its block skipped.

Sources (table, block, columns per block) and the survey's split into drop path and the rest, the
tables whose blocks are rolled when the item is created (docs/findings/items/0006-properties.md § 2, § 3)
against those applied only when worn or socketed:
  drop    uniqueitems prop1..12, setitems prop1..9, magicprefix / magicsuffix / automagic mod1..3,
          qualityitems mod1..2 (the superior builder, mode 1), setitems aprop1a..5b (rolled at creation,
          mode 4: states 165..169 when `add func` is not 0, the main list when it is 0)
  other   sets PCode2a..5b and FCode1..8 (set bonuses), gems weapon/helm/shield Mod1..3 (socketed),
          runes T1Code1..7 (runewords)
rareprefix and raresuffix carry no property columns. A "live" row passes the table's own row filter:
uniqueitems enabled = 1, the affix tables spawnable = 1; every other source has no filter (all rows live).

columns  per mapped column of the table: .txt blank cells, distinct values, range (integers), longest
         string, or the referenced names (refs); the observed type and range columns of the table docs.
codes    every property code a source uses: its properties row, its (func, stat) slots, and per source the
         rows and blocks naming it; codes no source names are listed at the end.
funcs    per distinct func value (any of func1..7): the codes using it, and on the drop path the rows, live
         rows and blocks naming such a code, the blocks with min = max, and the blocks with a non-numeric
         par; then the same rows and blocks off the drop path.
stats    every stat a used code writes, with its Save Bits, Save Param Bits, Encode, op, op param, op base and
         op stat1..3, and whether it is reached on the drop path.
summary  the counts above as one `SURVEY prop_survey key=value ...` line.

Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402



# (source name, table, list of (code, par, min, max) column names, drop path, live filter)
SOURCES = [
    ("uniqueitems", "uniqueitems",
     [("prop%d" % k, "par%d" % k, "min%d" % k, "max%d" % k) for k in range(1, 13)], True, ("enabled", "1")),
    ("setitems", "setitems",
     [("prop%d" % k, "par%d" % k, "min%d" % k, "max%d" % k) for k in range(1, 10)], True, None),
    ("magicprefix", "magicprefix",
     [("mod%dcode" % k, "mod%dparam" % k, "mod%dmin" % k, "mod%dmax" % k) for k in range(1, 4)], True,
     ("spawnable", "1")),
    ("magicsuffix", "magicsuffix",
     [("mod%dcode" % k, "mod%dparam" % k, "mod%dmin" % k, "mod%dmax" % k) for k in range(1, 4)], True,
     ("spawnable", "1")),
    ("automagic", "automagic",
     [("mod%dcode" % k, "mod%dparam" % k, "mod%dmin" % k, "mod%dmax" % k) for k in range(1, 4)], True,
     ("spawnable", "1")),
    ("qualityitems", "qualityitems",
     [("mod%dcode" % k, "mod%dparam" % k, "mod%dmin" % k, "mod%dmax" % k) for k in range(1, 3)], True, None),
    ("setitems.aprop", "setitems",
     [("aprop%d%s" % (k, s), "apar%d%s" % (k, s), "amin%d%s" % (k, s), "amax%d%s" % (k, s))
      for k in range(1, 6) for s in "ab"], True, None),
    ("sets", "sets",
     [("PCode%d%s" % (k, s), "PParam%d%s" % (k, s), "PMin%d%s" % (k, s), "PMax%d%s" % (k, s))
      for k in range(2, 6) for s in "ab"]
     + [("FCode%d" % k, "FParam%d" % k, "FMin%d" % k, "FMax%d" % k) for k in range(1, 9)], False, None),
    ("gems", "gems",
     [("%sMod%dCode" % (p, k), "%sMod%dParam" % (p, k), "%sMod%dMin" % (p, k), "%sMod%dMax" % (p, k))
      for p in ("weapon", "helm", "shield") for k in range(1, 4)], False, None),
    ("runes", "runes",
     [("T1Code%d" % k, "T1Param%d" % k, "T1Min%d" % k, "T1Max%d" % k) for k in range(1, 8)], False, None),
]


def decode(excel_dir, table):
    lay = LAYOUTS[table]
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (table, size)
    return [{(f.get("name") or f["col"]): decode_field(rec, f) for f in lay["fields"]} for rec in recs]


def txt_cells(excel_dir, table):
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    return {h: [r[i] if i < len(r) else "" for r in rows] for i, h in enumerate(header)}, len(rows)


def is_int(s):
    return s.lstrip("-").isdigit()


class Data:
    def __init__(self, excel_dir):
        self.dir = excel_dir
        self.props = decode(excel_dir, "properties")
        self.isc = decode(excel_dir, "itemstatcost")
        pc, _ = txt_cells(excel_dir, "properties")
        sc, _ = txt_cells(excel_dir, "itemstatcost")
        self.pcode = pc["code"]
        self.sname = sc["Stat"]
        self.pindex = {}
        for i, c in enumerate(self.pcode):
            self.pindex.setdefault(c, i)
        # per source: list of (row, live, [(slot, code, par, min, max)])
        self.plower = {}
        for c in self.pcode:
            self.plower.setdefault(c.lower(), c)
        self.uses = {}
        self.unresolved = collections.Counter()
        self.folded = collections.Counter()
        for name, table, quads, drop, live in SOURCES:
            cells, n = txt_cells(excel_dir, table)
            missing = [c for q in quads for c in q if c not in cells]
            assert not missing, (table, missing)
            rows = []
            for r in range(n):
                ok = True if live is None else cells[live[0]][r].strip() == live[1]
                blocks = []
                for k, (c, p, lo, hi) in enumerate(quads):
                    code = cells[c][r]
                    if code.strip() == "":
                        continue
                    if code not in self.pindex:
                        if code.lower() in self.plower:
                            self.folded[(name, code)] += 1
                            code = self.plower[code.lower()]
                        else:
                            # e.g. a commented-out `*enr`: the compiler stores -1 (no property)
                            self.unresolved[(name, code)] += 1
                            continue
                    blocks.append((k, code, cells[p][r], cells[lo][r], cells[hi][r]))
                if blocks:
                    rows.append((r, ok, blocks))
            self.uses[name] = rows
        self.drop = [s[0] for s in SOURCES if s[3]]
        self.other = [s[0] for s in SOURCES if not s[3]]

    def slots(self, pi):
        """(func, stat, set, val) for each of the seven slots with a func."""
        p = self.props[pi]
        out = []
        for k in range(1, 8):
            if p["func%d" % k]:
                out.append((p["func%d" % k], p["stat%d" % k], p["set%d" % k], p["val%d" % k]))
        return out

    def stat(self, s):
        return "-" if s == 0xFFFF else self.sname[s] if s < len(self.sname) else "#%d" % s


# ---------------------------------------------------------------- columns

def cmd_columns(excel_dir, table):
    lay = LAYOUTS[table]
    recs = decode(excel_dir, table)
    cells, _ = txt_cells(excel_dir, table)
    names = {"properties": txt_cells(excel_dir, "properties")[0]["code"],
             "itemstatcost": txt_cells(excel_dir, "itemstatcost")[0]["Stat"]}
    events = txt_cells(excel_dir, "events")[0].get("event", [])
    print("table %s: %d records, record %d B" % (table, len(recs), lay["size"]))
    print("%-18s %-8s %-6s %-8s %s" % ("column", "offset", "blank", "distinct", "values"))
    for f in lay["fields"]:
        col = f.get("col")
        if col is None:
            continue
        vals = [r[col] for r in recs]
        blank = sum(1 for c in cells[col] if c.strip() == "") if col in cells else "absent"
        dist = sorted(set(vals))
        if f["type"] == "ref":
            tbl = f["ref"].split(":")[0]
            lst = names.get(tbl, events)
            named = collections.Counter(lst[v] if v < len(lst) else ("none" if v in (0xFFFF, 0xFF) else "#%d" % v)
                                        for v in vals)
            if col == "code":
                desc = "own row index in %d of %d" % (sum(1 for i, v in enumerate(vals) if v == i), len(vals))
            else:
                desc = "%d named: %s" % (len([k for k in named if k != "none"]),
                                         " ".join("%s x%d" % kv for kv in sorted(named.items())[:12]))
        elif f["type"] == "tbl":
            desc = "string index %d..%d" % (min(vals), max(vals))
        elif f["type"] == "bit":
            desc = "set in %d" % sum(vals)
        else:
            desc = "%d..%d" % (min(vals), max(vals))
            if len(dist) <= 8:
                desc += "  {" + ", ".join("%d x%d" % (v, vals.count(v)) for v in dist) + "}"
        print("%-18s +0x%03X   %-6s %-8d %s" % (col, f["off"], blank, len(dist), desc))
    return 0


# ---------------------------------------------------------------- codes

def code_counts(d):
    """code -> {source: [rows, live rows, blocks]}."""
    out = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
    for src, rows in d.uses.items():
        for r, live, blocks in rows:
            seen = set()
            for _, code, *_ in blocks:
                c = out[code][src]
                c[2] += 1
                if code not in seen:
                    seen.add(code)
                    c[0] += 1
                    c[1] += live
    return out


def cmd_codes(excel_dir):
    d = Data(excel_dir)
    cc = code_counts(d)
    print("%-20s %4s %-44s %s" % ("code", "row", "slots func:stat", "source rows/live/blocks"))
    for code in sorted(cc, key=lambda c: d.pindex.get(c, 9999)):
        pi = d.pindex.get(code)
        if pi is None:
            print("%-20s %4s %-44s %s" % (code, "-", "UNRESOLVED", ""))
            continue
        sl = " ".join("%d:%s" % (f, d.stat(s)) for f, s, _, _ in d.slots(pi)) or "(no func)"
        srcs = " ".join("%s=%d/%d/%d" % (s, *cc[code][s]) for s, *_ in SOURCES if s in cc[code])
        print("%-20s %4d %-44s %s" % (code, pi, sl, srcs))
    unused = [c for c in d.pcode if c not in cc]
    print("\nused codes: %d (%d on the drop path); properties rows no source names: %d"
          % (len(cc), sum(1 for c in cc if any(s in d.drop for s in cc[c])), len(unused)))
    print("unused: " + " ".join(unused))
    if d.folded:
        print("resolved only case-insensitively: "
              + " ".join("%s:%s x%d" % (s, c, n) for (s, c), n in sorted(d.folded.items())))
    if d.unresolved:
        print("unresolved (blocks skipped): " + " ".join("%s:%s x%d" % (s, c, n) for (s, c), n in sorted(d.unresolved.items())))
    return 0


# ---------------------------------------------------------------- funcs

def func_table(d):
    """func -> dict of counts."""
    out = collections.defaultdict(lambda: collections.Counter())
    codes = collections.defaultdict(set)
    for pi, code in enumerate(d.pcode):
        for f, *_ in d.slots(pi):
            codes[f].add(code)
    for src, rows in d.uses.items():
        side = "drop" if src in d.drop else "other"
        for r, live, blocks in rows:
            row_funcs = set()
            for _, code, par, lo, hi in blocks:
                pi = d.pindex.get(code)
                if pi is None:
                    continue
                fs = set(f for f, *_ in d.slots(pi)) or {0}
                for f in fs:
                    out[f][side + "_blocks"] += 1
                    out[f][side + "_eq"] += lo.strip() == hi.strip()
                    out[f][side + "_textpar"] += par.strip() != "" and not is_int(par.strip())
                    out[f][side + "_codes_used:" + code] = 1
                row_funcs |= fs
            for f in row_funcs:
                out[f][side + "_rows"] += 1
                out[f][side + "_live"] += live
                out[f][side + "_rows:" + src] += 1
    return out, codes


def cmd_funcs(excel_dir):
    d = Data(excel_dir)
    ft, codes = func_table(d)
    print("func 0 = a properties row with no func in any slot")
    print("%4s %5s | %5s %5s %6s %5s %5s | %5s %6s | %s" % ("func", "codes", "drop", "live", "blocks", "min=", "text",
                                                       "other", "blocks", "drop rows by source; codes used"))
    for f in sorted(set(ft) | set(codes)):
        c = ft[f]
        used = sorted(k.split(":", 1)[1] for k in c if k.startswith("drop_codes_used:"))
        by = " ".join("%s=%d" % (k.split(":", 1)[1], v) for k, v in sorted(c.items()) if k.startswith("drop_rows:"))
        print("%4d %5d | %5d %5d %6d %5d %5d | %5d %6d | %s; %s"
              % (f, len(codes.get(f, ())), c["drop_rows"], c["drop_live"], c["drop_blocks"], c["drop_eq"],
                 c["drop_textpar"], c["other_rows"], c["other_blocks"], by or "-", " ".join(used) or "-"))
    return 0


# ---------------------------------------------------------------- stats

def stat_use(d):
    """stat id -> (drop path?, codes)."""
    out = collections.defaultdict(lambda: [False, set()])
    cc = code_counts(d)
    for code, srcs in cc.items():
        pi = d.pindex.get(code)
        if pi is None:
            continue
        drop = any(s in d.drop for s in srcs)
        for f, s, _, _ in d.slots(pi):
            if s != 0xFFFF:
                out[s][0] |= drop
                out[s][1].add(code)
    return out


def cmd_stats(excel_dir):
    d = Data(excel_dir)
    su = stat_use(d)
    print("%4s %-28s %4s %4s %4s %3s %3s %3s %-12s %-30s %s" % ("id", "stat", "drop", "save", "parm", "enc",
                                                              "op", "opp", "op base", "op stat1..3", "codes"))
    for s in sorted(su):
        r = d.isc[s]
        ops = ",".join(d.stat(r["op stat%d" % k]) for k in (1, 2, 3) if r["op stat%d" % k] != 0xFFFF) or "-"
        print("%4d %-28s %4s %4d %4d %3d %3d %3d %-12s %-30s %s"
              % (s, d.stat(s), "yes" if su[s][0] else "no", r["Save Bits"], r["Save Param Bits"], r["Encode"],
                 r["op"], r["op param"], d.stat(r["op base"]), ops, " ".join(sorted(su[s][1]))))
    return 0


# ---------------------------------------------------------------- summary

def cmd_summary(excel_dir):
    d = Data(excel_dir)
    cc = code_counts(d)
    ft, codes = func_table(d)
    su = stat_use(d)
    kv = ["properties=%d" % len(d.props), "itemstatcost=%d" % len(d.isc),
          "codes_used=%d" % len(cc),
          "codes_drop=%d" % sum(1 for c in cc if any(s in d.drop for s in cc[c])),
          "unresolved=%d" % sum(d.unresolved.values()), "folded=%d" % sum(d.folded.values()),
          "funcs=%d" % len(set(codes)), "funcs_drop=%d" % sum(1 for f in ft if ft[f]["drop_rows"]),
          "stats_used=%d" % len(su), "stats_drop=%d" % sum(1 for s in su if su[s][0])]
    drop = [s for s in su if su[s][0]]
    for col, key in (("Save Bits", "savebits"), ("Save Param Bits", "parambits"), ("Encode", "encode"), ("op", "op")):
        kv.append("stats_drop_%s=%d" % (key, sum(1 for s in drop if d.isc[s][col])))
    for src, rows in d.uses.items():
        kv.append("%s_rows=%d" % (src.replace(".", "_"), len(rows)))
    for f in sorted(ft):
        kv.append("func%d_drop_rows=%d" % (f, ft[f]["drop_rows"]))
    print("SURVEY prop_survey " + " ".join(kv))
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, excel_dir = argv[1], argv[2]
    if cmd == "columns" and len(argv) == 4 and argv[3] in ("properties", "itemstatcost"):
        return cmd_columns(excel_dir, argv[3])
    if len(argv) == 3 and cmd in ("codes", "funcs", "stats", "summary"):
        return {"codes": cmd_codes, "funcs": cmd_funcs, "stats": cmd_stats, "summary": cmd_summary}[cmd](excel_dir)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Survey the affix tables (magicprefix, magicsuffix, rareprefix, raresuffix, automagic), plan 0021 Phase 0.

Usage:
  python3 -I tools/affix_survey.py columns    <excel-dir> <table>
  python3 -I tools/affix_survey.py candidates <excel-dir> <type-or-item-code> <level> [--all-levels]
  python3 -I tools/affix_survey.py summary    <excel-dir>

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are
decoded from the .bin files with the layouts in tools/excel_layouts.py (what the game loads); the .txt
is read only to tell a blank cell from a zero. Record numbers are .bin record indices (the .txt data
row index once the `Expansion` marker is dropped).

columns     per mapped column of <table>: cells, blank cells in the .txt, distinct values, and the
            range (integers), the longest string, or the item-type codes named (references).
candidates  the rows of each table that name the item type, after expanding the type through the
            ItemTypes Equiv1/Equiv2 chains. <type-or-item-code> is an itemtypes Code (`axe`) or a base
            item code from weapons/armor/misc (`hax`); a base item contributes its `type` and `type2`.
            The type set is the start type(s) plus every type reachable through Equiv1/Equiv2 (index 0,
            the `None` row, ends a chain). A row is listed when one of its itype1..7 is in the set and
            none of its etype1..5 (etype1..4 for the rare tables) is. For the three tables with a level
            column, rows are also kept only when level <= <level> and (maxlevel = 0 or maxlevel >= <level>)
            unless --all-levels is given. Both rules are this survey's reading of the column names
            (leads), not a claim about the code: spawnable, rare, version and classspecific are printed,
            not filtered.
summary     per table: records, blank-name rows, value counts of version, spawnable, rare, the
            frequency-0 rows, classspecific rows, distinct groups; the last line is a
            `SURVEY affix_survey key=value ...` summary of integer counts.

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

TABLES = ["magicprefix", "magicsuffix", "rareprefix", "raresuffix", "automagic"]
MAGIC = ("magicprefix", "magicsuffix", "automagic")
ITEM_TABLES = ("weapons", "armor", "misc")
ITEM_COLS = ("code", "type", "type2", "level", "magic lvl", "auto prefix")


def decode(excel_dir, table, only=None):
    lay = LAYOUTS[table]
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (table, size)
    fields = [f for f in lay["fields"] if only is None or (f.get("name") or f["col"]) in only]
    return [{(f.get("name") or f["col"]): decode_field(rec, f) for f in fields} for rec in recs]


def txt_cells(excel_dir, table):
    """col -> list of .txt cells (Expansion rows dropped), for the columns the .txt has."""
    header, rows = read_txt(find_file(excel_dir, table, ".txt"))
    return {h: [r[i] if i < len(r) else "" for r in rows] for i, h in enumerate(header)}


def type_codes(excel_dir):
    return [r["Code"] for r in decode(excel_dir, "itemtypes")]


def name_col(table):
    return "name" if table.startswith("rare") else "Name"


def type_cols(table):
    n_e = 4 if table.startswith("rare") else 5
    return ["itype%d" % k for k in range(1, 8)], ["etype%d" % k for k in range(1, n_e + 1)]


# ---------------------------------------------------------------- columns

def cmd_columns(excel_dir, table):
    lay = LAYOUTS[table]
    recs = decode(excel_dir, table)
    cells = txt_cells(excel_dir, table)
    codes = type_codes(excel_dir)
    print("table %s: %d records, record %d B" % (table, len(recs), lay["size"]))
    print("%-16s %-8s %-6s %-7s %s" % ("column", "offset", "blank", "distinct", "values"))
    for f in lay["fields"]:
        col = f.get("col")
        if col is None:
            continue
        vals = [r[col] for r in recs]
        if col in cells:
            blank = sum(1 for c in cells[col] if c.strip() == "")
        else:
            blank = "absent"
        dist = sorted(set(vals), key=lambda v: (str(type(v)), v))
        if f["type"] == "str":
            desc = "str, longest %d" % max(len(v) for v in vals)
        elif f["type"] == "ref" and f["ref"].startswith("itemtypes"):
            named = collections.Counter(codes[v] if v < len(codes) else "#%d" % v for v in vals if v not in (0, 0xFFFF))
            desc = "types: " + " ".join("%s x%d" % kv for kv in sorted(named.items()))
            if not named:
                desc = "no type named"
        elif f["type"] == "ref":
            desc = "indices %s" % ",".join(str(v) for v in dist[:20])
        else:
            desc = "%d..%d" % (min(vals), max(vals))
            if len(dist) <= 8:
                desc += "  {" + ", ".join("%d x%d" % (v, vals.count(v)) for v in dist) + "}"
        print("%-16s +0x%03X   %-6s %-7d %s" % (col, f["off"], blank, len(dist), desc))
    return 0


# ---------------------------------------------------------------- candidates

def load_items(excel_dir):
    """code -> (table, row, type index, type2 index, level, magic lvl, auto prefix)."""
    out = {}
    for t in ITEM_TABLES:
        for i, r in enumerate(decode(excel_dir, t, ITEM_COLS)):
            if r["code"] and r["code"] not in out:
                out[r["code"]] = (t, i, r["type"], r["type2"], r["level"], r["magic lvl"], r["auto prefix"])
    return out


def expand(itypes, starts):
    """The start types plus every type reachable through Equiv1/Equiv2; index 0 (`None`) ends a chain."""
    seen, stack = set(), [s for s in starts if s]
    while stack:
        x = stack.pop()
        if x in seen or x == 0 or x >= len(itypes):
            continue
        seen.add(x)
        stack += [itypes[x]["Equiv1"], itypes[x]["Equiv2"]]
    return seen


def cmd_candidates(excel_dir, what, level, all_levels):
    itypes = decode(excel_dir, "itemtypes")
    codes = [r["Code"] for r in itypes]
    items = load_items(excel_dir)
    if what in items:
        t, row, ty, ty2, ql, ml, ap = items[what]
        starts, auto = [ty, ty2], ap
        print("base %s: %s row %d, type %s, type2 %s, level %d, magic lvl %d, auto prefix %d"
              % (what, t, row, codes[ty], codes[ty2] if ty2 else "-", ql, ml, ap))
    elif what in codes:
        starts, auto = [codes.index(what)], None
        print("item type %s (row %d)" % (what, starts[0]))
    else:
        print("unknown item type or base code: %s" % what)
        return 2
    header, prow = read_txt(find_file(excel_dir, "properties", ".txt"))
    props = [r[header.index("code")] for r in prow]
    tset = expand(itypes, starts)
    print("type set (%d): %s" % (len(tset), " ".join(sorted(codes[x] for x in tset))))
    print("level %d%s" % (level, " (level filter off)" if all_levels else ""))
    total = 0
    for table in TABLES:
        recs = decode(excel_dir, table)
        ic, ec = type_cols(table)
        rows = []
        for i, r in enumerate(recs):
            if not any(r[c] in tset for c in ic if r[c]):
                continue
            if any(r[c] in tset for c in ec if r[c] not in (0, 0xFFFF)):
                continue
            if table in MAGIC and not all_levels:
                if not (r["level"] <= level and (r["maxlevel"] == 0 or r["maxlevel"] >= level)):
                    continue
            rows.append((i, r))
        total += len(rows)
        print("\n== %s: %d rows" % (table, len(rows)))
        if table in MAGIC:
            if table == "automagic" and auto is not None:
                print("base auto prefix %d: %d of these rows have group %d"
                      % (auto, sum(1 for _, r in rows if r["group"] == auto), auto))
            print("%5s %-26s %5s %5s %5s %5s %5s %5s %4s %4s %-6s %s"
                  % ("row", "name", "level", "maxlv", "freq", "group", "vers", "spawn", "rare", "lreq", "class", "mod1code"))
            for i, r in rows:
                cls = "-"
                if r["classspecific"] != 0xFF:
                    cls = "cs%d" % r["classspecific"]
                elif r["class"] != 0xFF:
                    cls = "c%d/%d" % (r["class"], r["classlevelreq"])
                print("%5d %-26s %5d %5d %5d %5d %5d %5d %4d %4d %-6s %s"
                      % (i, r["Name"][:26], r["level"], r["maxlevel"], r["frequency"], r["group"], r["version"],
                         r["spawnable"], r["rare"], r["levelreq"], cls,
                         props[r["mod1code"]] if r["mod1code"] < len(props) else "-"))
        else:
            print("%5s %-20s %s" % ("row", "name", "itypes / etypes"))
            for i, r in rows:
                it = " ".join(codes[r[c]] for c in ic if r[c])
                et = " ".join(codes[r[c]] for c in ec if r[c] not in (0, 0xFFFF))
                print("%5d %-20s %s%s" % (i, r["name"], it, (" / " + et) if et else ""))
    print("\nSURVEY affix_candidates types=%d rows=%d" % (len(tset), total))
    return 0


# ---------------------------------------------------------------- summary

def cmd_summary(excel_dir):
    kv = []
    for table in TABLES:
        recs = decode(excel_dir, table)
        nc = name_col(table)
        blank = [i for i, r in enumerate(recs) if r[nc] == ""]
        print("== %s: %d records, blank name at %s" % (table, len(recs), blank or "none"))
        kv += ["%s_records=%d" % (table, len(recs)), "%s_blankname=%d" % (table, len(blank))]
        if table not in MAGIC:
            ic, ec = type_cols(table)
            noty = [i for i, r in enumerate(recs) if not any(r[c] for c in ic)]
            print("  rows with no itype: %s" % (noty or "none"))
            kv.append("%s_noitype=%d" % (table, len(noty)))
            continue
        named = [r for r in recs if r["Name"]]
        for col in ("version", "spawnable", "rare"):
            c = collections.Counter(r[col] for r in named)
            print("  %-10s %s" % (col, ", ".join("%d x%d" % x for x in sorted(c.items()))))
        f0 = [i for i, r in enumerate(recs) if r["Name"] and r["frequency"] == 0]
        cs = [i for i, r in enumerate(recs) if r["classspecific"] != 0xFF]
        live = [r for r in named if r["spawnable"] and r["frequency"]]
        groups = set(r["group"] for r in named)
        ml = [r for r in named if r["maxlevel"]]
        print("  frequency 0 (named rows): %d; spawnable and frequency > 0: %d" % (len(f0), len(live)))
        print("  classspecific set: %d; maxlevel set: %d; distinct group: %d" % (len(cs), len(ml), len(groups)))
        kv += ["%s_spawnable=%d" % (table, sum(1 for r in named if r["spawnable"])),
               "%s_rare=%d" % (table, sum(1 for r in named if r["rare"])),
               "%s_freq0=%d" % (table, len(f0)), "%s_live=%d" % (table, len(live)),
               "%s_classspecific=%d" % (table, len(cs)), "%s_groups=%d" % (table, len(groups))]
    print("SURVEY affix_survey " + " ".join(kv))
    return 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, excel_dir = argv[1], argv[2]
    if cmd == "columns" and len(argv) == 4 and argv[3] in TABLES:
        return cmd_columns(excel_dir, argv[3])
    if cmd == "candidates" and len(argv) in (5, 6):
        return cmd_candidates(excel_dir, argv[3], int(argv[4]), "--all-levels" in argv[5:])
    if cmd == "summary" and len(argv) == 3:
        return cmd_summary(excel_dir)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))

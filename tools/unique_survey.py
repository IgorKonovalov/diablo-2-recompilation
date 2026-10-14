"""Survey the generation columns of uniqueitems.bin and setitems.bin per base item (plan 0019 Phase 0).

Usage:
  python3 -I tools/unique_survey.py <excel-dir> [--quiet]

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Records are
decoded from the .bin files with the layouts in tools/excel_layouts.py (what the game loads); the .txt
is read only to tell a blank cell from a zero. Record numbers are .bin record indices (the .txt data
row index once the `Expansion` marker is dropped).

Sections:
  classes     UniqueItems row classes and the value ranges of version, enabled, ladder, carry1, rarity,
              lvl, lvl req in each. The classes are this survey's sorting, not a claim about the code:
                label     blank code and blank version (heading rows and the trailing blank row)
                nobase    blank code, version set (a named row with no base item)
                disabled  base code set, enabled bit 0 (blank or 0 in the .txt)
                classic   base code set, enabled 1, version 0
                expansion base code set, enabled 1, version 100
              SetItems has no version, enabled, ladder or carry1 column: its rows are classed by the
              `version` of the Sets row they name (classic 0, expansion 100), with lvl, lvl req, rarity.
  skip        the UniqueItems rows with a blank code (label and nobase) and the rows with code but
              enabled 0, with their raw .txt cells.
  bases       for every base code named by at least one UniqueItems or SetItems row: the base table and
              name, then each row: kind (U/S), record, lvl, rarity, version (unique: own column; set:
              the Sets row's), enabled (unique; set rows print `-`), ladder/carry1 flags, index.
  multi       the bases with more than one unique row, or more than one set row (counted over all rows
              and over the "live" rows: unique enabled 1; every set row).
  dupnames    the UniqueItems `index` values held by more than one row, with each row's record, code,
              version and enabled; and the same for SetItems.

--quiet prints only the summary. The last line is a `SURVEY unique_survey key=value ...` summary of
integer counts. Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from excel_bin import decode_field, find_file, read_bin, read_txt  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402

GEN_U = ["version", "enabled", "ladder", "carry1", "rarity", "lvl", "lvl req"]
GEN_S = ["lvl", "lvl req", "rarity"]
CLASSES_U = ["label", "nobase", "disabled", "classic", "expansion"]


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


def uclass(b, t):
    if t["code"] == "":
        return "label" if t["version"] == "" else "nobase"
    if b["enabled"] != 1:
        return "disabled"
    return "classic" if b["version"] == 0 else "expansion"


def rng(vals, blanks):
    if not vals:
        return "all blank" if blanks else "-"
    c = collections.Counter(vals)
    s = "%d..%d" % (min(vals), max(vals)) if len(c) > 1 else "%d" % vals[0]
    s += " (%d distinct)" % len(c) if len(c) > 2 else (" {%s}" % ",".join("%d:%d" % kv for kv in sorted(c.items())))
    if blanks:
        s += ", %d blank" % blanks
    return s


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    excel_dir = argv[0]
    quiet = "--quiet" in argv[1:]
    out = (lambda *a: None) if quiet else print

    ub, ut = decode(excel_dir, "uniqueitems"), txt_rows(excel_dir, "uniqueitems")
    sb, st = decode(excel_dir, "setitems"), txt_rows(excel_dir, "setitems")
    setb, sett = decode(excel_dir, "sets"), txt_rows(excel_dir, "sets")
    assert len(ub) == len(ut) and len(sb) == len(st) and len(setb) == len(sett)
    bases = {}
    for table in ("weapons", "armor", "misc"):
        for r in txt_rows(excel_dir, table):
            bases.setdefault(r["code"], (table, r["name"]))
    summary = collections.OrderedDict()
    summary["unique_rows"] = len(ub)
    summary["set_rows"] = len(sb)
    summary["sets_rows"] = len(setb)

    # ---------------------------------------------------------------- classes
    ucls = [uclass(b, t) for b, t in zip(ub, ut)]
    out("== UniqueItems row classes (%d records) ==" % len(ub))
    for c in CLASSES_U:
        idx = [i for i, k in enumerate(ucls) if k == c]
        summary["u_%s" % c] = len(idx)
        out("%-9s %3d rows" % (c, len(idx)))
        for col in GEN_U:
            vals = [ub[i][col] for i in idx if ut[i][col] != ""]
            blanks = sum(1 for i in idx if ut[i][col] == "")
            out("    %-8s %s" % (col, rng(vals, blanks)))
    split = next(i for i, t in enumerate(ut) if t["version"] == "100")
    late0 = [i for i in range(split, len(ub)) if ut[i]["version"] == "0"]
    out("first version-100 record: %d; version-0 records after it: %d" % (split, len(late0)))
    summary["u_first_v100"] = split
    summary["u_v0_after_first_v100"] = len(late0)

    scls = []
    for b in sb:
        v = setb[b["set"]]["version"]
        scls.append("classic" if v == 0 else "expansion" if v == 100 else "v%d" % v)
    out("\n== SetItems row classes by the version of their Sets row (%d records) ==" % len(sb))
    for c in ("classic", "expansion"):
        idx = [i for i, k in enumerate(scls) if k == c]
        summary["s_%s" % c] = len(idx)
        out("%-9s %3d rows, %d sets" % (c, len(idx), len({sb[i]["set"] for i in idx})))
        for col in GEN_S:
            vals = [sb[i][col] for i in idx if st[i][col] != ""]
            blanks = sum(1 for i in idx if st[i][col] == "")
            out("    %-8s %s" % (col, rng(vals, blanks)))
    other = [c for c in scls if c not in ("classic", "expansion")]
    summary["s_other_version"] = len(other)
    order = [setb[b["set"]]["version"] for b in sb]
    flips = sum(1 for a, b2 in zip(order, order[1:]) if a != b2)
    out("set-version changes along the record order: %d" % flips)
    summary["s_version_changes"] = flips
    out("Sets: %d rows, version %s, level %s"
        % (len(setb), rng([b["version"] for b in setb], 0),
           rng([int(t["level"]) for t in sett if t["level"] != ""], sum(1 for t in sett if t["level"] == ""))))
    lvl_lt = sum(1 for b in sb if b["lvl"] < int(sett[b["set"]]["level"]))
    lvl_eq = sum(1 for b in sb if b["lvl"] == int(sett[b["set"]]["level"]))
    out("SetItems lvl against its Sets level: %d below, %d equal, %d above"
        % (lvl_lt, lvl_eq, len(sb) - lvl_lt - lvl_eq))
    summary.update(s_lvl_below_set=lvl_lt, s_lvl_equal_set=lvl_eq)

    # ---------------------------------------------------------------- skip
    out("\n== UniqueItems rows a reader must skip or treat apart ==")
    out("rec  class     version enabled ladder carry1 rarity lvl lvlreq code index (.txt cells)")
    for i, c in enumerate(ucls):
        if c in ("label", "nobase", "disabled"):
            t = ut[i]
            out("%3d  %-9s %-7s %-7s %-6s %-6s %-6s %-3s %-6s %-4s %s"
                % (i, c, t["version"], t["enabled"], t["ladder"], t["carry1"], t["rarity"], t["lvl"],
                   t["lvl req"], t["code"], t["index"] or "(blank)"))

    # ---------------------------------------------------------------- bases
    per = collections.OrderedDict()
    for i, b in enumerate(ub):
        if b["code"]:
            per.setdefault(b["code"], []).append(("U", i))
    for i, b in enumerate(sb):
        per.setdefault(b["item"], []).append(("S", i))
    unresolved = [c for c in per if c not in bases]
    summary["bases"] = len(per)
    summary["bases_unresolved"] = len(unresolved)
    out("\n== Candidates per base code (%d bases; record order) ==" % len(per))
    out("kind rec  lvl rarity version enabled flags index")
    for code in sorted(per, key=lambda c: (bases.get(c, ("?",))[0], c)):
        table, name = bases.get(code, ("?", "?"))
        out("%s  (%s: %s)" % (code, table, name))
        for kind, i in per[code]:
            if kind == "U":
                b = ub[i]
                flags = ("L" if b["ladder"] else "-") + ("C" if b["carry1"] else "-")
                out("  U %3d %4d %6d %7d %7d %5s %s"
                    % (i, b["lvl"], b["rarity"], b["version"], b["enabled"], flags, b["index"]))
            else:
                b = sb[i]
                out("  S %3d %4d %6d %7d %7s %5s %s  [set %s]"
                    % (i, b["lvl"], b["rarity"], setb[b["set"]]["version"], "-", "--", b["index"],
                       sett[b["set"]]["index"]))

    # ---------------------------------------------------------------- multi
    def counts(code):
        rows = per[code]
        u = [i for k, i in rows if k == "U"]
        s = [i for k, i in rows if k == "S"]
        return len(u), sum(1 for i in u if ub[i]["enabled"] == 1), len(s)

    multi_u = [c for c in per if counts(c)[0] > 1]
    multi_u_live = [c for c in per if counts(c)[1] > 1]
    multi_s = [c for c in per if counts(c)[2] > 1]
    both = [c for c in per if counts(c)[1] >= 1 and counts(c)[2] >= 1]
    out("\n== Bases with more than one candidate ==")
    out("code  unique_rows unique_enabled set_rows")
    for c in sorted(set(multi_u) | set(multi_s), key=lambda c: (-sum(counts(c)), c)):
        out("%-5s %11d %14d %8d" % ((c,) + counts(c)))
    out("bases with >1 unique row: %d; >1 enabled unique row: %d; >1 set row: %d; "
        "both an enabled unique and a set row: %d" % (len(multi_u), len(multi_u_live), len(multi_s), len(both)))
    summary.update(bases_multi_unique=len(multi_u), bases_multi_unique_enabled=len(multi_u_live),
                   bases_multi_set=len(multi_s), bases_unique_and_set=len(both),
                   bases_unique_only=sum(1 for c in per if counts(c)[0] and not counts(c)[2]),
                   bases_set_only=sum(1 for c in per if counts(c)[2] and not counts(c)[0]))

    # ---------------------------------------------------------------- dupnames
    out("\n== Duplicated index names ==")
    for label, rows, key in (("UniqueItems", ub, "code"), ("SetItems", sb, "item")):
        names = collections.OrderedDict()
        for i, b in enumerate(rows):
            if b["index"]:
                names.setdefault(b["index"], []).append(i)
        dups = {n: ix for n, ix in names.items() if len(ix) > 1}
        out("%s: %d named rows, %d distinct, %d names on more than one row"
            % (label, sum(len(v) for v in names.values()), len(names), len(dups)))
        for n, ix in dups.items():
            if label == "UniqueItems":
                desc = ", ".join("%d (%s v%d en%d)" % (i, ub[i]["code"], ub[i]["version"], ub[i]["enabled"])
                                 for i in ix)
            else:
                desc = ", ".join("%d (%s)" % (i, sb[i]["item"]) for i in ix)
            out("  %-20s x%d: %s" % (n, len(ix), desc))
        summary["%s_dup_names" % label[0].lower()] = len(dups)
        summary["%s_dup_rows" % label[0].lower()] = sum(len(v) for v in dups.values())

    print("SURVEY unique_survey " + " ".join("%s=%d" % kv for kv in summary.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

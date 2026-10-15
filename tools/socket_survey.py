"""Survey of the gems and runes tables (plan 0029 Phase 0): the gem mod groups and every runeword row.

Usage:
  python3 -I tools/socket_survey.py gems    <excel-dir>   one line per gems.txt row: item, nummods, transform,
                                                          the weapon / helm / shield mod groups
  python3 -I tools/socket_survey.py runes   <excel-dir>   one block per runes.txt row: record index, Name, Rune
                                                          Name, complete, server, itype/etype, runes (code and
                                                          letter), socket count, bases, property lines
  python3 -I tools/socket_survey.py summary <excel-dir>   counts only; the last line is
                                                          `SURVEY socket_survey key=value ...` (tools/gate.py --full)

Every command ends with the SURVEY line. Definitions (data only, docs/tables/Runes.md; no code behind them):
  rune count   the number of non-blank Rune1..6 cells;
  bases        weapons/armor rows whose type or type2 reaches an itype through itemtypes Equiv1/Equiv2,
               reaches no etype, and whose gemsockets is at least the rune count (the base can hold the runes;
               whether the game also needs the item level for MaxSock25/40 is not checked);
  classic      every rune of the row is an item with misc.txt version 0 (runes are version 100, so no row is);
  item records are indexed over weapons + armor + misc in that order (Weapons.md), as Rune1..6 and gems `code`
  store them.
<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Stdlib only. Read-only.
"""
import os
import sys


def load(excel_dir, name):
    """(header, rows) of an excel .txt: LF split, CR stripped, empty lines skipped."""
    for fn in os.listdir(excel_dir):
        if fn.lower() == name + ".txt":
            with open(os.path.join(excel_dir, fn), "rb") as fh:
                lines = [ln.rstrip("\r") for ln in fh.read().decode("latin-1").split("\n")]
            break
    else:
        raise SystemExit("%s.txt not found in %s" % (name, excel_dir))
    header = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if ln:
            cells = ln.split("\t")
            rows.append({c: (cells[i].strip() if i < len(cells) else "") for i, c in enumerate(header)})
    return header, rows


class Data:
    def __init__(self, excel_dir):
        self.items = {}       # code -> row (weapons, armor, misc)
        self.kind = {}        # code -> table
        for t in ("weapons", "armor", "misc"):
            for r in load(excel_dir, t)[1]:
                if r.get("code"):
                    self.items.setdefault(r["code"], r)
                    self.kind.setdefault(r["code"], t)
        self.types = {r["Code"]: r for r in load(excel_dir, "itemtypes")[1] if r.get("Code")}
        self.gems = {r["code"]: r for r in load(excel_dir, "gems")[1] if r.get("code")}
        self.gem_rows = [r for r in load(excel_dir, "gems")[1] if r["name"] != "Expansion"]
        self.runes = load(excel_dir, "runes")[1]

    def ancestors(self, code):
        """The item type and every type it reaches through Equiv1/Equiv2."""
        out, todo = set(), [code]
        while todo:
            c = todo.pop()
            if c and c not in out and c in self.types:
                out.add(c)
                todo += [self.types[c].get("Equiv1", ""), self.types[c].get("Equiv2", "")]
        return out

    def bases(self, itypes, etypes, n):
        out = []
        for code, r in self.items.items():
            if self.kind[code] == "misc":
                continue
            reach = self.ancestors(r.get("type", "")) | self.ancestors(r.get("type2", ""))
            if reach & itypes and not reach & etypes and int(r.get("gemsockets") or 0) >= n:
                out.append(code)
        return out


def mods(r, fmt, count):
    out = []
    for k in range(1, count + 1):
        code = r.get(fmt % (k, "Code"), "")
        if code:
            par = r.get(fmt % (k, "Param"), "")
            out.append("%s%s %s..%s" % (code, "(%s)" % par if par and par != "0" else "",
                                         r.get(fmt % (k, "Min"), ""), r.get(fmt % (k, "Max"), "")))
    return out


def runeword(d, r):
    runes = [r["Rune%d" % k] for k in range(1, 7) if r["Rune%d" % k]]
    itypes = {r["itype%d" % k] for k in range(1, 7) if r["itype%d" % k]}
    etypes = {r["etype%d" % k] for k in range(1, 4) if r["etype%d" % k]}
    return dict(runes=runes, itypes=itypes, etypes=etypes, complete=r["complete"] == "1",
                server=r["server"] == "1",
                classic=bool(runes) and all((d.items.get(c, {}).get("version") or "0") == "0" for c in runes),
                bases=d.bases(itypes, etypes, len(runes)),
                lines=[
                    "%s%s %s..%s" % (r["T1Code%d" % k], "(%s)" % r["T1Param%d" % k] if r["T1Param%d" % k] else "",
                                     r["T1Min%d" % k], r["T1Max%d" % k])
                    for k in range(1, 8) if r["T1Code%d" % k]])


def summary(d):
    rws = [runeword(d, r) for r in d.runes]
    s = dict(gems=len(d.gem_rows),
             gems_classic=sum(1 for g in d.gem_rows if (d.items.get(g["code"], {}).get("version") or "0") == "0"),
             runewords=len(rws),
             complete=sum(w["complete"] for w in rws),
             server=sum(w["server"] for w in rws),
             complete_server=sum(w["complete"] and w["server"] for w in rws),
             classic=sum(w["classic"] for w in rws),
             complete_with_base=sum(w["complete"] and bool(w["bases"]) for w in rws),
             lines=sum(len(w["lines"]) for w in rws),
             complete_lines=sum(len(w["lines"]) for w in rws if w["complete"]))
    for n in range(1, 7):
        s["complete_runes%d" % n] = sum(1 for w in rws if w["complete"] and len(w["runes"]) == n)
    return s


def survey_line(d):
    return "SURVEY socket_survey " + " ".join("%s=%d" % kv for kv in summary(d).items())


def cmd_gems(d):
    for i, g in enumerate(d.gem_rows):
        it = d.items.get(g["code"], {})
        print("%2d %-4s %-20s letter=%-4s nummods=%s transform=%-2s version=%s" % (
            i, g["code"], g["name"], g["letter"] or "-", g["nummods"], g["transform"], it.get("version", "?")))
        for grp in ("weapon", "helm", "shield"):
            print("     %-6s %s" % (grp, "; ".join(mods(g, grp + "Mod%d%s", 3)) or "-"))


def letter(d, code):
    return d.gems.get(code, {}).get("letter") or code


def cmd_runes(d):
    for i, r in enumerate(d.runes):
        w = runeword(d, r)
        print("%3d %-12s %-22s complete=%d server=%d runes=%d" % (
            i, r["Name"], r["Rune Name"], w["complete"], w["server"], len(w["runes"])))
        print("     itype %s%s" % (" ".join(sorted(w["itypes"])) or "-",
                                   ("  etype " + " ".join(sorted(w["etypes"]))) if w["etypes"] else ""))
        print("     runes %s" % (" ".join("%s(%s)" % (letter(d, c), c) for c in w["runes"]) or "-"))
        print("     bases %d%s" % (len(w["bases"]), (": " + " ".join(sorted(w["bases"])[:12])
                                                     + (" ..." if len(w["bases"]) > 12 else "")) if w["bases"] else ""))
        for ln in w["lines"]:
            print("     + %s" % ln)


def main(argv):
    if len(argv) != 2 or argv[0] not in ("gems", "runes", "summary"):
        print(__doc__)
        return 2
    d = Data(argv[1])
    if argv[0] == "gems":
        cmd_gems(d)
    elif argv[0] == "runes":
        cmd_runes(d)
    else:
        for k, v in summary(d).items():
            print("%-20s %d" % (k, v))
    print(survey_line(d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

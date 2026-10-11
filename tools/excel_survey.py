"""Survey the excel tables in a merged tree: .txt shape, .bin shape, and whether they agree.

Usage: python3 -I tools/excel_survey.py <merged-root> <merged-manifest.tsv> [--md]

For every basename under data/global/excel/ prints: txt origin archive, txt data rows (lines
after the header that are not zero-length; tab-only lines count), columns in the header,
"Expansion" marker rows (first field equal to "Expansion"; other fields are usually empty but some
carry a stray value), bin origin archive, bin record count (leading u32 LE), bin record size
((size - 4) / count, or "?" when that is not an integer), and a verdict:
  rows=   bin count equals txt data rows
  rows-x  bin count equals txt data rows minus Expansion marker rows
  DIFF    neither
The layout assumption (u32 count, then fixed-size records) is the subject of docs/formats/excel-bin.md.
The last line is a `SURVEY excel key=value ...` summary of integer counts for tools/gate.py --full.
--md prints a markdown table instead of TSV. Stdlib only. Read-only.
"""
import os
import struct
import sys


def txt_shape(path):
    with open(path, "rb") as fh:
        # split on LF only: str.splitlines() also breaks on \x85, \x0b, \x1c..., which occur in cells
        lines = [ln.rstrip("\r") for ln in fh.read().decode("latin-1").split("\n")]
    header = lines[0].split("\t") if lines else []
    # a tab-only line still compiles to an (empty) record, e.g. the last line of uniqueitems.txt
    rows = [ln for ln in lines[1:] if ln != ""]
    exp = sum(1 for ln in rows if ln.split("\t")[0] == "Expansion")
    return len(rows), len(header), exp


def bin_shape(path):
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        head = fh.read(4)
    if len(head) < 4:
        return None, "?"
    count = struct.unpack("<I", head)[0]
    if count and (size - 4) % count == 0:
        return count, (size - 4) // count
    return count, "?" if count else ("0" if size == 4 else "?")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    root, manifest = args
    origin, names = {}, {}
    with open(manifest) as fh:
        next(fh)
        for ln in fh:
            path, archive, orig = ln.split("\t")[:3]
            if path.startswith("data/global/excel/"):
                origin[path] = archive
                base, ext = os.path.splitext(orig.rsplit("/", 1)[1])
                names.setdefault(base.lower(), {})[ext.lower()] = (path, base)
    cols = ["table", "txt_from", "txt_rows", "txt_cols", "exp_rows", "bin_from", "bin_count", "bin_recsize", "verdict"]
    out = []
    for key in sorted(names):
        forms = names[key]
        display = forms.get(".txt", forms.get(".bin"))[1]
        r = {"table": display}
        if ".txt" in forms:
            p = forms[".txt"][0]
            r["txt_from"] = origin[p]
            r["txt_rows"], r["txt_cols"], r["exp_rows"] = txt_shape(os.path.join(root, p))
        if ".bin" in forms:
            p = forms[".bin"][0]
            r["bin_from"] = origin[p]
            r["bin_count"], r["bin_recsize"] = bin_shape(os.path.join(root, p))
        if "txt_rows" in r and "bin_count" in r:
            if r["bin_count"] == r["txt_rows"]:
                r["verdict"] = "rows="
            elif r["bin_count"] == r["txt_rows"] - r["exp_rows"]:
                r["verdict"] = "rows-x"
            else:
                r["verdict"] = "DIFF"
        out.append([str(r.get(c, "")) for c in cols])
    if "--md" in argv:
        print("| " + " | ".join(cols) + " |")
        print("|" + "---|" * len(cols))
        for row in out:
            print("| " + " | ".join(row) + " |")
    else:
        print("\t".join(cols))
        for row in out:
            print("\t".join(row))
    # gate summary (tools/gate.py --full): integer counts only; bin_records sums the bins whose
    # layout fits (u32 count, fixed records), no_count_header counts the others
    # (the *code.bin files); a bin shorter than 4 bytes counts in errors only
    v = [r[cols.index("verdict")] for r in out]
    txt = [r for r in out if r[cols.index("txt_rows")]]
    bins = [r for r in out if r[cols.index("bin_from")]]
    print("SURVEY excel tables=%d txt=%d bin=%d txt_rows=%d bin_records=%d rows_eq=%d rows_x=%d diff=%d"
          " errors=%d no_count_header=%d"
          % (len(out), len(txt), len(bins), sum(int(r[cols.index("txt_rows")]) for r in txt),
             sum(int(r[cols.index("bin_count")]) for r in bins if r[cols.index("bin_recsize")] != "?"),
             v.count("rows="), v.count("rows-x"), v.count("DIFF"),
             sum(1 for r in bins if not r[cols.index("bin_count")].isdigit()),
             sum(1 for r in bins if r[cols.index("bin_recsize")] == "?" and r[cols.index("bin_count")].isdigit())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

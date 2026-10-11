"""Item art index: map every base, unique and set item to its inventory icon, drop animation,
colour transforms and worn-art keys (plan 0009 Phase 2).

Usage:
  python3 -I tools/item_art.py index <root> [--out PATH]   (PATH: a .tsv file or a directory)

<root> is a merged data tree (e.g. workspace/merged). Writes one TSV line per row of weapons, armor,
misc, uniqueitems and setitems (Expansion markers dropped, as in the .bin) to PATH (default
workspace/render/items/index.tsv), then the missing references to missing.tsv beside it, and prints a
summary ending with one machine-readable line:
  SURVEY item_art lines=N inv_missing=N flippy_missing=N worn_missing=N missing=N

The cells are read from the .txt tables; for every column read here `excel_bin.py diff` shows the
.txt and the .bin agree in every record (docs/tables/*.md). File lookups are case-insensitive.

What the columns mean (docs/tables/README.md, "Item art index"):
  inv_dc6 / flippy_dc6   data/global/items/<file>.dc6 as found in <root> (the real spelling), or the
                         wanted path when missing; inv_src / flippy_src say which column supplied it.
                         For uniques and sets the fallback (own file, else base uniqueinvfile or
                         setinvfile, else base invfile) is a HEURISTIC, not anchored game behaviour.
  transform columns      base Transform / InvTrans (ints), unique/set chrtransform / invtransform
                         (colors.txt codes); how the game combines them is not modelled.
  worn_*                 composit layer token from `component` (row of composit.txt; 16 = none),
                         the DCC component code (alternategfx, or armtype tokens per body part for
                         body armour), weapon classes; worn_files counts the player-class DCCs under
                         data/global/chars/<cls>/<layer>/ named <cls><layer><code>*.dcc. A data-only
                         interpretation of file names, not anchored game behaviour.
Stdlib only. Read-only except the two output files.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

EXCEL = os.path.join("data", "global", "excel")
ITEMS = os.path.join("data", "global", "items")
CHARS = os.path.join("data", "global", "chars")
PARTS = [("rArm", "RA"), ("lArm", "LA"), ("Torso", "TR"), ("Legs", "LG"), ("rSPad", "S1"), ("lSPad", "S2")]
HEADER = ["kind", "row", "id", "name", "base",
          "inv_dc6", "inv_src", "inv_status", "flippy_dc6", "flippy_src", "flippy_status",
          "base_transform", "base_invtrans", "chrtransform", "invtransform",
          "worn_layer", "worn_code", "wclass", "2handedwclass", "armtype_parts", "worn_files", "worn_status"]


class Table:
    def __init__(self, excel_dir, name):
        self.header, self.rows = excel_bin.read_txt(excel_bin.find_file(excel_dir, name, ".txt"))
        self.lower = {}
        for i, c in enumerate(self.header):
            self.lower.setdefault(c.lower(), i)

    def get(self, row, col):
        i = self.lower.get(col.lower())
        return "" if i is None else row[i].strip()


def file_map(root):
    """lower-case path relative to root -> real relative path, for every file under root."""
    out = {}
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), root)
            out.setdefault(rel.lower(), rel)
    return out


def chars_index(files):
    """(layer, code) -> number of player-class DCCs <cls><layer><code>*.dcc under chars/<cls>/<layer>/."""
    out = {}
    pre = CHARS.lower() + os.sep
    for low in files:
        if not low.startswith(pre) or not low.endswith(".dcc"):
            continue
        parts = low[len(pre):].split(os.sep)
        if len(parts) != 3:
            continue
        cls, layer, fname = parts
        if not fname.startswith(cls + layer) or len(fname) < len(cls + layer) + 3:
            continue
        code = fname[len(cls + layer):len(cls + layer) + 3]
        out.setdefault((layer, code), set()).add(cls)
    return out


def resolve_dc6(files, name):
    """Return (path, status): status ok | missing | none (blank cell)."""
    if not name:
        return "", "none"
    want = os.path.join(ITEMS, name + ".dc6")
    real = files.get(want.lower())
    return (real, "ok") if real else (want, "missing")


def worn_keys(t, row, composit, armtype, chars):
    """Worn-art keys of one base row: (layer, code, wclass, 2h, parts, files, status)."""
    comp = t.get(row, "component")
    try:
        ci = int(comp)
    except ValueError:
        ci = -1
    if not 0 <= ci < len(composit):
        return "", "", t.get(row, "wclass"), t.get(row, "2handedwclass"), "", "", "none"
    layer = composit[ci]
    parts, files, status = "", 0, "ok"
    if layer == "tr":
        # body armour: one armtype token per body part (rArm..lSPad hold armtype row indices)
        keys = []
        miss = 0
        for col, lay in PARTS:
            v = t.get(row, col)
            tok = armtype[int(v)] if v.isdigit() and int(v) < len(armtype) else "?"
            n = len(chars.get((lay.lower(), tok), ()))
            keys.append("%s=%s:%d" % (lay, tok, n))
            files += n
            miss += n == 0
        parts = ",".join(keys)
        code = ""
        status = "ok" if miss == 0 else "missing"
    else:
        code = t.get(row, "alternategfx").lower()
        files = len(chars.get((layer, code), ())) if code else 0
        status = "ok" if files else "missing"
    return layer.upper(), code, t.get(row, "wclass"), t.get(row, "2handedwclass"), parts, str(files), status


def cmd_index(root, out):
    excel_dir = os.path.join(root, EXCEL)
    files = file_map(root)
    chars = chars_index(files)
    composit = [r[1].strip().lower() for r in Table(excel_dir, "composit").rows]
    armtype = [r[1].strip().lower() for r in Table(excel_dir, "armtype").rows]
    lines, missing = [], []
    base = {}  # code -> (kind, table, row)
    counts = {}

    def emit(rec, rowno):
        lines.append(rec)
        counts[rec["kind"]] = counts.get(rec["kind"], 0) + 1
        for what in ("inv", "flippy", "worn"):
            if rec[what + "_status"] == "missing":
                path = rec[what + "_dc6"] if what != "worn" else (
                    rec["worn_layer"] + ":" + (rec["worn_code"] or rec["armtype_parts"]))
                missing.append([rec["kind"], str(rowno), rec["id"], rec["name"], what, path])

    for kind in ("weapons", "armor", "misc"):
        t = Table(excel_dir, kind)
        for i, row in enumerate(t.rows):
            code = t.get(row, "code")
            base.setdefault(code, (kind, t, row))
            inv, inv_st = resolve_dc6(files, t.get(row, "invfile"))
            flp, flp_st = resolve_dc6(files, t.get(row, "flippyfile"))
            if kind == "misc" and t.get(row, "component") in ("", "16"):
                wk = ("", "", "", "", "", "", "none")
            else:
                wk = worn_keys(t, row, composit, armtype, chars)
            rec = dict(kind=kind, row=str(i), id=code, name=t.get(row, "name"), base="",
                       inv_dc6=inv, inv_src="invfile" if inv else "", inv_status=inv_st,
                       flippy_dc6=flp, flippy_src="flippyfile" if flp else "", flippy_status=flp_st,
                       base_transform=t.get(row, "Transform"), base_invtrans=t.get(row, "InvTrans"),
                       chrtransform="", invtransform="")
            rec.update(zip(HEADER[-7:], wk))
            emit(rec, i)

    for kind, idcol, codecol, own in (("uniqueitems", "index", "code", "uniqueinvfile"),
                                      ("setitems", "index", "item", "setinvfile")):
        t = Table(excel_dir, kind)
        for i, row in enumerate(t.rows):
            code = t.get(row, codecol)
            b = base.get(code)
            bt, brow = (b[1], b[2]) if b else (None, None)
            cands = [(t.get(row, "invfile"), "invfile")]
            if b:
                cands += [(bt.get(brow, own), "base " + own), (bt.get(brow, "invfile"), "base invfile")]
            name, src = next(((n, s) for n, s in cands if n), ("", ""))
            inv, inv_st = resolve_dc6(files, name)
            fcands = [(t.get(row, "flippyfile"), "flippyfile")]
            if b:
                fcands.append((bt.get(brow, "flippyfile"), "base flippyfile"))
            fname, fsrc = next(((n, s) for n, s in fcands if n), ("", ""))
            flp, flp_st = resolve_dc6(files, fname)
            if b and not (b[0] == "misc" and bt.get(brow, "component") in ("", "16")):
                wk = worn_keys(bt, brow, composit, armtype, chars)
            else:
                wk = ("", "", "", "", "", "", "none")
            if code and not b:
                inv_st = inv_st if name else "nobase"
            rec = dict(kind=kind, row=str(i), id=t.get(row, idcol), name=t.get(row, idcol), base=code,
                       inv_dc6=inv, inv_src=src, inv_status=inv_st,
                       flippy_dc6=flp, flippy_src=fsrc, flippy_status=flp_st,
                       base_transform=bt.get(brow, "Transform") if b else "",
                       base_invtrans=bt.get(brow, "InvTrans") if b else "",
                       chrtransform=t.get(row, "chrtransform"), invtransform=t.get(row, "invtransform"))
            rec.update(zip(HEADER[-7:], wk))
            emit(rec, i)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="latin-1") as fh:
        fh.write("\t".join(HEADER) + "\n")
        for rec in lines:
            fh.write("\t".join(rec[h] for h in HEADER) + "\n")
    mpath = os.path.join(os.path.dirname(out), "missing.tsv")
    with open(mpath, "w", encoding="latin-1") as fh:
        fh.write("kind\trow\tid\tname\twhat\tpath\n")
        for m in missing:
            fh.write("\t".join(m) + "\n")

    def n(kind=None, st=None, what="inv"):
        return sum(1 for r in lines if (kind is None or r["kind"] == kind) and r[what + "_status"] == st)

    print("wrote %s (%d lines) and %s (%d missing references)" % (out, len(lines), mpath, len(missing)))
    for kind in ("weapons", "armor", "misc", "uniqueitems", "setitems"):
        print("  %-12s lines=%-4d inv ok=%-4d missing=%-3d none=%-3d nobase=%-2d  flippy ok=%-4d missing=%-3d"
              "  worn ok=%-4d missing=%-3d none=%d"
              % (kind, counts.get(kind, 0), n(kind, "ok"), n(kind, "missing"), n(kind, "none"),
                 n(kind, "nobase"), n(kind, "ok", "flippy"), n(kind, "missing", "flippy"),
                 n(kind, "ok", "worn"), n(kind, "missing", "worn"), n(kind, "none", "worn")))
    inv_m, flp_m, worn_m = n(None, "missing"), n(None, "missing", "flippy"), n(None, "missing", "worn")
    print("SURVEY item_art lines=%d inv_missing=%d flippy_missing=%d worn_missing=%d missing=%d"
          % (len(lines), inv_m, flp_m, worn_m, len(missing)))
    return 0


def main(argv):
    if len(argv) < 2 or argv[0] != "index":
        print(__doc__)
        return 2
    root = argv[1]
    out = os.path.join("workspace", "render", "items", "index.tsv")
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
        if os.path.isdir(out) or out.endswith(os.sep):
            out = os.path.join(out, "index.tsv")
    return cmd_index(root, out)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

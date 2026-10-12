"""Item art index: map every base, unique and set item to its inventory icon, drop animation,
colour transforms and worn-art keys (plan 0009 Phase 2).

Usage:
  python3 -I tools/item_art.py index <root> [--out PATH]   (PATH: a .tsv file or a directory)
  python3 -I tools/item_art.py tint <root> [--index PATH] [--out DIR]
      render every unique and set row with a colour code: the inventory icon (frame 0) shifted by
      (base InvTrans file, invtransform colour) and every drop-animation frame shifted by (base
      Transform file, chrtransform colour), into DIR/tint/<kind>/<row>_<id>/ (default DIR
      workspace/render/items), plus DIR/tint.tsv. Transform type n -> palette.ITEM_SHIFT_FILES[n-1]
      and which colour serves which view are LEADS (docs/formats/item-palette.md), not game behaviour.
  python3 -I tools/item_art.py sheets <root> [--index PATH] [--out DIR] [--jobs N]
      one contact sheet per index line, DIR/<code>.png for a base item and
      DIR/{unique,set}_<row>_<slug>.png otherwise: inventory icon (frame 0), drop animation (first
      and last frame of each direction), worn layer composed on the reference character (REF_CLASS
      ba, mode NU, direction 4, frame 0; cof.compose_frame); uniques and sets shifted as in `tint`,
      the worn layer with (base Transform, chrtransform). Also DIR/sheets.tsv (one line per index
      line: sheet file, per-panel note or reason) and DIR/index.html (local browsing page, never
      published or committed). Last line: SURVEY item_sheets lines=N sheets=N no_art=N worn=N errors=N
  python3 -I tools/item_art.py render <root> [out]
      regenerate <out>/items/ (default out workspace/render): index, palette swatches, tint, sheets.
      This is the render_all.py `items` step.

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


def _slug(text):
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_") or "x"


def shift_map(type_cell, code, codes, maps):
    """(transform type cell, colors.txt code) -> (dat name, 256-byte map) or (reason, None).
    Type n -> palette.ITEM_SHIFT_FILES[n-1], map = colour row: both LEADS (item-palette.md)."""
    import palette as pal
    if not code:
        return "no-colour", None
    if code not in codes:
        return "bad-colour:" + code, None
    t = int(type_cell) if type_cell.strip().isdigit() else 0
    if not 1 <= t <= len(pal.ITEM_SHIFT_FILES):
        return "type-%d" % t, None
    name = pal.ITEM_SHIFT_FILES[t - 1]
    return name, maps[name][codes.index(code)]


def cmd_tint(root, index_path, out_dir):
    import dc6
    import palette as pal
    import png
    units = pal.load(root, "units")
    codes = pal.colour_codes(root)
    maps = {n: pal.item_shift_maps(root, n) for n in pal.ITEM_SHIFT_FILES}
    with open(index_path, encoding="latin-1") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        rows = [dict(zip(head, ln.rstrip("\n").split("\t"))) for ln in fh]
    log = []
    counts = {"lines": 0, "inv": 0, "flp_files": 0, "flp_frames": 0, "skipped": 0, "errors": 0}

    def shifted(type_cell, code):
        """-> (file, palette) or (reason, None)."""
        what, remap = shift_map(type_cell, code, codes, maps)
        return what, (None if remap is None else pal.shift_rgb(units, remap))

    for r in rows:
        if r["kind"] not in ("uniqueitems", "setitems") or not (r["chrtransform"] or r["invtransform"]):
            continue
        counts["lines"] += 1
        dest = os.path.join(out_dir, "tint", r["kind"], "%s_%s" % (r["row"], _slug(r["id"])))
        rec = [r["kind"], r["row"], r["id"]]
        for view, dc6_col, st_col, type_col, code_col in (
                ("inv", "inv_dc6", "inv_status", "base_invtrans", "invtransform"),
                ("flp", "flippy_dc6", "flippy_status", "base_transform", "chrtransform")):
            what, rgb = shifted(r[type_col], r[code_col])
            if rgb is None or r[st_col] != "ok":
                rec += ["", r[code_col], what if rgb is None else "file-" + r[st_col]]
                counts["skipped"] += 1
                continue
            try:
                d = dc6.parse(open(os.path.join(root, r[dc6_col]), "rb").read())
            except (OSError, dc6.DC6Error) as e:
                rec += [what, r[code_col], "error:%s" % e]
                counts["errors"] += 1
                continue
            frames = d["frames"][:1] if view == "inv" else d["frames"]
            for f in frames:
                name = "inv.png" if view == "inv" else "flp_%d_%d.png" % (f["dir"], f["frame"])
                png.write_indexed(os.path.join(dest, name), f["width"], f["height"], dc6.frame_pixels(f), rgb)
            if view == "inv":
                counts["inv"] += 1
            else:
                counts["flp_files"] += 1
                counts["flp_frames"] += len(frames)
            rec += [what, r[code_col], "ok"]
        log.append(rec)
    os.makedirs(out_dir, exist_ok=True)
    tpath = os.path.join(out_dir, "tint.tsv")
    with open(tpath, "w", encoding="latin-1") as fh:
        fh.write("kind\trow\tid\tinv_dat\tinv_colour\tinv_status\tflp_dat\tflp_colour\tflp_status\n")
        for rec in log:
            fh.write("\t".join(rec) + "\n")
    reasons = {}
    for rec in log:
        for st in (rec[5], rec[8]):
            if st != "ok":
                reasons[st] = reasons.get(st, 0) + 1
    print("wrote %s (%d lines) and %s" % (tpath, len(log), os.path.join(out_dir, "tint")))
    print("  not rendered, by reason: %s" % (", ".join("%s %d" % kv for kv in sorted(reasons.items())) or "none"))
    print("SURVEY item_tint lines=%d inv=%d flp_files=%d flp_frames=%d skipped=%d errors=%d" % (
        counts["lines"], counts["inv"], counts["flp_files"], counts["flp_frames"], counts["skipped"],
        counts["errors"]))
    return 1 if counts["errors"] else 0


# ---------------------------------------------------------------- per-item sheets (plan 0009 Phase 4)

# Reference character for the worn panel: a renderer HEURISTIC, not game behaviour. Barbarian covers
# the most worn keys of the seven classes (745 of 861 index lines in mode NU; see the plan 0009 log);
# direction 4 faces the viewer; frame 0 of the neutral mode.
REF_CLASS = "ba"
REF_MODE = "nu"
REF_DIR = 4
REF_FRAME = 0
BODY_LAYERS = ("hd", "tr", "lg", "ra", "la", "s1", "s2")   # drawn as `lit` unless the item replaces them
GAP = 6


def sheet_name(r):
    """Sheet file name for one index line: <code>.png for a base item, <kind>_<row>_<slug>.png else."""
    if r["kind"] in ("weapons", "armor", "misc") and r["id"].isalnum():
        return r["id"].lower() + ".png"
    return "%s_%s_%s.png" % ({"uniqueitems": "unique", "setitems": "set"}.get(r["kind"], r["kind"]),
                              r["row"], _slug(r["id"]))


def _dc6_panels(root, path, remap, which, cache):
    """DC6 -> list of (w, h, pixels): frame 0 only (which='first0'), or per direction the first
    and the last frame (which='dirs')."""
    import dc6
    if path not in cache:
        cache[path] = dc6.parse(open(os.path.join(root, path), "rb").read())
    d = cache[path]
    by_dir = {}
    for f in d["frames"]:
        by_dir.setdefault(f["dir"], []).append(f)
    pick = []
    for di in sorted(by_dir):
        fs = sorted(by_dir[di], key=lambda f: f["frame"])
        pick += fs[:1] if which == "first0" else ([fs[0], fs[-1]] if len(fs) > 1 else fs[:1])
        if which == "first0":
            break
    out = []
    for f in pick:
        px = dc6.frame_pixels(f)
        if remap is not None:
            px = bytearray(remap[v] if v else 0 for v in px)
        out.append((f["width"], f["height"], px))
    return out


def _worn_panel(root, r, remap, cache):
    """-> ((w, h, pixels), note) or (None, reason). The item's layer(s) composed on REF_CLASS."""
    import cof
    lay = r["worn_layer"].lower()
    if r["worn_status"] != "ok" or not lay:
        return None, "no-worn-art"
    if lay == "tr":
        parts = {}
        for kv in r["armtype_parts"].split(","):
            k, v = kv.split("=", 1)
            parts[k.lower()] = v.split(":", 1)[0]
        wclass = "hth"
    else:
        parts = {lay: r["worn_code"]}
        wclass = r["wclass"].lower() if lay in ("rh", "lh") else "hth"
    unit = os.path.join("chars", REF_CLASS)
    cof_path = os.path.join(root, "data", "global", unit, "cof", REF_CLASS + REF_MODE + wclass + ".cof")
    if not os.path.isfile(cof_path):
        return None, "ref-no-cof:%s%s%s" % (REF_CLASS, REF_MODE, wclass)
    keep = set(BODY_LAYERS) | set(parts)
    c = cof.compose_frame(root, unit, REF_MODE, wclass, REF_DIR, REF_FRAME, parts,
                          keep=lambda n: n in keep, remaps={k: remap for k in parts} if remap else None,
                          cache=cache)
    if c is None:
        return None, "ref-compose-empty"
    got = dict(c["placed"])
    for k, v in sorted(parts.items()):
        want = REF_CLASS + k + v
        if k not in got or not got[k].lower().startswith(want):
            return None, "ref-no-dcc:%s???%s%s(%s)" % (REF_CLASS + k, REF_MODE, wclass, v)
    return (c["width"], c["height"], c["pixels"]), "%s %s%s dir%d" % (REF_CLASS, REF_MODE, wclass, REF_DIR)


def _assemble(panels):
    """Panels side by side, bottom-aligned, GAP px apart, 2 px margin. -> (w, h, pixels)."""
    m = 2
    w = 2 * m + sum(p[0] for p in panels) + GAP * (len(panels) - 1)
    h = 2 * m + max(p[1] for p in panels)
    px = bytearray(w * h)
    x = m
    for pw, ph, pp in panels:
        y = h - m - ph
        for row in range(ph):
            px[(y + row) * w + x:(y + row) * w + x + pw] = pp[row * pw:(row + 1) * pw]
        x += pw + GAP
    return w, h, px


def _sheet_one(root, out_dir, r, units, codes, maps, cache):
    """Render one sheet. -> (file or '', inv note, flippy note, worn note, status)."""
    import png
    tinted = r["kind"] in ("uniqueitems", "setitems")
    panels, notes = [], []
    for view, col, st, tcol, ccol, which in (
            ("inv", "inv_dc6", "inv_status", "base_invtrans", "invtransform", "first0"),
            ("flp", "flippy_dc6", "flippy_status", "base_transform", "chrtransform", "dirs")):
        if r[st] != "ok":
            notes.append("file-" + r[st])
            continue
        remap, note = None, "untinted"
        if tinted:
            what, remap = shift_map(r[tcol], r[ccol], codes, maps)
            note = "%s:%s" % (what, r[ccol]) if remap is not None else "untinted(%s)" % what
        try:
            ps = _dc6_panels(root, r[col], remap, which, cache)
        except Exception as e:  # noqa: BLE001 - logged per sheet
            notes.append("error:%s" % e)
            continue
        panels += ps
        notes.append(note + ("" if view == "inv" else " frames=%d" % len(ps)))
    remap = None
    wnote = ""
    if tinted:
        what, remap = shift_map(r["base_transform"], r["chrtransform"], codes, maps)
        wnote = " %s:%s" % (what, r["chrtransform"]) if remap is not None else ""
    try:
        wp, why = _worn_panel(root, r, remap, cache)
    except Exception as e:  # noqa: BLE001 - logged per sheet
        wp, why = None, "error:%s" % e
    if wp is not None:
        panels.append(wp)
        notes.append(why + wnote)
    else:
        notes.append(why)
    if not panels:
        return ["", notes[0], notes[1], notes[2], "no-art"]
    name = sheet_name(r)
    w, h, px = _assemble(panels)
    png.write_indexed(os.path.join(out_dir, name), w, h, px, units)
    errs = any(n.startswith("error:") for n in notes)
    return [name, notes[0], notes[1], notes[2], "error" if errs else "ok"]


def _sheet_chunk(args):
    root, out_dir, rows = args
    import palette as pal
    units = pal.load(root, "units")
    codes = pal.colour_codes(root)
    maps = {n: pal.item_shift_maps(root, n) for n in pal.ITEM_SHIFT_FILES}
    cache = {}
    return [(r["kind"], r["row"], r["id"], r["base"],
             _sheet_one(root, out_dir, r, units, codes, maps, cache)) for r in rows]


def _html(out_dir, log):
    import html
    rows = []
    for kind, row, ident, base, (name, inv, flp, worn, st) in log:
        img = '<img loading="lazy" src="%s">' % html.escape(name) if name else ""
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            html.escape(kind), row, html.escape(ident), html.escape(base), img,
            "<br>".join(html.escape(x) for x in ("inv: " + inv, "drop: " + flp, "worn: " + worn, st))))
    page = """<!doctype html><meta charset="utf-8"><title>Item sheets</title>
<style>body{background:#111;color:#ccc;font:13px sans-serif}td{border-bottom:1px solid #333;padding:4px;vertical-align:bottom}
img{image-rendering:pixelated;zoom:2}input{margin:6px 0;width:20em}</style>
<p>Local only, never published or committed (plan 0009 Phase 4). Panels: inventory icon, drop animation
(first and last frame per direction), worn layer on %s %s direction %d. Renderer heuristics, not evidence.</p>
<input id="q" placeholder="filter" oninput="for(const r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())">
<table><thead><tr><th>kind</th><th>row</th><th>id</th><th>base</th><th>sheet</th><th>notes</th></tr></thead><tbody>
%s
</tbody></table>
""" % (REF_CLASS, REF_MODE.upper(), REF_DIR, "\n".join(rows))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)


def cmd_sheets(root, index_path, out_dir, jobs=None):
    with open(index_path, encoding="latin-1") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        rows = [dict(zip(head, ln.rstrip("\n").split("\t"))) for ln in fh]
    os.makedirs(out_dir, exist_ok=True)
    jobs = jobs or os.cpu_count() or 1
    chunks = [rows[i::jobs] for i in range(jobs)]
    if jobs > 1:
        import multiprocessing
        with multiprocessing.Pool(jobs) as pool:
            parts = pool.map(_sheet_chunk, [(root, out_dir, c) for c in chunks])
    else:
        parts = [_sheet_chunk((root, out_dir, rows))]
    done = {}
    for part in parts:
        for rec in part:
            done[(rec[0], rec[1])] = rec
    log = [done[(r["kind"], r["row"])] for r in rows]
    spath = os.path.join(out_dir, "sheets.tsv")
    with open(spath, "w", encoding="latin-1") as fh:
        fh.write("kind\trow\tid\tbase\tsheet\tinv\tdrop\tworn\tstatus\n")
        for kind, row, ident, base, rec in log:
            fh.write("\t".join([kind, row, ident, base] + rec) + "\n")
    _html(out_dir, log)
    st = {}
    worn = {}
    for *_, rec in log:
        st[rec[4]] = st.get(rec[4], 0) + 1
        key = rec[3].split(":", 1)[0] if not rec[3].startswith(REF_CLASS + " ") else "ok"
        worn[key] = worn.get(key, 0) + 1
    print("wrote %d sheets, %s and index.html into %s" % (st.get("ok", 0) + st.get("error", 0), spath, out_dir))
    print("  status: %s" % ", ".join("%s %d" % kv for kv in sorted(st.items())))
    print("  worn panel: %s" % ", ".join("%s %d" % kv for kv in sorted(worn.items())))
    print("SURVEY item_sheets lines=%d sheets=%d no_art=%d worn=%d errors=%d" % (
        len(log), st.get("ok", 0) + st.get("error", 0), st.get("no-art", 0), worn.get("ok", 0),
        st.get("error", 0)))
    return 1 if st.get("error") else 0


def render(root, out):
    """render_all.py hook: regenerate <out>/items/ (index, tints, palette swatches, sheets, index.html)."""
    import palette as pal
    items = os.path.join(out, "items")
    index_path = os.path.join(items, "index.tsv")
    rc = cmd_index(root, index_path)
    rc = rc or pal.itemswatch(root, os.path.join(items, "palette"))
    rc = cmd_tint(root, index_path, items) or rc
    rc = cmd_sheets(root, index_path, items) or rc
    return rc


def main(argv):
    if len(argv) >= 2 and argv[0] == "render":
        return render(argv[1], argv[2] if len(argv) > 2 else os.path.join("workspace", "render"))
    if len(argv) >= 2 and argv[0] == "sheets":
        out_dir = os.path.join("workspace", "render", "items")
        if "--out" in argv:
            out_dir = argv[argv.index("--out") + 1]
        index_path = os.path.join(out_dir, "index.tsv")
        if "--index" in argv:
            index_path = argv[argv.index("--index") + 1]
        jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else None
        return cmd_sheets(argv[1], index_path, out_dir, jobs)
    if len(argv) >= 2 and argv[0] == "tint":
        out_dir = os.path.join("workspace", "render", "items")
        if "--out" in argv:
            out_dir = argv[argv.index("--out") + 1]
        index_path = os.path.join(out_dir, "index.tsv")
        if "--index" in argv:
            index_path = argv[argv.index("--index") + 1]
        return cmd_tint(argv[1], index_path, out_dir)
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

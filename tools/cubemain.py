"""CubeMain: the compiled form of the recipe cells, a survey of the stock rows, and the compile probe (plan 0030 P0).

Usage:
  python3 -I tools/cubemain.py rows      <excel-dir>              one block per cubemain.txt row: record index,
                                                                   header columns, each input and output cell with
                                                                   its decoded form; ends with the SURVEY line
  python3 -I tools/cubemain.py summary   <excel-dir>              counts only; the last line is
                                                                   `SURVEY cubemain key=value ...` (tools/gate.py --full)
  python3 -I tools/cubemain.py probe-txt <excel-dir> <out-dir>    write the compile-probe cubemain.txt: the stock rows,
                                                                   then PROBE_ROWS (docs/tables/CubeMain.md § Compile probe)

The cell compiler (compile_input, compile_output) turns an `input N` or `output`/`output b`/`output c` cell into the
fields of the compiled record; tools/excel_layouts.py uses it, through the `conv` field option, for the cubemain
layout that `tools/excel_bin.py diff` checks. The rules are read off the stock table and the compile probe
(docs/tables/CubeMain.md); the compiler itself is code the reverser reads (plan 0030 Phase 1).

A cell is a quoted comma list. Its first token is the item: an item code (weapons + armor + misc), an item type code
(itemtypes Code), `any`, `useitem` / `usetype` (outputs), a unique or set item name (uniqueitems / setitems
`index`), or a portal name (outputs). The other tokens are keywords (KEYWORDS), `qty=N`, `sock=N`, `pre=N`, `suf=N`.
Every cell of the stock table must decode with no token left over (`unexplained` in the SURVEY line).
<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). Stdlib only. Read-only,
except probe-txt, which writes only <out-dir>/cubemain.txt.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

ITEMS = "weapons:code+armor:code+misc:code"
TYPES = "itemtypes:Code"

# quality keywords: the quality byte they store (input +0x06, output +0x06)
QUALITY = {"low": 1, "nor": 2, "hiq": 3, "mag": 4, "set": 5, "rar": 6, "uni": 7, "crf": 8, "tmp": 9}

# input flag bits (input record +0x00, u16)
IN_ITEM, IN_TYPE, IN_NOS, IN_SOCK, IN_ETH, IN_NOE, IN_NAME, IN_UPG, IN_BAS, IN_EXC, IN_ELI, IN_NRU = (
    0x0001, 0x0002, 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0400, 0x0800)
IN_FLAGS = {"nos": IN_NOS, "sock": IN_SOCK, "eth": IN_ETH, "noe": IN_NOE, "upg": IN_UPG, "bas": IN_BAS,
            "exc": IN_EXC, "eli": IN_ELI, "nru": IN_NRU}

# output flag bits (output record +0x00, u16)
OUT_FLAGS = {"mod": 0x0001, "sock": 0x0002, "eth": 0x0004, "uni": 0x0008, "set": 0x0008, "uns": 0x0010,
             "rem": 0x0020, "reg": 0x0040, "exc": 0x0080, "eli": 0x0100, "rep": 0x0200, "rch": 0x0400}

# input keywords that an output cell accepts and the compiler ignores (the compile probe: no byte changes)
IGNORED_OUT = ("nos", "noe", "upg", "bas", "nru", "any")

# output kind byte (output record +0x08)
KIND_ITEM, KIND_TYPE, KIND_USEITEM, KIND_USETYPE = 0xFC, 0xFD, 0xFE, 0xFF
PORTALS = {"Cow Portal": 1, "Pandemonium Portal": 2, "Pandemonium Finale Portal": 3}
KIND_NAMES = {0: "none", KIND_ITEM: "item", KIND_TYPE: "type", KIND_USEITEM: "useitem", KIND_USETYPE: "usetype",
              1: "cow portal", 2: "pandemonium portal", 3: "pandemonium finale portal"}


def tokens(cell):
    c = cell.strip()
    if len(c) >= 2 and c[0] == '"' and c[-1] == '"':
        c = c[1:-1]
    return [t for t in c.split(",")] if c else []


def _lookup(refs, spec, key):
    return refs.index(spec).get(key)


def _names(refs):
    """index name -> ('uni'|'set', record index) over uniqueitems then setitems."""
    if "cube_names" not in refs.cache:
        out = {}
        for tag, spec in (("uni", "uniqueitems:index"), ("set", "setitems:index")):
            for k, v in refs.index(spec).items():
                out.setdefault(k, (tag, v))
        refs.cache["cube_names"] = out
    return refs.cache["cube_names"]


def _base_code(refs, tag, rec):
    """The item record index of a unique's or set item's base (`code` / `item` column)."""
    col = "code" if tag == "uni" else "item"
    code = refs.column("uniqueitems" if tag == "uni" else "setitems", col)[rec]
    return refs.index(ITEMS).get(code, -1)


def compile_input(cell, refs):
    """-> dict(flags, item, id, quality, qty, rest) for one `input N` cell; rest = tokens not explained."""
    d = dict(flags=0, item=0, id=0, quality=0, qty=0, rest=[], form=[])
    toks = tokens(cell)
    if not toks:
        return d
    head, kw = toks[0], toks[1:]
    names = _names(refs)
    if head == "any":
        d["flags"] |= IN_ITEM
        d["item"] = 0xFFFF
        d["form"].append("any")
    elif _lookup(refs, TYPES, head) is not None:
        # an input tries the item type before the item code: "axe" and "key" are both, and compile as the types
        # (stock rows 11, 81; the compile probe); an output tries the item first
        d["flags"] |= IN_TYPE
        d["item"] = _lookup(refs, TYPES, head)
        d["form"].append("type")
    elif _lookup(refs, ITEMS, head) is not None:
        d["flags"] |= IN_ITEM
        d["item"] = _lookup(refs, ITEMS, head)
        d["form"].append("item")
    elif head in names:
        tag, rec = names[head]
        d["flags"] |= IN_ITEM | IN_NAME
        d["item"] = _base_code(refs, tag, rec) & 0xFFFF
        d["id"] = rec + 1
        d["quality"] = QUALITY[tag]
        d["form"].append(tag + " name")
    else:
        d["rest"].append(head)
    for t in kw:
        if t in QUALITY:
            d["quality"] = QUALITY[t]
            d["form"].append(t)
        elif t in IN_FLAGS:
            d["flags"] |= IN_FLAGS[t]
            d["form"].append(t)
        elif t.startswith("qty="):
            d["qty"] = excel_bin.d2atoi(t[4:]) & 0xFF
            d["form"].append("qty")
        elif t.startswith("sock="):
            # the compile probe: "sock=N" in an input sets the sock flag; N is not stored
            d["flags"] |= IN_SOCK
            d["form"].append("sock=(ignored)")
        else:
            d["rest"].append(t)
    return d


def compile_output(cell, refs):
    """-> dict(flags, item, id, quality, qty, kind, pre1..3, suf1..3, rest) for one output cell."""
    d = dict(flags=0, item=0, id=0, quality=0, qty=0, kind=0, pre=[0, 0, 0], suf=[0, 0, 0], rest=[], form=[])
    slots = [0] * 6   # pre1..3, suf1..3: one array; a 4th pre= lands in suf1 (the compile probe)
    toks = tokens(cell)
    if not toks:
        return d
    head, kw = toks[0], toks[1:]
    names = _names(refs)
    if cell.strip() in PORTALS:
        d["kind"] = PORTALS[cell.strip()]
        d["form"].append("portal")
        return d
    if head == "useitem":
        d["kind"] = KIND_USEITEM
        d["form"].append("useitem")
    elif head == "usetype":
        d["kind"] = KIND_USETYPE
        d["form"].append("usetype")
    elif _lookup(refs, ITEMS, head) is not None:
        # an output tries the item code first ("axe" and "key", both an item and a type, compile as the items;
        # the compile probe and the sample table), an input the item type first
        d["kind"] = KIND_ITEM
        d["item"] = _lookup(refs, ITEMS, head)
        d["form"].append("item")
    elif _lookup(refs, TYPES, head) is not None:
        d["kind"] = KIND_TYPE
        d["item"] = _lookup(refs, TYPES, head)
        d["form"].append("type")
    elif head in names:
        tag, rec = names[head]
        d["kind"] = KIND_ITEM
        d["flags"] |= OUT_FLAGS[tag]
        d["item"] = _base_code(refs, tag, rec) & 0xFFFF
        d["id"] = rec + 1
        d["quality"] = QUALITY[tag]
        d["form"].append(tag + " name")
    else:
        d["rest"].append(head)
    npre = nsuf = 0
    for t in kw:
        if t in QUALITY:
            d["quality"] = QUALITY[t]
            d["form"].append(t)
        elif t in OUT_FLAGS and t not in ("uni", "set"):
            d["flags"] |= OUT_FLAGS[t]
            if t == "reg":
                # the compile probe: "useitem,reg" stores kind 0xFF (usetype), not 0xFE
                d["kind"] = KIND_USETYPE
            d["form"].append(t)
        elif t in IGNORED_OUT:
            d["form"].append(t + "(ignored)")
        elif t.startswith("qty="):
            d["qty"] = excel_bin.d2atoi(t[4:]) & 0xFF
            d["form"].append("qty")
        elif t.startswith("sock="):
            d["flags"] |= OUT_FLAGS["sock"]
            d["qty"] = excel_bin.d2atoi(t[5:]) & 0xFF
            d["form"].append("sock")
        elif t.startswith("pre=") and npre < 6:
            slots[npre] = excel_bin.d2atoi(t[4:]) & 0xFFFF
            npre += 1
            d["form"].append("pre")
        elif t.startswith("suf=") and nsuf < 3:
            slots[3 + nsuf] = excel_bin.d2atoi(t[4:]) & 0xFFFF
            nsuf += 1
            d["form"].append("suf")
        else:
            d["rest"].append(t)
    d["pre"], d["suf"] = slots[:3], slots[3:]
    return d


def in_part(part):
    def conv(cell, refs):
        return compile_input(cell, refs)[part]
    return conv


def out_part(part, k=None):
    def conv(cell, refs):
        v = compile_output(cell, refs)[part]
        return v[k] if k is not None else v
    return conv


# ---------------------------------------------------------------- survey

QNAME = {v: k for k, v in QUALITY.items()}


def load_rows(excel_dir):
    header, rows = excel_bin.read_txt(excel_bin.find_file(excel_dir, "cubemain", ".txt"))
    ix = {c: i for i, c in enumerate(header)}
    return ix, rows


def show_in(d):
    return "%s flags=0x%03X item=%d id=%d q=%s qty=%d" % (
        "/".join(d["form"]) or "-", d["flags"], d["item"] if d["item"] != 0xFFFF else -1, d["id"],
        QNAME.get(d["quality"], d["quality"]), d["qty"])


def show_out(d):
    pre = ",".join(str(v) for v in d["pre"] if v)
    suf = ",".join(str(v) for v in d["suf"] if v)
    return "%s kind=%s flags=0x%03X item=%d id=%d q=%s qty=%d%s%s" % (
        "/".join(d["form"]) or "-", KIND_NAMES.get(d["kind"], d["kind"]), d["flags"], d["item"], d["id"],
        QNAME.get(d["quality"], d["quality"]), d["qty"], " pre=" + pre if pre else "", " suf=" + suf if suf else "")


def survey(excel_dir, verbose):
    refs = excel_bin.Refs(excel_dir)
    ix, rows = load_rows(excel_dir)
    c = {k: 0 for k in ("rows", "enabled", "disabled", "ladder", "version0", "version100", "min_diff", "class",
                        "op", "inputs", "input_cells", "outputs_b", "outputs_c", "mod_lines", "mod_chance",
                        "unexplained")}
    kinds, in_forms, out_forms = {}, {}, {}
    for i, r in enumerate(rows):
        get = lambda col: r[ix[col]] if ix.get(col) is not None and ix[col] < len(r) else ""  # noqa: E731
        c["rows"] += 1
        c["enabled" if get("enabled") == "1" else "disabled"] += 1
        c["ladder"] += get("ladder") == "1"
        v = get("version")
        c["version100" if v == "100" else "version0"] += 1
        c["min_diff"] += get("min diff") not in ("", "0")
        c["class"] += get("class") != ""
        c["op"] += get("op") not in ("", "0")
        c["inputs"] += excel_bin.d2atoi(get("numinputs") or "0")
        lines = []
        for k in range(1, 8):
            cell = get("input %d" % k)
            if not cell:
                continue
            d = compile_input(cell, refs)
            c["input_cells"] += 1
            c["unexplained"] += bool(d["rest"])
            for f in d["form"]:
                in_forms[f] = in_forms.get(f, 0) + 1
            lines.append("    in%d  %-34s %s%s" % (k, cell, show_in(d), "  UNEXPLAINED " + ",".join(d["rest"])
                                                     if d["rest"] else ""))
        for col, p in (("output", ""), ("output b", "b "), ("output c", "c ")):
            cell = get(col)
            if not cell:
                continue
            if col != "output":
                c["outputs_" + col[-1]] += 1
            d = compile_output(cell, refs)
            c["unexplained"] += bool(d["rest"])
            kind = KIND_NAMES.get(d["kind"], str(d["kind"]))
            if col == "output":
                key = kind + ("," + QNAME[d["quality"]] if d["quality"] else "")
                kinds[key] = kinds.get(key, 0) + 1
            for f in d["form"]:
                out_forms[f] = out_forms.get(f, 0) + 1
            mods = []
            for m in range(1, 6):
                code = get("%smod %d" % (p, m))
                if code:
                    c["mod_lines"] += 1
                    c["mod_chance"] += get("%smod %d chance" % (p, m)) not in ("", "0")
                    mods.append("%s(%s)%s..%s" % (code, get("%smod %d param" % (p, m)), get("%smod %d min" % (p, m)),
                                                  get("%smod %d max" % (p, m))))
            lv = "lvl=%s plvl=%s ilvl=%s" % (get(p + "lvl") or "-", get(p + "plvl") or "-", get(p + "ilvl") or "-")
            lines.append("    %-4s %-34s %s %s%s%s" % ({"output": "out", "output b": "outb", "output c": "outc"}[col],
                                                       cell, show_out(d), lv, " mods " + " ".join(mods) if mods else "",
                                                       "  UNEXPLAINED " + ",".join(d["rest"]) if d["rest"] else ""))
        if verbose:
            print("%3d %s  enabled=%s ladder=%s version=%s op=%s numinputs=%s" % (
                i, get("description"), get("enabled") or "-", get("ladder") or "-", v or "-", get("op") or "-",
                get("numinputs")))
            print("\n".join(lines))
    print("output kinds (output column): " + ", ".join("%s %d" % kv for kv in sorted(kinds.items())))
    print("input forms and keywords: " + ", ".join("%s %d" % kv for kv in sorted(in_forms.items())))
    print("output forms and keywords: " + ", ".join("%s %d" % kv for kv in sorted(out_forms.items())))
    keys = dict(c)
    for k, n in kinds.items():
        keys["kind_" + k.replace(" ", "_").replace(",", "_")] = n
    print("SURVEY cubemain " + " ".join("%s=%d" % kv for kv in keys.items()))
    return 1 if c["unexplained"] else 0


# ---------------------------------------------------------------- compile probe

def _row(header, **cells):
    r = [""] * len(header)
    ix = {c: i for i, c in enumerate(header)}
    base = {"enabled": "1", "version": "100", "numinputs": "1", "input 1": "isc", "output": "rin", "*eol": "0"}
    base.update({k.replace("_", " "): v for k, v in cells.items()})
    for k, v in base.items():
        r[ix[k]] = v
    return r


def _q(s):
    return '"%s"' % s if "," in s else s


PROBE_INPUTS = ["rin", "ring", "any", "ring,low", "ring,nor", "ring,hiq", "ring,mag", "ring,set", "ring,rar",
                "ring,uni", "ring,crf", "ring,tmp", "ring,nos", "ring,sock", "ring,noe", "ring,eth", "ring,upg",
                "ring,bas", "ring,exc", "ring,eli", "ring,nru", "ring,qty=5", "ring,sock=3", "ring,qty=300",
                "rin,mag,nos,sock,noe,eth,upg,bas,exc,eli,nru,qty=2", "Angelic Halo", "Tal Rasha's Horadric Crest",
                "Harlequin Crest", "The Stone of Jordan", "any,sock=2", "key", "axe,mag"]
PROBE_OUTPUTS = ["ring", "ring,mag", "rin,low", "rin,nor", "rin,hiq", "rin,mag", "rin,set", "rin,rar", "rin,uni",
                 "rin,crf", "rin,tmp", "useitem,uns", "useitem,rem", "useitem,reg", "useitem,rep", "useitem,rch",
                 "useitem,mod", "useitem,eth", "useitem,exc", "useitem,eli", "useitem,nru", "useitem,upg",
                 "useitem,bas", "useitem,nos", "useitem,noe", "useitem,sock=4", "useitem,qty=7",
                 "rin,sock=2,qty=3", "rin,qty=3,sock=2", "rin,pre=1,pre=2,pre=3,suf=4,suf=5,suf=6",
                 "rin,pre=7,pre=8,pre=9,pre=10", "The Stone of Jordan", "Harlequin Crest", "Angelic Halo",
                 "Tal Rasha's Horadric Crest", "usetype,uni", "usetype,set", "any", "Cow Portal",
                 "Pandemonium Portal", "Pandemonium Finale Portal", "useitem,any", "axe", "key,mag"]


def probe_rows(header):
    rows = []
    # header columns: widths and placement of the columns that are blank in every stock row
    rows.append(_row(header, description="probe hdr a", ladder="1", min_diff="2", **{"class": "sor"}, op="5",
                     param="1234567", value="-7", numinputs="3", version="100"))
    rows.append(_row(header, description="probe hdr b", min_diff="1", op="300", param="-1", value="70000",
                     **{"class": "ass"}, version="1"))
    rows.append(_row(header, description="probe hdr c", enabled="0", min_diff="300", op="-2", param="65537",
                     value="-65537", **{"class": "dru"}, numinputs="7", version="0"))
    # outputs a/b/c with every lvl and mod column filled with distinct values
    mods = {"output": ("", ["str", "dex", "vit", "enr", "hp"], 10),
            "output b": ("b ", ["mana", "res-fire", "res-cold", "res-ltng", "res-pois"], 100),
            "output c": ("c ", ["ac", "ac%", "dmg%", "att", "light"], 200)}
    cells = {}
    for out, (p, codes, base) in mods.items():
        cells[out] = {"output": '"rin,mag"', "output b": '"amu,rar"', "output c": '"jew,mag"'}[out]
        cells[p + "lvl"], cells[p + "plvl"], cells[p + "ilvl"] = str(base + 1), str(base + 2), str(base + 3)
        for k, code in enumerate(codes, start=1):
            cells["%smod %d" % (p, k)] = code
            cells["%smod %d chance" % (p, k)] = str(base + 10 + k)
            cells["%smod %d param" % (p, k)] = str(base + 20 + k)
            cells["%smod %d min" % (p, k)] = str(base + 30 + k)
            cells["%smod %d max" % (p, k)] = str(base + 40 + k)
    r = _row(header, description="probe mods")
    ix = {c: i for i, c in enumerate(header)}
    for k, v in cells.items():
        r[ix[k]] = v
    rows.append(r)
    # widths of the mod fields; a skill name in a param cell
    rows.append(_row(header, description="probe mod widths", mod_1="aura", mod_1_chance="300", mod_1_param="70000",
                     mod_1_min="-3", mod_1_max="65537", mod_2="aura", mod_2_param="Holy Freeze", mod_2_min="1",
                     mod_2_max="2", mod_3="nosuchprop", mod_3_min="1", mod_3_max="1", lvl="300", plvl="-1",
                     ilvl="256"))
    for c in PROBE_INPUTS:
        rows.append(_row(header, description="probe in " + c, input_1=_q(c)))
    for c in PROBE_OUTPUTS:
        rows.append(_row(header, description="probe out " + c, output=_q(c)))
    return rows


def cmd_probe_txt(excel_dir, out_dir):
    path = excel_bin.find_file(excel_dir, "cubemain", ".txt")
    with open(path, "rb") as fh:
        raw = fh.read().decode("latin-1")
    header = raw.split("\r\n", 1)[0].split("\t")
    body = raw if raw.endswith("\r\n") else raw + "\r\n"
    extra = "".join("\t".join(r) + "\r\n" for r in probe_rows(header))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "cubemain.txt")
    with open(out, "wb") as fh:
        fh.write((body + extra).encode("latin-1"))
    print("wrote %s: stock rows + %d probe rows" % (out, len(probe_rows(header))))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "probe-txt" and len(argv) == 3:
        return cmd_probe_txt(argv[1], argv[2])
    if cmd in ("rows", "summary") and len(argv) == 2:
        return survey(argv[1], cmd == "rows")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

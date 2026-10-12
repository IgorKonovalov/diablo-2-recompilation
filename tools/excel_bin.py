"""Decode compiled excel .bin tables with a layout, and diff them cell by cell against the .txt source.

Usage:
  python3 -I tools/excel_bin.py diff  <excel-dir> <table> [--show N] [--list]
  python3 -I tools/excel_bin.py dump  <excel-dir> <table> [record ...]
  python3 -I tools/excel_bin.py probe <excel-dir> <table> [column ...]
  python3 -I tools/excel_bin.py unknown <excel-dir> <table>
  python3 -I tools/excel_bin.py bindiff <excel-dir> <table> <other.bin>
  python3 -I tools/excel_bin.py survey <excel-dir>

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). <table> is the
lowercase basename (treasureclassex, levels, leveldefs, ...). Layouts live in tools/excel_layouts.py.

diff     decodes every record of <table>.bin with its layout, turns each .txt cell into the value the
         compiler stores (docs/formats/excel-bin.md, "Cell encoding rules"), and compares every mapped
         column over every record; columns the .txt lacks are checked against the missing-column default. Prints per-column
         mismatch counts and the first --show N mismatches (default 5). --list prints every mismatch.
         Mismatches covered by an `explain` entry in the layout are counted separately as explained.
         Exit 0 only when there are no unexplained mismatches.
dump     prints the decoded fields of the given records (default: record 0).
probe    layout discovery: for each .txt column (or the ones named) lists every (offset, encoding)
         under which the .bin agrees with the column over every record. Encodings tried: integers
         (u8/s8/u16/s16/u32/s32, blank -> 0 or -1), single bits, NUL-terminated char arrays, 4-char
         space-padded codes, and indices into the rows of other tables (name, code or id columns).
bindiff  decodes <table>.bin and another build of it (e.g. an older archive's copy) with the same
         layout and lists every field that differs, record by record.
survey   runs diff for every table with a layout and prints its counts; the last line is the
         `SURVEY excel_layout tables= records= cells= unexplained= explained= errors= <table>_cells=
         <table>_bad= ...` summary that tools/gate.py --full compares with its baseline. Exit 1 when any
         table has unexplained mismatches or cannot be diffed.
unknown  lists the byte ranges of the record that no layout field covers, with the distinct values seen.

Text rules (docs/formats/excel-bin.md): split on LF only, strip CR, skip zero-length lines, drop rows
whose first field is "Expansion" (the .bin has no record for them). Stdlib only. Read-only.
"""
import builtins
import io
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

INT_FMT = {"u8": "<B", "s8": "<b", "u16": "<H", "s16": "<h", "u32": "<I", "s32": "<i"}
INT_SIZE = {"u8": 1, "s8": 1, "u16": 2, "s16": 2, "u32": 4, "s32": 4}


# ---------------------------------------------------------------- file readers

def find_file(excel_dir, table, ext):
    want = (table + ext).lower()
    for name in os.listdir(excel_dir):
        if name.lower() == want:
            return os.path.join(excel_dir, name)
    return None


def read_txt(path):
    """Return (header, rows). header: list of unique column keys (duplicates get '#2', '#3';
    an empty header name becomes '#col<N>'). rows: list of lists of cell strings, Expansion rows dropped."""
    with open(path, "rb") as fh:
        lines = [ln.rstrip("\r") for ln in fh.read().decode("latin-1").split("\n")]
    raw = lines[0].split("\t")
    header, seen = [], {}
    for i, name in enumerate(raw):
        key = name if name else "#col%d" % i
        if key in seen:
            seen[key] += 1
            key = "%s#%d" % (key, seen[key])
        else:
            seen[key] = 1
        header.append(key)
    rows = []
    for ln in lines[1:]:
        if ln == "":
            continue
        cells = ln.split("\t")
        if cells[0] == "Expansion":
            continue
        cells += [""] * (len(header) - len(cells))
        rows.append(cells[:len(header)])
    return header, rows


def read_bin(path):
    with open(path, "rb") as fh:
        data = fh.read()
    count = struct.unpack_from("<I", data, 0)[0]
    size = (len(data) - 4) // count
    assert 4 + size * count == len(data), path
    return [data[4 + i * size: 4 + (i + 1) * size] for i in range(count)], size


def load_table(excel_dir, table):
    tp = find_file(excel_dir, table, ".txt")
    bp = find_file(excel_dir, table, ".bin")
    header, rows = read_txt(tp) if tp else (None, None)
    recs, size = read_bin(bp) if bp else (None, None)
    return header, rows, recs, size


# ---------------------------------------------------------------- reference dictionaries

class Refs:
    """Lazily built name -> row-index maps over other tables (the indices a .bin stores)."""

    def __init__(self, excel_dir):
        self.dir = excel_dir
        self.cache = {}

    def column(self, table, col):
        key = (table, col)
        if key not in self.cache:
            header, rows = read_txt(find_file(self.dir, table, ".txt"))
            ci = header.index(col)
            self.cache[key] = [r[ci] for r in rows]
        return self.cache[key]

    def index(self, spec, distinct=False):
        """spec: 'table:col' or 'table1:col+table2:col+...' (concatenated, e.g. the item list).
        Returns dict value -> first row index (first match wins). With distinct=True the index is the
        ordinal among distinct values instead (a repeated value does not take a new index)."""
        key = ("idx", spec, distinct)
        if key not in self.cache:
            out, base = {}, 0
            for part in spec.split("+"):
                t, c = part.split(":")
                vals = self.column(t, c)
                for i, v in enumerate(vals):
                    if v not in out:
                        out[v] = len(out) if distinct else base + i
                base += len(vals)
            self.cache[key] = out
        return self.cache[key]

    def names(self, spec, distinct=False):
        key = ("names", spec, distinct)
        if key not in self.cache:
            out = []
            for part in spec.split("+"):
                out += self.column(*part.split(":"))
            if distinct:
                out = list(dict.fromkeys(out))
            self.cache[key] = out
        return self.cache[key]

    def strings(self):
        """String-table key -> index map (tools/tbl.py), from data/local/lng/eng next to the excel dir."""
        if "strings" not in self.cache:
            import tbl
            lng = os.path.join(self.dir, "..", "..", "local", "lng", "eng")
            self.cache["strings"] = tbl.Strings(os.path.normpath(lng))
        return self.cache["strings"]

    def calc(self, name):
        key = ("calc", name)
        if key not in self.cache:
            with open(find_file(self.dir, name, ".bin"), "rb") as fh:
                self.cache[key] = fh.read()
        return self.cache[key]

    def size(self, spec):
        return sum(len(self.column(*p.split(":"))) for p in spec.split("+"))


# ---------------------------------------------------------------- field decoding

def decode_field(rec, f, refs=None):
    """Return the raw value of field f in record rec: int for integer, bit and ref fields,
    str for char arrays and 4-char codes."""
    kind = f["type"]
    off = f["off"]
    if kind in INT_FMT:
        return struct.unpack_from(INT_FMT[kind], rec, off)[0]
    if kind == "bit":
        return (rec[off] >> f["bit"]) & 1
    if kind == "str":
        raw = rec[off:off + f["len"]]
        return raw.split(b"\0", 1)[0].decode("latin-1")
    if kind == "code":
        raw = rec[off:off + 4]
        if raw == b"\0\0\0\0":
            return ""
        return raw.decode("latin-1").rstrip(" ")
    if kind == "ref":
        return struct.unpack_from(INT_FMT[f.get("int", "u16")], rec, off)[0]
    if kind == "tbl":
        return struct.unpack_from("<H", rec, off)[0]
    if kind == "calc":
        return decode_calc(refs.calc(f["code"]), struct.unpack_from("<i", rec, off)[0])
    if kind in ("tokcount", "toksum"):
        return rec[off]
    if kind == "toklist":
        return tuple(rec[off:off + f["len"]])
    raise ValueError(kind)


def list_tokens(cell):
    """A quoted comma list cell ("lit,med,hvy") as its non-empty tokens; a trailing empty token is
    dropped (monstats2 act2male S1v "lit,…,nil," compiles to 9 entries)."""
    c = cell.strip().strip('"')
    return [t for t in c.split(",") if t] if c else []


def decode_calc(code, pos):
    """A calc field is an s32 offset into a header-less *code.bin file, -1 when the cell is blank.
    Expressions that are a single integer constant are rendered back to that integer
    (0x07 s8 / 0x08 s16 / 0x09 s32 constant, then 0x00 end); anything else renders as <expr@pos>."""
    if pos == -1:
        return ""
    op = code[pos] if 0 <= pos < len(code) else None
    for opc, fmt, n in ((7, "<b", 1), (8, "<h", 2), (9, "<i", 4)):
        if op == opc and pos + 1 + n < len(code) and code[pos + 1 + n] == 0:
            return str(struct.unpack_from(fmt, code, pos + 1)[0])
    return "<expr@%d>" % pos


def d2atoi(cell):
    """Integer parse as the compiled tables show it: an optional leading '-', then every character
    adds (byte - 0x30) to value*10, digits or not (a lone space cell gives -16)."""
    neg = cell.startswith("-")
    v = 0
    for ch in cell[1:] if neg else cell:
        v = v * 10 + (ord(ch) - 0x30)
    return -v if neg else v


def _wrap(v, kind):
    bits = INT_SIZE[kind] * 8
    v &= (1 << bits) - 1
    if kind[0] == "s" and v >= 1 << (bits - 1):
        v -= 1 << bits
    return v


def normalize(cell, f, refs=None):
    """Turn a .txt cell into the raw value the decoded field should equal."""
    kind = f["type"]
    if kind in INT_FMT or kind == "bit":
        if cell == "":
            v = f.get("blank", 0)
        else:
            v = d2atoi(cell)
        if kind == "bit":
            return v
        return _wrap(v, kind)
    if kind == "ref":
        it = f.get("int", "u16")
        if cell == "" and f.get("blank") is not None:
            return _wrap(f["blank"], it)
        idx = refs.index(f["ref"], f.get("distinct", False))
        key = cell
        if f.get("code4"):
            # 4-char code columns: the cell is cut or space-padded to 4 bytes before the lookup
            # ("staff" finds "staf", "ring " finds "ring")
            key = cell[:4].rstrip(" ")
        if key not in idx:
            return _wrap(f.get("fallback", -1), it)
        return _wrap(idx[key] + f.get("bias", 0), it)
    if kind == "code":
        return cell[:4].rstrip(" ")
    if kind == "tbl":
        return refs.strings().index(cell)
    if kind == "calc":
        return cell if cell.lstrip("-").isdigit() or cell == "" else "<expr>"
    if kind == "tokcount":
        return len(list_tokens(cell))
    if kind == "toksum":
        # cell = the f["cols"] cells joined by TAB: sum over them of (token count - 1), 0 for blank
        return sum(max(len(list_tokens(c)) - 1, 0) for c in cell.split("\t")) & 0xFF
    if kind == "toklist":
        idx = refs.index(f["ref"])
        toks = [idx.get(t, -1) & 0xFF for t in list_tokens(cell)][:f["len"]]
        return tuple(toks + [0xFF] * (f["len"] - len(toks)))
    if kind == "str":
        return cell[:f["len"] - 1] if f.get("truncate") else cell
    return cell


def absent_value(f, refs):
    """What a field holds when its column is missing from the .txt: integer, string and string-key
    fields stay 0, index fields (ref) and calc offsets stay -1 (observed over weapons/armor/misc,
    magicsuffix, automagic)."""
    if f["type"] == "ref":
        return _wrap(-1, f.get("int", "u16"))
    if f["type"] == "tbl":
        return 0
    if f["type"] in INT_FMT or f["type"] == "bit":
        return 0
    return normalize("", f, refs)


def show_value(v, f, refs):
    """Readable form of a raw value for mismatch reports."""
    if f["type"] == "ref" and isinstance(v, int):
        names = refs.names(f["ref"], f.get("distinct", False))
        i = v - f.get("bias", 0)
        return "%d(%s)" % (v, names[i] if 0 <= i < len(names) else "-")
    return v


# ---------------------------------------------------------------- commands

def get_layout(table):
    import excel_layouts
    lay = excel_layouts.LAYOUTS[table.lower()]
    return lay


def cmd_diff(excel_dir, table, show=5, list_all=False, stats=None, out=None):
    """Print the diff report (to `out`, default stdout). If `stats` is a dict, fill it with the integer
    counts: records, fields, cells, unexplained, explained."""
    def print(*a):  # noqa: A001 - route the report to `out`
        builtins.print(*a, file=out or sys.stdout)
    lay = get_layout(table)
    refs = Refs(excel_dir)
    src = lay.get("txt", table)
    header, rows = read_txt(find_file(excel_dir, src, ".txt"))
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    assert size == lay["size"], (size, lay["size"])
    assert len(recs) == len(rows), (len(recs), len(rows))
    explain = lay.get("explain", {})
    total = bad = expl = exprs = 0
    cols_checked = 0
    unmapped = []
    report = []
    fields = [f for f in lay["fields"] if f.get("col")]
    lower = {}
    for i, c in enumerate(header):
        lower.setdefault(c.lower(), i)

    def col_index(name):
        # the compiler finds columns by name, case-insensitively (weapons "alternateGfx" fills the
        # same field as armor/misc "alternategfx"); exact match first
        return header.index(name) if name in header else lower.get(name.lower())

    mapped = {col_index(f["col"]) for f in fields} - {None}
    tonly = {k.lower() for k in lay.get("txt_only", {})}
    partner = lay.get("split_with")
    elsewhere = []
    pcols = {f["col"].lower() for f in get_layout(partner)["fields"] if f.get("col")} if partner else set()
    for i, c in enumerate(header):
        if i in mapped and c.lower() in pcols:
            raise SystemExit("column %r is mapped in both %s and %s" % (c, table, partner))
        if i not in mapped and c.lower() in pcols:
            elsewhere.append(c)
        elif i not in mapped and not c.startswith("*") and c.lower() not in tonly:
            unmapped.append(c)
    absent_cells = 0
    absent_cols = []
    unresolved = {}
    for f in fields:
        ci = col_index(f["col"])
        nbad = nexp = nexpr = 0
        samples = []
        if ci is None:
            # column missing from this .txt: the field holds what a blank cell gives, except that a
            # string-key (tbl) field stays 0 instead of the not-found index
            absent_cols.append(f["col"])
            want = absent_value(f, refs)
            for i, rec in enumerate(recs):
                total += 1
                absent_cells += 1
                got = decode_field(rec, f, refs)
                if got != want:
                    nbad += 1
                    samples.append((i, rows[i][0], "<absent>", show_value(got, f, refs), None))
            bad += nbad
            if nbad:
                report.append((f["col"], nbad, 0, samples))
            continue
        cols_checked += 1
        if f["type"] == "ref" and "fallback" not in f:
            idx = refs.index(f["ref"], f.get("distinct", False))
            for row in rows:
                key = row[ci][:4].rstrip(" ") if f.get("code4") else row[ci]
                if row[ci] != "" and key not in idx:
                    unresolved.setdefault((f["col"], row[ci]), 0)
                    unresolved[(f["col"], row[ci])] += 1
        for i, (row, rec) in enumerate(zip(rows, recs)):
            cell = "\t".join(row[col_index(c)] for c in f["cols"]) if f.get("cols") else row[ci]
            want = normalize(cell, f, refs)
            got = decode_field(rec, f, refs)
            total += 1
            if want == got or (want == "<expr>" and str(got).startswith("<expr@")):
                if want == "<expr>":
                    nexpr += 1
                continue
            ex = explain.get((f["col"], i))
            if ex is None and callable(explain.get(f["col"])):
                ex = explain[f["col"]](i, row[ci], got)
            if ex:
                nexp += 1
                samples.append((i, row[0], row[ci], show_value(got, f, refs), ex))
            else:
                nbad += 1
                samples.append((i, row[0], row[ci], show_value(got, f, refs), None))
        bad += nbad
        expl += nexp
        exprs += nexpr
        if nbad or nexp:
            report.append((f["col"], nbad, nexp, samples))
    if stats is not None:
        stats.update(records=len(recs), fields=cols_checked, cells=total, unexplained=bad, explained=expl)
    print("table %s: %d records x %d mapped fields = %d cells; %d unexplained, %d explained mismatches"
          % (table, len(recs), cols_checked, total, bad, expl))
    if absent_cols:
        print("  %d cells from %d layout columns absent from this .txt, checked as blank cells: %s"
              % (absent_cells, len(absent_cols), ", ".join(absent_cols)))
    if unresolved:
        print("  non-blank reference cells that match no row (stored as the not-found value): " +
              ", ".join("%s=%r x%d" % (c, v, n) for (c, v), n in sorted(unresolved.items())))
    if exprs:
        print("  %d calc cells are expressions (offset present, bytecode not decoded)" % exprs)
    for col, nbad, nexp, samples in report:
        print("  %-24s unexplained %d  explained %d" % (col, nbad, nexp))
        for s in (samples if list_all else samples[:show]):
            i, key, txt, got, ex = s
            print("      rec %4d %-28r txt=%-20r bin=%-20r%s" % (i, key[:28], txt, got, ("  [" + ex + "]") if ex else ""))
    if elsewhere:
        print("  %d .txt columns are compiled into %s.bin instead (diff that table)" % (len(elsewhere), partner))
    if unmapped and lay.get("partial"):
        print("  .txt columns outside this partial layout (not mapped, not checked): " + ", ".join(unmapped))
    elif unmapped:
        print("  .txt columns with no .bin field: " + ", ".join(unmapped))
    tonly = lay.get("txt_only", {})
    if tonly:
        print("  .txt-only columns (documented as not compiled): " + ", ".join(sorted(tonly)))
    return 0 if bad == 0 else 1


def field_size(f):
    if f["type"] == "ref":
        return INT_SIZE[f.get("int", "u16")]
    return INT_SIZE.get(f["type"]) or {"bit": 1, "str": f.get("len", 0), "code": 4, "tbl": 2, "calc": 4,
                                       "tokcount": 1, "toksum": 1, "toklist": f.get("len", 0)}[f["type"]]


def covered(lay):
    cov = {}
    for f in lay["fields"]:
        n = field_size(f)
        for b in range(f["off"], f["off"] + n):
            cov.setdefault(b, []).append(f.get("col") or f.get("name"))
    return cov


def cmd_unknown(excel_dir, table):
    lay = get_layout(table)
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    cov = covered(lay)
    b = 0
    while b < size:
        if b in cov:
            b += 1
            continue
        e = b
        while e < size and e not in cov:
            e += 1
        vals = {}
        for r in recs:
            vals[r[b:e]] = vals.get(r[b:e], 0) + 1
        top = sorted(vals.items(), key=lambda kv: -kv[1])[:6]
        print("+0x%03X..+0x%03X (%d B) not covered: %d distinct; %s" % (
            b, e - 1, e - b, len(vals), ", ".join("%s x%d" % (k.hex(), n) for k, n in top)))
        b = e
    for f in lay["fields"]:
        if f.get("col"):
            continue
        n = field_size(f)
        vals = {}
        for r in recs:
            vals[r[f["off"]:f["off"] + n]] = vals.get(r[f["off"]:f["off"] + n], 0) + 1
        top = sorted(vals.items(), key=lambda kv: -kv[1])[:6]
        print("+0x%03X %-10s (%d B, no .txt column): %d distinct; %s" % (
            f["off"], f["name"], n, len(vals), ", ".join("%s x%d" % (k.hex(), c) for k, c in top)))
    bytes_with_bits = {}
    for f in lay["fields"]:
        if f["type"] == "bit":
            bytes_with_bits.setdefault(f["off"], set()).add(f["bit"])
    for off, used in sorted(bytes_with_bits.items()):
        free = [b for b in range(8) if b not in used]
        if free:
            seen = {b: sum((r[off] >> b) & 1 for r in recs) for b in free}
            print("+0x%03X unmapped bits: %s" % (off, ", ".join("bit%d set in %d records" % kv for kv in seen.items())))


def cmd_dump(excel_dir, table, idxs):
    lay = get_layout(table)
    refs = Refs(excel_dir)
    recs, size = read_bin(find_file(excel_dir, table, ".bin"))
    for i in idxs or [0]:
        print("record %d" % i)
        for f in sorted(lay["fields"], key=lambda f: (f["off"], f.get("bit", 0))):
            print("  +0x%03X %-5s %-24s %r" % (f["off"], f["type"], f.get("col") or f.get("name"),
                                              show_value(decode_field(recs[i], f, refs), f, refs)))


# ---------------------------------------------------------------- probe

REF_CANDIDATES = [
    "weapons:code+armor:code+misc:code",
    "itemtypes:Code",
    "treasureclassex:Treasure Class",
    "monstats:Id",
    "levels:Name",
    "superuniques:Superunique",
    "skills:skill",
    "missiles:Missile",
    "monprop:Id",
    "montype:type",
    "monai:AI",
    "monsounds:Id",
    "monstats2:Id",
    "states:state",
    "sounds:Sound",
    "bodylocs:Code",
    "storepage:Code",
    "playerclass:Code",
    "hitclass:Code",
    "elemtypes:Code",
    "monmode:code",
    "objgroup:GroupName",
    "lvltypes:Name",
    "lvlwarp:Name",
    "lvlmaze:Name",
    "lvlsub:Name",
    "itemstatcost:Stat",
    "properties:code",
    "colors:Code",
    "overlay:overlay",
    "events:event",
    "misscalc:code",
    "skillcalc:code",
    "weapons:name+armor:name+misc:name",
    "soundenviron:Handle",
    "monseq:sequence",
]


def _int_ok(recs, vals, off, kind, blank):
    fmt = INT_FMT[kind]
    bits = INT_SIZE[kind] * 8
    for r, v in zip(recs, vals):
        x = struct.unpack_from(fmt, r, off)[0]
        w = blank if v is None else v
        if not -(1 << (bits - 1)) <= w < (1 << bits):
            return False
        w &= (1 << bits) - 1
        if kind[0] == "s" and w >= 1 << (bits - 1):
            w -= 1 << bits
        if x != w:
            return False
    return True


def probe_column(recs, size, cells, refs, ref_specs):
    out = []
    ints = []
    isint = True
    for c in cells:
        if c == "":
            ints.append(None)
            continue
        try:
            ints.append(int(c))
        except ValueError:
            isint = False
            break
    if isint:
        for kind in ("u8", "s8", "u16", "s16", "u32", "s32"):
            n = INT_SIZE[kind]
            for blank in (0, -1):
                if blank == -1 and None not in ints:
                    continue
                for off in range(0, size - n + 1):
                    if _int_ok(recs, ints, off, kind, blank):
                        out.append((off, kind + ("" if blank == 0 or None not in ints else " blank=-1")))
        if set(v or 0 for v in ints) <= {0, 1}:
            for off in range(size):
                for bit in range(8):
                    if all(((r[off] >> bit) & 1) == (v or 0) for r, v in zip(recs, ints)):
                        out.append((off, "bit%d" % bit))
    nonblank = [c for c in cells if c]
    if nonblank:
        enc = [c.encode("latin-1") for c in cells]
        maxlen = max(len(e) for e in enc)
        for off in range(0, size - maxlen + 1):
            if all(r[off:off + len(e)] == e and (off + len(e) >= size or r[off + len(e)] == 0)
                   for r, e in zip(recs, enc)):
                out.append((off, "str(maxlen %d)" % maxlen))
        if maxlen <= 4:
            for off in range(0, size - 3):
                for blank in (b"    ", b"\0\0\0\0"):
                    if all(r[off:off + 4] == (e.ljust(4, b" ") if e else blank) for r, e in zip(recs, enc)):
                        out.append((off, "code blank=%r" % blank))
        if not isint:
            for spec in ref_specs:
                try:
                    idx = refs.index(spec)
                except Exception:
                    continue
                if not all(c in idx for c in nonblank):
                    continue
                vals = [idx[c] if c else None for c in cells]
                for kind in ("u8", "u16", "s16", "u32", "s32"):
                    n = INT_SIZE[kind]
                    for blank in (0, -1):
                        for off in range(0, size - n + 1):
                            if _int_ok(recs, vals, off, kind, blank):
                                out.append((off, "ref %s %s blank=%d" % (spec, kind, blank)))
    return out


def cmd_probe(excel_dir, table, cols):
    header, rows, recs, size = load_table(excel_dir, table)
    refs = Refs(excel_dir)
    specs = []
    for s in REF_CANDIDATES:
        if all(find_file(excel_dir, p.split(":")[0], ".txt") for p in s.split("+")):
            try:
                refs.index(s)
                specs.append(s)
            except ValueError:
                pass
    for ci, col in enumerate(header):
        if cols and col not in cols:
            continue
        cells = [r[ci] for r in rows]
        res = probe_column(recs, size, cells, refs, specs)
        distinct = len(set(cells))
        shown = res if len(res) <= 12 else res[:12] + [("...", "%d more" % (len(res) - 12))]
        print("%-22s (%d distinct) %s" % (col, distinct, "; ".join(
            "+0x%03X %s" % (o, k) if isinstance(o, int) else "%s %s" % (o, k) for o, k in shown) or "NO MATCH"))


def cmd_bindiff(excel_dir, table, other):
    """Field-by-field comparison of <table>.bin in excel_dir with another build of the same table."""
    lay = get_layout(table)
    refs = Refs(excel_dir)
    a, size = read_bin(find_file(excel_dir, table, ".bin"))
    b, size_b = read_bin(other)
    print("%s: %d records x %d B vs %d records x %d B" % (table, len(a), size, len(b), size_b))
    if size != size_b:
        return 1
    cov = covered(lay)
    nchg = 0
    for i, (ra, rb) in enumerate(zip(a, b)):
        if ra == rb:
            continue
        for f in lay["fields"]:
            n = field_size(f)
            if ra[f["off"]:f["off"] + n] != rb[f["off"]:f["off"] + n]:
                nchg += 1
                va = show_value(decode_field(ra, f, refs), f, refs) if f["type"] != "calc" else ra[f["off"]:f["off"] + 4].hex()
                vb = show_value(decode_field(rb, f, refs), f, refs) if f["type"] != "calc" else rb[f["off"]:f["off"] + 4].hex()
                print("  rec %4d %-22s +0x%03X %-14s %r -> %r" % (
                    i, decode_field(ra, lay["fields"][0], refs) if lay["fields"][0]["type"] == "str" else "",
                    f["off"], f.get("col") or f.get("name"), vb, va))
        for off in range(size):
            if off not in cov and ra[off] != rb[off]:
                print("  rec %4d uncovered byte +0x%03X %02x -> %02x" % (i, off, rb[off], ra[off]))
    if len(a) != len(b):
        print("  record counts differ")
    print("  %d changed fields (shown as other -> %s/%s.bin)" % (nchg, excel_dir, table))
    return 0


def cmd_survey(excel_dir):
    """Run `diff` for every layout in excel_layouts.LAYOUTS (sorted) and print one line per table, then
    the gate summary line. A table whose diff cannot run (missing file, size or count mismatch, a column
    mapped twice) counts in `errors` and contributes no cells."""
    import excel_layouts
    totals = dict(tables=0, records=0, cells=0, unexplained=0, explained=0, errors=0)
    per = []
    for table in sorted(excel_layouts.LAYOUTS):
        st = {}
        try:
            cmd_diff(excel_dir, table, show=0, stats=st, out=io.StringIO())
        except (Exception, SystemExit) as e:  # a broken layout must show up as a count, not a crash
            totals["errors"] += 1
            print("%-16s ERROR %s" % (table, (str(e) or type(e).__name__)[:100]))
            per.append((table, None))
            continue
        totals["tables"] += 1
        for k in ("records", "cells", "unexplained", "explained"):
            totals[k] += st[k]
        print("%-16s records %5d  fields %4d  cells %7d  unexplained %d  explained %d"
              % (table, st["records"], st["fields"], st["cells"], st["unexplained"], st["explained"]))
        per.append((table, st))
    keys = ["%s=%d" % kv for kv in totals.items()]
    for table, st in per:
        if st is not None:
            keys.append("%s_cells=%d" % (table, st["cells"]))
            keys.append("%s_bad=%d" % (table, st["unexplained"]))
    print("SURVEY excel_layout " + " ".join(keys))
    return 0 if totals["unexplained"] == 0 and totals["errors"] == 0 else 1


def main(argv):
    if len(argv) >= 2 and argv[0] == "survey":
        return cmd_survey(argv[1])
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, excel_dir, table = argv[0], argv[1], argv[2].lower()
    rest = argv[3:]
    if cmd == "diff":
        show = 5
        if "--show" in rest:
            show = int(rest[rest.index("--show") + 1])
        return cmd_diff(excel_dir, table, show, "--list" in rest)
    if cmd == "dump":
        return cmd_dump(excel_dir, table, [int(x) for x in rest]) or 0
    if cmd == "probe":
        return cmd_probe(excel_dir, table, rest) or 0
    if cmd == "bindiff":
        return cmd_bindiff(excel_dir, table, rest[0])
    if cmd == "unknown":
        return cmd_unknown(excel_dir, table) or 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

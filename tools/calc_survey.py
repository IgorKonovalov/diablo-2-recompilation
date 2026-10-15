"""Byte survey of the four formula pools (*code.bin) against their formula cells (plan 0035 Phase 0).

Usage:
  python3 -I tools/calc_survey.py cells   <excel-dir> [pool]
  python3 -I tools/calc_survey.py ops     <excel-dir>
  python3 -I tools/calc_survey.py summary <excel-dir>

The pools are itemscode.bin (weapons, armor, misc), misscode.bin (missiles), skillscode.bin (skills) and
skilldesccode.bin (skilldesc). A formula field is a K field of tools/excel_layouts.py: an s32 offset into the pool, -1
for no string. For each pool the survey takes every field of every record (tables in load order: weapons, armor, misc
for itemscode), sorts the non-negative offsets, and gives each cell the bytes from its offset to the next cell's
offset (or the end of the pool). It checks: every offset is inside the pool, no two fields share an offset, the
first string starts at 0 (so no byte is outside every string), each string walks as opcodes to exactly its end with
`00` last (operand bytes: 01, 04, 07 one; 05, 08 two; 06, 09 four; every other opcode none; docs/formats/calc.md),
whether the pool order is record order and, within a record, the .txt column order (column_order), and that every variable operand (04/05/06) is a row of the pool's variable
list (skillcalc for skills and skilldesc, misscalc for missiles) whose code occurs in the cell's text.

cells    one line per string: pool, offset, length, table, record, column, the .txt text and the bytes.
ops      per pool and over all pools: each opcode byte met by the walk, the number of strings that hold it, and the
         shortest example text with its bytes.
summary  counts only.

Every command ends with `SURVEY calc_bytes key=value ...`; tools/gate.py --full compares the summary line with its
baseline. It pairs cells with bytes only; tools/calc.py (plan 0035 Phase 1) compiles the texts. Stdlib only.
Read-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import excel_layouts as L  # noqa: E402

# the variable list of each pool's formulas (04/05/06 operand = row index), as the texts show; itemscode has none
VARS = {"misscode": "misscalc", "skillscode": "skillcalc", "skilldesccode": "skillcalc"}
POOLS = [("itemscode", ["weapons", "armor", "misc"]), ("misscode", ["missiles"]), ("skillscode", ["skills"]),
         ("skilldesccode", ["skilldesc"])]
OPERAND = {0x01: 1, 0x04: 1, 0x05: 2, 0x06: 4, 0x07: 1, 0x08: 2, 0x09: 4}
MAX_OP = 0x16


def walk(bs):
    """[opcode, ...] of a byte string, and whether it walks to exactly its end with 00 last and no earlier 00."""
    ops, i = [], 0
    while i < len(bs):
        op = bs[i]
        ops.append(op)
        if op > MAX_OP:
            return ops, False
        i += 1 + OPERAND.get(op, 0)
        if op == 0:
            return ops, i == len(bs)
    return ops, False


def operands(bs):
    """[(opcode, operand value), ...] of a walked byte string (operand None for opcodes without one)."""
    out, i = [], 0
    while i < len(bs):
        op, n = bs[i], OPERAND.get(bs[i], 0)
        out.append((op, int.from_bytes(bs[i + 1:i + 1 + n], "little", signed=op in (7, 8, 9)) if n else None))
        i += 1 + n
        if op == 0:
            break
    return out


class Pool:
    def __init__(self, excel_dir, name, tables):
        self.name = name
        self.vars = []
        if name in VARS:
            h, rows = eb.read_txt(eb.find_file(excel_dir, VARS[name], ".txt"))
            self.vars = [r[0] for r in rows]
        with open(eb.find_file(excel_dir, name, ".bin"), "rb") as fh:
            self.data = fh.read()
        self.fields = []       # (table, record, column, field offset, value, text, .txt column index or -1)
        for t in tables:
            header, rows, recs, _ = eb.load_table(excel_dir, t)
            ix = {c: i for i, c in enumerate(header)}
            ks = [f for f in L.LAYOUTS[t]["fields"] if f.get("type") == "calc"]
            for r, rec in enumerate(recs):
                for f in ks:
                    v = int.from_bytes(rec[f["off"]:f["off"] + 4], "little", signed=True)
                    ci = ix.get(f["col"])
                    text = rows[r][ci] if ci is not None and ci < len(rows[r]) else None
                    self.fields.append((t, r, f["col"], f["off"], v, text, -1 if ci is None else ci))
        used = sorted((f[4], k) for k, f in enumerate(self.fields) if f[4] >= 0)
        self.strings = []      # (offset, bytes, field index)
        for n, (v, k) in enumerate(used):
            end = used[n + 1][0] if n + 1 < len(used) else len(self.data)
            self.strings.append((v, self.data[v:end], k))
        self.offsets = [v for v, _ in used]

    def stats(self):
        n = len(self.data)
        out = dict(fields=len(self.fields),
                   blank=sum(1 for f in self.fields if f[4] == -1 and not (f[5] or "")),
                   minus1_nonblank=sum(1 for f in self.fields if f[4] == -1 and (f[5] or "")),
                   bad_offset=sum(1 for f in self.fields if f[4] < -1 or f[4] >= n),
                   strings=len(self.strings),
                   shared=len(self.offsets) - len(set(self.offsets)),
                   blank_with_string=sum(1 for _, _, k in self.strings if not (self.fields[k][5] or "")),
                   bytes=n,
                   gap=self.offsets[0] if self.offsets else n,
                   walk_bad=0, walk_bad_bytes=0, var_refs=0, var_out_of_range=0, var_not_in_text=0)
        for _, bs, k in self.strings:
            text = (self.fields[k][5] or "").lower()
            for op, v in operands(bs):
                if op in (4, 5, 6):
                    out["var_refs"] += 1
                    if not 0 <= v < len(self.vars):
                        out["var_out_of_range"] += 1
                    elif self.vars[v].lower() not in text:
                        out["var_not_in_text"] += 1
        for _, bs, _ in self.strings:
            _, ok = walk(bs)
            if not ok:
                out["walk_bad"] += 1
                out["walk_bad_bytes"] += len(bs)
        tabpos = {t: i for i, t in enumerate(dict.fromkeys(f[0] for f in self.fields))}
        keys = [(tabpos[self.fields[k][0]], self.fields[k][1], self.fields[k][6]) for _, _, k in self.strings]
        out["record_order"] = int([k[:2] for k in keys] == sorted(k[:2] for k in keys))
        out["column_order"] = int(keys == sorted(keys))
        return out


def load(excel_dir):
    return [Pool(excel_dir, n, ts) for n, ts in POOLS]


def opcode_table(pools):
    """{pool name or '*': {op: [count, example (text, bytes)]}}"""
    out = {}
    for p in pools:
        for key in (p.name, "*"):
            tab = out.setdefault(key, {})
            for _, bs, k in p.strings:
                ops, _ = walk(bs)
                text = p.fields[k][5] or ""
                for op in sorted(set(ops)):
                    e = tab.setdefault(op, [0, None])
                    e[0] += 1
                    if e[1] is None or len(text) < len(e[1][0]):
                        e[1] = (text, bs)
    return out


def summary_line(pools):
    kv = []
    tot = dict(fields=0, strings=0, bytes=0, walk_bad=0, minus1_nonblank=0)
    for p in pools:
        s = p.stats()
        for k in tot:
            tot[k] += s[k]
        kv += [("%s_%s" % (p.name, k), s[k]) for k in ("fields", "strings", "bytes", "gap", "shared", "bad_offset",
                                                       "blank_with_string", "minus1_nonblank", "walk_bad",
                                                       "walk_bad_bytes", "record_order", "column_order", "var_refs",
                                                       "var_out_of_range", "var_not_in_text")]
    ops = opcode_table(pools)["*"]
    head = [("fields", tot["fields"]), ("strings", tot["strings"]), ("bytes", tot["bytes"]),
            ("walk_bad", tot["walk_bad"]), ("minus1_nonblank", tot["minus1_nonblank"]), ("opcodes", len(ops))]
    return "SURVEY calc_bytes " + " ".join("%s=%s" % p for p in head + kv)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("cells", "ops", "summary"):
        print(__doc__)
        return 2
    pools = load(argv[1])
    if argv[0] == "cells":
        for p in pools:
            if len(argv) > 2 and p.name != argv[2]:
                continue
            for off, bs, k in p.strings:
                t, r, col, _, _, text, _ = p.fields[k]
                _, ok = walk(bs)
                print("%-13s %5d %3d  %-9s %4d %-16s %-40s %s%s" % (p.name, off, len(bs), t, r, col, text, bs.hex(" "),
                                                                    "" if ok else "  WALK?"))
            for t, r, col, _, v, text, _ in p.fields:
                if v == -1 and text:
                    print("%-13s    -1        %-9s %4d %-16s %r (non-blank, no string)" % (p.name, t, r, col, text))
    elif argv[0] == "ops":
        tab = opcode_table(pools)
        for key in [p.name for p in pools] + ["*"]:
            print("== %s" % ("all pools" if key == "*" else key))
            for op, (n, (text, bs)) in sorted(tab[key].items()):
                print("  %02X  strings %4d  e.g. %-36s %s" % (op, n, text, bs.hex(" ")))
    print(summary_line(pools))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""The act light clock's three tables in the pinned image (plan 0063 Phase 1, ADR-0031), checked against the doc.

    python3 -I tools/actclock_survey.py summary <game.exe>   counts, the rule's mismatches, checksums, doc check
    python3 -I tools/actclock_survey.py md <game.exe>        the Markdown rows of docs/tables/ActClockTables.md (generated)

g_ActClockTable0/1/2 at 0x007443F0, 0x00744438, 0x00744480: six rows of three dwords (start, type, colour word), 72 bytes
each, contiguous. Table 2's `start` column is by the rule 60 * ((p + 5) % 6) and table 1's `type` column by the rule T1[p].type = T0[p].type;
every other value is listed in the doc, and
`doc_missing` / `doc_mismatches` compare the doc's listed rows with the image element by element.
Ends with `SURVEY actclock key=value ...`; tools/gate.py --full compares it with its baseline. The image is read only when
its sha256 is the pinned one. Stdlib only. Read-only.
"""
import hashlib
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
DOC = os.path.join(HERE, "..", "docs", "tables", "ActClockTables.md")
PINNED_SHA256 = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
BASES = (0x007443F0, 0x00744438, 0x00744480)
IMAGE_BASE = 0x400000


def load(path):
    d = open(path, "rb").read()
    if hashlib.sha256(d).hexdigest() != PINNED_SHA256:
        raise SystemExit("actclock_survey: not the pinned Game.exe: " + path)
    return d


def read_rows(data, va):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    so = pe + 24 + struct.unpack_from("<H", data, pe + 20)[0]
    rva = va - IMAGE_BASE
    for i in range(nsec):
        vsize, sva, rsize, raw = struct.unpack_from("<IIII", data, so + 40 * i + 8)
        if sva <= rva and rva + 72 <= sva + min(vsize, rsize):
            w = struct.unpack_from("<18I", data, raw + rva - sva)
            return [tuple(w[3 * r:3 * r + 3]) for r in range(6)]
    raise ValueError("0x%08X not in a raw section" % va)


def rule_t2_start(p):
    return 60 * ((p + 5) % 6)


def rule_t1_type(tabs, p):
    return tabs[0][p][1]


def tables(data):
    return [read_rows(data, b) for b in BASES]


def md(tabs):
    out = []
    for t, rows in enumerate(tabs):
        for p, (s, ty, c) in enumerate(rows):
            start = "by rule" if t == 2 else str(s)
            typ = "by rule" if t == 1 else str(ty)
            out.append("| T%d | %d | %s | %s | 0x%06X |" % (t, p, start, typ, c))
    return out


def doc_check(tabs):
    """(missing, mismatching) over the 18 rows of the doc: T2's start and T1's type are by rule, so they are not listed."""
    text = open(DOC).read() if os.path.exists(DOC) else ""
    found = {}
    for m in re.finditer(r"^\| T([012]) \| ([0-5]) \| (\d+|by rule) \| (\d+|by rule) \| 0x([0-9A-F]{6}) \|$", text, re.M):
        found[(int(m.group(1)), int(m.group(2)))] = (m.group(3), m.group(4), int(m.group(5), 16))
    miss = bad = 0
    for t, rows in enumerate(tabs):
        for p, (s, ty, c) in enumerate(rows):
            f = found.get((t, p))
            if f is None:
                miss += 1
            elif f != ("by rule" if t == 2 else str(s), "by rule" if t == 1 else str(ty), c):
                bad += 1
    return miss, bad


def crc(vals):
    return zlib.crc32(struct.pack("<%dI" % len(vals), *vals)) & 0xFFFFFFFF


def summary(exe):
    tabs = tables(load(exe))
    kv = {"tables": len(tabs), "rows": sum(len(t) for t in tabs)}
    for t, rows in enumerate(tabs):
        kv["t%d_crc" % t] = crc([x for r in rows for x in r])
    kv["t2_start_rule_mismatches"] = sum(1 for p, r in enumerate(tabs[2]) if r[0] != rule_t2_start(p))
    kv["t1_type_rule_mismatches"] = sum(1 for p, r in enumerate(tabs[1]) if r[1] != rule_t1_type(tabs, p))
    kv["doc_missing"], kv["doc_mismatches"] = doc_check(tabs)
    print("SURVEY actclock " + " ".join("%s=%s" % kv_ for kv_ in kv.items()))
    bad = kv["t2_start_rule_mismatches"] + kv["t1_type_rule_mismatches"] + kv["doc_missing"] + kv["doc_mismatches"]
    return 0 if bad == 0 else 1


def main(argv):
    if len(argv) != 3 or argv[1] not in ("summary", "md"):
        print(__doc__)
        return 2
    if argv[1] == "md":
        print("\n".join(md(tables(load(argv[2])))))
        return 0
    return summary(argv[2])


if __name__ == "__main__":
    sys.exit(main(sys.argv))

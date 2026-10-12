"""Read Diablo II string tables (.tbl): header, hash table, keys and values; resolve keys.

Usage: python3 -I tools/tbl.py <file.tbl> [...]          header fields and entry counts per file
       python3 -I tools/tbl.py dump <file.tbl>          entry, node, key, value (\\n \\t \\\\ escaped)
       python3 -I tools/tbl.py --key <lng-dir> <key>     compiled index of a key (three-table precedence)
       python3 -I tools/tbl.py lookup <lng-dir> <key>    index, table, entry and value of a key
       python3 -I tools/tbl.py survey <merged-root>      every data/local/lng/**/*.tbl, every check below,
                                                        and the uniqueprefix/uniquesuffix/uniqueappellation
                                                        lookup check; last line `SURVEY tbl ...` (gate)

Layout (docs/formats/tbl.md): 21-byte header (u16 crc, u16 count, u32 hash_size, u8 version,
u32 string_start, u32 max_probes, u32 file_size), u16 index[count] (entry -> hash node), then
hash_size 17-byte nodes (u8 used, u16 entry, u32 hash, u32 key_off, u32 str_off, u16 str_len), then
the key and value bytes (NUL-terminated, UTF-8; str_len counts the NUL). Offsets are from the start
of the file. Observed in every file:
  - node.hash = elf_hash(key) % hash_size, and the nodes are what inserting entries 0..count-1 by
    linear probing (+1, wrapping) from that home slot gives; max_probes = the longest probe count;
  - crc = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) of the bytes from string_start to the end.

Key -> compiled index, as observed in the excel .bin files: index = base + entry, with base 0 for
string.tbl, 10000 for patchstring.tbl, 20000 for expansionstring.tbl. A key present in several
tables resolves to patchstring first, then expansionstring, then string. A key found nowhere
(including the empty key) resolves to 5382. That order is data behaviour; the game's run-time
order is not anchored ([L], docs/formats/tbl.md). Stdlib only. Read-only.
"""
import glob
import os
import re
import struct
import sys

TABLES = [("patchstring.tbl", 10000), ("expansionstring.tbl", 20000), ("string.tbl", 0)]
NOT_FOUND = 5382
HEADER = 21
NODE = 17
UNIQUE_TABLES = ("uniqueprefix", "uniquesuffix", "uniqueappellation")


def elf_hash(key):
    """PJW/ELF hash over the key bytes (unsigned)."""
    h = 0
    for c in key:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h


def crc16_ccitt(data, crc=0xFFFF):
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


class Tbl:
    """One .tbl file. entries[e] = (node, key bytes, value bytes without the NUL)."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            d = self.data = fh.read()
        self.crc, self.count, self.hash_size = struct.unpack_from("<HHI", d, 0)
        self.version = d[8]
        self.string_start, self.max_probes, self.file_size = struct.unpack_from("<III", d, 9)
        self.index = struct.unpack_from("<%dH" % self.count, d, HEADER)
        self.nodes_at = HEADER + 2 * self.count
        self.nodes = [struct.unpack_from("<BHIIIH", d, self.nodes_at + NODE * n) for n in range(self.hash_size)]
        self.entries = []
        for e in range(self.count):
            n = self.index[e]
            used, entry, h, ko, so, sl = self.nodes[n]
            if not used or entry != e:
                raise ValueError("entry %d points at node %d (used=%d entry=%d)" % (e, n, used, entry))
            key = d[ko:d.index(b"\0", ko)]
            if sl < 1 or so + sl > len(d) or d[so + sl - 1] != 0:
                raise ValueError("entry %d: value at 0x%x length %d does not end with its NUL" % (e, so, sl))
            self.entries.append((n, key, d[so:so + sl - 1]))
        self.first = {}
        for e, (_, key, _) in enumerate(self.entries):
            self.first.setdefault(key, e)

    def header(self):
        return dict(crc=self.crc, count=self.count, hash_size=self.hash_size, version=self.version,
                    string_start=self.string_start, max_probes=self.max_probes,
                    file_size=self.file_size, actual_size=len(self.data))

    def find(self, key):
        """Entry number of `key` through the file's own hash table, or None (probes <= max_probes)."""
        if isinstance(key, str):
            key = key.encode("latin-1")
        n = elf_hash(key) % self.hash_size
        for _ in range(self.max_probes):
            used, entry, h, ko, so, sl = self.nodes[n]
            if not used:
                return None
            if self.data[ko:ko + len(key) + 1] == key + b"\0":
                return entry
            n = (n + 1) % self.hash_size
        return None

    def value(self, e):
        return self.entries[e][2].decode("utf-8")

    def checks(self):
        """Structural checks over the whole file -> dict of failure counts (all 0 when clean)."""
        d, hs = self.data, self.hash_size
        f = dict(size=int(self.file_size != len(self.data)), version=int(self.version != 1),
                 string_start=int(self.string_start != self.nodes_at + NODE * hs),
                 used=int(sum(nd[0] for nd in self.nodes) != self.count),
                 crc=int(crc16_ccitt(d[self.string_start:]) != self.crc), hash=0, slot=0,
                 max_probes=0, utf8=0, find=0, unaccounted=0)
        slots, longest = [None] * hs, 0
        for e, (node, key, val) in enumerate(self.entries):
            home = elf_hash(key) % hs
            f["hash"] += self.nodes[node][2] != home
            s, probes = home, 1
            while slots[s] is not None:
                s, probes = (s + 1) % hs, probes + 1
            slots[s], longest = e, max(longest, probes)
            f["slot"] += s != node
            try:
                val.decode("utf-8")
            except UnicodeDecodeError:
                f["utf8"] += 1
            f["find"] += self.find(key) != self.first[key]
        f["max_probes"] = int(longest != self.max_probes)
        # every byte after the nodes belongs to exactly one key or one value
        cover = bytearray(len(d) - self.string_start)
        for node, key, val in self.entries:
            ko, so, sl = self.nodes[node][3], self.nodes[node][4], self.nodes[node][5]
            for a, b in ((ko, ko + len(key) + 1), (so, so + sl)):
                for i in range(a - self.string_start, b - self.string_start):
                    cover[i] += 1
        f["unaccounted"] = sum(c != 1 for c in cover)
        return f

    def dups(self):
        return len(self.entries) - len(self.first)


class Strings:
    """The three tables of one language directory, resolved as the excel .bin files show."""

    def __init__(self, lng_dir):
        self.tables = {}
        for name, base in TABLES:
            p = os.path.join(lng_dir, name)
            if os.path.exists(p):
                self.tables[base] = Tbl(p)

    def index(self, key):
        if not key:
            return NOT_FOUND
        for name, base in TABLES:  # highest precedence first
            t = self.tables.get(base)
            if t is not None:
                e = t.find(key)
                if e is not None:
                    return base + e
        return NOT_FOUND

    def text(self, index):
        """Value of a compiled index, or None when its table is not shipped for this language."""
        base = 20000 if index >= 20000 else 10000 if index >= 10000 else 0
        t = self.tables.get(base)
        if t is None or index - base >= t.count:
            return None
        return t.value(index - base)


def esc(b):
    return b.decode("utf-8", "replace").replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")


SRC_LINE = re.compile(r'^(.*?),\s*(\S*),\s*"(.*)"\s*$')


def source_text(lng_dir):
    """key -> value from the UTF-16 source .txt files shipped in a language directory (first wins)."""
    out = {}
    for p in sorted(glob.glob(os.path.join(lng_dir, "*.txt"))):
        with open(p, "rb") as fh:
            raw = fh.read()
        if raw[:2] not in (b"\xff\xfe", b"\xfe\xff"):
            continue
        for line in raw.decode("utf-16").splitlines():
            m = SRC_LINE.match(line)
            if m and not line.startswith(("//", "#")):
                out.setdefault(m.group(1), m.group(3).replace("\\n", "\n"))
    return out


def unique_rows(excel_dir, name):
    """(Name cell, stored u16) per record of <name>.txt / <name>.bin (u32 count, then u16 records)."""
    with open(os.path.join(excel_dir, name + ".bin"), "rb") as fh:
        b = fh.read()
    n = struct.unpack_from("<I", b, 0)[0]
    if len(b) != 4 + 2 * n:
        raise ValueError("%s.bin: %d bytes for %d records" % (name, len(b), n))
    stored = struct.unpack_from("<%dH" % n, b, 4)
    with open(os.path.join(excel_dir, name + ".txt"), "rb") as fh:
        lines = fh.read().decode("latin-1").splitlines()
    col = lines[0].split("\t").index("Name")
    names = [ln.split("\t")[col] for ln in lines[1:] if ln.strip()]
    if len(names) != n:
        raise ValueError("%s: %d .txt rows, %d .bin records" % (name, len(names), n))
    return list(zip(names, stored))


def survey(root):
    lng = os.path.join(root, "data", "local", "lng")
    paths = sorted(glob.glob(os.path.join(lng, "**", "*.tbl"), recursive=True))
    other = len(glob.glob(os.path.join(root, "data", "**", "*.tbl"), recursive=True)) - len(paths)
    t = dict(files=len(paths), languages=0, entries=0, header_count=0, nodes=0, dup_keys=0,
             value_bytes=0, errors=0, check_failures=0)
    langs = set()
    for p in paths:
        rel = os.path.relpath(p, lng)
        try:
            tb = Tbl(p)
        except Exception as ex:  # report and keep going over every file
            t["errors"] += 1
            print("%s\tFAIL\t%s" % (rel, ex))
            continue
        langs.add(rel.split(os.sep)[0])
        f = tb.checks()
        bad = sum(f.values())
        t["check_failures"] += bad
        t["entries"] += len(tb.entries)
        t["header_count"] += tb.count
        t["nodes"] += tb.hash_size
        t["dup_keys"] += tb.dups()
        t["value_bytes"] += sum(len(v) for _, _, v in tb.entries)
        print("%s\t%s\tentries=%d hash_size=%d max_probes=%d dup_keys=%d crc=0x%04x%s" % (
            rel, "ok" if not bad else "CHECK-FAIL", len(tb.entries), tb.hash_size, tb.max_probes,
            tb.dups(), tb.crc, "" if not bad else " " + " ".join("%s=%d" % kv for kv in f.items() if kv[1])))
    t["languages"] = len(langs)

    # uniqueprefix / uniquesuffix / uniqueappellation: key lookup vs the compiled index and the source text
    excel = os.path.join(root, "data", "global", "excel")
    u = dict(unique_rows=0, unique_bin_eq=0, unique_text_eq=0, unique_src_eq=0, unique_src_missing=0)
    eng = Strings(os.path.join(lng, "eng"))
    src = source_text(os.path.join(lng, "eng"))
    rows = {name: unique_rows(excel, name) for name in UNIQUE_TABLES}
    for name in UNIQUE_TABLES:
        for key, stored in rows[name]:
            u["unique_rows"] += 1
            idx = eng.index(key)
            u["unique_bin_eq"] += idx == stored
            val = eng.text(idx)
            u["unique_text_eq"] += val is not None and val == eng.text(stored)
            if key not in src:
                u["unique_src_missing"] += 1
            elif val == src[key]:
                u["unique_src_eq"] += 1
            else:
                print("unique %s %r: tbl %r, source %r" % (name, key, val, src[key]))
    print("unique names (eng): " + " ".join("%s=%d" % kv for kv in u.items()))
    # the same keys in every other language directory that ships .tbl files: found / not found
    keys = [k for name in UNIQUE_TABLES for k, _ in rows[name]]
    found_other = 0
    for lang in sorted(langs - {"eng"}):
        s = Strings(os.path.join(lng, lang))
        found = sum(s.index(k) != NOT_FOUND for k in keys)
        found_other += found
        print("unique names (%s, tables %s): found %d of %d" % (
            lang, "+".join(n for n, b in TABLES if b in s.tables), found, len(keys)))
    u["unique_other_found"] = found_other
    print("other .tbl files under data/ outside lng/ (fonts, another format), not read: %d" % other)
    t.update(u)
    t["other_tbl"] = other
    print("SURVEY tbl " + " ".join("%s=%d" % kv for kv in t.items()))
    ok = (not t["errors"] and not t["check_failures"] and t["entries"] == t["header_count"]
          and u["unique_bin_eq"] == u["unique_rows"] == u["unique_text_eq"])
    return 0 if ok else 1


def main(argv):
    if len(argv) == 3 and argv[0] == "--key":
        print(Strings(argv[1]).index(argv[2]))
        return 0
    if len(argv) == 3 and argv[0] == "lookup":
        s = Strings(argv[1])
        i = s.index(argv[2])
        base = 20000 if i >= 20000 else 10000 if i >= 10000 else 0
        name = dict((b, n) for n, b in TABLES)[base]
        txt = s.text(i)
        print("%d\t%s\t%d\t%s" % (i, name, i - base, esc(txt.encode("utf-8")) if txt is not None else "<none>"))
        return 0
    if len(argv) == 2 and argv[0] == "dump":
        tb = Tbl(argv[1])
        for e, (node, key, val) in enumerate(tb.entries):
            print("%d\t%d\t%s\t%s" % (e, node, esc(key), esc(val)))
        return 0
    if len(argv) == 2 and argv[0] == "survey":
        return survey(argv[1])
    if not argv or argv[0] in ("dump", "lookup", "survey"):
        print(__doc__)
        return 2
    bad = 0
    for p in argv:
        try:
            tb = Tbl(p)
            hdr = tb.header()
            ok = hdr["file_size"] == hdr["actual_size"]
            bad += not ok
            print("%s\t%s\tkeys=%d\t%s" % (p, "ok" if ok else "SIZE-MISMATCH", len(tb.entries),
                                          " ".join("%s=%d" % kv for kv in hdr.items())))
        except Exception as ex:  # report and keep going over every file
            bad += 1
            print("%s\tFAIL\t%s" % (p, ex))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

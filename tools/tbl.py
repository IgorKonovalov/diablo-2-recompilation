"""Read Diablo II string tables (.tbl): header, hash table, keys and values; resolve keys.

Usage: python3 -I tools/tbl.py <file.tbl> [...]          header fields and entry counts per file
       python3 -I tools/tbl.py dump <file.tbl>          entry, node, key, value (\\n \\t \\\\ escaped)
       python3 -I tools/tbl.py --key <lng-dir> <key>     compiled index of a key (three-table precedence)
       python3 -I tools/tbl.py lookup <lng-dir> <key>    index, table, entry and value of a key
       python3 -I tools/tbl.py survey <merged-root>      every data/local/lng/**/*.tbl, every check below,
                                                        and the uniqueprefix/uniquesuffix/uniqueappellation
                                                        lookup check; last line `SURVEY tbl ...` (gate)
       python3 -I tools/tbl.py index <lng-dir> <ld> <index>  run-time GetByIndex model: table, entry, node, text
       python3 -I tools/tbl.py key   <lng-dir> <ld> <key>    run-time GetByKey model: index, text
       python3 -I tools/tbl.py probe <lng-dir> <ld> <key>    FindInTable model per loaded table: home, probed slots
       python3 -I tools/tbl.py check <lng-dir> <log>...      every SIDX/SKEY line of tools/gdb/strings.gdb logs
                                                        against the model; last line `CHECK strings ...`
                                                        (<ld> = loaded tables: spx expansion, sp classic)

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
order is the one the code uses (docs/findings/data/0003-string-tables.md). Stdlib only. Read-only.

Run-time model (GameStrings, data/0003): GetByIndex (>= 20000 -> expansionstring, or 11078 without it; >= 10000 ->
patchstring; else string; entry >= count -> 500), GetByKey (empty key -> 0; patchstring, expansionstring, string;
not found -> 0 and "<key> -not xlated call ken" plus a space: the suffix " -not xlated call ken w" loses its last
character in the conversion), FindInTable (home = signed-char ELF hash % hash_size, up to max_probes nodes stepping
+1, an unused node skipped, not a stop), and the UTF-8 -> UTF-16 conversion with its font-map character count. Unlike Tbl.find, which stops at an unused node
(equivalent on the shipped files for keys that are present), the model probes exactly as the game does.
"""
import glob
import json
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


def elf_hash_signed(key):
    """STRTABLE_Hash's hash: PJW/ELF over the key bytes read as *signed* chars (movsx), u32 arithmetic."""
    h = 0
    for c in key:
        if c >= 0x80:
            c -= 0x100
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h = (h ^ (g >> 24)) & 0x0FFFFFFF
    return h


NOT_XLATED = b" -not xlated call ken w"  # data 0x00730520


GARBAGE = None  # a unit the game leaves unwritten (uninitialised memory); check compares only the length there


def read_font_map(path):
    """data/local/font/<charset>/default.map, as sub_00527790 reads it: "KAMAP\n", a name ended by 0x1A, then at
    name end + 5: u16 n, u8 r, r (lo, hi) byte ranges, n 4-byte pairs, n u16. Returns the ranges (the only part
    the string conversion uses, through the character count 0x00527D50 / 0x005276E0)."""
    with open(path, "rb") as fh:
        d = fh.read()
    if not d.startswith(b"KAMAP\n"):
        raise ValueError("%s: no KAMAP header" % path)
    end = d.index(b"\x1a", 6)
    at = end + 5
    r = d[at + 2]
    return [(d[at + 3 + 2 * i], d[at + 4 + 2 * i]) for i in range(r)]


def char_count(b, limit, ranges):
    """0x00527D50 with a font map loaded: walk at most `limit` bytes up to the NUL; a byte >= 0x20 outside every
    range counts as a two-byte character (0x005276E0), any other byte as one. Returns the character count."""
    i = n = 0
    while i < limit and i < len(b) and b[i]:
        c = b[i]
        two = c >= 0x20 and not any(lo <= c <= hi for lo, hi in ranges)
        i += 2 if two else 1
        n += 1
    return n


UTF8 = ((0x80, 0x00, 0x7F, 0), (0xE0, 0xC0, 0x7FF, 0x80), (0xF0, 0xE0, 0xFFFF, 0x800),
        (0xF8, 0xF0, 0x1FFFFF, 0x10000), (0xFC, 0xF8, 0x3FFFFFF, 0x200000), (0xFE, 0xFC, 0x7FFFFFFF, 0x4000000))


def utf8_one(b, i, avail):
    """0x00526100 with its table at 0x007309B8: (code unit, bytes) or None for an invalid or cut sequence."""
    if avail <= 0:
        return None
    c = b[i]
    v = c - 0x100 if c >= 0x80 else c  # movsx
    for k, (mask, val, lmask, lo) in enumerate(UTF8):
        if c & mask == val:
            v &= lmask
            return (v & 0xFFFF, k + 1) if v >= lo else None
        if avail <= k + 1:
            return None
        x = b[i + k + 1] ^ 0x80
        if x & 0xC0:
            return None
        v = (v << 6) | x
    return None


def convert(b, limit):
    """0x00526320: UTF-8 bytes -> at most limit - 1 u16 units, stopping at the end or at a bad sequence (whose slot
    is left unwritten, GARBAGE, and terminated after it)."""
    out, i = [], 0
    if not b:
        return out
    while len(out) < limit - 1:
        r = utf8_one(b, i, len(b) - i)
        if r is None:
            return out + [GARBAGE]
        out.append(r[0])
        i += r[1]
        if i >= len(b):
            break
    return out


def units_str(units):
    return "".join(chr(u) for u in units if u is not None)


class GameStrings:
    """Run-time lookups of one language directory, as data/0003 reads the code. `ld` names the loaded tables:
    "spx" in an expansion game, "sp" in a classic one (string, patchstring, expansionstring). `font_map` is the
    language's default.map (eng: data/local/font/latin/default.map), which sets the character count of every
    conversion; without it the count is strlen (0x00882B2C null)."""

    def __init__(self, lng_dir, ld, font_map=None):
        files = {"s": "string.tbl", "p": "patchstring.tbl", "x": "expansionstring.tbl"}
        self.t = {k: Tbl(os.path.join(lng_dir, files[k])) for k in ld}
        if font_map is None:
            cand = os.path.join(lng_dir, os.pardir, os.pardir, "font", "latin", "default.map")
            font_map = cand if os.path.exists(cand) else ""
        self.ranges = read_font_map(font_map) if font_map else None

    def count(self, b, limit):
        if self.ranges is None:
            z = b.find(b"\0")
            return min(limit, len(b) if z < 0 else z)
        return char_count(b, limit, self.ranges)

    def units(self, tb, node):
        """The converted value of a node (STRTABLE_LoadAll at 0x00525C49-0x00525C64): limit = count + 1."""
        so, sl = tb.nodes[node][4], tb.nodes[node][5]
        b = tb.data[so:so + sl - 1]
        return convert(b, self.count(b, sl) + 1)

    def text(self, tb, node):
        return units_str(self.units(tb, node))

    def entry_to_node(self, t, entry):
        """STRTABLE_EntryToString: entry >= count -> 500; returns (node, text)."""
        tb = self.t[t]
        if entry >= tb.count:
            entry = 500
        node = tb.index[entry]
        if node >= tb.hash_size or not tb.nodes[node][0]:
            raise ValueError("fatal: entry %d of %s names node %d" % (entry, t, node))
        return node, self.text(tb, node)

    def by_index(self, idx):
        """STRTABLE_GetByIndex (u16 index) -> (table, entry argument, node, text)."""
        idx &= 0xFFFF
        if idx >= 20000:
            if "x" in self.t:
                return ("x", idx - 20000) + self.entry_to_node("x", idx - 20000)
            idx = 11078
        if "p" in self.t and idx >= 10000:
            return ("p", idx - 10000) + self.entry_to_node("p", idx - 10000)
        if "s" not in self.t:
            raise ValueError("fatal 0x246: string.tbl not loaded")
        return ("s", idx) + self.entry_to_node("s", idx)

    def find(self, t, key):
        """STRTABLE_FindInTable -> (home, [[slot, probe count], ...], entry or None, slot or None). An unused node
        is skipped; only max_probes ends the search."""
        tb = self.t[t]
        slot = home = elf_hash_signed(key) % tb.hash_size
        probes = []
        for n in range(tb.max_probes):
            probes.append([slot, n + 1])
            used, entry, _, ko, _, _ = tb.nodes[slot]
            if used == 1 and tb.data[ko:tb.data.index(b"\0", ko)] == key:
                return home, probes, entry, slot
            slot = (slot + 1) % tb.hash_size
        return home, probes, None, None

    def by_key(self, key):
        """STRTABLE_GetByKey -> (index, [find records], text)."""
        if not key:
            return 0, [], ""
        finds = []
        for t, base in (("p", 10000), ("x", 20000), ("s", 0)):
            if t not in self.t:
                continue
            home, probes, entry, slot = self.find(t, key)
            finds.append({"t": t, "home": home, "probes": probes, "res": entry, "slot": slot})
            if entry is not None:
                return base + entry, finds, self.text(self.t[t], slot)
        # sub_00524AC0_NotXlated: key + suffix, counted by 0x00527D50 as n characters and converted by 0x00526320
        # with a limit of n, which writes at most n - 1 units: the last character is lost.
        raw = key + NOT_XLATED
        u = convert(raw, self.count(raw, len(raw)))
        return 0, finds, units_str(u) if GARBAGE not in u else u


def check(lng_dir, logs):
    """Compare every SIDX and SKEY line of the logs with GameStrings. Prints mismatches and the counts."""
    models = {}
    c = dict(sidx=0, sidx_ok=0, skey=0, skey_ok=0, fallback_11078=0, fallback_500=0, finds=0, finds_missed=0,
             chains_gt1=0, not_found=0, empty_key=0, unwritten_unit=0, logerr=0)
    idx_seen, key_seen, tbl_hits, ld_seen = set(), set(), {}, {}
    worst = (0, None)
    for path in logs:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if ln.startswith("LOGERR strings"):
                    c["logerr"] += 1
                    print("%s: %s" % (path, ln.rstrip()))
                if not ln.startswith(("SIDX ", "SKEY ")):
                    continue
                tag, d = ln[:4], json.loads(ln[5:])
                ld = d["ld"]
                ld_seen[ld] = ld_seen.get(ld, 0) + 1
                m = models.get(ld) or models.setdefault(ld, GameStrings(lng_dir, ld))
                if tag == "SIDX":
                    c["sidx"] += 1
                    idx_seen.add((d["idx"], ld))
                    t, entry, node, text = m.by_index(d["idx"])
                    got = (d["t"], d["ta"], d["entry"], d["node"], d["text"], d["len"])
                    want = (t, t, entry, node, text, len(text))
                    c["fallback_11078"] += d["idx"] >= 20000 and "x" not in ld
                    c["fallback_500"] += entry >= m.t[t].count
                    tbl_hits[t] = tbl_hits.get(t, 0) + 1
                    if got == want:
                        c["sidx_ok"] += 1
                    else:
                        print("SIDX mismatch %s idx=%d ld=%s: log %r model %r" % (path, d["idx"], ld, got, want))
                else:
                    c["skey"] += 1
                    key = d["key"].encode("latin-1") if d["key"] is not None else None
                    key_seen.add((key, ld))
                    idx, finds, text = m.by_key(key)
                    logf = [(f["t"], f["home"], f["n"], f["res"], f["slot"]) for f in d["f"]]
                    want = [(f["t"], f["home"], len(f["probes"]), f["res"], f["slot"]) for f in finds]
                    if isinstance(text, list):  # a bad sequence: one unit the game leaves unwritten
                        good = units_str(text[:-1])
                        # the unwritten unit reads as whatever was there; a 0 there ends the string one unit early
                        ok_text = d["len"] in (len(text) - 1, len(text)) and d["text"][:len(good)] == good[:200]
                        c["unwritten_unit"] += 1
                    else:
                        ok_text = d["text"] == text[:200] and d["len"] == len(text)
                    ok = d["idx"] == idx and logf == want and ok_text
                    c["empty_key"] += not key
                    c["not_found"] += bool(key) and idx == 0
                    for f in finds:
                        c["finds"] += 1
                        n = len(f["probes"])
                        if f["res"] is None:
                            c["finds_missed"] += 1
                        elif n > 1:
                            c["chains_gt1"] += 1
                            if n > worst[0]:
                                worst = (n, (key, f["t"], f["home"], f["slot"], f["res"]))
                    if ok:
                        c["skey_ok"] += 1
                    else:
                        print("SKEY mismatch %s key=%r ld=%s: log idx=%d f=%r text=%r len=%d; model idx=%d f=%r "
                              "text=%r" % (path, key, ld, d["idx"], logf, d["text"], d["len"], idx, want, text))
    c["distinct_idx"] = len(idx_seen)
    c["distinct_key"] = len(key_seen)
    print("tables loaded per line: " + " ".join("%s=%d" % kv for kv in sorted(ld_seen.items())))
    print("SIDX lines per table: " + " ".join("%s=%d" % kv for kv in sorted(tbl_hits.items())))
    if worst[1]:
        print("longest hit chain: %d nodes, key %r table %s home %d -> slot %d, entry %r" % ((worst[0],) + worst[1]))
    print("CHECK strings " + " ".join("%s=%d" % kv for kv in c.items()))
    bad = c["sidx"] - c["sidx_ok"] + c["skey"] - c["skey_ok"] + c["logerr"]
    return 1 if bad or not (c["sidx"] or c["skey"]) else 0


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
    if len(argv) >= 3 and argv[0] == "check":
        return check(argv[1], argv[2:])
    if len(argv) == 4 and argv[0] in ("index", "key", "probe"):
        m = GameStrings(argv[1], argv[2])
        if argv[0] == "index":
            t, entry, node, text = m.by_index(int(argv[3], 0))
            print("%s\t%d\t%d\t%s" % (t, entry, node, esc(text.encode("utf-8", "surrogatepass"))))
        elif argv[0] == "key":
            idx, finds, text = m.by_key(argv[3].encode("latin-1"))
            print("%d\t%s" % (idx, esc(text.encode("utf-8", "surrogatepass"))))
        else:
            for t in m.t:
                home, probes, entry, slot = m.find(t, argv[3].encode("latin-1"))
                print("%s\thome=%d\tn=%d\tslot=%s\tentry=%s\tmax_probes=%d" % (
                    t, home, len(probes), slot, entry, m.t[t].max_probes))
        return 0
    if not argv or argv[0] in ("dump", "lookup", "survey", "check", "index", "key", "probe"):
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

"""Read Diablo II character saves (.d2s, version 96): header, sections, stats, skills, item lists.

Usage:
  python3 -I tools/d2s.py survey <excel-dir> <file.d2s ...>   parse every save; checksum, sections,
                                                               byte and bit accounting, histograms
  python3 -I tools/d2s.py dump <excel-dir> <file.d2s>          print the header, stats and every item
  python3 -I tools/d2s.py checksum <file.d2s>                  print the stored and computed checksums
  python3 -I tools/d2s.py setstat <excel-dir> <in.d2s> <out.d2s> <stat-id> <value>
                                                               rewrite one character stat in place
                                                               (same bit width) and re-checksum

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). The stat and
item property lists are read with the save-bit columns of itemstatcost.txt. Layout in
docs/formats/d2s.md. Little-endian; bit fields are read LSB first within each byte. survey exits 0
only if every save's checksum and file-size field match, every section is where its header says, and
every item ends on the byte where the next item (or section) starts, with only zero padding bits.
Stdlib only. Read-only, except setstat, which writes <out.d2s>.
"""
import collections
import os
import struct
import sys

MAGIC = 0xAA55AA55
HEADER_SIZE = 765          # 'gf' starts here in every version-96 save
QUEST_OFF, WP_OFF, NPC_OFF = 0x14F, 0x279, 0x2C9

CLASSES = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]
QUALITY = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique", 8: "crafted"}

# Stats saved as a group: one id, then the values of the following ids with no id of their own.
# (first id, number of values). See docs/formats/d2s.md "Property lists".
GROUPS = {17: 2, 48: 2, 50: 2, 52: 2, 54: 3, 57: 3}


class D2sError(Exception):
    pass


class Bits:
    """LSB-first bit reader over a bytes object."""

    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos  # pos in bits

    def read(self, n):
        v = 0
        for i in range(n):
            byte = self.pos >> 3
            if byte >= len(self.data):
                raise D2sError("bit read past end at bit %d" % self.pos)
            v |= ((self.data[byte] >> (self.pos & 7)) & 1) << i
            self.pos += 1
        return v

    def align(self):
        """Skip to the next byte; return the value of the padding bits that were skipped."""
        self.last_pad = (-self.pos) % 8
        return self.read(self.last_pad) if self.last_pad else 0


def checksum(data):
    """Rotate-left-1-and-add over every byte, with the checksum field (+0x0C) taken as zero."""
    s = 0
    for i, x in enumerate(data):
        if 12 <= i < 16:
            x = 0
        s = (((s << 1) | (s >> 31)) + x) & 0xFFFFFFFF
    return s


def load_isc(excel_dir):
    """id -> dict of the save-bit columns of itemstatcost.txt."""
    text = open(os.path.join(excel_dir, "itemstatcost.txt"), encoding="latin1").read()
    rows = [l.rstrip("\r").split("\t") for l in text.split("\n") if l.strip("\r")]
    ix = {c: i for i, c in enumerate(rows[0])}

    def col(r, c):
        v = r[ix[c]] if ix[c] < len(r) else ""
        return int(v) if v.strip() else 0

    isc = {}
    for r in rows[1:]:
        if not r[ix["ID"]].strip():
            continue
        isc[col(r, "ID")] = dict(name=r[ix["Stat"]], save_bits=col(r, "Save Bits"),
                                 save_add=col(r, "Save Add"), param_bits=col(r, "Save Param Bits"),
                                 csv_bits=col(r, "CSvBits"), csv_param=col(r, "CSvParam"),
                                 csv_signed=col(r, "CSvSigned"))
    return isc


def s32(b, o):
    return struct.unpack_from("<i", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def parse_header(b):
    if len(b) < HEADER_SIZE or u32(b, 0) != MAGIC:
        raise D2sError("bad magic or short file")
    h = dict(version=u32(b, 4), file_size=u32(b, 8), checksum=u32(b, 12), weapon_set=u32(b, 16),
             name=b[0x14:0x24].split(b"\0")[0].decode("latin1"), status=b[0x24], progression=b[0x25],
             unk_26=u16(b, 0x26), cls=b[0x28], unk_29=u16(b, 0x29), level=b[0x2B], unk_2c=u32(b, 0x2C),
             last_played=u32(b, 0x30), unk_34=u32(b, 0x34),
             hotkeys=[u32(b, 0x38 + 4 * i) for i in range(16)],
             mouse=[u32(b, 0x78 + 4 * i) for i in range(4)], appearance=bytes(b[0x88:0xA8]),
             difficulty=bytes(b[0xA8:0xAB]), map_seed=u32(b, 0xAB), unk_af=u16(b, 0xAF),
             merc_dead=u16(b, 0xB1), merc_seed=u32(b, 0xB3), merc_name=u16(b, 0xB7),
             merc_type=u16(b, 0xBB - 2), merc_exp=u32(b, 0xBB), unk_bf=bytes(b[0xBF:QUEST_OFF]))
    if h["version"] != 96:
        raise D2sError("version %d" % h["version"])
    return h


def parse_fixed_sections(b):
    """The quest, waypoint and NPC sections: tag, version, size, body. Each size counts from its tag."""
    out = {}
    for name, off, tag, has_ver in (("quests", QUEST_OFF, b"Woo!", True), ("waypoints", WP_OFF, b"WS", True),
                                    ("npcs", NPC_OFF, b"\x01w", False)):
        if b[off:off + len(tag)] != tag:
            raise D2sError("%s tag missing at 0x%X" % (name, off))
        p = off + len(tag)
        ver = u32(b, p) if has_ver else None
        p += 4 if has_ver else 0
        size = u16(b, p)
        out[name] = dict(off=off, version=ver, size=size, end=off + size)
    if out["quests"]["end"] != WP_OFF or out["waypoints"]["end"] != NPC_OFF or out["npcs"]["end"] != HEADER_SIZE:
        raise D2sError("section sizes do not chain: %r" % out)
    return out


def parse_stats(b, pos, isc):
    if b[pos:pos + 2] != b"gf":
        raise D2sError("'gf' missing at 0x%X" % pos)
    r = Bits(b, (pos + 2) * 8)
    stats = []
    while True:
        sid = r.read(9)
        if sid == 0x1FF:
            break
        if sid not in isc or not isc[sid]["csv_bits"]:
            raise D2sError("character stat %d has no CSvBits" % sid)
        param = r.read(isc[sid]["csv_param"]) if isc[sid]["csv_param"] else None
        stats.append((sid, param, r.read(isc[sid]["csv_bits"])))
    pad = r.align()
    return stats, r.pos // 8, pad


def parse_skills(b, pos):
    if b[pos:pos + 2] != b"if":
        raise D2sError("'if' missing at 0x%X" % pos)
    return list(b[pos + 2:pos + 32]), pos + 32


def parse_props(r, isc):
    """One property list, ended by id 0x1FF. Returns [(id, param, [values])]."""
    props = []
    while True:
        sid = r.read(9)
        if sid == 0x1FF:
            return props
        if sid not in isc or not isc[sid]["save_bits"]:
            raise D2sError("item stat %d has no Save Bits (bit %d)" % (sid, r.pos))
        e = isc[sid]
        param = r.read(e["param_bits"]) if e["param_bits"] else None
        vals = []
        for k in range(GROUPS.get(sid, 1)):
            ek = isc[sid + k]
            vals.append(r.read(ek["save_bits"]) - ek["save_add"])
        props.append((sid, param, vals))


def parse_item(b, pos, isc, kinds):
    """One item at byte pos (its 'JM'). Returns (item, end byte). kinds: code -> 'armor'|'weapon'|'misc'."""
    if b[pos:pos + 2] != b"JM":
        raise D2sError("'JM' missing at 0x%X" % pos)
    r = Bits(b, pos * 8 + 16)
    it = dict(off=pos, flags=r.read(32))
    f = it["flags"]
    it.update(identified=f >> 4 & 1, socketed=f >> 11 & 1, new=f >> 13 & 1, ear=f >> 16 & 1,
              starter=f >> 17 & 1, simple=f >> 21 & 1, ethereal=f >> 22 & 1, personalized=f >> 24 & 1,
              runeword=f >> 26 & 1)
    it["version"] = r.read(10)
    it["location"], it["body"], it["x"], it["y"], it["store"] = r.read(3), r.read(4), r.read(4), r.read(4), r.read(3)
    if it["ear"]:
        it["ear_class"], it["ear_level"] = r.read(3), r.read(7)
        it["ear_name"] = "".join(chr(c) for c in iter(lambda: r.read(7), 0))
        it["pad"] = r.align()
        it["pad_bits"] = r.last_pad
        return it, r.pos // 8
    it["code"] = bytes(r.read(8) for _ in range(4)).decode("latin1")
    it["n_filled"] = r.read(3)
    if it["simple"]:
        it["pad"] = r.align()
        it["pad_bits"] = r.last_pad
        return it, r.pos // 8
    code = it["code"].strip()
    it["seed"], it["ilvl"], it["quality"] = r.read(32), r.read(7), r.read(4)
    it["has_gfx"] = r.read(1)
    it["gfx"] = r.read(3) if it["has_gfx"] else None
    it["has_class"] = r.read(1)
    it["class_affix"] = r.read(11) if it["has_class"] else None
    q = it["quality"]
    if q in (1, 3):
        it["qdata"] = r.read(3)
    elif q == 4:
        it["prefix"], it["suffix"] = r.read(11), r.read(11)
    elif q in (5, 7):
        it["qid"] = r.read(12)
    elif q in (6, 8):
        it["names"] = (r.read(8), r.read(8))
        it["affixes"] = [r.read(11) if r.read(1) else None for _ in range(6)]
    elif q != 2:
        raise D2sError("quality %d at 0x%X" % (q, pos))
    if it["runeword"]:
        it["rw"] = (r.read(12), r.read(4))
    if it["personalized"]:
        it["pname"] = "".join(chr(c) for c in iter(lambda: r.read(7), 0))
    if code in ("tbk", "ibk"):
        it["tome"] = r.read(5)
    it["realm"] = r.read(1)
    if it["realm"]:
        raise D2sError("realm data present at 0x%X (not seen in samples)" % pos)
    kind = kinds.get(code)
    if kind == "armor":
        it["defense"] = r.read(isc[31]["save_bits"]) - isc[31]["save_add"]
    if kind in ("armor", "weapon"):
        it["maxdur"] = r.read(isc[73]["save_bits"])
        if it["maxdur"]:
            it["dur"] = r.read(isc[72]["save_bits"])
    if kinds.get(code + "#stack"):
        it["quantity"] = r.read(9)
    if it["socketed"]:
        it["sockets"] = r.read(4)
    if q == 5:
        it["set_lists"] = r.read(5)
    it["props"] = parse_props(r, isc)
    for k in range(5) if q == 5 else ():
        if it["set_lists"] >> k & 1:
            it.setdefault("set_props", []).append(parse_props(r, isc))
    if it["runeword"]:
        it["rw_props"] = parse_props(r, isc)
    it["pad"] = r.align()
    it["pad_bits"] = r.last_pad
    return it, r.pos // 8


def load_kinds(excel_dir):
    """Item code -> 'weapon' | 'armor' | 'misc', plus code+'#stack' for stackable items."""
    kinds = {}
    for table in ("weapons", "armor", "misc"):
        text = open(os.path.join(excel_dir, table + ".txt"), encoding="latin1").read()
        rows = [l.rstrip("\r").split("\t") for l in text.split("\n") if l.strip("\r")]
        ix = {c: i for i, c in enumerate(rows[0])}
        for r in rows[1:]:
            code = r[ix["code"]].strip() if ix["code"] < len(r) else ""
            if not code:
                continue
            kinds[code] = table.rstrip("s") if table != "misc" else "misc"
            st = r[ix["stackable"]].strip() if ix["stackable"] < len(r) else ""
            if st == "1":
                kinds[code + "#stack"] = True
    kinds = {k: ("armor" if v == "armo" else v) for k, v in kinds.items()}
    return kinds


def parse_items(b, pos, isc, kinds, tag=b"JM"):
    """An item list: 'JM', u16 count, then count top-level items, each followed by its socketed items."""
    if b[pos:pos + 2] != tag:
        raise D2sError("item list tag missing at 0x%X" % pos)
    count = u16(b, pos + 2)
    p = pos + 4
    items = []
    for _ in range(count):
        it, p = parse_item(b, p, isc, kinds)
        it["end"] = p
        items.append(it)
        for _ in range(it.get("n_filled", 0)):
            sub, p = parse_item(b, p, isc, kinds)
            sub["parent"], sub["end"] = it["off"], p
            items.append(sub)
    return dict(count=count, items=items), p


def parse(b, isc, kinds):
    h = parse_header(b)
    f = dict(header=h, sections=parse_fixed_sections(b))
    f["stats"], p, f["stats_pad"] = parse_stats(b, HEADER_SIZE, isc)
    f["skills"], p = parse_skills(b, p)
    f["items"], p = parse_items(b, p, isc, kinds)
    f["corpses"], p = parse_corpses(b, p, isc, kinds)
    if h["status"] & 0x20:
        if b[p:p + 2] != b"jf":
            raise D2sError("'jf' missing at 0x%X" % p)
        p += 2
        if h["merc_seed"]:
            f["merc_items"], p = parse_items(b, p, isc, kinds)
        if b[p:p + 2] != b"kf":
            raise D2sError("'kf' missing at 0x%X" % p)
        f["golem"] = b[p + 2]
        p += 3
        if f["golem"]:
            it, p = parse_item(b, p, isc, kinds)
            f["golem_item"] = it
    f["end"] = p
    return f


def parse_corpses(b, pos, isc, kinds):
    if b[pos:pos + 2] != b"JM":
        raise D2sError("corpse 'JM' missing at 0x%X" % pos)
    n = u16(b, pos + 2)
    p = pos + 4
    corpses = []
    for _ in range(n):
        unk = bytes(b[p:p + 12])
        lst, p = parse_items(b, p + 12, isc, kinds)
        corpses.append(dict(unk=unk, items=lst))
    return corpses, p


def all_items(f):
    yield from f["items"]["items"]
    for c in f["corpses"]:
        yield from c["items"]["items"]
    if "merc_items" in f:
        yield from f["merc_items"]["items"]
    if "golem_item" in f:
        yield f["golem_item"]


def stub_check(b):
    """A save written at character creation: only the 335-byte header prefix."""
    return len(b) == 335 and u32(b, 0) == MAGIC and u32(b, 8) == 335


def survey(excel_dir, paths):
    isc, kinds = load_isc(excel_dir), load_kinds(excel_dir)
    s = collections.defaultdict(collections.Counter)
    bad = 0
    for path in paths:
        b = open(path, "rb").read()
        name = os.path.basename(path)
        ok_sum = checksum(b) == u32(b, 12)
        ok_size = u32(b, 8) == len(b)
        s["checksum matches"][ok_sum] += 1
        s["file_size field == size"][ok_size] += 1
        if stub_check(b):
            s["kind"]["stub (335 B)"] += 1
            s["stub status"][b[0x24]] += 1
            if not (ok_sum and ok_size):
                bad += 1
                print("BAD", name)
            continue
        try:
            f = parse(b, isc, kinds)
        except D2sError as e:
            print("FAIL", name, e)
            bad += 1
            continue
        left = len(b) - f["end"]
        s["kind"]["full"] += 1
        s["leftover bytes"][left] += 1
        if left or not (ok_sum and ok_size):
            bad += 1
            print("BAD", name, "leftover", left)
        h = f["header"]
        s["class"][CLASSES[h["cls"]] if h["cls"] < 7 else h["cls"]] += 1
        s["status"][h["status"]] += 1
        s["stats pad bits"][f["stats_pad"]] += 1
        s["stat ids"][tuple(x[0] for x in f["stats"])] += 1
        for it in all_items(f):
            s["item code"][it.get("code", "ear")] += 1
            s["item simple"][it["simple"]] += 1
            s["item quality"][QUALITY.get(it.get("quality"), "-")] += 1
            s["item version (10 bits)"][it["version"]] += 1
            s["item pad value"][it["pad"]] += 1
            s["item pad bit count"][it["pad_bits"]] += 1
            s["item length (bytes), simple"][(it["end"] - it["off"]) if it["simple"] else "-"] += 1
            for lst in [it.get("props", [])] + it.get("set_props", []) + [it.get("rw_props", [])]:
                for sid, param, vals in lst:
                    s["property ids"][sid] += 1
            if it.get("has_gfx"):
                s["gfx (code)"][(it["code"].strip(), it["gfx"])] += 1
            for k in ("has_class", "realm", "personalized", "ear", "runeword", "ethereal", "socketed", "new", "starter"):
                s["flag " + k][it.get(k)] += 1
            s["flags bit 23"][it["flags"] >> 23 & 1] += 1
            s["flags other bits"][it["flags"] & ~(1 << 4 | 1 << 11 | 1 << 13 | 1 << 16 | 1 << 17 | 1 << 21
                                                   | 1 << 22 | 1 << 23 | 1 << 24 | 1 << 26)] += 1
            s["item location, store"][(it["location"], it["store"])] += 1
            s["item flags (hex)"]["%08X" % it["flags"]] += 1
    for k in sorted(s):
        print("%-28s %s" % (k, ", ".join("%s=%d" % kv for kv in s[k].most_common(30))))
    print("saves %d, bad %d" % (len(paths), bad))
    return 1 if bad else 0


def dump(excel_dir, path):
    isc, kinds = load_isc(excel_dir), load_kinds(excel_dir)
    b = open(path, "rb").read()
    f = parse(b, isc, kinds)
    for k, v in f["header"].items():
        if k not in ("unk_bf",):
            print("%-14s %r" % (k, v))
    print("sections", f["sections"])
    for sid, param, v in f["stats"]:
        print("stat %3d %-14s %r%s" % (sid, isc[sid]["name"], v, "" if param is None else " param %d" % param))
    print("skills", f["skills"])
    for it in all_items(f):
        print({k: v for k, v in it.items() if k not in ("flags",)}, "flags=%08X" % it["flags"])
    print("end", f["end"], "size", len(b))


def setstat(excel_dir, src, dst, sid, value):
    """Rewrite one character stat's value bits (same width) and fix the checksum."""
    isc = load_isc(excel_dir)
    b = bytearray(open(src, "rb").read())
    r = Bits(b, (HEADER_SIZE + 2) * 8)
    while True:
        s = r.read(9)
        if s == 0x1FF:
            raise D2sError("stat %d not present" % sid)
        if isc[s]["csv_param"]:
            r.read(isc[s]["csv_param"])
        n = isc[s]["csv_bits"]
        if s == sid:
            if value >> n:
                raise D2sError("value does not fit in %d bits" % n)
            for i in range(n):
                bit = r.pos + i
                b[bit >> 3] = (b[bit >> 3] & ~(1 << (bit & 7))) | ((value >> i & 1) << (bit & 7))
            break
        r.read(n)
    struct.pack_into("<I", b, 12, checksum(b))
    open(dst, "wb").write(b)
    print("wrote", dst, "checksum %08X" % u32(b, 12))


def main(argv):
    if len(argv) >= 3 and argv[0] == "survey":
        return survey(argv[1], argv[2:])
    if len(argv) == 3 and argv[0] == "dump":
        dump(argv[1], argv[2])
        return 0
    if len(argv) == 2 and argv[0] == "checksum":
        b = open(argv[1], "rb").read()
        print("stored %08X computed %08X" % (u32(b, 12), checksum(b)))
        return 0 if u32(b, 12) == checksum(b) else 1
    if len(argv) == 6 and argv[0] == "setstat":
        setstat(argv[1], argv[2], argv[3], int(argv[4]), int(argv[5]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

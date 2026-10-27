"""Read Diablo II character saves (.d2s, version 96; 93..95 on request): header, sections, stats, skills, item lists.

Usage:
  python3 -I tools/d2s.py survey <excel-dir> <file.d2s ...>   parse every save; checksum, sections,
                                                               byte and bit accounting, histograms
  python3 -I tools/d2s.py dump <excel-dir> <file.d2s>          print the header, stats and every item
  python3 -I tools/d2s.py checksum <file.d2s>                  print the stored and computed checksums
  python3 -I tools/d2s.py setstat <excel-dir> <in.d2s> <out.d2s> <stat-id> <value>
                                                               rewrite one character stat in place
                                                               (same bit width) and re-checksum
  python3 -I tools/d2s.py setstats <excel-dir> <in.d2s> <out.d2s> <id>=<value> ...
                                                               set, add or (value 0) remove character
                                                               stats; re-encodes the stat list, fixes
                                                               header level, file size and checksum
  python3 -I tools/d2s.py setwp <in.d2s> <out.d2s> <difficulty> <waypoints|all|none>
                                                               replace one difficulty's 14-byte waypoint
                                                               bit field and re-checksum. difficulty:
                                                               0|1|2 or normal|nightmare|hell;
                                                               waypoints: comma-separated bit indices
                                                               0..38 (ranges a-b allowed), 'all' = 0..38
  python3 -I tools/d2s.py roundtrip <excel-dir> <file.d2s ...>
                                                               re-encode every item and every file from
                                                               its parsed form; exit 0 only if all are
                                                               byte-identical (tests the writer)
  python3 -I tools/d2s.py checkuniq <excel-dir> <file.d2s ...>
                                                               compare each unique item's property list
                                                               with its uniqueitems.txt row (min..max)
  python3 -I tools/d2s.py build <excel-dir> <recipe.json> <in.d2s> <out.d2s>
                                                               build a save from a base save and a recipe
  python3 -I tools/d2s.py questbits <file.d2s> [<base.d2s>]
                                                               the set bits of every non-zero quest word,
                                                               per difficulty; with a base, only the bits
                                                               that differ from it (+ set, - cleared)
  python3 -I tools/d2s.py classic <excel-dir> <in.d2s> <out.d2s>
                                                               make an expansion save classic: clear status
                                                               bit 5 and drop the jf/kf trailer (no mercenary
                                                               items, no golem), fix size and checksum; the
                                                               way the classic base cls/smpsor.d2s was made

build recipe (JSON object; every key optional; example tools/d2s_recipes/lightsorc.json):
  game         required: "classic" or "expansion", must match the base save's status byte (0x24 bit 5); the
               build keeps the base's status, so the base decides what the character is
  class        must equal the base save's class (Sorceress, ...)
  seed         seeds the item-seed generator, so the build is reproducible (else system random)
  name         header name (the file must be saved as <name>.d2s)
  progression  header 0x25; difficulty: the three header bytes 0xA8..0xAA
  waypoints    {"normal"|"nightmare"|"hell": "all" | "none" | "0-8,12"}
  stats        the whole character stat list, {itemstatcost Stat name or id: value}; stats 6..11
               (life, mana, stamina) in whole points (written << 8); header level follows stat 12
  skills       {skills.txt skill name: level}; byte i = the class's i-th skills.txt row (file order)
  mouse        {"left"|"right"|"swap_left"|"swap_right": skills.txt skill name}
  hotkeys      [skill name, ...] (at most 16): F1, F2, ... bound to these skills for the right button
               ("left:<name>" sets the 0x8000 slot flag, read as the left button); later slots stay as in
               the base
  keep_items   item codes of the base save's top-level items to keep; a kept item keeps its socketed items
  items        list of new items: {"unique": uniqueitems index}, {"code": item code}, a magic item
               {"code": item code, "suffix": magicsuffix record index 1..} (no prefix; the suffix's
               mod1..3 become its properties through properties.txt, at "roll"), or a rare item
               {"code": item code, "rare": [name1, name2]} (the two 8-bit name ids as stored, name1 =
               RarePrefix row + 156; an optional "suffix" fills affix slot 1 as above, else no affix and
               no property), placed by
               "equip": bodylocs Code (or "rarm2" / "larm2", the weapon-switch hands, body 11 / 12) |
               "belt_slot": 0..15 | "store": "inventory"|"cube"|"stash" with x, y;
               plan 0041 Phase 2 adds {"set": setitems index} (quality 5: prop1..9 to the main list, aprop pairs
               to the set lists by add func, items/0006), {"code": ..., "prefix": magicprefix record index}
               (with or without "suffix"), "ethereal": true (flags bit 22; armor or weapon with durability), and
               the property funcs 5, 6 (damage by base column), 10 (skill tab), 14 (sockets: give "sockets"), 20
               (indestructible) and 22 (skill param, e.g. an aura) in the unique, set and affix rows;
               optional "seed", "ilvl" (99), "gfx", "roll" ("max" | "min"), "quantity", "tome" (tbk/ibk, 0),
               "sockets": N (flags bit 11 and the 4-bit socket count, base stat 194; 1..min(6, invwidth x
               invheight, gemsockets, the type's MaxSock for the ilvl), else refused; also refused above the
               quality clamp of ITEMS_SetSockets, magic 4 and rare 2, unless the item has
               "unclamped_sockets": true), "quest_diff" (required by a simple quest item with
               questdiffcheck, e.g. mss: the stat 356 value it stores), "filled": [item, ...]
               (at most N socketed items, each an item entry with no placement, e.g. {"code": "gsv"},
               {"code": "jew", "suffix": 371}; it must be a gem, rune or jewel (item type reaching sock); written
               after its parent with location 6 and x = socket index 0, 1, ...). The parent keeps an empty
               property list: a filled item's own stats are not copied into it, and no runeword is formed
               (flags bit 26 stays clear), whatever the runes; the game's insert path does that, not the builder
               "item_stats": {stat id: value} adds entries to an extended item's property list (plan 0030
               Phase 2: stat 356 on Wirt's Leg); "lone_follower": true (plan 0038 H1b, test state) writes a
               group follower whose head is absent (e.g. item_stats {"49": 10}, fire-max without fire-min) as an
               entry of its own, its id and its own Save Bits, instead of refusing it;
               "dur": N (plan 0043 Phase 2, test state) writes current durability N (0..the full maximum) for
               a damaged item; "broken": true (plan 0043 Phase 2b, test state, with "dur": 0) sets flags bit 8;
               {"code": ..., "crafted": [name1, name2]} (plan 0043 Phase 2b) is a crafted item (quality 8) built
               as a rare one, with an optional "prefix" in affix slot 0 and "suffix" in slot 1 (their mods as the
               properties), a state the cube's crafting does not make (no recipe mods);
               test-state keys (plan 0029 Phase 2): "identified": false clears flags bit 4 (an unidentified
               item); "quality": "low" | "superior" (3-bit field "qdata", 0) | "rare" | "crafted" ("names"
               [name1, name2], (160, 121), no affixes) on a plain code: the quality with empty quality fields and the
               normal base stats, a state the game's builders do not make
  belt_fill    item code put in every slot of the equipped belt (belts.txt numboxes), or a list of
               exactly four codes, one per belt column (slot k is in column k % 4, hot key 1 + k % 4);
               needs one belt among the new items
  acts_open    ["normal", "nightmare", "hell"]: set bit 0 of the act-travel quest words (7, 15, 23;
               26 and 28 in an expansion save) so the waypoint menu opens Acts II-V (save/0002, [I])
  quests       "all" (every difficulty) or a list of difficulties: acts_open for each, plus bit 0 of
               the quest words 1-6, 9-14, 17-22, 25-27 (and 35-40 in an expansion save); words 0, 8,
               16, 24, 29-34 and 41 are left as in the base (save/0002 Recipe, [I]). Waypoints and
               progression are not implied: give them with the waypoints and progression keys
  quest_bits   {"normal"|"nightmare"|"hell": {word: [bit, ...] | {"set": [bit, ...], "clear": [bit, ...]}}}:
               set (a plain list) or set and clear single bits of quest words 0..47 (bit 0..15) of that
               difficulty's quest record (block d at 0x159 + 0x60 d, word q at + 2q, bit s = 16 q + s,
               save/0002). Applied after acts_open and quests, so it can also clear what they set; a bit both
               set and cleared is refused. What a bit means is not the builder's business (save/0002, [L] leads).
               Also accepted, the list form [[difficulty, word, bit, 0|1], ...] (plan 0030 Phase 2's cow recipes),
               applied the same way
  merc         {"id": Hireling.txt Id, "seed": 1.., "name": name id, "exp": experience, "dead": bool,
               "items": [item, ...]}: the mercenary header 0xAF..0xBE (flags bit 16 = dead, seed, name id as stored,
               hireling id, experience; docs/formats/d2s.md) and, in an expansion save, the mercenary item list after
               'jf' (items placed with "equip" only; hand items written last). The Id must have a row of the save's
               Version (100 expansion, 0 classic); name runs 0 .. (string index of NameLast - of NameFirst) of that
               row; seed 0 is refused (it means no mercenary). A classic save takes no merc items.
               Test-state key (plan 0038 H1b): "name_unchecked": true writes any u16 name id, past the row's
               range too
  Extension keys (backlog 2026-10-27 H1a gaps; all off unless given, test states; d2s.md § Versions 92..95,
  § Realm data). With any of them, or an item with "realm", the build writes in the extended form, otherwise
  exactly as without them:
  save_version 93..96 (header 0x04): <= 94 writes the stats in the old form ('gf', a 2-byte mask over stats
               0..stat_slots-1, a u32 per set bit; only stat_slots 9..16), <= 95 writes every item's current
               durability (stat 72) in 8 bits, <= 93 writes two realm words, not three. 92 and below are refused
               (undocumented layouts). A base with corpse, golem or (unreplaced) mercenary items is refused for a
               version other than 96, since those bytes are copied from the base in the version-96 widths
  stat_slots   header 0x29 (the old stat reader's count); skill_count: header 0x2A and that many skill bytes
               (padded with 0, a cut-off non-zero byte refused)
  item "realm": [u32, u32] or [u32, u32, u32]: the realm flag 1 and its words (three above version 93; the
               game writes the third as 0); in the extended form an ear's realm bit 0 follows its name
Unique properties come from the row's prop/par/min/max through properties.txt (funcs 1, 2, 3, 7, 8,
11, 15, 16, 17, 19, 21; any other func is an error). Armor defense = maxac (+1 with enhanced defense),
durability = the base value, current = the full maximum; flags = identified | bit 23 (| simple).
Items in the two hand slots are written last. The quest and NPC sections are kept from the base, except acts_open and quests.
The builder refuses (error, exit 1, nothing written) when two top-level items, kept or new, share space: grid
rectangles (x, y, invwidth x invheight of weapons/armor/misc) that overlap in one storage page (inventory, cube,
stash), two items in one belt slot, or two in one equipped body slot: in run:2026-10-14-uniques two
covered charms gave no magic find.
Reading: parse(b, isc, kinds, extended=True) (API only; the commands read as before) takes versions 93..96, the old
stat form, header 0x2A skill bytes, realm data and an ear's realm bit; encode_item(it, isc, kinds, ver) writes them.
Tests: python3 -I tools/test_d2s.py (builds every recipe in tools/d2s_recipes/ on its base save; skips without
workspace/).

<excel-dir> is a data/global/excel directory (e.g. workspace/merged/data/global/excel). The stat and
item property lists are read with the save-bit columns of itemstatcost.txt. Layout in
docs/formats/d2s.md. Little-endian; bit fields are read LSB first within each byte. survey exits 0
only if every save's checksum and file-size field match, every section is where its header says, and
every item ends on the byte where the next item (or section) starts, with only zero padding bits.
Stdlib only. Read-only, except setstat, setstats, setwp and build, which write <out.d2s>.
"""
import collections
import os
import struct
import sys

MAGIC = 0xAA55AA55
HEADER_SIZE = 765          # 'gf' starts here in every version-96 save
QUEST_OFF, WP_OFF, NPC_OFF = 0x14F, 0x279, 0x2C9
# WS: 'WS', u32 version, u16 size, then three 24-byte blocks (normal, nightmare, hell), each
# a u16 marker 0x0102 (bytes 02 01), a 14-byte waypoint bit field (seven u16 words, LSB first,
# bit n = waypoint n, n < 112), and 8 bytes the game never writes (save/0001 § 3).
WP_BLOCK0, WP_BLOCK_SIZE, WP_FIELD_OFF, WP_FIELD_BYTES = WP_OFF + 8, 24, 2, 14
WP_COUNT = 39              # levels.txt Waypoint values 0..38 (255 = none)
DIFFICULTIES = ["normal", "nightmare", "hell"]
# Quest words of the quest objects of Acts I-IV and of Act V (save/0002 § Recipe, build key quests)
QUEST_WORDS = list(range(1, 7)) + list(range(9, 15)) + list(range(17, 23)) + list(range(25, 28))
QUEST_WORDS_ACT5 = list(range(35, 41))

CLASSES = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]
QUALITY = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique", 8: "crafted"}

# Stats saved as a group: one id, then the values of the following ids with no id of their own.
# (first id, number of values). See docs/formats/d2s.md "Property lists".
GROUPS = {17: 2, 48: 2, 50: 2, 52: 2, 54: 3, 57: 3}


class D2sError(Exception):
    pass


# Extended reading and writing (backlog 2026-10-27 H1a gaps; d2s.md § Versions 92..95, § Realm data). Off unless
# asked for: parse(..., extended=True), encode_item(..., ver=N), the build keys save_version, stat_slots,
# skill_count and the item key realm. Without them every function reads and writes exactly as before.
EXT_VERSIONS = (93, 94, 95, 96)
OLD_STATS_MAX = 94        # D2S_ReadStats: version <= 94 takes the bitmask form (save/0001 § Plan 0038 H1a row 68)
DUR8_MAX = 95             # ITEMS_ReadFull: version <= 95 reads stat 72 in 8 bits (0x0062D425, 0x0062D759)
REALM3_MIN = 94           # a third realm u32 is read for a version above 93 (0x0062D2D3-0x0062D2DF)
OLD_SLOTS = range(9, 17)  # stat_slots whose bitmask takes 2 bytes under the finding's reading (12, 16 run-confirmed)


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


def parse_header(b, extended=False):
    """The 0x14F-byte header. Only version 96 unless extended (backlog 2026-10-27 H1a gaps, d2s.md § Versions 92..95):
    then 93..96; 92 stays refused, its item property widths are not documented (1.09 widths plus per-id overrides)."""
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
    if extended:
        h["stat_slots"], h["skill_count"] = b[0x29], b[0x2A]
    if extended and h["version"] in EXT_VERSIONS:
        return h
    if extended and h["version"] == 92:
        raise D2sError("version 92: item properties use the 1.09 widths with per-id overrides that are not "
                       "documented (d2s.md § Versions 92..95)")
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


def wp_field_off(d):
    """File offset of difficulty d's 14-byte waypoint bit field."""
    return WP_BLOCK0 + d * WP_BLOCK_SIZE + WP_FIELD_OFF


def parse_waypoints(b):
    """Per difficulty: (block head bytes, set bit indices, the 8 trailing bytes)."""
    out = []
    for d in range(3):
        blk = b[WP_BLOCK0 + d * WP_BLOCK_SIZE:WP_BLOCK0 + (d + 1) * WP_BLOCK_SIZE]
        field = int.from_bytes(blk[WP_FIELD_OFF:WP_FIELD_OFF + WP_FIELD_BYTES], "little")
        out.append(dict(head=bytes(blk[:WP_FIELD_OFF]), bits=[i for i in range(8 * WP_FIELD_BYTES) if field >> i & 1],
                        tail=bytes(blk[WP_FIELD_OFF + WP_FIELD_BYTES:])))
    return out


def load_wp_names(excel_dir):
    """levels.txt Waypoint index -> (level Id, LevelName)."""
    text = open(os.path.join(excel_dir, "levels.txt"), encoding="latin1").read()
    rows = [l.rstrip("\r").split("\t") for l in text.split("\n") if l.strip("\r")]
    ix = {c: i for i, c in enumerate(rows[0])}
    names = {}
    for r in rows[1:]:
        w = r[ix["Waypoint"]].strip() if ix["Waypoint"] < len(r) else ""
        if w and w != "255":
            names[int(w)] = (int(r[ix["Id"]]), r[ix["LevelName"]])
    return names


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


def parse_stats_old(b, pos, n):
    """The version <= 94 stat form: 'gf', a bitmask over stats 0..n-1 (n = header 0x29), one u32 per set bit.
    Returns ([(id, None, value)], end). Only n in 9..16 (a 2-byte mask) is accepted."""
    if b[pos:pos + 2] != b"gf":
        raise D2sError("'gf' missing at 0x%X" % pos)
    if n not in OLD_SLOTS:
        raise D2sError("stat_slots %d: the mask width is documented for 9..16 only (2 bytes)" % n)
    mask, p, stats = u16(b, pos + 2), pos + 4, []
    for sid in range(n):
        if mask >> sid & 1:
            stats.append((sid, None, u32(b, p)))
            p += 4
    return stats, p


def parse_skills(b, pos, count=30):
    """'if' and count skill bytes (header 0x2A; 30 in every 1.14d save)."""
    if b[pos:pos + 2] != b"if":
        raise D2sError("'if' missing at 0x%X" % pos)
    return list(b[pos + 2:pos + 2 + count]), pos + 2 + count


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


def read_realm(r, it, ver):
    """The realm flag and, when it is 1, two u32 and (version above 93) a third (d2s.md § Realm data)."""
    it["realm"] = r.read(1)
    if it["realm"]:
        it["realm_data"] = [r.read(32) for _ in range(3 if ver >= REALM3_MIN else 2)]


def parse_item(b, pos, isc, kinds, ver=None):
    """One item at byte pos (its 'JM'). Returns (item, end byte). kinds: code -> 'armor'|'weapon'|'misc'.
    ver: None reads as before (version 96, realm data refused, nothing after an ear's name); a save version reads
    the realm data, the ear's realm bit and, for ver <= 95, stat 72 in 8 bits."""
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
        if ver is not None:
            read_realm(r, it, ver)   # ITEMS_WriteCompact writes the realm bit after the name (0x0062B277 -> 0x0062B341)
        it["pad"] = r.align()
        it["pad_bits"] = r.last_pad
        return it, r.pos // 8
    it["code"] = bytes(r.read(8) for _ in range(4)).decode("latin1")
    code = it["code"].strip()
    if it["simple"]:
        # A simple item has no n_filled (save/0001 § 7): gold amount, quest stat 356, realm bit.
        if code == "gld":
            it["gold_big"] = r.read(1)
            it["gold"] = r.read(32 if it["gold_big"] else 12)
        if kinds.get(code + "#qdc"):
            it["quest_diff"] = r.read(isc[356]["save_bits"])
        if ver is not None:
            read_realm(r, it, ver)
        else:
            it["realm"] = r.read(1)
            if it["realm"]:
                raise D2sError("realm data present at 0x%X (not seen in samples)" % pos)
        it["pad"] = r.align()
        it["pad_bits"] = r.last_pad
        return it, r.pos // 8
    it["n_filled"] = r.read(3)
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
    if code in ("tbk", "ibk"):
        # Part of the normal-quality fields, before the runeword field (save/0001 § 7).
        it["tome"] = r.read(5)
    if it["runeword"]:
        it["rw"] = (r.read(12), r.read(4))
    if it["personalized"]:
        it["pname"] = "".join(chr(c) for c in iter(lambda: r.read(7), 0))
    if ver is not None:
        read_realm(r, it, ver)
    else:
        it["realm"] = r.read(1)
        if it["realm"]:
            raise D2sError("realm data present at 0x%X (not seen in samples)" % pos)
    kind = kinds.get(code)
    if kind == "armor":
        it["defense"] = r.read(isc[31]["save_bits"]) - isc[31]["save_add"]
    if kind in ("armor", "weapon"):
        it["maxdur"] = r.read(isc[73]["save_bits"])
        if it["maxdur"]:
            it["dur"] = r.read(8 if ver is not None and ver <= DUR8_MAX else isc[72]["save_bits"])
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
    """Item code -> 'weapon' | 'armor' | 'misc', plus code+'#stack' for stackable items and
    code+'#qdc' for items with questdiffcheck = 1 (a simple one carries stat 356)."""
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
            qdc = r[ix["questdiffcheck"]].strip() if "questdiffcheck" in ix and ix["questdiffcheck"] < len(r) else ""
            if qdc == "1":
                kinds[code + "#qdc"] = True
    kinds = {k: ("armor" if v == "armo" else v) for k, v in kinds.items()}
    return kinds


def parse_items(b, pos, isc, kinds, tag=b"JM", ver=None):
    """An item list: 'JM', u16 count, then count top-level items, each followed by its socketed items."""
    if b[pos:pos + 2] != tag:
        raise D2sError("item list tag missing at 0x%X" % pos)
    count = u16(b, pos + 2)
    p = pos + 4
    items = []
    for _ in range(count):
        it, p = parse_item(b, p, isc, kinds, ver)
        it["end"] = p
        items.append(it)
        for _ in range(it.get("n_filled", 0)):
            sub, p = parse_item(b, p, isc, kinds, ver)
            sub["parent"], sub["end"] = it["off"], p
            items.append(sub)
    return dict(count=count, items=items), p


def parse(b, isc, kinds, extended=False):
    """A full save. extended (default off): versions 93..96, the old stat form (<= 94), header 0x2A skill bytes,
    realm data and the ear realm bit, the 8-bit stat 72 (<= 95); f["ver"] is then the save version (no key otherwise)."""
    h = parse_header(b, extended)
    ver = h["version"] if extended else None
    f = dict(header=h, sections=parse_fixed_sections(b))
    if extended:
        f["ver"] = ver
    if ver is not None and ver <= OLD_STATS_MAX:
        f["stats"], p = parse_stats_old(b, HEADER_SIZE, h["stat_slots"])
        f["stats_pad"] = 0
    else:
        f["stats"], p, f["stats_pad"] = parse_stats(b, HEADER_SIZE, isc)
    f["skills"], p = parse_skills(b, p, h["skill_count"] if extended else 30)
    f["skills_end"] = p
    f["items"], p = parse_items(b, p, isc, kinds, ver=ver)
    f["items_end"] = p
    f["corpses"], p = parse_corpses(b, p, isc, kinds, ver)
    f["corpses_end"] = p
    if h["status"] & 0x20:
        if b[p:p + 2] != b"jf":
            raise D2sError("'jf' missing at 0x%X" % p)
        p += 2
        if h["merc_seed"]:
            f["merc_items"], p = parse_items(b, p, isc, kinds, ver=ver)
        f["kf_off"] = p
        if b[p:p + 2] != b"kf":
            raise D2sError("'kf' missing at 0x%X" % p)
        f["golem"] = b[p + 2]
        p += 3
        if f["golem"]:
            it, p = parse_item(b, p, isc, kinds, ver)
            f["golem_item"] = it
    f["end"] = p
    return f


def parse_corpses(b, pos, isc, kinds, ver=None):
    if b[pos:pos + 2] != b"JM":
        raise D2sError("corpse 'JM' missing at 0x%X" % pos)
    n = u16(b, pos + 2)
    p = pos + 4
    corpses = []
    for _ in range(n):
        unk = bytes(b[p:p + 12])
        lst, p = parse_items(b, p + 12, isc, kinds, ver=ver)
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
    nfull = nstub = nitems = leftover = 0
    nextended = nprops = nparam = 0
    nlists = collections.Counter()
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
            nstub += 1
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
        nfull += 1
        leftover += left
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
        for d, w in enumerate(parse_waypoints(b)):
            s["waypoint block (diff, head, bits, tail zero)"][(d, w["head"].hex(), tuple(w["bits"]),
                                                              not any(w["tail"]))] += 1
        for it in all_items(f):
            nitems += 1
            s["item code"][it.get("code", "ear")] += 1
            s["item simple"][it["simple"]] += 1
            s["item quality"][QUALITY.get(it.get("quality"), "-")] += 1
            s["item version (10 bits)"][it["version"]] += 1
            s["item pad value"][it["pad"]] += 1
            s["item pad bit count"][it["pad_bits"]] += 1
            s["item length (bytes), simple"][(it["end"] - it["off"]) if it["simple"] else "-"] += 1
            if "props" in it:
                # every property list: main, then the set bonus lists, then the runeword list
                lists = [("main", it["props"])] + [("set", x) for x in it.get("set_props", [])]
                if "rw_props" in it:
                    lists.append(("runeword", it["rw_props"]))
                nextended += 1
                for kind, lst in lists:
                    nlists[kind] += 1
                    for sid, param, vals in lst:
                        nprops += 1
                        nparam += param is not None
                        s["property ids"][sid] += 1
                        if sid in GROUPS:
                            s["property groups"][sid] += 1
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
    print("property lists               %d over %d extended items (main %d, set bonus %d, runeword %d)"
          % (sum(nlists.values()), nextended, nlists["main"], nlists["set"], nlists["runeword"]))
    print("properties                   %d (%d with a param), %d distinct ids: %s"
          % (nprops, nparam, len(s["property ids"]), ", ".join(map(str, sorted(s["property ids"])))))
    print("property groups              %s" % (", ".join("%d x%d" % kv for kv in s["property groups"].most_common())
                                               or "none"))
    print("saves %d, bad %d" % (len(paths), bad))
    # gate summary (tools/gate.py --full): integer counts only
    print("SURVEY d2s files=%d full=%d stubs=%d errors=%d items=%d leftover_bytes=%d"
          " extended=%d lists=%d lists_set=%d lists_rw=%d props=%d props_param=%d prop_ids=%d %s"
          % (len(paths), nfull, nstub, bad, nitems, leftover,
             nextended, sum(nlists.values()), nlists["set"], nlists["runeword"], nprops, nparam,
             len(s["property ids"]), " ".join("group_%d=%d" % (g, s["property groups"][g]) for g in sorted(GROUPS))))
    return 1 if bad else 0


def dump(excel_dir, path):
    isc, kinds = load_isc(excel_dir), load_kinds(excel_dir)
    b = open(path, "rb").read()
    f = parse(b, isc, kinds)
    for k, v in f["header"].items():
        if k not in ("unk_bf",):
            print("%-14s %r" % (k, v))
    print("sections", f["sections"])
    names = load_wp_names(excel_dir)
    for d, w in enumerate(parse_waypoints(b)):
        print("waypoints %-9s head %s bits %s tail %s" % (DIFFICULTIES[d], w["head"].hex(), w["bits"],
                                                         "zero" if not any(w["tail"]) else w["tail"].hex()))
        for i in w["bits"]:
            print("  wp %2d level %3d %s" % ((i,) + names.get(i, (-1, "?"))))
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


def setstats(excel_dir, src, dst, assigns):
    """Rewrite the whole 'gf' stat list with stats set, added (absent stats) or removed (value 0),
    re-encoded in ascending id order; fix the header level (stat 12), file size and checksum."""
    isc = load_isc(excel_dir)
    b = bytes(open(src, "rb").read())
    parse_header(b)
    stats, end, _ = parse_stats(b, HEADER_SIZE, isc)
    vals = {sid: (param, v) for sid, param, v in stats}
    for sid, value in assigns:
        if sid not in isc or not isc[sid]["csv_bits"]:
            raise D2sError("stat %d is not a character stat (no CSvBits)" % sid)
        if isc[sid]["csv_param"]:
            raise D2sError("stat %d takes a parameter; not supported" % sid)
        if value >> isc[sid]["csv_bits"] or value < 0:
            raise D2sError("stat %d: value does not fit in %d bits" % (sid, isc[sid]["csv_bits"]))
        if value:
            vals[sid] = (None, value)
        else:
            vals.pop(sid, None)
    bits = []

    def put(v, n):
        bits.extend((v >> i) & 1 for i in range(n))
    for sid in sorted(vals):
        param, v = vals[sid]
        put(sid, 9)
        if isc[sid]["csv_param"]:
            put(param, isc[sid]["csv_param"])
        put(v, isc[sid]["csv_bits"])
    put(0x1FF, 9)
    bits.extend([0] * ((-len(bits)) % 8))
    body = bytes(sum(bits[i + j] << j for j in range(8)) for i in range(0, len(bits), 8))
    out = bytearray(b[:HEADER_SIZE] + b"gf" + body + b[end:])
    if 12 in vals:
        out[0x2B] = vals[12][1]
    struct.pack_into("<I", out, 8, len(out))
    struct.pack_into("<I", out, 12, checksum(out))
    open(dst, "wb").write(out)
    print("wrote", dst, "stats %d bytes (was %d), file %d bytes, checksum %08X"
          % (len(body) + 2, end - HEADER_SIZE, len(out), u32(out, 12)))


def parse_wp_list(spec):
    if spec == "all":
        return set(range(WP_COUNT))
    if spec == "none":
        return set()
    out = set()
    for part in spec.split(","):
        a, dash, z = part.partition("-")
        try:
            lo = int(a)
            hi = int(z) if dash else lo
        except ValueError:
            raise D2sError("waypoint %r is not an integer or a range a-b" % part) from None
        if hi < lo:
            raise D2sError("waypoint range %r is reversed or empty" % part)
        out.update(range(lo, hi + 1))
    if any(not 0 <= i < WP_COUNT for i in out):
        raise D2sError("waypoint index outside 0..%d" % (WP_COUNT - 1))
    return out


def setwp(src, dst, difficulty, spec):
    """Replace one difficulty's waypoint bit field with exactly the given bits; fix the checksum."""
    if difficulty in DIFFICULTIES:
        d = DIFFICULTIES.index(difficulty)
    else:
        try:
            d = int(difficulty)
        except ValueError:
            raise D2sError("difficulty %r: use 0|1|2 or normal|nightmare|hell" % difficulty) from None
    if not 0 <= d < 3:
        raise D2sError("difficulty %r" % difficulty)
    b = bytearray(open(src, "rb").read())
    parse_header(b)
    parse_fixed_sections(b)
    if b[WP_OFF + 2:WP_OFF + 8] != b"\x01\x00\x00\x00\x50\x00":
        raise D2sError("unexpected WS version/size")
    field = sum(1 << i for i in parse_wp_list(spec))
    o = wp_field_off(d)
    b[o:o + WP_FIELD_BYTES] = field.to_bytes(WP_FIELD_BYTES, "little")
    struct.pack_into("<I", b, 12, checksum(b))
    open(dst, "wb").write(b)
    print("wrote", dst, "%s field @0x%X = %s checksum %08X" % (DIFFICULTIES[d], o, b[o:o + WP_FIELD_BYTES].hex(), u32(b, 12)))

# ---------------------------------------------------------------- writing (encoders, roundtrip, build)


class BitWriter:
    """LSB-first bit writer, the inverse of Bits. A value that does not fit its width is an error
    (the game clamps, save/0001 § 7; the builder refuses instead, so nothing is silently changed)."""

    def __init__(self):
        self.bits = []

    def write(self, v, n):
        if v < 0 or v >> n:
            raise D2sError("value %d does not fit in %d bits" % (v, n))
        self.bits.extend((v >> i) & 1 for i in range(n))

    def tobytes(self):
        bits = self.bits + [0] * ((-len(self.bits)) % 8)
        return bytes(sum(bits[i + j] << j for j in range(8)) for i in range(0, len(bits), 8))


def encode_stats(stats, isc):
    """'gf' + the character stat list [(id, param, value)] in the given order, 0x1FF, zero padding."""
    w = BitWriter()
    for sid, param, v in stats:
        e = isc[sid]
        if not e["csv_bits"]:
            raise D2sError("character stat %d has no CSvBits" % sid)
        w.write(sid, 9)
        if e["csv_param"]:
            w.write(param, e["csv_param"])
        w.write(v, e["csv_bits"])
    w.write(0x1FF, 9)
    return b"gf" + w.tobytes()


def encode_stats_old(stats, n):
    """The version <= 94 stat form (inverse of parse_stats_old): 'gf', a 2-byte mask over stats 0..n-1, a u32 per
    set bit in id order. A stat at or above n, a param or a value outside the u32 is refused."""
    if n not in OLD_SLOTS:
        raise D2sError("stat_slots %d: the mask width is documented for 9..16 only (2 bytes)" % n)
    vals = {}
    for sid, param, v in stats:
        if sid >= n or param is not None:
            raise D2sError("old stat form: stat %d%s cannot be written with stat_slots %d"
                           % (sid, " (param)" if param is not None else "", n))
        if not 0 <= v < 1 << 32:
            raise D2sError("old stat form: stat %d value %d is not a u32" % (sid, v))
        vals[sid] = v
    mask = sum(1 << s for s in vals)
    return b"gf" + struct.pack("<H", mask) + b"".join(struct.pack("<I", vals[s]) for s in sorted(vals))


def write_realm(w, it, ver):
    """Inverse of read_realm: the flag, then the words (two, three above version 93)."""
    if not it.get("realm", 0):
        w.write(0, 1)
        return
    data = it["realm_data"]
    if len(data) != (3 if ver >= REALM3_MIN else 2):
        raise D2sError("realm data %r: %d words for version %d" % (data, 3 if ver >= REALM3_MIN else 2, ver))
    w.write(1, 1)
    for x in data:
        w.write(x, 32)


def encode_props(w, props, isc):
    """One property list (the inverse of parse_props): [(id, param, [values])], values without Save Add."""
    for sid, param, vals in props:
        e = isc[sid]
        if not e["save_bits"]:
            raise D2sError("item stat %d has no Save Bits" % sid)
        w.write(sid, 9)
        if e["param_bits"]:
            w.write(param, e["param_bits"])
        if len(vals) != GROUPS.get(sid, 1):
            raise D2sError("stat %d takes %d values, got %r" % (sid, GROUPS.get(sid, 1), vals))
        for k, v in enumerate(vals):
            ek = isc[sid + k]
            w.write(v + ek["save_add"], ek["save_bits"])
    w.write(0x1FF, 9)


def write_name7(w, name):
    for c in name:
        w.write(ord(c), 7)
    w.write(0, 7)


def encode_item(it, isc, kinds, ver=None):
    """One item record, the inverse of parse_item: takes the dict parse_item returns (or one built
    with the same keys) and gives the bytes from 'JM' to the end of the item's last byte. ver as parse_item's."""
    w = BitWriter()
    w.write(0x4D4A, 16)  # 'J', 'M'
    f = it["flags"]
    w.write(f, 32)
    w.write(it["version"], 10)
    for k, n in (("location", 3), ("body", 4), ("x", 4), ("y", 4), ("store", 3)):
        w.write(it[k], n)
    if f >> 16 & 1:
        w.write(it["ear_class"], 3)
        w.write(it["ear_level"], 7)
        write_name7(w, it["ear_name"])
        if ver is not None:
            write_realm(w, it, ver)
        return w.tobytes()
    code = it["code"].ljust(4)
    for c in code:
        w.write(ord(c), 8)
    c3 = code.strip()
    if f >> 21 & 1:
        if c3 == "gld":
            big = it.get("gold_big", int(it["gold"] > 4095))
            w.write(big, 1)
            w.write(it["gold"], 32 if big else 12)
        if kinds.get(c3 + "#qdc"):
            w.write(it["quest_diff"], isc[356]["save_bits"])
        if ver is not None:
            write_realm(w, it, ver)
        else:
            w.write(it.get("realm", 0), 1)
        return w.tobytes()
    w.write(it.get("n_filled", 0), 3)
    w.write(it["seed"], 32)
    w.write(it["ilvl"], 7)
    q = it["quality"]
    w.write(q, 4)
    w.write(it["has_gfx"], 1)
    if it["has_gfx"]:
        w.write(it["gfx"], 3)
    w.write(it["has_class"], 1)
    if it["has_class"]:
        w.write(it["class_affix"], 11)
    if q in (1, 3):
        w.write(it["qdata"], 3)
    elif q == 4:
        w.write(it["prefix"], 11)
        w.write(it["suffix"], 11)
    elif q in (5, 7):
        w.write(it["qid"], 12)
    elif q in (6, 8):
        w.write(it["names"][0], 8)
        w.write(it["names"][1], 8)
        for a in it["affixes"]:
            w.write(a is not None, 1)
            if a is not None:
                w.write(a, 11)
    elif q != 2:
        raise D2sError("quality %d" % q)
    if c3 in ("tbk", "ibk"):
        w.write(it["tome"], 5)
    if f >> 26 & 1:
        w.write(it["rw"][0], 12)
        w.write(it["rw"][1], 4)
    if f >> 24 & 1:
        write_name7(w, it["pname"])
    if ver is not None:
        write_realm(w, it, ver)
    else:
        w.write(it.get("realm", 0), 1)
    kind = kinds.get(c3)
    if kind == "armor":
        w.write(it["defense"] + isc[31]["save_add"], isc[31]["save_bits"])
    if kind in ("armor", "weapon"):
        w.write(it["maxdur"], isc[73]["save_bits"])
        if it["maxdur"]:
            w.write(it["dur"], 8 if ver is not None and ver <= DUR8_MAX else isc[72]["save_bits"])
    if kinds.get(c3 + "#stack"):
        w.write(it["quantity"], 9)
    if f >> 11 & 1:
        w.write(it["sockets"], 4)
    if q == 5:
        w.write(it["set_lists"], 5)
    encode_props(w, it["props"], isc)
    for lst in it.get("set_props", []) if q == 5 else ():
        encode_props(w, lst, isc)
    if f >> 26 & 1:
        encode_props(w, it["rw_props"], isc)
    return w.tobytes()


def encode_items(items, isc, kinds, tag=b"JM", ver=None):
    """An item list: tag, u16 count of top-level items (those without 'parent'), then every record."""
    count = sum(1 for it in items if "parent" not in it)
    return tag + struct.pack("<H", count) + b"".join(encode_item(it, isc, kinds, ver) for it in items)


def finish(out):
    """Fix file_size and checksum of a whole save image."""
    out = bytearray(out)
    struct.pack_into("<I", out, 8, len(out))
    struct.pack_into("<I", out, 12, checksum(out))
    return bytes(out)


def roundtrip(excel_dir, paths):
    """Re-encode every full save from its parsed form and compare byte for byte: each item record on
    its own (main list, corpses, mercenary, golem), and the file rebuilt from the 765-byte head, the
    encoded stats, the skills, the encoded main item list and the bytes from the corpse list on."""
    isc, kinds = load_isc(excel_dir), load_kinds(excel_dir)
    nfiles = nitems = bad_items = bad_files = 0
    for path in paths:
        b = open(path, "rb").read()
        if stub_check(b):
            continue
        f = parse(b, isc, kinds)
        nfiles += 1
        for it in all_items(f):
            nitems += 1
            enc = encode_item(it, isc, kinds)
            end = it.get("end", it["off"] + len(enc))  # the golem item carries no 'end'
            if enc != b[it["off"]:end]:
                bad_items += 1
                print("ITEM DIFF", os.path.basename(path), "at 0x%X" % it["off"], it.get("code"))
        rebuilt = (b[:HEADER_SIZE] + encode_stats(f["stats"], isc) + b"if" + bytes(f["skills"])
                   + encode_items(f["items"]["items"], isc, kinds) + b[f["items_end"]:])
        if finish(rebuilt) != b:
            bad_files += 1
            print("FILE DIFF", os.path.basename(path))
    print("SURVEY d2s_roundtrip files=%d items=%d item_diffs=%d file_diffs=%d"
          % (nfiles, nitems, bad_items, bad_files))
    return 1 if bad_items or bad_files else 0


def load_txt(excel_dir, name):
    """(column -> index, data rows) of an excel .txt table."""
    text = open(os.path.join(excel_dir, name), encoding="latin1").read()
    rows = [l.rstrip("\r").split("\t") for l in text.split("\n") if l.strip("\r")]
    ix = {c: i for i, c in enumerate(rows[0])}
    return ix, rows[1:]


def cell(ix, r, c):
    return r[ix[c]].strip() if c in ix and ix[c] < len(r) else ""


class Tables:
    """The excel rows the builder reads, by name."""

    def __init__(self, excel_dir):
        self.isc, self.kinds = load_isc(excel_dir), load_kinds(excel_dir)
        self.isc_by_name = {e["name"]: sid for sid, e in self.isc.items()}
        ix, rows = load_txt(excel_dir, "uniqueitems.txt")
        # record index = data row index with the 'Expansion' marker row dropped (UniqueItems.md)
        self.uniques = {}
        for rec, r in enumerate(r for r in rows if r[ix["index"]] != "Expansion"):
            name = r[ix["index"]]
            self.uniques.setdefault(name, []).append((rec, {c: cell(ix, r, c) for c in ix}))
        ix, rows = load_txt(excel_dir, "magicsuffix.txt")
        # record index = data row index with the 'Expansion' marker row dropped (MagicPrefix.md); a save stores
        # the suffix record index as is (d2s.md: suffix 277 = 'of Wealth', item_goldbonus)
        self.suffixes = [{c: cell(ix, r, c) for c in ix} for r in rows if r[ix["Name"]] != "Expansion"]
        ix, rows = load_txt(excel_dir, "magicprefix.txt")
        self.prefixes = [{c: cell(ix, r, c) for c in ix} for r in rows if r[ix["Name"]] != "Expansion"]
        ix, rows = load_txt(excel_dir, "setitems.txt")
        # record index = data row index with the 'Expansion' marker row dropped (SetItems.md, [C])
        self.setitems = {}
        for rec, r in enumerate(r for r in rows if r[ix["index"]] != "Expansion"):
            self.setitems.setdefault(r[ix["index"]], []).append((rec, {c: cell(ix, r, c) for c in ix}))
        ix, rows = load_txt(excel_dir, "properties.txt")
        self.props = {}
        for r in rows:
            slots = []
            for k in range(1, 8):
                if cell(ix, r, "func%d" % k):
                    slots.append(dict(func=int(cell(ix, r, "func%d" % k)), stat=cell(ix, r, "stat%d" % k),
                                      val=cell(ix, r, "val%d" % k)))
            self.props[r[ix["code"]]] = slots
        ix, rows = load_txt(excel_dir, "skills.txt")
        self.skills = {r[ix["skill"]]: dict(id=int(r[ix["Id"]]), cls=cell(ix, r, "charclass")) for r in rows}
        self.class_skills = {}
        for r in rows:  # the class's skills in file order (docs/formats/d2s.md § Skills, [L])
            if cell(ix, r, "charclass"):
                self.class_skills.setdefault(cell(ix, r, "charclass"), []).append(r[ix["skill"]])
        self.base = {}
        for t in ("armor", "weapons", "misc"):
            ix, rows = load_txt(excel_dir, t + ".txt")
            for r in rows:
                if cell(ix, r, "code"):
                    self.base[cell(ix, r, "code")] = {c: cell(ix, r, c) for c in ix}
        ix, rows = load_txt(excel_dir, "itemtypes.txt")
        self.types = {cell(ix, r, "Code"): {c: cell(ix, r, c) for c in ix} for r in rows if cell(ix, r, "Code")}
        ix, rows = load_txt(excel_dir, "belts.txt")
        self.belts = [int(cell(ix, r, "numboxes")) for r in rows if r[0] != "Expansion"]
        ix, rows = load_txt(excel_dir, "hireling.txt")
        self.hirelings = [{c: cell(ix, r, c) for c in ix} for r in rows]
        self.excel_dir = excel_dir
        ix, rows = load_txt(excel_dir, "bodylocs.txt")
        self.bodylocs = {cell(ix, r, "Code"): i for i, r in enumerate(rows) if cell(ix, r, "Code")}
        ix, rows = load_txt(excel_dir, "experience.txt")
        self.experience = {r[0]: r for r in rows}
        self.exp_cols = ix

    def unique(self, name):
        rows = [x for x in self.uniques.get(name, []) if x[1]["enabled"] == "1"]
        if len(rows) != 1:
            raise D2sError("unique %r: %d enabled rows" % (name, len(rows)))
        return rows[0]

    def setitem(self, name):
        rows = self.setitems.get(name, [])
        if len(rows) != 1:
            raise D2sError("set item %r: %d rows" % (name, len(rows)))
        return rows[0]

    def stat_id(self, name):
        if name not in self.isc_by_name:
            raise D2sError("itemstatcost has no stat %r" % name)
        return self.isc_by_name[name]


def unique_stats(tables, row, pick="max", base=None):
    """The (id, param) -> value map of a unique's prop1..12 at their max (or min), through the
    properties.txt stat slots. Supported funcs: 1, 2, 3, 8 (value), 15 / 16 (min / max of the row into
    two stats), 11 (skill on an event), 17 (par as the value), 19 (charged skill), 21 (param = the
    slot's val). Anything else
    is an error: the builder does not guess. Func 7 with no stat (dmg%) is read as stats 17 and 18."""
    out = {}

    def add(sid, param, v):
        key = (sid, param)
        out[key] = out.get(key, 0) + v
    for k in range(1, 13):
        code = row.get("prop%d" % k, "")
        if not code:
            continue
        par, lo, hi = row["par%d" % k], row["min%d" % k], row["max%d" % k]
        lo = int(lo) if lo else None
        hi = int(hi) if hi else None
        v = (hi if pick == "max" else lo) if (lo is not None and hi is not None) else (lo if lo is not None else hi)
        slots = tables.props.get(code)
        if not slots:
            raise D2sError("property %r: not in properties.txt or no stat slot" % code)
        prev = None
        for s in slots:
            fn = s["func"]
            sid = tables.stat_id(s["stat"]) if s["stat"] else None
            if fn in (1, 2, 8):
                add(sid, None, v)
                prev = v
            elif fn == 3:
                add(sid, None, prev)
            elif fn == 7 and sid is None:
                # dmg%: no stat named; Biggin's Bonnet (qitsor) stores dmg% 30 as group 17 = [30, 30]
                add(17, None, v)
                add(18, None, v)
            elif fn == 15:
                add(sid, None, lo)
            elif fn == 16:
                add(sid, None, hi)
            elif fn == 17:
                add(sid, None, int(par))
            elif fn == 19:
                skill = tables.skills.get(par) or ({"id": int(par)} if par.isdigit() else None)
                if skill is None:
                    raise D2sError("property %r: skill %r not in skills.txt" % (code, par))
                # param = skill id << 6 | skill level (max column); value = charges << 8 | charges
                # (min column), as the samples' stats 201/204 decode ([L], see d2s.md § tools)
                add(sid, skill["id"] << 6 | hi, lo << 8 | lo)
            elif fn == 11:
                skill = tables.skills.get(par) or ({"id": int(par)} if par.isdigit() else None)
                if skill is None:
                    raise D2sError("property %r: skill %r not in skills.txt" % (code, par))
                # skill on an event (hit-skill, gethit-skill...): param = skill id << 6 | skill level
                # (max column), value = chance % (min column), the same param packing as func 19 ([L])
                add(sid, skill["id"] << 6 | hi, lo)
            elif fn == 21:
                add(sid, int(s["val"]), v)
            elif fn in (5, 6) and base is not None:
                # plan 0041 Phase 2: E1 of items/properties (min / max damage by base column; the clamp is not
                # reached on stock data)
                cols = (("mindam", "2handmindam", "minmisdam"), ("maxdam", "2handmaxdam", "maxmisdam"))[fn - 5]
                b1, b2 = (int(base.get(c) or 0) for c in cols[:2])
                weapon = base.get("_kind") == "weapon"
                s1, s2, st = (21, 23, 159) if fn == 5 else (22, 24, 160)
                if not (weapon and b1 == 0 and b2 != 0):
                    add(s1, None, v)
                if not (weapon and b2 == 0 and b1 != 0):
                    add(s2, None, v)
                if not (weapon and base.get("throwable", "") != "1"):
                    add(st, None, v)
                prev = v
            elif fn == 20:
                # items/properties E: AddStat(list, 152, 0, 1) (indestructible)
                add(152, None, 1)
            elif fn == 22:
                # items/properties E: W(stat, (u16) par, v), par a skill (by name or id): Azurewrath's aura
                skill = tables.skills.get(par) or ({"id": int(par)} if par.isdigit() else None)
                if skill is None:
                    raise D2sError("property %r: skill %r not in skills.txt" % (code, par))
                add(sid, skill["id"] & 0xFFFF, v)
                prev = v
            elif fn == 10:
                # E of items/properties: param = par mod 3 + (par div 3) x 8 (class in bits 3.., tab in 0..1)
                pv = int(par)
                add(sid, pv % 3 + (pv // 3) * 8, v)
                prev = v
            elif fn == 14:
                # 'sock': the builder takes the socket count from the recipe's "sockets" key (flags bit 11 and the
                # 4-bit field), as the game's E5 sets it; no property entry
                pass
            else:
                raise D2sError("property %r: func %d has no known value rule" % (code, fn))
    return out


def props_list(stats, lone_follower=False):
    """(id, param) -> value map to a property list in ascending (id, param) order, the order of every
    sample list; a group head takes its followers' values and the followers get no entry. A follower without
    its head is refused, unless lone_follower (the test-state item key "lone_follower": true): then it gets an
    entry of its own, its id and its own Save Bits, which no stock builder writes."""
    followers = {h + k: h for h, n in GROUPS.items() for k in range(1, n)}
    out = []
    for (sid, param), v in sorted(stats.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)):
        if sid in followers:
            if (followers[sid], None) not in stats:
                if lone_follower:
                    out.append((sid, param, [v]))
                    continue
                raise D2sError("stat %d without its group head %d (give \"lone_follower\": true to write it "
                               "alone, a test state)" % (sid, followers[sid]))
            continue
        vals = [v] + [stats.get((sid + k, None), 0) for k in range(1, GROUPS.get(sid, 1))]
        out.append((sid, param, vals))
    return out


def check_unique(tables, it):
    """Compare a unique item's main property list with its UniqueItems row: same (id, param) set and
    every value within [min, max]. Returns a list of problems (empty = match)."""
    rows = [r for name, lst in tables.uniques.items() for rec, r in lst if rec == it["qid"]]
    if not rows:
        return ["unique id %d has no record" % it["qid"]]
    lo, hi = unique_stats(tables, rows[0], "min"), unique_stats(tables, rows[0], "max")
    got = {}
    for sid, param, vals in it["props"]:
        for k, v in enumerate(vals):
            got[(sid + k, param if k == 0 else None)] = v
    problems = []
    for key in sorted(set(lo) | set(got), key=lambda k: (k[0], k[1] or 0)):
        if key not in got or key not in lo:
            problems.append("%r: table %r, item %r" % (key, lo.get(key), got.get(key)))
        elif not min(lo[key], hi[key]) <= got[key] <= max(lo[key], hi[key]):
            problems.append("%r: %d outside %d..%d" % (key, got[key], lo[key], hi[key]))
    return problems


def checkuniq(excel_dir, paths):
    t = Tables(excel_dir)
    bad = 0
    for path in paths:
        b = open(path, "rb").read()
        if stub_check(b):
            continue
        for it in all_items(parse(b, t.isc, t.kinds)):
            if it.get("quality") != 7:
                continue
            name = [n for n, lst in t.uniques.items() for rec, r in lst if rec == it["qid"]]
            p = check_unique(t, it)
            bad += bool(p)
            print("%s %s unique %d %s: %s" % (os.path.basename(path), it["code"].strip(), it["qid"],
                                              name[0] if name else "?", "ok" if not p else "; ".join(p)))
    return 1 if bad else 0


FLAG_IDENTIFIED, FLAG_SOCKETED, FLAG_SIMPLE, FLAG_23 = 1 << 4, 1 << 11, 1 << 21, 1 << 23
FLAG_ETHEREAL = 1 << 22
FLAG_BROKEN = 1 << 8
SWAP_BODIES = {"rarm2": 11, "larm2": 12}
LOCATIONS = {"stored": 0, "equipped": 1, "belt": 2, "socketed": 6}
STORES = {"inventory": 1, "cube": 4, "stash": 5}
QUALITIES = {"low": 1, "normal": 2, "superior": 3, "rare": 6, "crafted": 8}


def new_item(t, spec, rng):
    """An item dict for encode_item from a recipe entry (see build)."""
    if "rare" in spec and "crafted" in spec:
        raise D2sError("item %r: rare or crafted, not both" % spec)
    crafted = "crafted" in spec
    if sum(k in spec for k in ("unique", "set")) + ("suffix" in spec or "prefix" in spec or "rare" in spec
                                                      or crafted) > 1:
        raise D2sError("item %r: one of unique, set, or prefix / suffix / rare / crafted" % spec)
    if "prefix" in spec and "rare" in spec:
        raise D2sError("item %r: prefix goes with a magic item, not rare" % spec)
    rare = spec.get("crafted") if crafted else spec.get("rare")
    if rare is not None and (not isinstance(rare, list) or len(rare) != 2
                             or not all(isinstance(n, int) and 0 <= n < 256 for n in rare)):
        raise D2sError("item %r: rare / crafted must be [name1, name2], two 8-bit name ids" % spec)
    if "unique" in spec:
        rec, row = t.unique(spec["unique"])
        code = row["code"]
    elif "set" in spec:
        # plan 0041 Phase 2: a set item; prop1..9 to the main list, aprop1a..5b to the set lists (add func 1, 2:
        # pair k -> list k - 1, set_lists bit k - 1) or to the main list (add func 0 / blank), items/0006 § 2 [C]
        rec, row = t.setitem(spec["set"])
        code = row["item"]
    elif "suffix" in spec or "prefix" in spec:
        rec, code = spec.get("suffix", 0), spec["code"]
        pre = spec.get("prefix", 0)
        if "suffix" in spec and (not isinstance(rec, int) or not 1 <= rec < len(t.suffixes)):
            raise D2sError("suffix %r: not a magicsuffix record index 1..%d" % (rec, len(t.suffixes) - 1))
        if "prefix" in spec and (not isinstance(pre, int) or not 1 <= pre < len(t.prefixes)):
            raise D2sError("prefix %r: not a magicprefix record index 1..%d" % (pre, len(t.prefixes) - 1))
        # the affix rows' mod1..3 read as a unique row's prop/par/min/max (same properties.txt funcs); the prefix's
        # mods first (props 1..3), then the suffix's (4..6)
        row = {}
        for base_k, aff in ((0, t.prefixes[pre] if pre else None), (3, t.suffixes[rec] if rec else None)):
            for n in (1, 2, 3):
                for k, m in (("prop", "code"), ("par", "param"), ("min", "min"), ("max", "max")):
                    row["%s%d" % (k, base_k + n)] = aff.get("mod%d%s" % (n, m), "") if aff else ""
        row["magic"] = True
        row["prefix"] = pre
    elif rare is not None:
        rec, row, code = None, {"rare": True}, spec["code"]
    else:
        rec, row, code = None, None, spec["code"]
    base = t.base.get(code)
    if base is None:
        raise D2sError("item code %r not in weapons/armor/misc" % code)
    simple = base.get("compactsave") == "1"
    it = dict(flags=FLAG_IDENTIFIED | FLAG_23 | (FLAG_SIMPLE if simple else 0), version=101,
              code=code.ljust(4), body=0, x=0, y=0, store=0, realm=0)
    if "realm" in spec:
        # test state (backlog 2026-10-27 H1a gaps): the realm flag 1 and its words, two, or three for a save
        # version above 93 (d2s.md § Realm data); the game writes the third as 0
        rd = spec["realm"]
        if not (isinstance(rd, list) and len(rd) in (2, 3)
                and all(isinstance(x, int) and 0 <= x < 1 << 32 for x in rd)):
            raise D2sError("item %r: realm must be [u32, u32] or [u32, u32, u32]" % spec)
        it.update(realm=1, realm_data=list(rd))
    if "equip" in spec:  # a bodylocs.txt Code; x = the body slot in every equipped sample item
        # "rarm2" / "larm2": the weapon-switch hands, body 11 and 12 (not in bodylocs.txt; [L] community save
        # layouts, plan 0041 Phase 2 checks them in the run)
        body = SWAP_BODIES[spec["equip"]] if spec["equip"] in SWAP_BODIES else t.bodylocs[spec["equip"]]
        it.update(location=1, body=body, x=body)
    elif "belt_slot" in spec:  # belt slot 0..15 in x, y 0, as the samples' potions
        it.update(location=2, x=spec["belt_slot"])
    elif spec.get("store") in STORES:
        it.update(location=0, store=STORES[spec["store"]], x=spec["x"], y=spec["y"])
    else:
        raise D2sError("item %r: give equip, belt_slot or store (inventory|cube) with x, y" % spec)
    if simple:
        if row is not None:
            raise D2sError("%r is a simple item, it can't be unique" % code)
        if t.kinds.get(code + "#qdc"):
            # a simple quest item with questdiffcheck carries stat 356 (d2s.md § Simple items); its value is
            # given, not guessed: what the game writes there (a difficulty?) is [L]
            qd, nb = spec.get("quest_diff"), t.isc[356]["save_bits"]
            if not (isinstance(qd, int) and 0 <= qd < 1 << nb):
                raise D2sError("item %r: a simple quest item (questdiffcheck) needs \"quest_diff\": 0..%d (stat 356)"
                               % (code, (1 << nb) - 1))
            it["quest_diff"] = qd
        return it
    kind = t.kinds.get(code)
    quality = (2 if row is None else (8 if crafted else 6) if rare is not None else 4 if row.get("magic")
               else 5 if "set" in spec else 7)
    it.update(n_filled=0, seed=spec.get("seed", rng.getrandbits(32)), ilvl=spec.get("ilvl", 99),
              quality=quality, has_class=0, class_affix=None)
    if "quality" in spec:
        # a test state for plan 0029 Phase 2: the quality byte with empty quality fields (no affixes, no
        # QualityItems mods); the base stats stay the normal ones
        if row is not None:
            raise D2sError("item %r: quality goes with a plain code, not with unique or suffix" % spec)
        q = QUALITIES.get(spec["quality"])
        if q is None:
            raise D2sError("item %r: quality %r, one of %s" % (spec, spec["quality"], ", ".join(QUALITIES)))
        it["quality"] = q
        if q in (1, 3):
            it["qdata"] = spec.get("qdata", 0)
        elif q in (6, 8):
            it["names"] = tuple(spec.get("names", (160, 121)))
            it["affixes"] = [None] * 6
    if spec.get("identified", True) is False:
        it["flags"] &= ~FLAG_IDENTIFIED
    if spec.get("ethereal"):
        # flags bit 22 (d2s.md); the game's builders make ethereal items only from bases without nodurability and
        # with a non-zero durability (items/0006 § 6, [I]); refused otherwise
        if kind not in ("armor", "weapon") or base.get("nodurability") == "1":
            raise D2sError("item %r: ethereal needs an armor or weapon base with durability" % spec)
        it["flags"] |= FLAG_ETHEREAL
    var = int(t.types.get(base["type"], {}).get("VarInvGfx") or 0)
    it["has_gfx"] = int(var > 0)
    it["gfx"] = spec.get("gfx", it["seed"] % var) if var else None
    if rare is not None:
        # names as stored (name1 = RarePrefix row + 156, d2s.md [I]); affix slots prefix, suffix, ... alternately:
        # the suffix, if given, goes in slot 1 (the first suffix slot) and its mod lines become the properties
        it["names"] = tuple(rare)
        # crafted (plan 0043 Phase 2b): quality 8 with the same fields; a "prefix" fills slot 0
        it["affixes"] = [(row.get("prefix") or None) if row.get("magic") else None,
                         (rec or None) if row.get("magic") else None, None, None, None, None]
        stats = unique_stats(t, row, spec.get("roll", "max")) if row.get("magic") else {}
    elif row is not None and "set" in spec:
        it["qid"] = rec
        pick = spec.get("roll", "max")
        main = {k: v for k, v in row.items() if not k.startswith(("prop", "par", "min", "max"))}
        for n in range(1, 10):
            for k in ("prop", "par", "min", "max"):
                main["%s%d" % (k, n)] = row.get("%s%d" % (k, n), "")
        stats = unique_stats(t, main, pick, dict(base, _kind=kind))
        func = int(row.get("add func") or 0)
        lists = []
        for k in range(1, 6):
            pair = {}
            for j, ab in enumerate("ab"):
                for c, a in (("prop", "aprop"), ("par", "apar"), ("min", "amin"), ("max", "amax")):
                    pair["%s%d" % (c, j + 1)] = row.get("%s%d%s" % (a, k, ab), "")
            ps = unique_stats(t, pair, pick, dict(base, _kind=kind))
            if not ps:
                lists.append(None)
                continue
            if func == 0:
                for key, v in ps.items():
                    stats[key] = stats.get(key, 0) + v
                lists.append(None)
            else:
                lists.append(ps)
        it["set_lists"] = sum(1 << k for k, ps in enumerate(lists) if ps)
        it["set_props"] = [props_list(ps) for ps in lists if ps]
    elif row is not None:
        if row.get("magic"):
            it["prefix"], it["suffix"] = row.get("prefix", 0), rec
        else:
            it["qid"] = rec
        stats = unique_stats(t, row, spec.get("roll", "max"), dict(base, _kind=kind))
    else:
        stats = {}
    for k, v in spec.get("item_stats", {}).items():
        # test-state key (plan 0030 Phase 2): extra entries of the item's property list, {stat id: value}, e.g. stat
        # 356 (questitemdifficulty) on an extended quest item such as Wirt's Leg
        stats[(int(k), None)] = v
    # test-state key (backlog 2026-10-27, plan 0038 batch H1b row 124): a group follower (e.g. 49 fire-max) with no
    # head is written alone, with its own id and Save Bits, so the reader meets a follower read by itself
    it["props"] = props_list(stats, lone_follower=bool(spec.get("lone_follower")))
    if kind == "armor":
        # base defense: maxac, and maxac + 1 when the item has enhanced defense (stat 16), as every
        # sample with stat 16 stores it (Hand of Broc gloves 4 of 2..3, rare chain mail 76 of 72..75)
        it["defense"] = int(base["maxac"]) + (1 if (16, None) in stats else 0)
    if kind in ("armor", "weapon"):
        it["maxdur"] = 0 if base.get("nodurability") == "1" else int(base["durability"])
        if it["maxdur"]:
            # current = the full maximum: base + flat stat 73 + base * stat 75 %, as the superior
            # long sword of qitnec stores it (44 + 12 % = 49)
            it["dur"] = (it["maxdur"] + stats.get((73, None), 0)
                         + it["maxdur"] * stats.get((75, None), 0) // 100)
            if "dur" in spec:
                # test-state key (plan 0043 Phase 2): a damaged item, current durability 0..full maximum (a broken
                # item at 0 keeps the broken flag clear: the game sets it, the builder does not)
                d = spec["dur"]
                if not isinstance(d, int) or not 0 <= d <= it["dur"]:
                    raise D2sError("item %r: dur %r, 0..%d (the full maximum)" % (code, d, it["dur"]))
                it["dur"] = d
            if spec.get("broken"):
                # test-state key (plan 0043 Phase 2b): flags bit 8, the broken flag ItemData+0x18 0x100 the game sets
                # when an armour's durability reaches 0 (items/0011 § 7); only with "dur": 0
                if spec.get("dur") != 0:
                    raise D2sError("item %r: broken needs \"dur\": 0" % spec)
                it["flags"] |= FLAG_BROKEN
    if spec.get("broken") and not it.get("maxdur"):
        raise D2sError("item %r: broken needs an armor or weapon base with durability" % spec)
    if "dur" in spec and not it.get("maxdur"):
        raise D2sError("item %r: dur needs an armor or weapon base with durability" % spec)
    if code in ("tbk", "ibk"):
        # the 5-bit tome field of a normal-quality book (d2s.md); 0 in the one sample tome (qitdru tbk)
        it["tome"] = spec.get("tome", 0)
    if t.kinds.get(code + "#stack"):
        it["quantity"] = spec.get("quantity", int(base.get("maxstack") or 1))
    if "sockets" in spec:
        n, cap = spec["sockets"], max_sockets(t, base, it["ilvl"])
        if not isinstance(n, int) or not 1 <= n <= cap:
            raise D2sError("item %r: sockets %r, this base at ilvl %d takes 1..%d (min(6, invwidth x invheight, "
                           "gemsockets, MaxSock by ilvl), items/properties F5-F6)" % (code, n, it["ilvl"], cap))
        qcap = SOCKET_QUALITY_CAP.get(it["quality"])
        if qcap is not None and n > qcap and not spec.get("unclamped_sockets"):
            raise D2sError("item %r: sockets %d on a %s item; ITEMS_SetSockets clamps that quality to %d "
                           "(items/0007: magic 4, rare 2, crafted 3). Give \"unclamped_sockets\": true to build "
                           "it anyway" % (code, n, QUALITY[it["quality"]], qcap))
        it["flags"] |= FLAG_SOCKETED
        it["sockets"] = n
    return it


# The quality clamp of ITEMS_SetSockets (docs/findings/items/0007-sockets-runewords.md): magic 4, rare 2, crafted and
# quality 9 at 3. The game applies it when an item is given sockets, not when a save is loaded, so a build above it is
# an item the game would never make; build refuses one unless the item says "unclamped_sockets": true.
SOCKET_QUALITY_CAP = {4: 4, 6: 2, 8: 3, 9: 3}


def max_sockets(t, base, ilvl):
    """What ITEMS_SetSockets lets a base hold (docs/specs/items/properties.md F5, F6): min(6, invwidth x invheight,
    gemsockets, the item type's MaxSock1 for ilvl <= 25, MaxSock25 for ilvl <= 40, else MaxSock40)."""
    ty = t.types.get(base["type"], {})
    col = "MaxSock1" if ilvl <= 25 else "MaxSock25" if ilvl <= 40 else "MaxSock40"
    return min(6, int(base.get("invwidth") or 1) * int(base.get("invheight") or 1),
               int(base.get("gemsockets") or 0), int(ty.get(col) or 0))


def is_socket_filler(t, code):
    """True when the item's type reaches `sock` (Socket Filler: gems, runes, jewels) through itemtypes Equiv1/2."""
    todo, seen = [t.base[code]["type"]], set()
    while todo:
        c = todo.pop()
        if c == "sock":
            return True
        if c and c not in seen and c in t.types:
            seen.add(c)
            todo += [t.types[c].get("Equiv1", ""), t.types[c].get("Equiv2", "")]
    return False


def new_group(t, spec, rng):
    """A recipe item and, when it has "filled", its socketed children: [parent, child, ...]. Each child is an item
    spec without a placement ({"code": "gsv"}, {"code": "jew", "suffix": 371}, ...); it is written after the parent
    as save/0001 § 6 states, with location 6 (socketed), x = its socket index (0, 1, ...), y = body = store = 0, as
    the socketed runes of the qitbarb sample are (docs/formats/d2s.md)."""
    filled = spec.get("filled", [])
    if filled and "sockets" not in spec:
        raise D2sError("item %r: \"filled\" needs \"sockets\"" % spec.get("code", spec.get("unique")))
    parent = new_item(t, {k: v for k, v in spec.items() if k != "filled"}, rng)
    if len(filled) > parent.get("sockets", 0):
        raise D2sError("item %r: %d filled items, %d sockets" % (parent["code"].strip(), len(filled), parent["sockets"]))
    group = [parent]
    for k, cs in enumerate(filled):
        if any(key in cs for key in ("equip", "belt_slot", "store", "x", "y", "sockets", "filled")):
            raise D2sError("filled item %r: no placement or sockets of its own" % cs)
        code = cs.get("code") or t.unique(cs["unique"])[1]["code"]
        if code not in t.base or not is_socket_filler(t, code):
            raise D2sError("filled item %r: not a socket filler (gem, rune or jewel: item type reaching sock)" % code)
        child = new_item(t, dict(cs, store="inventory", x=0, y=0), rng)
        child.update(location=LOCATIONS["socketed"], store=0, x=k, y=0, body=0, parent=None)
        group.append(child)
    parent["n_filled"] = len(filled)
    return group


STORE_NAMES = {1: "inventory", 4: "cube", 5: "stash"}


def check_layout(items, sizes):
    """Refuse a top-level item list where two items share space: overlapping grid rectangles in one
    storage page (location 0, same store; an item covers x..x+invwidth-1, y..y+invheight-1), two items in
    one belt slot (location 2, same x) or two in one equipped body slot (location 1, same body).
    sizes: item code -> (invwidth, invheight). The game does not honour a covered item, without a word: two
    kept base-save scrolls once covered two charms, whose stats were then missing (run:2026-10-14-uniques)."""
    def name(it):
        return "%s at %s" % (it.get("code", "ear").strip(),
                             {0: "(%d, %d)" % (it["x"], it["y"]), 1: "body %d" % it["body"],
                              2: "belt slot %d" % it["x"]}.get(it["location"], "location %d" % it["location"]))
    problems = []
    cells, slots = {}, {}
    for it in items:
        if "parent" in it:
            continue
        loc = it["location"]
        if loc == 0:
            code = it.get("code", "").strip()
            if code not in sizes:
                raise D2sError("item %r: no inventory size (invwidth/invheight)" % code)
            w, h = sizes[code]
            page = STORE_NAMES.get(it["store"], "store %d" % it["store"])
            hits = {}  # other item's id -> (other, first shared cell), one report per pair
            for x in range(it["x"], it["x"] + w):
                for y in range(it["y"], it["y"] + h):
                    other = cells.setdefault((it["store"], x, y), it)
                    if other is not it:
                        hits.setdefault(id(other), (other, x, y))
            for other, x, y in hits.values():
                problems.append("%s: %s overlaps %s at cell (%d, %d)" % (page, name(it), name(other), x, y))
        elif loc in (1, 2):
            key = (loc, it["body"] if loc == 1 else it["x"])
            other = slots.setdefault(key, it)
            if other is not it:
                problems.append("%s and %s share a slot" % (name(it), name(other)))
    if problems:
        raise D2sError("items share space (the game does not honour a covered item):\n  " + "\n  ".join(problems))


def item_sizes(t):
    """item code -> (invwidth, invheight) from weapons/armor/misc."""
    return {code: (int(r.get("invwidth") or 1), int(r.get("invheight") or 1)) for code, r in t.base.items()}


QUEST_WORD_COUNT = 48      # 96-byte record per difficulty (save/0002)


def quest_word_off(d, q):
    """File offset of quest word q (0..47) of difficulty d: the record of block d at 0x159 + 0x60 d (save/0002)."""
    return QUEST_OFF + 10 + 0x60 * d + 2 * q


def quest_bits_spec(q, spec):
    """(bits to set, bits to clear) of one quest_bits entry; refuses bad words, bits and a bit in both lists."""
    if not (str(q).isdigit() and 0 <= int(q) < QUEST_WORD_COUNT):
        raise D2sError("quest_bits: word %r, want 0..%d" % (q, QUEST_WORD_COUNT - 1))
    if isinstance(spec, list):
        st, cl = spec, []
    elif isinstance(spec, dict) and set(spec) <= {"set", "clear"}:
        st, cl = spec.get("set", []), spec.get("clear", [])
    else:
        raise D2sError("quest_bits: word %s: give a list of bits or {\"set\": [...], \"clear\": [...]}" % q)
    for x in st + cl:
        if not (isinstance(x, int) and 0 <= x < 16):
            raise D2sError("quest_bits: word %s: bit %r, want 0..15" % (q, x))
    if set(st) & set(cl):
        raise D2sError("quest_bits: word %s: bits %s both set and cleared" % (q, sorted(set(st) & set(cl))))
    return st, cl


def quest_words(b):
    """[[u16 word 0..47] per difficulty] of a save image."""
    return [[struct.unpack_from("<H", b, quest_word_off(d, q))[0] for q in range(QUEST_WORD_COUNT)]
            for d in range(3)]


def questbits(path, base=None):
    with open(path, "rb") as fh:
        cur = quest_words(fh.read())
    ref = None
    if base:
        with open(base, "rb") as fh:
            ref = quest_words(fh.read())
    n = 0
    for d in range(3):
        for q in range(QUEST_WORD_COUNT):
            w = cur[d][q]
            if ref is None:
                if w:
                    print("%-9s word %2d  0x%04X  bits %s" % (DIFFICULTIES[d], q, w,
                                                              [x for x in range(16) if w >> x & 1]))
                    n += 1
                continue
            diff = w ^ ref[d][q]
            if diff:
                print("%-9s word %2d  0x%04X -> 0x%04X  %s" % (DIFFICULTIES[d], q, ref[d][q], w, " ".join(
                    ("+%d" if w >> x & 1 else "-%d") % x for x in range(16) if diff >> x & 1)))
                n += 1
    print("%d word(s) %s" % (n, "differ" if ref is not None else "non-zero"))


GAMES = ("classic", "expansion")


def check_game(rc, status):
    """Refuse a recipe whose "game" (classic | expansion) is not the base save's: the header status byte
    0x24 bit 5 (0x20) marks an expansion character (d2s.md). The key is required, because the builder keeps the
    status byte of the base: a classic recipe built on an expansion base is an expansion character, and two runs
    were mislabelled that way (run:2026-10-15-drlg-maze s4, run:2026-10-15-objects s7-s8)."""
    game = rc.get("game")
    if game not in GAMES:
        raise D2sError('recipe key "game" must be "classic" or "expansion", got %r' % (game,))
    base = GAMES[bool(status & 0x20)]
    if game != base:
        raise D2sError("recipe game %r, base save is %s (status byte 0x%02X); build it on a%s %s base"
                       % (game, base, status, "n" if game == "expansion" else "", game))


def hireling_names(t, row):
    """(first, last) string indices of a hireling row's NameFirst / NameLast keys (tools/tbl.py)."""
    here = os.path.dirname(os.path.abspath(__file__))
    if here not in sys.path:
        sys.path.insert(0, here)
    import tbl
    if not hasattr(t, "_strings"):
        t._strings = tbl.Strings(os.path.normpath(os.path.join(t.excel_dir, "..", "..", "local", "lng", "eng")))
    return t._strings.index(row["NameFirst"]), t._strings.index(row["NameLast"])


def set_merc(t, m, b, expansion, rng):
    """Write the mercenary header (0xAF..0xBE, docs/formats/d2s.md) from the recipe's "merc" object and return its
    item groups. id: Hireling.txt Id, which must have a row of the save's version (100 expansion, 0 classic); seed:
    non-zero (a zero seed means no mercenary, and an expansion save then has no mercenary item list); name: the name
    id as stored, 0 .. string index of NameLast - string index of NameFirst (any u16 with the test-state key
    "name_unchecked": true); exp: u32; dead: bool (flags bit 16);
    items: item specs placed with "equip" only (a classic save has no mercenary item list, so none there)."""
    unknown = set(m) - {"id", "seed", "name", "name_unchecked", "exp", "dead", "items"}
    if unknown:
        raise D2sError("merc: unknown key(s) %s" % ", ".join(sorted(unknown)))
    version = "100" if expansion else "0"
    rows = [r for r in t.hirelings if r["Id"] == str(m.get("id")) and r["Version"] == version]
    if not rows:
        raise D2sError("merc: no hireling.txt row with Id %r and Version %s" % (m.get("id"), version))
    seed = m.get("seed", 0)
    if not 0 < seed < 1 << 32:
        raise D2sError("merc: seed must be 1 .. 2^32-1 (0 means no mercenary)")
    first, last = hireling_names(t, rows[0])
    name = m.get("name", 0)
    if m.get("name_unchecked"):
        # test-state key (backlog 2026-10-27, plan 0038 batch H1b row 48): the name id is written as given, past
        # the row's NameLast too, so the reader's reset of such a name can be met; it must still fit the u16
        if not isinstance(name, int) or not 0 <= name <= 0xFFFF:
            raise D2sError("merc: name %r outside the u16 0 .. 65535" % (name,))
    elif not 0 <= name <= last - first:
        raise D2sError("merc: name %r outside 0 .. %d (%s .. %s)" % (name, last - first, rows[0]["NameFirst"],
                                                                     rows[0]["NameLast"]))
    exp = m.get("exp", 0)
    flags = (u32(b, 0xAF) & ~0x10000) | (0x10000 if m.get("dead") else 0)
    struct.pack_into("<IIHHI", b, 0xAF, flags, seed, name, m["id"], exp)
    specs = m.get("items", [])
    if specs and not expansion:
        raise D2sError("merc: items need an expansion save (a classic save has no 'jf' list)")
    for spec in specs:
        if "equip" not in spec or any(k in spec for k in ("store", "belt_slot")):
            raise D2sError("merc item %r: place it with \"equip\" only" % spec.get("code", spec.get("unique")))
    groups = [new_group(t, spec, rng) for spec in specs]
    check_layout([it for g in groups for it in g], item_sizes(t))
    return groups


def build(excel_dir, recipe_path, src, dst):
    """Build a save from a base save and a JSON recipe (keys documented in the module docstring)."""
    import json
    import random
    t = Tables(excel_dir)
    isc = t.isc
    if isinstance(recipe_path, dict):    # a recipe already loaded (tools/merc_saves.py)
        rc = recipe_path
    else:
        with open(recipe_path) as fh:
            rc = json.load(fh)
    rng = random.Random(rc["seed"]) if "seed" in rc else random.SystemRandom()
    with open(src, "rb") as fh:
        b = bytearray(fh.read())
    f = parse(bytes(b), isc, t.kinds)
    ver = ext_version(rc, f)
    h = f["header"]
    cls_name = CLASSES[h["cls"]]
    if rc.get("class", cls_name) != cls_name:
        raise D2sError("recipe class %r, base save class %s" % (rc["class"], cls_name))
    check_game(rc, b[0x24])
    if "name" in rc:
        name = rc["name"].encode("latin1")
        if not 2 <= len(name) <= 15:
            raise D2sError("name length")
        b[0x14:0x24] = name.ljust(16, b"\0")
    if "progression" in rc:
        b[0x25] = rc["progression"]
    if "difficulty" in rc:
        b[0xA8:0xAB] = bytes(rc["difficulty"])
    for slot, key in enumerate(("left", "right", "swap_left", "swap_right")):
        if key in rc.get("mouse", {}):
            struct.pack_into("<I", b, 0x78 + 4 * slot, t.skills[rc["mouse"][key]]["id"])
    # hotkeys: F1.. in order; a right-button binding is the skill id with no flag, as the played sample
    # smpsor.d2s binds Teleport (54) and Nova (48); "left:<skill>" sets the 0x8000 slot flag ([I], d2s.md)
    if len(rc.get("hotkeys", [])) > 16:
        raise D2sError("hotkeys: at most 16 (F1..F16), got %d" % len(rc["hotkeys"]))
    for slot, name in enumerate(rc.get("hotkeys", [])):
        flag = 0x8000 if name.startswith("left:") else 0
        skill = name[5:] if flag else name
        if skill not in t.skills:
            raise D2sError("hotkeys: skill %r not in skills.txt" % skill)
        sid = t.skills[skill]["id"]
        struct.pack_into("<HH", b, 0x38 + 4 * slot, sid | flag, 0)
    for d, spec in rc.get("waypoints", {}).items():
        o = wp_field_off(DIFFICULTIES.index(d))
        b[o:o + WP_FIELD_BYTES] = sum(1 << i for i in parse_wp_list(spec)).to_bytes(WP_FIELD_BYTES, "little")
    # acts_open: OR bit 0 into the act-travel quest words of each listed difficulty (save/0002 [I]):
    # 7, 15, 23 (Acts II-IV), and 26, 28 (Act V tab drawn / selectable) when the save is expansion.
    # quests: the same, plus bit 0 of the quest words of every act (1-6, 9-14, 17-22, 25-27, and
    # 35-40 when expansion); 0, 8, 16, 24, 29-34 and 41 are not touched (save/0002 Recipe [I])
    expansion = bool(b[0x24] & 0x20)
    q_all = rc.get("quests", [])
    q_all = DIFFICULTIES if q_all == "all" else q_all
    for d in set(rc.get("acts_open", [])) | set(q_all):
        words = [7, 15, 23] + ([26, 28] if expansion else [])
        if d in q_all:
            words += QUEST_WORDS + (QUEST_WORDS_ACT5 if expansion else [])
        base = QUEST_OFF + 10 + 0x60 * DIFFICULTIES.index(d)
        for q in sorted(set(words)):
            struct.pack_into("<H", b, base + 2 * q, struct.unpack_from("<H", b, base + 2 * q)[0] | 1)
    # quest_bits, list form [[difficulty, word, bit, 0|1], ...] (plan 0030 Phase 2's cow recipes): the same
    # operation one bit at a time, checked as the mapping form
    qb = rc.get("quest_bits", {})
    if isinstance(qb, list):
        qm = {}
        for d, q, bit, v in qb:
            e = qm.setdefault(d, {}).setdefault(str(q), {"set": [], "clear": []})
            e["set" if v else "clear"].append(bit)
        rc = dict(rc, quest_bits=qm)
    # quest_bits: single bits of any quest word, set or cleared, after acts_open and quests (save/0002 § Recipe)
    for d, words in rc.get("quest_bits", {}).items():
        if d not in DIFFICULTIES:
            raise D2sError("quest_bits: difficulty %r (normal, nightmare or hell)" % (d,))
        for q, spec in words.items():
            st, cl = quest_bits_spec(q, spec)
            o = quest_word_off(DIFFICULTIES.index(d), int(q))
            w = struct.unpack_from("<H", b, o)[0]
            w = (w | sum(1 << x for x in st)) & ~sum(1 << x for x in cl) & 0xFFFF
            struct.pack_into("<H", b, o, w)
    # stats: the full list, in ascending id order; 6..11 are given in whole points (8 fraction bits)
    stats = []
    for key, v in rc["stats"].items():
        sid = int(key) if key.isdigit() else t.stat_id(key)
        stats.append((sid, None, v << 8 if 6 <= sid <= 11 else v))
    stats.sort()
    if any(isc[s]["csv_param"] for s, _, _ in stats):
        raise D2sError("param character stats not supported")
    lvl = dict((s, v) for s, _, v in stats).get(12)
    if lvl is not None:
        b[0x2B] = lvl
    if "stat_slots" in rc:
        b[0x29] = rc["stat_slots"]
    skills = list(f["skills"])
    if "skills" in rc:
        code = {"Amazon": "ama", "Sorceress": "sor", "Necromancer": "nec", "Paladin": "pal",
                "Barbarian": "bar", "Druid": "dru", "Assassin": "ass"}[cls_name]
        order = t.class_skills[code]
        skills = [0] * 30
        for name, lvl_s in rc["skills"].items():
            skills[order.index(name)] = lvl_s
    if "skill_count" in rc:
        # test state: header 0x2A and that many skill bytes (the reader takes 0x2A bytes, d2s.md § Skills [C]);
        # bytes past 30 are 0, and a non-zero skill byte that would be cut off is refused
        n = rc["skill_count"]
        if any(skills[n:]):
            raise D2sError("skill_count %d cuts off a non-zero skill byte" % n)
        skills = (skills + [0] * n)[:n]
        b[0x2A] = n
    # keep_items: a kept item keeps its socketed items, which follow it in the base save's list (save/0001 § 6)
    kept = {it["off"] for it in f["items"]["items"]
            if "parent" not in it and it.get("code", "").strip() in rc.get("keep_items", [])}
    groups = [[it] + [c for c in f["items"]["items"] if c.get("parent") == it["off"]]
              for it in f["items"]["items"] if it["off"] in kept]
    for g in groups:
        if len(g) - 1 != g[0].get("n_filled", 0):
            raise D2sError("kept item %r: n_filled %d, %d socketed items follow it"
                           % (g[0]["code"].strip(), g[0].get("n_filled", 0), len(g) - 1))
    new_groups = [new_group(t, spec, rng) for spec in rc.get("items", [])]
    new = [it for g in new_groups for it in g]
    if "belt_fill" in rc:
        belt = [it for it in new if it.get("body") == t.bodylocs["belt"]]
        if len(belt) != 1:
            raise D2sError("belt_fill needs one equipped belt")
        boxes = t.belts[int(t.base[belt[0]["code"].strip()]["belt"])]
        fill = rc["belt_fill"]
        if isinstance(fill, list) and len(fill) != 4:
            raise D2sError("belt_fill: give one code or a list of four (one per column), got %d" % len(fill))
        cols = fill if isinstance(fill, list) else [fill] * 4      # slot k is in column k % 4 (hot key 1 + k % 4)
        belt_items = [new_item(t, dict(code=cols[k % 4], belt_slot=k), rng) for k in range(boxes)]
        new += belt_items
        new_groups += [[it] for it in belt_items]
    # items in the two hand slots are written after the others (save/0001 § 6), each with its socketed items
    hands = (t.bodylocs["rarm"], t.bodylocs["larm"]) + tuple(SWAP_BODIES.values())
    groups += new_groups
    check_layout([it for g in groups for it in g], item_sizes(t))

    def in_hand(g):
        return g[0]["location"] == 1 and g[0]["body"] in hands
    allit = [it for g in groups if not in_hand(g) for it in g] + [it for g in groups if in_hand(g) for it in g]
    tail = bytes(b[f["items_end"]:])
    if "merc" in rc:
        merc_groups = set_merc(t, rc["merc"], b, expansion, rng)
        new += [it for g in merc_groups for it in g]
        if expansion:
            merc = [it for g in merc_groups if not in_hand(g) for it in g] + \
                   [it for g in merc_groups if in_hand(g) for it in g]
            tail = (bytes(b[f["items_end"]:f["corpses_end"]]) + b"jf" + encode_items(merc, isc, t.kinds, ver=ver)
                    + bytes(b[f["kf_off"]:]))
    if ver is not None:
        struct.pack_into("<I", b, 4, ver)
    gf = encode_stats_old(stats, b[0x29]) if ver is not None and ver <= OLD_STATS_MAX else encode_stats(stats, isc)
    out = (bytes(b[:HEADER_SIZE]) + gf + b"if" + bytes(skills)
           + encode_items(allit, isc, t.kinds, ver=ver) + tail)
    out = finish(out)
    parse(out, isc, t.kinds, extended=ver is not None)  # must read back
    with open(dst, "wb") as fh:
        fh.write(out)
    for it in new:
        if "seed" in it:
            print("item %s seed %d" % (it["code"].strip(), it["seed"]))
    print("wrote", dst, "%d bytes, %d items, checksum %08X" % (len(out), len(allit), u32(out, 12)))


EXT_KEYS = ("save_version", "stat_slots", "skill_count")


def ext_version(rc, f):
    """The save version an extended build writes, or None for the ordinary version-96 build (every key of the
    extension absent). save_version: 93..96 (92 and the legacy versions are not buildable: d2s.md § Versions
    92..95, § Legacy versions); stat_slots alone, skill_count alone or an item with "realm" give 96."""
    items = list(rc.get("items", [])) + list(rc.get("merc", {}).get("items", []))
    items += [c for it in list(items) for c in it.get("filled", [])]
    if not any(k in rc for k in EXT_KEYS) and not any("realm" in it for it in items):
        return None
    ver = rc.get("save_version", 96)
    if ver not in EXT_VERSIONS:
        raise D2sError("save_version %r: 93..96 (92: the 1.09 property widths' per-id overrides are not documented; "
                       "< 92: the legacy layouts are not documented; d2s.md § Versions 92..95)" % (ver,))
    if "stat_slots" in rc and not (isinstance(rc["stat_slots"], int) and 0 <= rc["stat_slots"] < 256):
        raise D2sError("stat_slots %r: a byte" % (rc["stat_slots"],))
    if "skill_count" in rc and not (isinstance(rc["skill_count"], int) and 0 <= rc["skill_count"] < 256):
        raise D2sError("skill_count %r: a byte" % (rc["skill_count"],))
    if ver != 96:
        # the bytes after the main item list are copied from the base; items there were written in the
        # version-96 widths, so they are refused rather than carried into a file of another version
        if any(c["items"]["count"] for c in f["corpses"]) or f.get("golem") or (
                f.get("merc_items", {}).get("count") and "merc" not in rc):
            raise D2sError("save_version %d: the base has corpse, golem or mercenary items (written in the "
                           "version-96 widths)" % ver)
    return ver


def to_classic(b, isc, kinds):
    """Classic image of an expansion save (bytes): status bit 5 (0x20) cleared and the expansion trailer, "jf" "kf"
    and the golem byte, removed; size and checksum fixed. Refused when the save is not expansion, has mercenary
    items or a golem, since those would be dropped. Everything else, the quest section included, is kept. This is
    how the classic base workspace/runtime/monspawn-chars/cls/smpsor.d2s was made, and that save loaded as a
    classic character (docs/findings/monsters/experiments.md); a converted save is not otherwise verified."""
    f = parse(bytes(b), isc, kinds)
    if not b[0x24] & 0x20:
        raise D2sError("classic: the save is already classic (status byte 0x%02X)" % b[0x24])
    if f.get("merc_items", {}).get("count") or f.get("golem"):
        raise D2sError("classic: the save has mercenary items or a golem")
    end = f["end"]
    if bytes(b[end - 5:end]) != b"jfkf\0" or end != len(b):
        raise D2sError("classic: unexpected trailer %r at 0x%X" % (bytes(b[end - 5:end]), end - 5))
    out = bytearray(b[:end - 5])
    out[0x24] &= ~0x20 & 0xFF
    out = finish(out)
    parse(out, isc, kinds)  # must read back
    return out


def classic(excel_dir, src, dst):
    with open(src, "rb") as fh:
        b = fh.read()
    out = to_classic(b, load_isc(excel_dir), load_kinds(excel_dir))
    with open(dst, "wb") as fh:
        fh.write(out)
    print("wrote", dst, "%d bytes, checksum %08X" % (len(out), u32(out, 12)))


def main(argv):
    if len(argv) in (2, 3) and argv[0] == "questbits":
        questbits(*argv[1:])
        return 0
    if len(argv) == 4 and argv[0] == "classic":
        classic(argv[1], argv[2], argv[3])
        return 0
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
    if len(argv) >= 5 and argv[0] == "setstats":
        assigns = []
        for a in argv[4:]:
            sid, eq, v = a.partition("=")
            if not eq:
                print("setstats: expected <stat-id>=<value>, got %r" % a)
                return 2
            assigns.append((int(sid), int(v)))
        setstats(argv[1], argv[2], argv[3], assigns)
        return 0
    if len(argv) == 5 and argv[0] == "setwp":
        setwp(argv[1], argv[2], argv[3], argv[4])
        return 0
    if len(argv) >= 3 and argv[0] == "roundtrip":
        return roundtrip(argv[1], argv[2:])
    if len(argv) >= 3 and argv[0] == "checkuniq":
        return checkuniq(argv[1], argv[2:])
    if len(argv) == 5 and argv[0] == "build":
        build(argv[1], argv[2], argv[3], argv[4])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except D2sError as e:
        print("error:", e, file=sys.stderr)
        sys.exit(1)

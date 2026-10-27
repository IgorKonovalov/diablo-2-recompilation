"""Build the test saves of plan 0038 batch H1a (run:2026-10-27-sweep-d2s-load) from the sample saves.

Usage:
  python3 -I tools/h1a_saves.py <excel-dir> <out-dir>

Every case is one directory <out-dir>/<case>/ holding one <name>.d2s (never written into a saves directory;
tools/h1a_sessions.py installs them). Unless a case says otherwise the base is workspace/samples/d2s/qitsor.d2s
(expansion Sorceress `qitsor`, level 1, 14 items, version 96), the name stays `qitsor`, and file_size and the
checksum are recomputed after the edit. These are ADR-0003 inputs on stock tables (ADR-0013 § Neutral), and
several are malformed on purpose: they back the code that reads the built bytes, never how a game makes them.

Header and file cases (the reader's codes):
  base       qitsor unchanged (the file listed on the character screen before a swap; tools/h1a_sessions.py)
  hc         base with status bit 2 (hardcore)              classic    base with status bit 5 cleared (header only)
  prog5      base with progression (0x25) 5                  prog10     base with progression 10
  magic      u32 0x000 = 0x12345678 (no fix-up)              short      the first 7 bytes of base
  v97        version 97                                      v91        version 91
  class8     class byte 8                                    class7     class byte 7
  hcsoft     base, status bit 2 clear (= base; swapped over the hc listing)
  hcon       hc (swapped over the base listing)              hcdead     hc with status bit 3 (dead)
  expon      base (swapped over the classic listing)         clson      classic (swapped over the base listing)
  prog4      progression 4 (swapped over prog5, Nightmare)   prog0      progression 0 (swapped over prog10, Hell)
  both       checksum + 1 and file_size + 1
  hdrshort   the first 0x100 bytes of base (shorter than the 0x14F-byte header; no fix-up)
  v97sum     version 97 and the checksum + 1          namehc     header name `qitsox` and status bit 2
  class8hc   class byte 8 and status bit 2
  wpbad      the Normal waypoint marker 0x0303
  stubok     samples/d2s/stub-seedtest.d2s with the name `qitsor` (status bit 0: a new character), 335 bytes
  stubtrail  stubok + 10 bytes 0xEE after the header (file_size and checksum over all 345)
  big8k      base, zero-padded to 8192 bytes (file_size 8192, checksum over them), then 200 bytes 0xEE
  bigbad     base, zero-padded to 8392 bytes, file_size 8392 and the checksum over all of them
Sections, items and legacy formats (loaded, then Save and Exit):
  fields     last_played 0x11111111, unk_34 0x22222222, graphics 0x88..0x97 = 0x01, colours 0x98..0xA7 = 0x05,
             0xCF = 0x5A, the rest of unk_bf (0xBF..0xCE, 0xD0..0x14E) = 0x77, Normal difficulty byte 0x85 (act 5,
             bit 7), Hell quest words 1 (bits 1, 13, 14), 2 (bits 13, 14) and 3 (bit 1), Normal waypoints with
             bit 0 clear and bit 1 set, Nightmare marker 0x0101 and Hell marker 0, each with waypoint bits 0..3 set
  skills29   skill count 0x2A = 29 and the last skill byte removed, skill bytes 0 and 28 = 1, header name `QITSOR`
  items      an ear at inventory (0, 0) (simple form, class 3, level 42, name `earname`, realm bit 0); the stash
             unique cap personalized (flags bit 24, name `Hoarder`); the stash magic gloves with realm data
             (1, 0x11223344, 0x55667788, 0x99AABBCC)
  uniqbad    the stash unique amulet with unique id 4000 (12 bits)
  setbad     the stash magic gloves rewritten as a set item (quality 5) with set id 4000, no set lists
  param      the equipped short staff's property 107 (item_singleskill) with param 270 (9 bits; a reader taking
             the param signed would get -242)
  v94        version 94: the stat section in the old form (`gf`, a 2-byte bitmask over stats 0..15, a u32 per set
             bit) and stat 72 (current durability) in 8 bits, the width ITEMS_ReadFull uses for version <= 95
  v94s12     v94 with the stat-slot count 0x29 = 12: the bitmask covers stats 0..11 only (stat 12 dropped)
  slots8     base with 0x29 = 8                       act6       base with the Normal difficulty byte 0x86
  stub7      stubok with class byte 7 (a new character of class 7)
  name15     name `qitsorfifteenzz` (15 characters, file qitsorfifteenzz.d2s) with byte 0x23 = 'Z'
  mercmf     tools/d2s_recipes/mercmf.json built on workspace/samples/d2s-owner/smpsor-l50.d2s (MercMF.d2s)

Every file's size, size field, checksum and sha256 is printed. Stdlib only.
"""
import hashlib
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d2s  # noqa: E402

ROOT = os.path.dirname(HERE)
SAMPLES = os.path.join(ROOT, "workspace", "samples", "d2s")
QITSOR = os.path.join(SAMPLES, "qitsor.d2s")
STUB = os.path.join(SAMPLES, "stub-seedtest.d2s")
BASE_X = os.path.join(ROOT, "workspace", "samples", "d2s-owner", "smpsor-l50.d2s")


def fix(b):
    b = bytearray(b)
    struct.pack_into("<I", b, 8, len(b))
    struct.pack_into("<I", b, 12, d2s.checksum(bytes(b)))
    return b


def write(out, case, name, b):
    path = os.path.join(out, case, name + ".d2s")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b)
    size_field = struct.unpack_from("<I", b, 8)[0] if len(b) >= 12 else None
    stored = struct.unpack_from("<I", b, 12)[0] if len(b) >= 16 else None
    print("%-10s %-22s %5d bytes  size field %s  checksum stored %s computed %08X  sha256 %s" % (
        case, name + ".d2s", len(b), size_field, "%08X" % stored if stored is not None else None,
        d2s.checksum(bytes(b)), hashlib.sha256(b).hexdigest()))


class Realm:
    """A realm value for d2s.encode_item: the 1-bit flag, then the three u32 the version-96 reader takes."""

    def __init__(self, a, b, c):
        self.words = (a, b, c)


class RealmWriter(d2s.BitWriter):
    def write(self, value, n):
        if isinstance(value, Realm):
            super().write(1, 1)
            for w in value.words:
                super().write(w, 32)
            return
        super().write(value, n)


def encode(it, isc, kinds):
    saved = d2s.BitWriter
    d2s.BitWriter = RealmWriter
    try:
        return d2s.encode_item(it, isc, kinds)
    finally:
        d2s.BitWriter = saved


def encode_ear(it):
    """The simple-item ear: common part, class 3, level 7, name 7 bits per character with its 0, realm bit 0
    (ITEMS_WriteCompact 0x0062B1D3-0x0062B277, then the realm bit at 0x0062B341-0x0062B387)."""
    w = d2s.BitWriter()
    w.write(0x4D4A, 16)
    w.write(it["flags"], 32)
    w.write(it["version"], 10)
    for k, n in (("location", 3), ("body", 4), ("x", 4), ("y", 4), ("store", 3)):
        w.write(it[k], n)
    w.write(it["ear_class"], 3)
    w.write(it["ear_level"], 7)
    d2s.write_name7(w, it["ear_name"])
    w.write(0, 1)
    return w.tobytes()


def rebuild(b, f, items, isc, kinds):
    """Replace the main item list of save b (parsed as f) by the given item records (bytes per top-level item)."""
    start = f["skills_end"]
    end = f["items_end"]
    lst = b"JM" + struct.pack("<H", len(items)) + b"".join(items)
    return fix(bytes(b[:start]) + lst + bytes(b[end:]))


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    excel, out = argv
    isc = d2s.load_isc(excel)
    kinds = d2s.load_kinds(excel)
    base = open(QITSOR, "rb").read()
    f = d2s.parse(base, isc, kinds)

    def edit(fn):
        b = bytearray(base)
        fn(b)
        return fix(b)

    write(out, "base", "qitsor", base)
    hc = edit(lambda b: b.__setitem__(0x24, b[0x24] | 0x04))
    classic = edit(lambda b: b.__setitem__(0x24, b[0x24] & ~0x20))
    write(out, "hc", "qitsor", hc)
    write(out, "classic", "qitsor", classic)
    for p in (0, 4, 5, 10):
        write(out, "prog%d" % p, "qitsor", edit(lambda b, p=p: b.__setitem__(0x25, p)))
    b = bytearray(base)
    struct.pack_into("<I", b, 0, 0x12345678)
    write(out, "magic", "qitsor", bytes(b))
    write(out, "short", "qitsor", base[:7])
    for v in (97, 91):
        write(out, "v%d" % v, "qitsor", edit(lambda b, v=v: struct.pack_into("<I", b, 4, v)))
    for c in (8, 7):
        write(out, "class%d" % c, "qitsor", edit(lambda b, c=c: b.__setitem__(0x28, c)))
    write(out, "hcdead", "qitsor", edit(lambda b: b.__setitem__(0x24, b[0x24] | 0x0C)))
    b = bytearray(base)
    struct.pack_into("<I", b, 0x0C, (struct.unpack_from("<I", b, 0x0C)[0] + 1) & 0xFFFFFFFF)
    struct.pack_into("<I", b, 0x08, len(b) + 1)
    write(out, "both", "qitsor", bytes(b))
    # the order of D2S_ReadHeader's tests: each case fails two of them, so its code names the first
    write(out, "hdrshort", "qitsor", base[:0x100])
    b = bytearray(fix(bytearray(base[:4]) + struct.pack("<I", 97) + bytearray(base[8:])))
    struct.pack_into("<I", b, 0x0C, (struct.unpack_from("<I", b, 0x0C)[0] + 1) & 0xFFFFFFFF)
    write(out, "v97sum", "qitsor", bytes(b))
    b = bytearray(base)
    b[0x14:0x24] = b"qitsox".ljust(16, b"\0")
    b[0x24] |= 0x04
    write(out, "namehc", "qitsor", fix(b))
    write(out, "class8hc", "qitsor", edit(lambda b: (b.__setitem__(0x28, 8), b.__setitem__(0x24, b[0x24] | 4))))
    write(out, "wpbad", "qitsor", edit(lambda b: struct.pack_into("<H", b, d2s.WP_BLOCK0, 0x0303)))

    stub = bytearray(open(STUB, "rb").read())
    stub[0x14:0x24] = b"qitsor".ljust(16, b"\0")
    write(out, "stubok", "qitsor", fix(stub))
    write(out, "stubtrail", "qitsor", fix(bytes(stub) + b"\xEE" * 10))

    b = bytearray(base) + bytearray(8192 - len(base))
    b = fix(b)
    write(out, "big8k", "qitsor", bytes(b) + b"\xEE" * 200)
    write(out, "bigbad", "qitsor", fix(bytearray(base) + bytearray(8392 - len(base))))

    def fields(b):
        struct.pack_into("<I", b, 0x30, 0x11111111)
        struct.pack_into("<I", b, 0x34, 0x22222222)
        b[0x88:0x98] = b"\x01" * 16
        b[0x98:0xA8] = b"\x05" * 16
        b[0xBF:0xCF] = b"\x77" * 16
        b[0xCF] = 0x5A
        b[0xD0:0x14F] = b"\x77" * (0x14F - 0xD0)
        b[0xA8] = 0x85
        for q, bits in ((1, (1, 13, 14)), (2, (13, 14)), (3, (1,))):
            o = d2s.quest_word_off(2, q)
            w = struct.unpack_from("<H", b, o)[0]
            for s in bits:
                w |= 1 << s
            struct.pack_into("<H", b, o, w)
        o = d2s.WP_BLOCK0
        w = struct.unpack_from("<H", b, o + 2)[0]
        struct.pack_into("<H", b, o + 2, (w & ~1) | 2)
        for d, marker in ((1, 0x0101), (2, 0)):
            o = d2s.WP_BLOCK0 + d * d2s.WP_BLOCK_SIZE
            struct.pack_into("<H", b, o, marker)
            struct.pack_into("<H", b, o + 2, 0x000F)
    write(out, "fields", "qitsor", edit(fields))

    # skills29: one skill byte fewer, the count byte says so, and an upper-case header name
    p = f["skills_end"] - 30
    sk = bytearray(base[p:p + 30])
    sk[0] = 1
    sk[28] = 1
    b = bytearray(base[:p]) + sk[:29] + bytearray(base[p + 30:])
    b[0x2A] = 29
    b[0x14:0x24] = b"QITSOR".ljust(16, b"\0")
    write(out, "skills29", "qitsor", fix(b))

    top = [it for it in f["items"]["items"] if "parent" not in it]
    code = lambda it: it.get("code", "").strip()  # noqa: E731

    def records(change):
        recs = []
        for it in top:
            r = change(dict(it))
            if r is not None:
                recs.append(r)
        return recs

    def items_change(it):
        if code(it) == "cap":
            it["flags"] |= 1 << 24
            it["pname"] = "Hoarder"
        elif code(it) == "lgl":
            it["realm"] = Realm(0x11223344, 0x55667788, 0x99AABBCC)
        return encode(it, isc, kinds)

    ear = dict(flags=(1 << 4) | (1 << 16) | (1 << 21) | (1 << 23), version=101, location=0, body=0, x=0, y=0,
               store=1, ear_class=3, ear_level=42, ear_name="earname")
    recs = records(items_change) + [encode_ear(ear)]
    write(out, "items", "qitsor", rebuild(base, f, recs, isc, kinds))

    def uniq_change(it):
        if code(it) == "amu" and it.get("quality") == 7:
            it["qid"] = 4000
        return encode(it, isc, kinds)
    write(out, "uniqbad", "qitsor", rebuild(base, f, records(uniq_change), isc, kinds))

    def set_change(it):
        if code(it) == "lgl":
            it["quality"] = 5
            it["qid"] = 4000
            it["set_lists"] = 0
            it.pop("prefix", None)
            it.pop("suffix", None)
        return encode(it, isc, kinds)
    write(out, "setbad", "qitsor", rebuild(base, f, records(set_change), isc, kinds))

    def param_change(it):
        if code(it) == "sst":
            it["props"] = [(107, 270, [1])]
        return encode(it, isc, kinds)
    write(out, "param", "qitsor", rebuild(base, f, records(param_change), isc, kinds))

    # v94: the old stat form and the 8-bit current durability
    stats = {sid: v for sid, _, v in f["stats"]}
    if any(sid > 15 for sid in stats):
        raise SystemExit("v94: a stat above 15 cannot be written in the old form")
    mask = sum(1 << sid for sid in stats)
    gf = b"gf" + struct.pack("<H", mask) + b"".join(struct.pack("<I", stats[s]) for s in range(16) if s in stats)
    saved72 = isc[72]["save_bits"]
    isc[72]["save_bits"] = 8
    try:
        recs = records(lambda it: encode(it, isc, kinds))
    finally:
        isc[72]["save_bits"] = saved72
    b = rebuild(base, f, recs, isc, kinds)
    p_if = f["skills_end"] - 32
    b = bytearray(b[:d2s.HEADER_SIZE]) + gf + bytearray(b[p_if:])
    struct.pack_into("<I", b, 4, 94)
    write(out, "v94", "qitsor", fix(b))

    # the stat-slot count: a version-94 file with 0x29 = 12 (the bitmask over stats 0..11, still 2 bytes) and a
    # version-96 file with 0x29 = 8 (not used by D2S_ReadStatsBits)
    stats12 = {sid: v for sid, v in stats.items() if sid < 12}
    mask = sum(1 << sid for sid in stats12)
    gf = b"gf" + struct.pack("<H", mask) + b"".join(struct.pack("<I", stats12[i]) for i in range(12) if i in stats12)
    b = bytearray(b[:d2s.HEADER_SIZE]) + gf + bytearray(b[d2s.HEADER_SIZE + 4 + 4 * len(stats):])
    b[0x29] = 12
    write(out, "v94s12", "qitsor", fix(b))
    write(out, "slots8", "qitsor", edit(lambda b: b.__setitem__(0x29, 8)))
    write(out, "act6", "qitsor", edit(lambda b: b.__setitem__(0xA8, 0x86)))
    stub7 = bytearray(stub)
    stub7[0x28] = 7
    write(out, "stub7", "qitsor", fix(stub7))

    name = "qitsorfifteenzz"
    b = bytearray(base)
    b[0x14:0x23] = name.encode()
    b[0x23] = ord("Z")
    write(out, "name15", name, fix(b))

    mm = os.path.join(out, "mercmf", "MercMF.d2s")
    os.makedirs(os.path.dirname(mm), exist_ok=True)
    subprocess.run([sys.executable, "-I", os.path.join(HERE, "d2s.py"), "build", excel,
                    os.path.join(HERE, "d2s_recipes", "mercmf.json"), BASE_X, mm], check=True,
                   stdout=subprocess.DEVNULL)
    b = open(mm, "rb").read()
    write(out, "mercmf", "MercMF", b)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

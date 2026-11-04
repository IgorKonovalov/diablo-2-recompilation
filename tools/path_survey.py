"""Survey of the path types and the columns a path request reads (plan 0054 Phase 0).

Usage:
  python3 -I tools/path_survey.py types   <game.exe>
  python3 -I tools/path_survey.py md      <game.exe>
  python3 -I tools/path_survey.py columns <excel-dir>
  python3 -I tools/path_survey.py rows    <excel-dir>
  python3 -I tools/path_survey.py summary <excel-dir> <game.exe>
  python3 -I tools/path_survey.py dirtables <game.exe>
  python3 -I tools/path_survey.py dirmd    <game.exe>
  python3 -I tools/path_survey.py readers  <game.exe>
  python3 -I tools/path_survey.py rules    <game.exe>

types    the 17 slots of g_PathPlanFuncs (0x006EB6D8, u32 planner address, 0 = none) and of the flags table
         (0x006EB690, u32 flags word), read from the pinned image (sha256 checked), with the symbol name of the
         planner address when re/symbols.csv has one.
md       the same as the Markdown table of docs/tables/PathTypes.md § The 17 slots (generated, not typed).
columns  the unit-size columns a request reads through PATH_PatternFromSize (MonStats2 SizeX, Missiles Size, the
         player's fixed size) and the Skills columns that name the start / do functions the findings tie to a path
         type: value counts.
rows     the stock Skills rows per (function column, number) the findings tie to a path type, with the missile
         columns they name, and the Missiles rows that name class 195 (plan 0054 H1 cases).
summary  counts only (the direction tables' counts and checksums included).
dirtables the direction and step tables of the path planners (docs/tables/PathDirTables.md): each table's address,
         element width, shape and checksum, read from the image; the values of the tables that have no rule (ADR-0031).
dirmd    the Markdown of that doc's value blocks (generated, not typed): the tables that have no rule, and no other.
rules    for each table a rule gives, the rule's values compared with the image element by element: elements,
         mismatches and both checksums, never the values. Exit 1 on any mismatch; summary does the same.
readers  for each table, the instructions that read it (recorded in READERS) disassembled with objdump, and whether
         the operand size is the width the doc states (needs objdump).

Every command ends with `SURVEY path key=value ...`; tools/gate.py --full compares the summary line with its
baseline. The image is read only when its sha256 is the pinned one (docs/inventory.md). Slot meanings are [L]
here; the planner names come from re/symbols.csv. Stdlib only. Read-only.
"""
import collections
import hashlib
import math
import os
import re
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402

PINNED_SHA256 = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
FLAGS_VA = 0x006EB690   # u32 per path type (drlg/0009 § 11.1: PathSetType copies bits 8..18 into path +0x34)
FUNCS_VA = 0x006EB6D8   # data:g_PathPlanFuncs
N_TYPES = 17
SYMBOLS = os.path.join(HERE, "..", "re", "symbols.csv")

# (column, number) -> (path type, finding) : the stock callers the findings tie to one path type. Each number is the
# Skills srvstfunc (start) or srvdofunc (do) value; the type is the finding's, [I].
SKILL_FUNCS = (
    ("srvstfunc", 38, 7, "skills/0012 (Whirlwind, leaps: start 38 ends at PathSetType 7)"),
    ("srvstfunc", 48, 2, "skills/0016 (monster 8a: start 48 ends at PathSetType 2)"),
    ("srvdofunc", 73, 14, "skills/0011 (do 73 sets 14 on the missile it creates)"),
    ("srvdofunc", 103, 1, "skills/0017 (monster 8b: do 103 sets 1)"),
    ("srvdofunc", 117, 10, "skills/0003 H1 (do 117 Firestorm reaches callback 0x005C9290: type 10)"),
)


def load_image(exe):
    data = open(exe, "rb").read()
    if hashlib.sha256(data).hexdigest() != PINNED_SHA256:
        raise SystemExit("path_survey: %s is not the pinned Game.exe" % exe)
    return data


def read_u32s(data, va, n):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    optsz = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    so = pe + 24 + optsz
    rva = va - base
    for i in range(nsec):
        vsize, sva, rsize, raw = struct.unpack_from("<IIII", data, so + 40 * i + 8)
        if sva <= rva and rva + 4 * n <= sva + min(max(vsize, rsize), rsize):
            return list(struct.unpack_from("<%dI" % n, data, raw + rva - sva))
    raise ValueError("0x%08X + %d words not in a raw section" % (va, n))


def read_bytes(data, va, n):
    """n raw bytes at a virtual address of the image (the section's file-backed part only)."""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    optsz = struct.unpack_from("<H", data, pe + 20)[0]
    base = struct.unpack_from("<I", data, pe + 24 + 28)[0]
    so = pe + 24 + optsz
    rva = va - base
    for i in range(nsec):
        vsize, sva, rsize, raw = struct.unpack_from("<IIII", data, so + 40 * i + 8)
        if sva <= rva and rva + n <= sva + min(max(vsize, rsize), rsize):
            return data[raw + rva - sva: raw + rva - sva + n]
    raise ValueError("0x%08X + %d bytes not in a raw section" % (va, n))


# The direction and step tables of the path planners (docs/tables/PathDirTables.md). Each is a constant of the image.
#   name   symbol in re/symbols.csv
#   va     address of the first element the doc lists (the centred tables start below the symbol's address)
#   kind   "i32" (little-endian signed dword per element) or "u8"
#   count  elements from va
#   read   the operand size the reading instructions use: DWORD, WORD (the low half of the dword) or BYTE
#   readers instruction addresses that read the table, found by a byte scan of .text for any 4-byte value inside
#          the table's span (no table is read through a pointer unless the row says so)
#   via_ptr True when the readers dereference a register that holds a pointer into the table
DIRTABLES = (
    dict(name="g_DirOctant", va=0x006F1518, kind="i32", count=75, shape="[25][3]", read="DWORD", via_ptr=False,
         readers=(0x678D03, 0x678D23, 0x678D48, 0x678D53, 0x678D5C, 0x678D88, 0x678D93, 0x678D9C)),
    dict(name="g_PathDirTriples", va=0x006F1648, kind="u8", count=75, shape="[25][3]", read="BYTE", via_ptr=False,
         readers=(0x678CC0, 0x678CE0, 0x678DC0, 0x678DCD, 0x678DD8, 0x678E03, 0x678E0D, 0x678E18)),
    dict(name="g_PathDistNear", va=0x006F1698, kind="i32", count=64, shape="[8][8]", read="DWORD", via_ptr=False,
         readers=(0x6793B0,)),
    dict(name="g_PathStep8Long", va=0x006F1798, kind="i32", count=16, shape="[8][2]", read="WORD", via_ptr=False,
         readers=(0x67942C, 0x679434, 0x679477, 0x67947F, 0x6794D3, 0x6794DB, 0x679C01, 0x679C0D, 0x679DBE,
                  0x679DC6, 0x67A33F, 0x67A347)),
    dict(name="g_PathSearchTurnRows", va=0x006F17D8, kind="i32", count=64, shape="[8][8]", read="DWORD", via_ptr=True,
         readers=(0x67A665, 0x67A676, 0x67A9B1, 0x67A9BE)),
    dict(name="g_T15Step", va=0x006F1D98, kind="i32", count=32, shape="[16][2]", read="WORD", via_ptr=False,
         readers=(0x67BC42, 0x67BC53, 0x67BC8C, 0x67BC9E, 0x67BCD3, 0x67BCE5, 0x67BD1F, 0x67BD31)),
    dict(name="g_T15DirFromStep", va=0x006F1E18, kind="i32", count=9, shape="[-4..4]", read="DWORD", via_ptr=False,
         readers=(0x67BBE3, 0x67BEDD)),
    dict(name="g_T15TurnB", va=0x006F1E40, kind="i32", count=16, shape="[16]", read="DWORD", via_ptr=True,
         readers=(0x67BC87, 0x67BCCB, 0x67BD1A)),
    dict(name="g_T15NextB", va=0x006F1E80, kind="i32", count=16, shape="[16]", read="DWORD", via_ptr=True,
         readers=(0x67BFFD,)),
    dict(name="g_T15TurnA", va=0x006F1EC0, kind="i32", count=16, shape="[16]", read="DWORD", via_ptr=True,
         readers=(0x67BC87, 0x67BCCB, 0x67BD1A)),
    dict(name="g_T15NextA", va=0x006F1F00, kind="i32", count=16, shape="[16]", read="DWORD", via_ptr=True,
         readers=(0x67BFFD,)),
    dict(name="g_PathDir8", va=0x006EB398, kind="i32", count=16, shape="[8][2]", read="WORD", via_ptr=False,
         readers=(0x6481C7, 0x6481CF, 0x648207, 0x648213, 0x64824E, 0x64825A)),
    dict(name="g_PathSignTable", va=0x006EB490 - 160, kind="i32", count=81, shape="[-40..40]", read="DWORD",
         via_ptr=False, readers=(0x648028, 0x648039, 0x6480B4, 0x6480C0)),
    dict(name="g_PathDirTable", va=0x006EB7E0, kind="i32", count=384, shape="[128][3]", read="DWORD", via_ptr=False,
         readers=(0x64FCE0, 0x64FCE7, 0x64FCF8, 0x64FD0F)),
    dict(name="g_PathDirZero", va=0x006EB7D4, kind="i32", count=2, shape="[2]", read="DWORD", via_ptr=False,
         readers=(0x64FF33, 0x64FF38, 0x6507D6, 0x6507DB)),
    dict(name="g_PathFaceStep", va=0x006EB548, kind="i32", count=64, shape="[64]", read="BYTE", via_ptr=False,
         readers=(0x648620, 0x64887B)),
)


def sign(x):
    return (x > 0) - (x < 0)


def step_dx(d):
    """dx of direction d (masked to 0..7): the eight compass steps, clockwise from +x with y down."""
    d &= 7
    return sign(2 - min(d, 8 - d))


def rule_step8():
    return [x for d in range(8) for x in (step_dx(d), step_dx(d - 2))]


def rule_t15_step():
    return [x for d in range(16) for x in (step_dx(d - 2), step_dx(d - 4))]


def rule_t15_dir_from_step():
    out = []
    for i in range(-4, 5):
        dx = (i + 1) % 3 - 1
        dy = (i - dx) // 3
        out.append(-1 if i == 0 else [d for d in range(8) if (step_dx(d - 2), step_dx(d - 4)) == (dx, dy)][0])
    return out


def rule_t15_up():
    return [((d & 6) + 2) & 7 for d in range(16)]


def rule_t15_next_a():
    return [((d & 6) + 6) & 7 for d in range(16)]


def rule_t15_turn_b():
    return [(((d + 1) & 6) + 6) & 7 for d in range(16)]


def rule_sign_table():
    out = []
    for i in range(-40, 41):
        a = (i + 4) % 9 - 4
        b = (i - a) // 9
        out.append(sign(a) if abs(a) >= abs(b) else 0)
    return out


def dirtable_z(q):
    """IEEE-754 binary64: the quotient and atan in double, truncated toward zero, clamped to 7."""
    return min(7, int(math.atan(q / 127.0) / (math.pi / 32.0)))


def rule_dir_table():
    out = []
    for q in range(128):
        den = q * q + 127 * 127
        out += [math.isqrt(4096 * 4096 * q * q // den), math.isqrt(4096 * 4096 * 127 * 127 // den), dirtable_z(q)]
    return out


def rule_face_step():
    """g_PathFaceStep: d = ((i + 32) & 63) - 32; t = (|d| + 7) >> 3; sign(d) * min(8, t * t). The readers take the low byte."""
    out = []
    for i in range(64):
        d = ((i + 32) & 63) - 32
        out.append(sign(d) * min(8, ((abs(d) + 7) >> 3) ** 2))
    return out


def dirtable_z_margin():
    """The smallest distance to an integer of z's quotient over q 1..126 (q 0 is exact, q 127 is clamped)."""
    return min(abs(v - round(v)) for v in (math.atan(q / 127.0) / (math.pi / 32.0) for q in range(1, 127)))


# The tables a rule gives (docs/tables/PathDirTables.md § The rules, ADR-0031). Every other table's values are in the doc.
RULES = {
    "g_PathStep8Long": rule_step8,
    "g_PathDir8": rule_step8,
    "g_T15Step": rule_t15_step,
    "g_T15DirFromStep": rule_t15_dir_from_step,
    "g_T15TurnA": rule_t15_up,
    "g_T15NextB": rule_t15_up,
    "g_T15NextA": rule_t15_next_a,
    "g_T15TurnB": rule_t15_turn_b,
    "g_PathSignTable": rule_sign_table,
    "g_PathDirTable": rule_dir_table,
    "g_PathDirZero": lambda: [0, 0],
    "g_PathFaceStep": rule_face_step,
}
DIST_COPY_VA = 0x006EB180   # the table of UnitInteractDistance, docs/specs/items/inventory.md I2: 64 i32


def mismatches(image, computed):
    """Elements that differ, a difference in length counting each missing element."""
    return sum(1 for a, b in zip(image, computed) if a != b) + abs(len(image) - len(computed))


def rule_report(dt):
    """-> [(name, elements, mismatches, image crc, rule crc)], one row per table a rule gives."""
    out = []
    for t, v in dt:
        if t["name"] in RULES:
            r = RULES[t["name"]]()
            out.append((t["name"], len(v), mismatches(v, r), crc(v), crc(r)))
    return out


def table_values(data, t):
    raw = read_bytes(data, t["va"], t["count"] * (4 if t["kind"] == "i32" else 1))
    return list(struct.unpack("<%d%s" % (t["count"], "i" if t["kind"] == "i32" else "B"), raw))


def dirtables(exe):
    data = load_image(exe)
    return [(t, table_values(data, t)) for t in DIRTABLES]


def crc(vals):
    return zlib.crc32(struct.pack("<%di" % len(vals), *vals)) & 0xFFFFFFFF


def cmd_dirtables(exe):
    for t, v in dirtables(exe):
        print("%s  0x%08X  %s %s  read as %s%s  crc32 %d" % (
            t["name"], t["va"], t["kind"], t["shape"], t["read"], " through a pointer" if t["via_ptr"] else "", crc(v)))
        if t["name"] not in RULES:
            print("    " + " ".join(str(x) for x in v))


def fmt_rows(v, per):
    return "\n".join(" ".join("%d" % x for x in v[i:i + per]) for i in range(0, len(v), per))


# (name, values per printed line) for the Markdown of the doc's value blocks: the tables no rule gives
MD_ROWS = {"g_DirOctant": 3, "g_PathDirTriples": 3, "g_PathDistNear": 8, "g_PathSearchTurnRows": 8}


def cmd_dirmd(exe):
    for t, v in dirtables(exe):
        if t["name"] in MD_ROWS:
            print("#### %s  `0x%08X`\n\n```\n%s\n```\n" % (t["name"], t["va"], fmt_rows(v, MD_ROWS[t["name"]])))


def cmd_rules(exe):
    rep = rule_report(dirtables(exe))
    for name, n, bad, ci, cr in rep:
        print("%-18s elements %3d  mismatches %d  crc32 image %d  rule %d" % (name, n, bad, ci, cr))
    print("rule tables %d  elements %d  mismatches %d  z margin %.6f" % (
        len(rep), sum(r[1] for r in rep), sum(r[2] for r in rep), dirtable_z_margin()))
    return 1 if any(r[2] for r in rep) else 0


def objdump_at(exe, addr):
    """The instruction text at addr, from objdump (None when objdump is not there or prints nothing)."""
    try:
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % addr,
                              "--stop-address=0x%x" % (addr + 12), exe], capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    for ln in out.splitlines():
        m = re.match(r"^\s+([0-9a-f]+):\s+(.*)$", ln)
        if m and int(m.group(1), 16) == addr:
            return m.group(2).strip()
    return None


def operand_size(text):
    """DWORD / WORD / BYTE of the memory operand in an objdump line; a bare ds:0x... operand is a DWORD move
    (objdump omits the size when the register names it: eax -> DWORD)."""
    m = re.search(r"\b(DWORD|WORD|BYTE) PTR", text)
    if m:
        return m.group(1)
    if re.search(r"\bmov\s+e[a-z]{2},ds:0x", text):
        return "DWORD"
    return None


def reader_report(exe):
    """-> [(table name, address, instruction text, operand size, matches the table's stated width)]"""
    load_image(exe)
    out = []
    for t in DIRTABLES:
        for a in t["readers"]:
            txt = objdump_at(exe, a)
            sz = operand_size(txt) if txt else None
            out.append((t["name"], a, txt, sz, sz == t["read"]))
    return out


def cmd_readers(exe):
    for name, a, txt, sz, ok in reader_report(exe):
        print("%-22s 0x%08X  %-9s %s  %s" % (name, a, sz or "?", "ok " if ok else "BAD", txt))


def symbols():
    out = {}
    try:
        for line in open(SYMBOLS):
            f = line.rstrip("\n").split(",")
            if len(f) > 3 and f[0].startswith("0x") and f[1] == "func":
                out[int(f[0], 16)] = f[2]
    except OSError:
        pass
    return out


def slots(exe):
    data = load_image(exe)
    fl = read_u32s(data, FLAGS_VA, N_TYPES)
    fn = read_u32s(data, FUNCS_VA, N_TYPES)
    sym = symbols()
    return [(t, fn[t], fl[t], sym.get(fn[t], "")) for t in range(N_TYPES)]


def cmd_types(exe):
    for t, fn, fl, name in slots(exe):
        print("%2d  planner %s  flags 0x%05X  %s" % (t, "0x%08X" % fn if fn else "none      ", fl, name))


def cmd_md(exe):
    print("| type | planner (`g_PathPlanFuncs[type]`) | symbol | flags (`0x006EB690[type]`) |")
    print("|---:|---|---|---|")
    for t, fn, fl, name in slots(exe):
        print("| %d | %s | %s | `0x%05X` |" % (t, "`0x%08X`" % fn if fn else "none (0)", "`%s`" % name if name else "-", fl))


class Cols:
    def __init__(self, d):
        self.d = d
        self.ms2 = eb.load_table(d, "monstats2")
        self.mi = eb.load_table(d, "missiles")
        self.sk = eb.load_table(d, "skills")

    def col(self, tab, name):
        h, rows = tab[0], tab[1]
        i = h.index(name)
        return [r[i] for r in rows]


def counts(vals):
    c = collections.Counter(v if v != "" else "blank" for v in vals)
    return " ".join("%s:%d" % (k, c[k]) for k in sorted(c, key=lambda x: (x == "blank", str(x))))


def skill_hits(c):
    """-> [(column, number, type, finding, [(row index, skill, charclass, [missiles])])]"""
    h, rows = c.sk[0], c.sk[1]
    ix = {n: i for i, n in enumerate(h)}
    out = []
    for col, num, typ, why in SKILL_FUNCS:
        hit = []
        for i, r in enumerate(rows):
            if r[ix[col]] == str(num):
                ms = [r[ix[m]] for m in ("srvmissile", "srvmissilea", "srvmissileb", "srvmissilec") if r[ix[m]]]
                hit.append((i, r[ix["skill"]], r[ix["charclass"]], ms))
        out.append((col, num, typ, why, hit))
    return out


def class195(c):
    h, rows = c.mi[0], c.mi[1]
    ix = {n: i for i, n in enumerate(h)}
    name = rows[195][ix["Missile"]] if len(rows) > 195 else ""
    users = []
    for i, r in enumerate(c.sk[1]):
        for m in ("srvmissile", "srvmissilea", "srvmissileb", "srvmissilec"):
            if name and r[c.sk[0].index(m)] == name:
                users.append((r[c.sk[0].index("skill")], m))
    return name, users


def cmd_columns(d):
    c = Cols(d)
    print("MonStats2 SizeX  (%d rows): %s" % (len(c.ms2[1]), counts(c.col(c.ms2, "SizeX"))))
    print("MonStats2 SizeY  (%d rows): %s" % (len(c.ms2[1]), counts(c.col(c.ms2, "SizeY"))))
    print("Missiles Size    (%d rows): %s" % (len(c.mi[1]), counts(c.col(c.mi, "Size"))))
    for col in ("srvstfunc", "srvdofunc"):
        print("Skills %-9s (%d rows): %d distinct, %d blank" % (
            col, len(c.sk[1]), len({v for v in c.col(c.sk, col) if v}), sum(1 for v in c.col(c.sk, col) if not v)))


def cmd_rows(d):
    c = Cols(d)
    for col, num, typ, why, hit in skill_hits(c):
        print("%s %d -> type %d  [%s]" % (col, num, typ, why))
        for i, s, cc, ms in hit:
            print("    skills row %d %s (%s) missiles: %s" % (i, s, cc or "-", ",".join(ms) or "-"))
    name, users = class195(c)
    print("Missiles row 195: %r named by %s" % (name, users or "no Skills srvmissile column"))


def cmd_summary(d, exe):
    kv = collections.OrderedDict()
    sl = slots(exe)
    kv["path_types"] = len(sl)
    kv["path_planner_slots_set"] = sum(1 for s in sl if s[1])
    kv["path_planner_distinct"] = len({s[1] for s in sl if s[1]})
    kv["path_planner_named"] = sum(1 for s in sl if s[3])
    kv["path_flags_nonzero"] = sum(1 for s in sl if s[2])
    kv["path_flags_40000"] = sum(1 for s in sl if s[2] & 0x40000)
    kv["path_no_planner_types"] = sum(1 for s_ in sl if not s_[1])
    kv["path_no_planner_and_40000"] = sum(1 for s_ in sl if not s_[1] and s_[2] & 0x40000)
    c = Cols(d)
    sx = collections.Counter(c.col(c.ms2, "SizeX"))
    kv["ms2_rows"] = len(c.ms2[1])
    for v in ("0", "1", "2", "3"):
        kv["ms2_sizex_%s" % v] = sx.get(v, 0)
    kv["ms2_sizex_other"] = kv["ms2_rows"] - sum(sx.get(v, 0) for v in ("0", "1", "2", "3"))
    mz = collections.Counter(c.col(c.mi, "Size"))
    kv["missiles_rows"] = len(c.mi[1])
    for v in ("1", "2", "3", ""):
        kv["missiles_size_%s" % (v or "blank")] = mz.get(v, 0)
    for col, num, typ, why, hit in skill_hits(c):
        kv["skills_%s_%d_rows" % (col, num)] = len(hit)
    kv["missiles_195_users"] = len(class195(c)[1])
    dt = dirtables(exe)
    kv["dirtables"] = len(dt)
    kv["dirtable_elements"] = sum(len(v) for _, v in dt)
    for t, v in dt:
        kv["dirtab_%s" % t["name"][2:].lower()] = crc(v)
    byname = {t["name"]: v for t, v in dt}
    kv["dirtab_dir8_eq_step8long"] = int(byname["g_PathDir8"] == byname["g_PathStep8Long"])
    kv["dirtab_word_tables_fit_i16"] = int(all(-32768 <= x <= 32767 for t, v in dt if t["read"] == "WORD" for x in v))
    kv["dirtab_octant_max"] = max(byname["g_DirOctant"][i] for i in range(75))
    copy = list(struct.unpack("<64i", read_bytes(load_image(exe), DIST_COPY_VA, 256)))
    kv["dirtab_distnear_eq_6eb180"] = int(copy == byname["g_PathDistNear"])
    rep = rule_report(dt)
    kv["dirtab_kept_tables"] = len(dt) - len(rep)
    kv["dirtab_kept_elements"] = kv["dirtable_elements"] - sum(r[1] for r in rep)
    kv["dirtab_rule_tables"] = len(rep)
    kv["dirtab_rule_elements"] = sum(r[1] for r in rep)
    kv["dirtab_rule_mismatches"] = sum(r[2] for r in rep)
    kv["dirtab_z_margin_micro"] = int(dirtable_z_margin() * 1000000)
    print("SURVEY path " + " ".join("%s=%s" % kv_ for kv_ in kv.items()))
    return 1 if kv["dirtab_rule_mismatches"] else 0


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    rc = 0
    if cmd in ("types", "md"):
        (cmd_types if cmd == "types" else cmd_md)(argv[2])
    elif cmd == "columns":
        cmd_columns(argv[2])
    elif cmd == "rows":
        cmd_rows(argv[2])
    elif cmd == "dirtables":
        cmd_dirtables(argv[2])
    elif cmd == "dirmd":
        cmd_dirmd(argv[2])
    elif cmd == "readers":
        cmd_readers(argv[2])
    elif cmd == "rules":
        rc = cmd_rules(argv[2])
    elif cmd == "summary" and len(argv) >= 4:
        rc = cmd_summary(argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    if cmd in ("types", "md", "columns", "rows", "dirtables", "dirmd", "readers", "rules"):
        print("SURVEY path cmd=%s" % cmd)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

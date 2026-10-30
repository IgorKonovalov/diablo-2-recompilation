"""Survey of the path types and the columns a path request reads (plan 0054 Phase 0).

Usage:
  python3 -I tools/path_survey.py types   <game.exe>
  python3 -I tools/path_survey.py md      <game.exe>
  python3 -I tools/path_survey.py columns <excel-dir>
  python3 -I tools/path_survey.py rows    <excel-dir>
  python3 -I tools/path_survey.py summary <excel-dir> <game.exe>

types    the 17 slots of g_PathPlanFuncs (0x006EB6D8, u32 planner address, 0 = none) and of the flags table
         (0x006EB690, u32 flags word), read from the pinned image (sha256 checked), with the symbol name of the
         planner address when re/symbols.csv has one.
md       the same as the Markdown table of docs/tables/PathTypes.md § The 17 slots (generated, not typed).
columns  the unit-size columns a request reads through PATH_PatternFromSize (MonStats2 SizeX, Missiles Size, the
         player's fixed size) and the Skills columns that name the start / do functions the findings tie to a path
         type: value counts.
rows     the stock Skills rows per (function column, number) the findings tie to a path type, with the missile
         columns they name, and the Missiles rows that name class 195 (plan 0054 H1 cases).
summary  counts only.

Every command ends with `SURVEY path key=value ...`; tools/gate.py --full compares the summary line with its
baseline. The image is read only when its sha256 is the pinned one (docs/inventory.md). Slot meanings are [L]
here; the planner names come from re/symbols.csv. Stdlib only. Read-only.
"""
import collections
import hashlib
import os
import struct
import sys

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
    print("SURVEY path " + " ".join("%s=%s" % kv_ for kv_ in kv.items()))


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd in ("types", "md"):
        (cmd_types if cmd == "types" else cmd_md)(argv[2])
    elif cmd == "columns":
        cmd_columns(argv[2])
    elif cmd == "rows":
        cmd_rows(argv[2])
    elif cmd == "summary" and len(argv) >= 4:
        cmd_summary(argv[2], argv[3])
    else:
        print(__doc__)
        return 2
    if cmd in ("types", "md", "columns", "rows"):
        print("SURVEY path cmd=%s" % cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

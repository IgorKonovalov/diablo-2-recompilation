#!/usr/bin/env python3
"""lane/r71: the constants of AI rows 25 and 94 in the pinned image (ADR-0031), checked element by element.

    python3 -I tools/ai_const_survey.py summary <game.exe>   the rules' mismatches and the checksums, never the values
    python3 -I tools/ai_const_survey.py values <game.exe>    every value (keep under workspace/logs/, never in docs/)
    python3 -I tools/ai_const_survey.py emu <game.exe>       the wisp's frame tables again, from the think's own stores
                                                             run in tools/ai_resume.py's interpreter (needs objdump)
    python3 -I tools/ai_const_survey.py skills <excel dir>   Skills' aitype counts and each row's EType byte in skills.bin
    python3 -I tools/ai_const_survey.py logs <logs/ai dir>   AID lines of rows 25, 94, 106, 143 (and 2, the control) over *.log

Row 94 `DesertTurret`: `STEP` at 0x006E33A0 (8 rows of two i32), by the rule `step_rule`; `SWEEP` at 0x006E33E0 (64 i32,
index v + 8·d), listed: `sweep_cases` is a description by cases with one patched cell, which ADR-0031 does not count as
a rule, kept here to report that it equals the other 63 cells.
Row 25 `WillOWisp`: four frame tables the think stores at every entry (0x005F39E1..0x005F3E07), 132 dword stores read
from the bytes by a decoder that refuses any other instruction: `A` EBP-0x2F4 and `B` EBP-0x214 (8-byte rows, index
p + 4·s, p 1..4, s 6..12: 28 rows each), `A5` EBP-0x38 and `B5` EBP-0x64 (index 1..5). `B5` is by the rule `b5_rule`.
`A` and `B` have no rule known and are not in docs/ (the architect's call): only their checksums are in the summary.

Every command ends with `SURVEY ai_const key=value ...`; tools/gate.py --full compares the summary line with its
baseline. The image is read only when its sha256 is the pinned one. Stdlib only, except `emu`. Read-only.
"""
import hashlib
import os
import struct
import sys
import zlib

PINNED_SHA256 = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
STEP, SWEEP = 0x006E33A0, 0x006E33E0
STORES_LO, STORES_HI = 0x005F39E1, 0x005F3E0A
FRAMES = {"A": (-0x2F4, 25, 53), "B": (-0x214, 25, 53), "A5": (-0x38, 1, 6), "B5": (-0x64, 1, 6)}


def load(path):
    d = open(path, "rb").read()
    if hashlib.sha256(d).hexdigest() != PINNED_SHA256:
        raise SystemExit("not the pinned image: " + path)
    return d


def off(a):
    if 0x00401000 <= a < 0x006CC000:
        return a - 0x00401000 + 0x1000
    if 0x006CC000 <= a < 0x00705000:
        return a - 0x006CC000 + 0x2CC000
    raise ValueError(hex(a))


def clamp1(v):
    return max(-1, min(1, v))


def step_rule(i):
    """STEP[i], i in 0..7."""
    j, k = (i + 1) % 8, (i - 1) % 8
    return clamp1(2 - min(j, 8 - j)), clamp1(2 - min(k, 8 - k))


def sweep_cases(d, v):
    """The description by cases: stay on d; one step up when (d - v) mod 8 is 1..4; one step down when 5..7. Not a rule
    (ADR-0031): the cell d = 3, v = 7 breaks it."""
    e = (d - v) % 8
    return v if e == 0 else (v + 1) % 8 if e <= 4 else (v - 1) % 8


def b5_rule(a5, p):
    """B5[p] = A5[((p + 1) mod 5) + 1], p in 1..5."""
    return a5[((p + 1) % 5) + 1]


def wisp_frame(d):
    """{ebp offset: value} from the bytes of the stores; any other instruction raises."""
    regs = {"eax": -5, "edx": 1, "ecx": None}
    names = {0: "eax", 1: "ecx", 2: "edx"}
    a, mem, n = STORES_LO, {}, 0
    i4 = lambda o: struct.unpack_from("<i", d, o)[0]
    while a < STORES_HI:
        o = off(a)
        b = d[o]
        if b == 0xB9:
            regs["ecx"] = i4(o + 1)
            a += 5
        elif d[o:o + 2] == b"\x33\xC9":
            regs["ecx"] = 0
            a += 2
        elif d[o:o + 4] == b"\x83\x7D\x08\x00":
            a += 4
        elif b == 0xC7 and d[o + 1] == 0x85:
            mem[i4(o + 2)] = i4(o + 6)
            a += 10
            n += 1
        elif b == 0xC7 and d[o + 1] == 0x45:
            mem[struct.unpack_from("<b", d, o + 2)[0]] = i4(o + 3)
            a += 7
            n += 1
        elif b == 0x89 and d[o + 1] in (0x85, 0x8D, 0x95):
            mem[i4(o + 2)] = regs[names[(d[o + 1] >> 3) & 7]]
            a += 6
            n += 1
        elif b == 0x89 and d[o + 1] in (0x45, 0x4D, 0x55):
            mem[struct.unpack_from("<b", d, o + 2)[0]] = regs[names[(d[o + 1] >> 3) & 7]]
            a += 3
            n += 1
        else:
            raise ValueError("unexpected instruction at %08x" % a)
    return mem, n


def wisp_tables(mem):
    out = {}
    for name, (base, lo, hi) in FRAMES.items():
        out[name] = {e: (mem[base + 8 * e], mem[base + 8 * e + 4]) for e in range(lo, hi)}
    return out


def crc(vals):
    return zlib.crc32(struct.pack("<%di" % len(vals), *vals)) & 0xFFFFFFFF


def flat(t):
    return [v for e in sorted(t) for v in t[e]]


def report(d):
    kv = {}
    step = struct.unpack_from("<16i", d, off(STEP))
    sweep = struct.unpack_from("<64i", d, off(SWEEP))
    kv["step_elements"] = len(step)
    kv["step_rule_mismatches"] = sum(1 for i in range(8) if tuple(step[2 * i:2 * i + 2]) != step_rule(i))
    kv["step_crc"] = crc(step)
    kv["sweep_elements"] = len(sweep)
    kv["sweep_cells_outside_cases"] = sum(1 for dd in range(8) for v in range(8) if sweep[8 * dd + v] != sweep_cases(dd, v))
    kv["sweep_crc"] = crc(sweep)
    mem, n = wisp_frame(d)
    t = wisp_tables(mem)
    kv["wisp_stores"] = n
    used = sum(len(x) * 2 for x in t.values())
    kv["wisp_elements"] = used
    kv["wisp_a_crc"], kv["wisp_b_crc"] = crc(flat(t["A"])), crc(flat(t["B"]))
    kv["wisp_a5_crc"], kv["wisp_b5_crc"] = crc(flat(t["A5"])), crc(flat(t["B5"]))
    kv["wisp_b5_rule_mismatches"] = sum(1 for p in range(1, 6) if t["B5"][p] != b5_rule(t["A5"], p))
    kv["wisp_zero_rows"] = sum(1 for x in t.values() for v in x.values() if v == (0, 0))
    return kv, step, sweep, t


def cmd_skills(ex):
    """What row 106's score meets in the stock table: the aitype values, and blank EType in the compiled table."""
    import collections
    import csv
    rows = list(csv.DictReader(open(os.path.join(ex, "skills.txt"), encoding="latin-1"), delimiter="\t"))
    rows = [r for r in rows if r["skill"] != "Expansion"]
    types = collections.Counter(int(r["aitype"]) for r in rows if r["aitype"])
    print("AITYPE " + " ".join("%d=%d" % kv for kv in sorted(types.items())))
    d = open(os.path.join(ex, "skills.bin"), "rb").read()
    n = struct.unpack_from("<I", d, 0)[0]
    if 4 + n * 0x23C != len(d):
        raise SystemExit("skills.bin: unexpected size")
    et = collections.Counter(d[4 + 0x23C * i + 0x1DC] for i in range(n))
    print("ETYPE_BYTE " + " ".join("%d=%d" % kv for kv in sorted(et.items())))
    hi = sum(1 for i in range(n) if d[4 + 0x23C * i + 0x231])
    print("AITYPE_HIGH_BYTE_NONZERO %d" % hi)
    print("SURVEY ai_const_skills rows=%d aitype_rows=%d" % (n, sum(types.values())))
    return 0


def cmd_logs(dirname):
    """Can a log test these rows? Counts over every *.log directly in the directory."""
    keys = {"ai=%d" % k: '"ai":%d,' % k for k in (25, 94, 106, 143, 2)}
    keys["th=0x005EB970"], keys["c=418"] = '"th":6207856,', '"c":418,'
    n = dict.fromkeys(keys, 0)
    files = sorted(f for f in os.listdir(dirname) if f.endswith(".log"))
    for f in files:
        for ln in open(os.path.join(dirname, f), encoding="latin-1"):
            if ln.startswith("AID "):
                for k, v in keys.items():
                    n[k] += v in ln
    print("LOGS files=%d " % len(files) + " ".join("%s:%d" % kv for kv in n.items()))
    print("SURVEY ai_const_logs files=%d" % len(files))
    return 0


def main(argv):
    if len(argv) == 2 and argv[0] == "skills":
        return cmd_skills(argv[1])
    if len(argv) == 2 and argv[0] == "logs":
        return cmd_logs(argv[1])
    if len(argv) != 2 or argv[0] not in ("summary", "values", "emu"):
        print(__doc__)
        return 2
    d = load(argv[1])
    kv, step, sweep, t = report(d)
    bad = kv["step_rule_mismatches"] + kv["wisp_b5_rule_mismatches"] + (kv["wisp_stores"] != kv["wisp_elements"])
    if argv[0] == "values":
        print("STEP", step)
        for i in range(8):
            print("SWEEP d=%d" % i, sweep[8 * i:8 * i + 8])
        print("SWEEP outside the cases:", [(dd, v, sweep[8 * dd + v]) for dd in range(8) for v in range(8) if sweep[8 * dd + v] != sweep_cases(dd, v)])
        for name in ("A", "B"):
            for s in range(6, 13):
                print(name, "s=%d" % s, [t[name][p + 4 * s] for p in range(1, 5)])
        print("A5", [t["A5"][p] for p in range(1, 6)])
        print("B5", [t["B5"][p] for p in range(1, 6)])
    if argv[0] == "emu":
        here = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, here)
        import ai_resume as R
        code = R.Code(exe=argv[1])
        st = R.State()
        ebp = R.STK_TOP - 0x1000
        st.r.update({"esp": ebp - 0x400, "ebp": ebp, "eax": R.u32(-5), "edx": 1, "ecx": 0, "ebx": 0, "esi": 0, "edi": 0})
        st.wr(ebp + 8, 4, 0)
        st.eip = 0x005F39D1
        m = R.Machine(code, ())
        while st.eip != STORES_HI:
            i = code.at(st.eip)
            if i and i[1] == ".byte":    # Code's 0x200 window cut this 10-byte store: decode again from its own start
                del code.ins[st.eip]
                code.loaded.discard(st.eip)
                code._load(st.eip)
            st = m.step(st)[0]
        diff = 0
        for name, (base, lo, hi) in FRAMES.items():
            for e in range(lo, hi):
                got = (R.s32(st.rd(ebp + base + 8 * e, 4)), R.s32(st.rd(ebp + base + 8 * e + 4, 4)))
                diff += got != t[name][e]
        print("emu: rows compared %d, differences %d" % (sum(len(x) for x in t.values()), diff))
        kv = {"emu_rows": sum(len(x) for x in t.values()), "emu_differences": diff}
        bad += diff
    print("SURVEY ai_const " + " ".join("%s=%s" % x for x in kv.items()))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

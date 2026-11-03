#!/usr/bin/env python3
"""Plan 0054 Phase 1.1 (`lane/r54a`): static scans of the pinned Game.exe behind docs/findings/path/0001.

    python3 -I tools/path_scan.py sites  <game.exe> [--target 0xADDR]   every direct call (E8) and jump (E9) to the
                                                                          target (default PathPlan 0x00649970)
    python3 -I tools/path_scan.py tables <game.exe>                       the image tables PathPlan and its helpers read
    python3 -I tools/path_scan.py draws  <game.exe>                       LCG multiplier uses and RNG calls in the P1.1
                                                                          function ranges
    python3 -I tools/path_scan.py writers <game.exe> --off 0xNN [--size 1|2|4]   instructions storing to [reg+off]

sites: the raw E8/E9 scan finds every rel32 whose target is the address; each hit is kept only when objdump, run from
the containing function's entry (re/symbols.csv, else the nearest preceding int3-padded boundary) up to the site,
decodes an instruction starting exactly at the hit (so a byte pattern inside another instruction is dropped and
counted). Per site: the containing function, its name and subsystem from re/symbols.csv, the three stack arguments
(the last three pushes before the call, as objdump prints them), and the path-type evidence found in the same
function before the site: every `call PathSetType` (0x00648CF0) with its second push, every store to `[reg+0x3c]`
(the path type word), and every call to the AI's type setters (0x005A6290 MonPathPlanType's own body excluded). The
owner (the request register's column) is then given by tools/path_register.txt-style rules in the finding, not here:
this prints the raw evidence only.

draws: for each range in RANGES (the functions read by P1.1), counts `imul ...,0x6ac690c5` and calls to the RNG
functions named in re/symbols.csv (names starting RNG_ or containing Rng/Draw, listed in RNG_FNS), plus every call
target, so a reader can follow which callees are outside the scan.

Every command ends with a `SCAN path ...` summary line. Stdlib plus objdump. Read-only.
"""
import argparse
import csv
import hashlib
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PINNED = "631066c1649c4ea9ffe48bf97e24c00bca1f7a6759c21150f1a79982589adaaf"
PATHPLAN = 0x00649970
PATHSETTYPE = 0x00648CF0
BASE = 0x400000

# the functions P1.1 reads (entry, end): objdump ranges
RANGES = (
    (0x00649970, 0x00649C92, "sub_00649970_PathPlan"),
    (0x006498A0, 0x00649955, "sub_006498A0_PathTargetRefresh"),
    (0x006497D0, 0x00649898, "sub_006497D0_PathTargetObjectAdjust"),
    (0x00649760, 0x006497C9, "sub_00649760_PathPlanStraight"),
    (0x006492F0, 0x006493FA, "sub_006492F0_PathPlanToUnit"),
    (0x00647FB0, 0x00648018, "sub_00647FB0_PathPointsOutsideRoom"),
    (0x00648050, 0x0064811D, "sub_00648050_PathTargetNudgePlayer"),
    (0x00648120, 0x006482FB, "sub_00648120_PathTargetFree"),
    (0x006483A0, 0x00648427, "sub_006483A0_PathTargetNotTown"),
    (0x00648CF0, 0x00648DBE, "sub_00648CF0_PathSetType"),
    (0x00648E70, 0x00648E93, "sub_00648E70_PathSetByte90"),
    (0x00649070, 0x0064909E, "sub_00649070_PathSetStopDist"),
    (0x006490E0, 0x00649117, "sub_006490E0_PathSetByte94"),
    (0x00649140, 0x00649179, "sub_00649140_PathAddByte94"),
    (0x00649D00, 0x00649EE5, "PATH_DynamicCreate"),
    (0x00554850, 0x00554A17, "sub_00554850_SUnitPathCreate"),
    (0x0064FE40, 0x0064FF90, "sub_0064FE40_PathAimNextPoint"),
    (0x00650350, 0x006503F0, "sub_00650350_PathReplan"),
    (0x00678DF0, 0x00678E30, "sub_00678DF0_PathDirIndex3"),
    (0x00678C10, 0x00678DF0, "sub_00678C10_PathDirIndex"),
)


def load(exe):
    data = open(exe, "rb").read()
    if hashlib.sha256(data).hexdigest() != PINNED:
        raise SystemExit("path_scan: %s is not the pinned Game.exe" % exe)
    return data


def sections(data):
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    n = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    so = pe + 24 + opt
    out = []
    for i in range(n):
        name = data[so + 40 * i:so + 40 * i + 8].rstrip(b"\0").decode()
        vs, va, rs, raw = struct.unpack_from("<IIII", data, so + 40 * i + 8)
        out.append((name, BASE + va, vs, raw, rs))
    return out


def va_bytes(data, va, n):
    for name, sva, vs, raw, rs in sections(data):
        if sva <= va and va + n <= sva + rs:
            return data[raw + va - sva:raw + va - sva + n]
    raise ValueError(hex(va))


def symbols():
    funcs = {}
    with open(os.path.join(ROOT, "re", "symbols.csv")) as f:
        for r in csv.DictReader(f):
            if r["kind"] == "func":
                funcs[int(r["address"], 16)] = (r["name"], r["subsystem"], r["confidence"])
    return funcs


def objdump(exe, lo, hi):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=0x%x" % lo,
                          "--stop-address=0x%x" % hi, exe], capture_output=True, text=True, check=True).stdout
    ins = []
    for ln in out.splitlines():
        m = re.match(r"^\s+([0-9a-f]+):\s+(.*)$", ln)
        if m:
            ins.append((int(m.group(1), 16), m.group(2).strip()))
    return ins


def func_start(data, funcs, site):
    cands = [a for a in funcs if a <= site]
    best = max(cands) if cands else None
    # walk back over code until an int3 pad (0xCC 0xCC) boundary, if it is nearer than the symbol entry
    text = [s for s in sections(data) if s[0] == ".text"][0]
    a = site
    while a > text[1] + 2:
        b = va_bytes(data, a - 2, 2)
        if b == b"\xcc\xcc" and a % 16 == 0:
            break
        a -= 1
    if best is None or a > best:
        return a, None
    return best, funcs[best]


def rel_hits(data, target, op):
    text = [s for s in sections(data) if s[0] == ".text"][0]
    _, sva, vs, raw, rs = text
    blob = data[raw:raw + min(vs, rs)]
    hits = []
    i = blob.find(op)
    while i >= 0:
        if i + 5 <= len(blob):
            rel = struct.unpack_from("<i", blob, i + 1)[0]
            site = sva + i
            if (site + 5 + rel) & 0xFFFFFFFF == target:
                hits.append(site)
        i = blob.find(op, i + 1)
    return hits


REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")


def resolve(before, push):
    """The pushed operand of `push` (address, text): an immediate as is; a register resolved to the last write to it
    before the push in the same linear window when that write is `mov r,imm`, `xor r,r`, `lea r,[q+imm]` with q
    itself resolved, or `mov r,q`; otherwise the register name with '?'."""
    op = push[1].split(None, 1)[1]
    if op not in REGS:
        return op
    seen = set()

    def val(reg, upto):
        if (reg, upto) in seen:
            return None
        seen.add((reg, upto))
        for a, t in reversed([x for x in before if x[0] < upto]):
            m = re.match(r"(\w+)\s+(.*)$", t)
            if not m:
                continue
            mn, ops = m.group(1), m.group(2)
            parts = [x.strip() for x in ops.split(",")]
            if mn in ("call",):
                if reg in ("eax", "ecx", "edx"):
                    return None
                continue
            if not parts or parts[0] != reg:
                if mn in ("pop",) and ops == reg:
                    return None
                continue
            if mn == "xor" and len(parts) == 2 and parts[1] == reg:
                return 0
            if mn == "mov" and len(parts) == 2:
                if re.match(r"^0x[0-9a-f]+$", parts[1]):
                    return int(parts[1], 16)
                if parts[1] in REGS:
                    return val(parts[1], a)
                return None
            if mn == "lea" and len(parts) == 2:
                mm = re.match(r"^\[(\w+)\+0x([0-9a-f]+)\]$", parts[1])
                if mm and mm.group(1) in REGS:
                    b = val(mm.group(1), a)
                    return None if b is None else b + int(mm.group(2), 16)
                return None
            return None
        return None

    v = val(op, push[0])
    return "%s=0x%x" % (op, v) if v is not None else op + "?"


def cmd_sites(exe, target):
    data = load(exe)
    funcs = symbols()
    rows, dropped = [], 0
    for op, kind in ((b"\xe8", "call"), (b"\xe9", "jmp")):
        for site in rel_hits(data, target, op):
            lo, meta = func_start(data, funcs, site)
            ins = objdump(exe, lo, site + 5)
            at = [t for t in ins if t[0] == site]
            if not at or not at[0][1].startswith(kind):
                dropped += 1
                continue
            before = [t for t in ins if t[0] < site]
            pushes = [t for t in before if t[1].startswith("push")][-3:]
            ev = []
            for k, (a, t) in enumerate(before):
                if t.startswith("call") and "0x648cf0" in t:
                    pp = [x for x in before[:k] if x[1].startswith("push")][-2:]
                    ev.append("settype@%08X(%s)" % (a, resolve(before, pp[0]) if len(pp) == 2 else "?"))
                elif re.search(r"mov\s+DWORD PTR \[\w+\+0x3c\],", t):
                    ev.append("st3c@%08X(%s)" % (a, t.split(",", 1)[1]))
                elif t.startswith("call") and re.search(r"0x5a6290|0x5de190|0x5a6260", t):
                    ev.append("aitype@%08X(%s)" % (a, t.split()[-1]))
            name = meta[0] if meta else "-"
            sub = meta[1] if meta else "-"
            rows.append((site, kind, lo, name, sub, [p[1].split(None, 1)[1] for p in pushes], ev))
    for site, kind, lo, name, sub, pushes, ev in sorted(rows):
        print("S %08X %s fn=%08X %s sub=%s args=[%s] type=[%s]" % (
            site, kind, lo, name, sub, " | ".join(reversed(pushes)), " ".join(ev) if ev else "-"))
    nf = len(set(r[2] for r in rows))
    print("SCAN path sites target=%08X calls=%d jumps=%d functions=%d dropped=%d" % (
        target, sum(r[1] == "call" for r in rows), sum(r[1] == "jmp" for r in rows), nf, dropped))


def cmd_tables(exe):
    data = load(exe)
    w = struct.unpack("<17i", va_bytes(data, 0x006EB648, 68))
    print("T98 " + " ".join("%d:%d" % (i, v) for i, v in enumerate(w)))
    fl = struct.unpack("<17I", va_bytes(data, 0x006EB690, 68))
    print("TFLAGS " + " ".join("%d:%05X" % (i, v) for i, v in enumerate(fl)))
    pf = struct.unpack("<17I", va_bytes(data, 0x006EB6D8, 68))
    print("TFUNCS " + " ".join("%d:%08X" % (i, v) for i, v in enumerate(pf)))
    d8 = struct.unpack("<16i", va_bytes(data, 0x006EB398, 64))
    print("TDIR8 " + " ".join("%d:(%d,%d)" % (i, d8[2 * i], d8[2 * i + 1]) for i in range(8)))
    t3 = va_bytes(data, 0x006F1648, 3 * 25)
    print("T1648 " + " ".join("%d:(%d,%d,%d)" % (i, t3[3 * i], t3[3 * i + 1], t3[3 * i + 2]) for i in range(25)))
    t490 = struct.unpack("<81i", va_bytes(data, 0x006EB490 - 160, 324))
    print("T490 " + " ".join("%d:%d" % (i - 40, v) for i, v in enumerate(t490)))
    print("TACTS " + " ".join("%d:%d" % (i, v) for i, v in enumerate(struct.unpack("<6i", va_bytes(data, 0x006EB2F0, 24)))))
    m = va_bytes(data, 0x0057F174, 18)
    jt = struct.unpack("<4I", va_bytes(data, 0x0057F164, 16))
    print("TPLRMOVE " + " ".join("mode%d:%08X" % (k + 2, jt[b]) for k, b in enumerate(m)))
    print("TNPCMASK %08X %08X" % struct.unpack("<II", va_bytes(data, 0x006CE268, 4) + va_bytes(data, 0x006CE270, 4)))
    iat = struct.unpack("<I", va_bytes(data, 0x006CC34C, 4))[0]
    hint = va_bytes(data, BASE + iat + 2, 16).split(b"\0")[0].decode() if iat and iat < 0x1000000 else "?"
    print("TIAT 006CC34C -> %s" % hint)
    jt = struct.unpack("<5I", va_bytes(data, 0x00649958, 20))
    print("TJT649958 " + " ".join("%d:%08X" % (i, v) for i, v in enumerate(jt)))
    jt2 = struct.unpack("<6I", va_bytes(data, 0x00554A18, 24))
    print("TJT554A18 " + " ".join("%d:%08X" % (i, v) for i, v in enumerate(jt2)))
    print("SCAN path tables t98_nonzero=%d" % sum(1 for v in w if v))


RNG_FNS = None


def rng_fns():
    out = {}
    for a, (n, s, c) in symbols().items():
        if n.startswith("RNG_") or "Draw" in n or "Rng" in n:
            out[a] = n
    return out


def cmd_draws(exe):
    rf = rng_fns()
    tot_l = tot_r = 0
    for lo, hi, name in RANGES:
        ins = objdump(exe, lo, hi)
        lcg = [a for a, t in ins if "0x6ac690c5" in t]
        calls = []
        rng = []
        for a, t in ins:
            m = re.match(r"(call|jmp)\s+0x([0-9a-f]+)$", t)
            if m and t.startswith("call"):
                tgt = int(m.group(2), 16)
                calls.append(tgt)
                if tgt in rf:
                    rng.append((a, rf[tgt]))
            elif t.startswith("call") and "PTR" in t:
                calls.append(t)
        tot_l += len(lcg)
        tot_r += len(rng)
        cs = sorted(set("%08X" % c if isinstance(c, int) else c.replace(" ", "") for c in calls))
        print("D %08X %s insns=%d lcg=%d rngcalls=%d callees=%s" % (lo, name, len(ins), len(lcg), len(rng),
                                                                   ",".join(cs) if cs else "-"))
    print("SCAN path draws ranges=%d lcg=%d rngcalls=%d rngfns=%d" % (len(RANGES), tot_l, tot_r, len(rf)))


def cmd_writers(exe, off, size):
    data = load(exe)
    text = [s for s in sections(data) if s[0] == ".text"][0]
    ins = objdump(exe, text[1], text[1] + text[2])
    pat = re.compile(r"^(mov|or|and|add|sub|inc|dec)\w*\s+%s PTR \[(\w+)\+0x%x\]," % (
        {1: "BYTE", 2: "WORD", 4: "DWORD"}[size], off))
    n = 0
    for a, t in ins:
        if pat.match(t):
            print("W %08X %s" % (a, t))
            n += 1
    print("SCAN path writers off=0x%x size=%d n=%d" % (off, size, n))


# The request register (plan 0054 P1.1): every server site of PathPlan with its owner, the path type at the call and
# where that type comes from, read at the site (docs/findings/path/0001 § 6). Client sites (the 0x004... code, out of
# scope by the owner's decision 5) take the type the scan resolves, else "current".
REGISTER = {
    0x0054CBB9: ("player", "15", "packet 0x5F handler 0x0054CD50 (g_SrvPacketTable+0x2F8): reach test 0x0054CB10, type, mask, +0x91 saved and restored"),
    0x0057F117: ("player", "7|8", "PlrModeStartMove: PathMoveReset sets 7 for a player (0x00648E07); mode 19 sets 8 (0x0057F106)"),
    0x0059FDB1: ("missile", "4", "MissileCreate: the type PATH_DynamicCreate gives a missile (0x00649DBB); no PathSetType between"),
    0x005A62EF: ("mode machine", "request", "MonPathPlanType: the AI's or mode machine's type argument (0x005A62E6)"),
    0x005A634E: ("mode machine", "15", "MonPathPlanType: the fallback after 2, 7, 9, 13 left no point (0x005A6345)"),
    0x005A760D: ("mode machine", "current", "MonModeStartSkill: base class 110, path without points"),
    0x005A7638: ("mode machine", "current", "MonModeStartSkill: path with points"),
    0x005A7854: ("mode machine", "8", "0x005A77C0, the monster knockback start (g_MonModeRecords entry 0x006E22C0)"),
    0x005AA59D: ("missile", "current", "GuidedSetTarget: the missile's own type"),
    0x005AC08B: ("missile", "10", "MissCbReseedPathX (0x005AC07B)"),
    0x005AE879: ("missile", "current", "MissDo07Homing"),
    0x005AEC89: ("missile", "current", "MissDo11StepToTarget"),
    0x005AF21C: ("missile", "current", "MissDo16TurnTarget"),
    0x005B0767: ("missile", "current", "MissDo35Reseed"),
    0x005C92E9: ("missile", "10", "MissCbReseedPathXPlusArg (0x005C92D9)"),
    0x005CBB1B: ("skill", "8", "SkillDo89Jump (0x005CBB0A)"),
    0x005CBBBE: ("skill", "9", "SkillDo89Jump (0x005CBB9D)"),
    0x005CBC32: ("skill", "2", "SkillSt48SwarmMove (0x005CBC29)"),
    0x005CBC4D: ("skill", "1", "SkillSt48SwarmMove, after the type-2 plan (0x005CBC44)"),
    0x005CD1AE: ("missile", "10", "MissCbReseedRoll (0x005CD19B)"),
    0x005CD48D: ("skill", "1", "SkillDo103DiabRun (0x005CD484)"),
    0x005CF877: ("skill", "current", "SkillSt31Charge: the caster's own type"),
    0x005D0113: ("skill", "14", "SkillDo73BlessedHammer, on the hammer missile's path (0x005D0107)"),
    0x005D4141: ("missile", "10", "MissCbReseedFromArg (0x005D4131)"),
    0x005D9067: ("skill", "7", "SkillSt38Whirlwind (0x005D905B)"),
    0x005DA007: ("skill", "9", "LeapAttackPath (0x005D9FC5)"),
    0x005DA10B: ("skill", "8", "LeapAttackPath (0x005DA0FA)"),
    0x005DD580: ("AI", "2", "MonAiPreferDecoy: a test plan, the path restored (0x005DD577)"),
    0x005E912D: ("AI", "2", "0x005E8F20: a test plan, the path restored (0x005E9124)"),
    0x005FBFB7: ("AI", "2", "0x005FBDD0: a test plan, the path restored (0x005FBFAF); force EDI = 0"),
    0x006503C9: ("movement", "13|2", "PathReplan: +0x3C written directly, 13 (flag) or 2 (0x006503AF, 0x006503BB)"),
    0x006503DD: ("movement", "15|current", "PathReplan: 15 after a failed 2/13/15 plan (0x006503D2), else the current type"),
    0x00663E1B: ("unreferenced", "16", "0x00663E00: no call, jump or pointer in the image (findptr)"),
    0x00663EEB: ("unreferenced", "16", "0x00663ED0: no call, jump or pointer in the image (findptr)"),
}


def cmd_register(exe):
    import collections
    data = load(exe)
    funcs = symbols()
    sites = []
    for site in rel_hits(data, PATHPLAN, b"\xe8"):
        lo, meta = func_start(data, funcs, site)
        ins = objdump(exe, lo, site + 5)
        if not any(a == site and t.startswith("call") for a, t in ins):
            continue
        before = [t for t in ins if t[0] < site]
        pushes = [t for t in before if t[1].startswith("push")][-3:]
        types = []
        for k, (a, t) in enumerate(before):
            if t.startswith("call") and "0x648cf0" in t:
                pp = [x for x in before[:k] if x[1].startswith("push")][-2:]
                types.append(resolve(before, pp[0]) if len(pp) == 2 else "?")
        sites.append((site, lo, meta, pushes, types))
    own = collections.Counter()
    typ = collections.Counter()
    force = collections.Counter()
    unclassified = 0
    for site, lo, meta, pushes, types in sorted(sites):
        f = pushes[0][1].split(None, 1)[1] if pushes else "?"
        force[f] += 1
        name = meta[0] if meta else "%08X" % lo
        if site in REGISTER:
            o, t, why = REGISTER[site]
        elif site < 0x00500000:
            o, t = "client", (types[-1].split("=")[-1] if types else "current")
            if t.startswith("0x"):
                t = str(int(t, 16))
            why = "client code, out of scope (owner decision 5); type as scanned"
        else:
            o, t, why = "UNCLASSIFIED", "?", "-"
            unclassified += 1
        own[o] += 1
        typ[(o == "client", t)] += 1
        print("R %08X fn=%08X %s owner=%s type=%s force=%s | %s" % (site, lo, name, o, t, f, why))
    print("OWNERS " + " ".join("%s:%d" % kv for kv in sorted(own.items())))
    print("TYPES server " + " ".join("%s:%d" % (k[1], v) for k, v in sorted(typ.items()) if not k[0]))
    print("TYPES client " + " ".join("%s:%d" % (k[1], v) for k, v in sorted(typ.items()) if k[0]))
    print("FORCE " + " ".join("%s:%d" % kv for kv in sorted(force.items())))
    print("SCAN path register sites=%d server=%d client=%d unclassified=%d" % (
        len(sites), len(sites) - own["client"], own["client"], unclassified))


FLAG_RANGES = ((0x00647F00, 0x00651000), (0x00678B00, 0x0067D000))   # the path module: PATH_*, the planners


def cmd_flags(exe):
    """Every instruction of the path module that tests, sets or clears an immediate bit of [reg+0x34] (the path
    flags), grouped by bit, with the containing function (re/symbols.csv)."""
    import collections
    data = load(exe)
    funcs = symbols()
    by = collections.defaultdict(list)
    n = 0
    for lo, hi in FLAG_RANGES:
        for a, t in objdump(exe, lo, hi):
            m = re.match(r"^(test|or|and)\s+(DWORD|BYTE|WORD) PTR \[(\w+)\+0x34\],(0x[0-9a-f]+)$", t)
            if not m:
                continue
            v = int(m.group(4), 16)
            if m.group(1) == "and":
                v = ~v & {"DWORD": 0xFFFFFFFF, "WORD": 0xFFFF, "BYTE": 0xFF}[m.group(2)]
            named = [(lo2, nm) for lo2, hi2, nm in RANGES if lo2 <= a < hi2]
            if named:
                nm = named[0][1]
            else:
                fn = max(f for f in funcs if f <= a)
                nm = funcs[fn][0] if a - fn < 0x200 else "-"
            for b in range(32):
                if v >> b & 1:
                    by[1 << b].append("%s@%08X(%s)" % (m.group(1), a, nm))
            n += 1
    for bit in sorted(by):
        print("F %08X n=%d %s" % (bit, len(by[bit]), " ".join(by[bit])))
    print("SCAN path flags instructions=%d bits=%d" % (n, len(by)))


def cmd_settypes(exe):
    """Every direct call of PathSetType (0x00648CF0) with its type argument (the first of its two pushes) resolved
    as `sites` resolves a register; per type, the server (>= 0x00500000) and client call counts."""
    import collections
    data = load(exe)
    funcs = symbols()
    srv, cli = collections.Counter(), collections.Counter()
    for site in rel_hits(data, PATHSETTYPE, b"\xe8"):
        lo, meta = func_start(data, funcs, site)
        ins = objdump(exe, lo, site + 5)
        if not any(a == site and t.startswith("call") for a, t in ins):
            continue
        before = [t for t in ins if t[0] < site]
        pp = [t for t in before if t[1].startswith("push")][-2:]
        v = resolve(before, pp[0]) if len(pp) == 2 else "?"
        v = v.split("=")[-1]
        if v.startswith("0x"):
            v = str(int(v, 16))
        (srv if site >= 0x00500000 else cli)[v] += 1
        print("T %08X fn=%08X %s type=%s" % (site, lo, meta[0] if meta else "-", v))
    key = lambda kv: (len(kv[0]), kv[0])
    print("SETTYPE server " + " ".join("%s:%d" % kv for kv in sorted(srv.items(), key=key)))
    print("SETTYPE client " + " ".join("%s:%d" % kv for kv in sorted(cli.items(), key=key)))
    print("SCAN path settypes calls=%d server=%d client=%d" % (sum(srv.values()) + sum(cli.values()),
                                                                sum(srv.values()), sum(cli.values())))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sites", "tables", "draws", "writers", "register", "flags", "settypes"])
    ap.add_argument("exe")
    ap.add_argument("--target", default="0x00649970")
    ap.add_argument("--off", default="0x3c")
    ap.add_argument("--size", type=int, default=4)
    a = ap.parse_args(argv)
    if a.cmd == "sites":
        cmd_sites(a.exe, int(a.target, 16))
    elif a.cmd == "tables":
        cmd_tables(a.exe)
    elif a.cmd == "draws":
        cmd_draws(a.exe)
    elif a.cmd == "register":
        cmd_register(a.exe)
    elif a.cmd == "flags":
        cmd_flags(a.exe)
    elif a.cmd == "settypes":
        cmd_settypes(a.exe)
    else:
        cmd_writers(a.exe, int(a.off, 16), a.size)


if __name__ == "__main__":
    main(sys.argv[1:])

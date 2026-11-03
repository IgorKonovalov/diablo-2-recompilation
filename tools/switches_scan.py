#!/usr/bin/env python3
"""Plan 0062 P1: the switches scan over the pinned Game.exe (run with python3 -I).

Usage: switches_scan.py <game.exe> <section> [> out]
  table   the g_CmdLineOptions rows (58 by the loop bound of ConfigLoadIni and the option lookup)
  fields  every use of a config field through a config-pointer global or a declared root register
  disp    per option offset: every [reg+offset] instruction in .text outside the traced uses
  args    every string in .rdata/.data that looks like a switch name, and its code references
  options per option row: its traced uses (fields) and the raw hits at its offset in any addressing form (disp)
  compare every call of a string-compare routine with an immediate string pushed in the 6 instructions before, and
          every inline `repz cmps` with an immediate string in the 8 before
  strings every code-referenced string matching the debug word list
  handlers the 52 slots of g_OptionApplyTable: address, instruction count, config fields read
  scmd    the second option table (0x006D5BE8) and the registered -lng row
  packets g_SrvPacketTable 1..0x66: handler, flag word, stub or body; and every code reference to the flag column
  dead    the rows whose offset no traced use reads, with the raw hit count at that offset in any addressing form
Disassembly is objdump's linear sweep of .text: bytes it misreads (jump tables, padding) can hide an instruction,
so `disp` is a bound on the sites seen, not a proof. The run prints the instruction count it covered.
"""
import re, struct, subprocess, sys

TABLE = 0x00705040; ENTRY = 0x5C; COUNT = 0x14D8 // 0x5C
SECTIONS = [(0x401000, 0x2CB000, 0x1000), (0x6CC000, 0x39000, 0x2CC000), (0x705000, 0x48000, 0x305000)]
# config-pointer globals, written by the module runs: client 0x0044B8A9, multiplayer 0x00442153, launcher 0x004359D8
GLOBALS = [0x7A0438, 0x77BBD8, 0x7795D4]
# functions that receive the config in a register or stack slot: (start, stop, register at entry, label)
ROOTS = [
    (0x405C30, 0x405EF0, "edx", "InitGame"),
    (0x44B8A4, 0x44BA00, "esi", "ClientRun"),
    (0x442151, 0x442180, "ecx", "MultiplayerRun"),
    (0x441B70, 0x442150, "ecx", "MultiplayerInit"),
    (0x4359D6, 0x436000, "ecx", "LauncherRun"),
    (0x43B7A1, 0x43B820, "ecx", "LauncherComInt"),
    (0x44E5B1, 0x44E600, "eax", "GetConfig 0x0044E5AC"),
    (0x43C18F, 0x43C2C0, "edi", "LauncherNetCfg"),
]
HANDLERS_TABLE = 0x70F488; HANDLERS = 52
LINE = re.compile(r"^\s*([0-9a-f]+):\t(.*)$")
REGS = "eax ebx ecx edx esi edi ebp".split()
SUB = {"al": "eax", "ah": "eax", "ax": "eax", "bl": "ebx", "bh": "ebx", "bx": "ebx", "cl": "ecx", "ch": "ecx", "cx": "ecx",
       "dl": "edx", "dh": "edx", "dx": "edx", "si": "esi", "di": "edi"}


def off(v):
    for va, size, raw in SECTIONS:
        if va <= v < va + size:
            return v - va + raw
    return None


def disasm(exe):
    out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "-j", ".text", exe],
                         capture_output=True, text=True, check=True).stdout
    res = []
    for l in out.splitlines():
        m = LINE.match(l)
        if m:
            res.append((int(m.group(1), 16), re.sub(r"\s+", " ", m.group(2).strip())))
    return res


def rows(d):
    r = []
    for i in range(COUNT):
        o = off(TABLE) + i * ENTRY
        s = lambda a, b: d[o + a:o + b].split(b"\0")[0].decode("latin1")
        r.append((i, TABLE + i * ENTRY, s(0, 27), s(27, 54), s(54, 81), d[o + 0x51],
                  struct.unpack_from("<I", d, o + 0x54)[0], struct.unpack_from("<I", d, o + 0x58)[0]))
    return r


def dest(ins):
    p = ins.split(" ", 1)
    if len(p) < 2:
        return p[0], None
    return p[0], p[1].split(",")[0]


def reg_of(t):
    t = t.strip()
    return SUB.get(t, t if t in REGS else None)


def trace(ins, i, regs, stop=None):
    # with a declared stop the walk passes `ret`: a root's body has early returns
    """Walk forward from index i holding the config in `regs`, linear (branches ignored), until ret or all lost."""
    uses = []
    regs = set(regs)
    while i < len(ins) and regs:
        a, t = ins[i]
        if stop and a >= stop:
            break
        op, d0 = dest(t)
        for m in re.finditer(r"\[(e[a-ds][xpi])(\+0x[0-9a-f]+)?(\-0x[0-9a-f]+)?\]", t):
            if m.group(1) in regs and not m.group(3):
                uses.append((a, int(m.group(2)[3:], 16) if m.group(2) else 0, t))
        if op == "ret" and not stop:
            break
        if stop and op == "int3":  # the padding after the function: a root's walk ends there
            break
        if op == "pop" and stop:  # an early return's epilogue, the body goes on
            i += 1
            continue
        if op == "jmp" and "0x" in t and "PTR" not in t and abs(int(t.split()[-1], 16) - a) > 0x1000:
            if "ecx" in regs:
                uses.append((a, -1, t))
            if not stop or stop - a < 0x20:
                break
        if op == "push" and d0 in regs:
            uses.append((a, -2, t))
        if op == "call":
            uses.append((a, -3, t + " [" + ",".join(sorted(regs)) + "]"))
            regs -= {"eax", "ecx", "edx"}
        else:
            r = reg_of(d0) if d0 else None
            if r and op not in ("cmp", "test", "push"):
                src = t.split(",", 1)[1].strip() if "," in t else ""
                if op == "mov" and src in regs:
                    regs.add(r)
                elif op == "xchg":
                    regs.discard(r)
                else:
                    regs.discard(r)
        i += 1
    return uses


def cmd_table(d):
    r = rows(d)
    print("# COUNT", len(r), "entry", hex(ENTRY), "bound 0x14D8")
    for x in r:
        print("%2d 0x%08X %-10s %-14s -%-12s type=%d off=0x%03X default=%d" % x)


def starts(ins):
    return {a: k for k, (a, _) in enumerate(ins)}


def traced(d, ins):
    idx = starts(ins)
    res = []
    for k, (a, t) in enumerate(ins):
        for g in GLOBALS:
            if "0x%x" % g in t and t.startswith("mov ") and t.split(",")[0].split()[-1] in REGS:
                res.append(("global 0x%08X" % g, a, trace(ins, k + 1, [t.split(",")[0].split()[-1]])))
    for lo, hi, r, label in ROOTS:
        res.append((label, lo, trace(ins, idx[lo], [r], hi)))
    hs = sorted({struct.unpack_from("<I", d, off(HANDLERS_TABLE) + 4 * i)[0] for i in range(HANDLERS)} - {0})
    for h, nxt in zip(hs, hs[1:] + [hs[-1] + 0x20]):
        res.append(("handler", h, trace(ins, idx[h], ["ecx"], nxt)))
    return res


def reads_ecx(ins, idx, target):
    """Linear from the entry: does the callee read ECX before writing it? (None: not a direct call)"""
    m = re.search(r"call 0x([0-9a-f]+)", target)
    if not m or int(m.group(1), 16) not in idx:
        return None
    k = idx[int(m.group(1), 16)]
    for a, t in ins[k:k + 60]:
        op, d0 = dest(t)
        if op in ("ret", "jmp", "call"):
            return False if op != "call" else "call-first"
        if "ecx" in t or re.search(r"\bcl\b|\bcx\b", t):
            if op in ("mov", "lea", "movzx", "movsx") and reg_of(d0) == "ecx" and "ecx" not in t.split(",", 1)[1]:
                return False
            if op == "xor" and t.endswith("ecx,ecx"):
                return False
            return "0x%08X %s" % (a, t)
    return False


def cmd_fields(d, ins):
    res = traced(d, ins)
    idx = starts(ins)
    print("# roots", len(res), "instructions", len(ins))
    n = 0
    for label, a, uses in res:
        for u in uses:
            if u[1] >= 0:
                print("%-16s from 0x%08X use 0x%08X +0x%03X %s" % (label, a, u[0], u[1], u[2]))
                n += 1
    print("# field uses", n)
    calls = 0
    print("# escapes: the config register pushed, or live in a call (linear walk over-approximates)")
    for label, a, uses in res:
        for u in uses:
            if u[1] == -2:
                print("%-16s from 0x%08X push 0x%08X %s" % (label, a, u[0], u[2]))
                calls += 1
            elif u[1] == -1:
                print("%-16s from 0x%08X jmp  0x%08X %s" % (label, a, u[0], u[2]))
                calls += 1
            elif u[1] == -3 and "ecx" in u[2].split("[")[-1]:
                print("%-16s from 0x%08X call 0x%08X %s entry-reads-ecx=%s" % (label, a, u[0], u[2], reads_ecx(ins, idx, u[2])))
                calls += 1
    print("# escapes", calls)


def cmd_disp(d, ins):
    known = set()
    for label, a, uses in traced(d, ins):
        for u in uses:
            if u[1] >= 0:
                known.add(u[0])
    offs = sorted({x[6] for x in rows(d)} | {0x8A, 0x8B, 0x229})
    pat = {o: re.compile(r"\[[^\]]*\+0x%x\]" % o) for o in offs}
    addp = {o: re.compile(r"^(add|sub) e[a-ds][xpi],0x%x$" % o) for o in offs}
    print("# instructions covered", len(ins), "offsets", len(offs))
    for o in offs:
        hits = [(a, t) for a, t in ins if pat[o].search(t) or addp[o].search(t)]
        print("off=0x%03X total=%d traced=%d" % (o, len(hits), sum(a in known for a, _ in hits)))
        if o >= 0x80:
            for a, t in hits:
                if a not in known:
                    print("   0x%08X %s" % (a, t))


def cmd_options(d, ins):
    tr = {}
    for label, a, uses in traced(d, ins):
        for u in uses:
            if u[1] >= 0:
                tr.setdefault(u[1], []).append((label, u[0], u[2]))
    grouped = {}
    for x in rows(d):
        grouped.setdefault(x[6], []).append(x)
    for o in sorted(grouped):
        names = ",".join("-" + x[4] for x in grouped[o])
        print("off=0x%03X %s type=%d" % (o, names, grouped[o][0][5]))
        for label, a, t in tr.get(o, []):
            print("   %-16s 0x%08X %s" % (label.replace("global ", ""), a, t))
    extra = sorted(set(tr) - set(grouped))
    print("# config fields used but written by no option:", ["0x%03X" % o for o in extra])


def cmd_args(d, ins):
    # every NUL-delimited printable string starting with '-' in .rdata/.data
    for va, size, raw in SECTIONS[1:]:
        blob = d[raw:raw + size]
        for m in re.finditer(rb"(?<=\0)-[A-Za-z0-9_ %./-]{1,40}(?=\0)", blob):
            v = va + m.start()
            refs = [a for a, t in ins if "0x%x" % v in t]
            print("0x%08X %r refs=%s" % (v, m.group(0).decode(), ["0x%08X" % a for a in refs[:6]]))


STRCMP = {0x6841E9: "_stricmp", 0x686040: "_strnicmp"}


def cstr(d, v):
    o = off(v)
    if o is None or not (0x6CC000 <= v < 0x74D000):
        return None
    e = d.find(b"\0", o, o + 80)
    if e <= o:
        return None
    b = d[o:e]
    if all(32 <= c < 127 for c in b):
        return b.decode()
    return None


def cmd_compare(d, ins, cmps):
    n = 0
    print("# routines", {hex(k): v for k, v in cmps.items()})
    for k, (a, t) in enumerate(ins):
        hit = None
        if re.fullmatch(r"call 0x[0-9a-f]+", t) and int(t.split()[-1], 16) in cmps:
            hit = cmps[int(t.split()[-1], 16)]; back = 6
        elif t.startswith("repz cmps"):
            hit = "repz cmps"; back = 8
        if not hit:
            continue
        got = []
        for _, u in ins[max(0, k - back):k]:
            for m in re.finditer(r"0x([0-9a-f]{6})\b", u):
                s = cstr(d, int(m.group(1), 16))
                if s and "[" not in u:
                    got.append((m.group(1), s))
        for v, s in got:
            print("0x%08X %-10s 0x00%s %r" % (a, hit, v.upper(), s))
            n += 1
    print("# compares with an immediate string", n)


WORDS = re.compile(r"debug|cheat|\bgod\b|invinc|nocheck|profile|dump|\btrace|\bdev\b|developer|<[A-Z]+>|secret|\btest", re.I)


def cmd_strings(d, ins):
    seen = {}
    for a, t in ins:
        for m in re.finditer(r"0x([67][0-9a-f]{5})\b", t):
            v = int(m.group(1), 16)
            if v >= 0x6CC000:
                seen.setdefault(v, []).append(a)
    n = 0
    for v in sorted(seen):
        s = cstr(d, v)
        if s and len(s) >= 3 and WORDS.search(s):
            print("0x%08X %-48r refs=%s" % (v, s[:48], ["0x%08X" % x for x in seen[v][:4]]))
            n += 1
    print("# strings", n)


def cmd_handlers(d, ins):
    idx = starts(ins)
    hs = [struct.unpack_from("<I", d, off(HANDLERS_TABLE) + 4 * i)[0] for i in range(HANDLERS)]
    distinct = sorted(set(hs) - {0})
    print("# slots", HANDLERS, "null", hs.count(0), "distinct", len(distinct))
    stubs = 0
    for i, h in enumerate(hs):
        if not h:
            print("%2d null" % i)
            continue
        k = idx[h]; body = []
        while ins[k][1].split()[0] not in ("ret", "int3") and len(body) < 80:
            body.append(ins[k][1]); k += 1
        if ins[k][1].split()[0] == "ret" and not body:
            print("%2d 0x%08X ret-only" % (i, h))
        else:
            n = len(body)
            print("%2d 0x%08X first-ret-after=%d %s" % (i, h, n, " ; ".join(body[:2])[:70]))
    print("# ret-only distinct", sum(1 for h in distinct if ins[idx[h]][1].startswith("ret")))


def cmd_scmd(d, ins):
    for i in range(8):
        fl, _, name, fn = struct.unpack_from("<IIII", d, off(0x6D5BE8) + 16 * i)
        print("row %d flags=0x%X name=-%s handler=0x%08X" % (i, fl, cstr(d, name), fn))
    print("registered at 0x0045127C: name=-%s flags=0x20000 buffer=0x007A0710 size=0x104" % cstr(d, 0x6D5EF4))
    print("callers of 0x006C50B0 (GetCommandLineA + parse):", sum("0x6c50b0" in t for _, t in ins))
    print("callers of 0x006C4FB0:", ["0x%08X" % a for a, t in ins if t == "call 0x6c4fb0"])
    print("GetCommandLineA import uses:", ["0x%08X" % a for a, t in ins if "0x6cc3ac" in t])


def cmd_packets(d, ins):
    idx = starts(ins)
    n = st = nulls = fl1 = 0
    for i in range(1, 0x67):
        h, f = struct.unpack_from("<II", d, off(0x6E0D18) + 8 * i)
        n += 1; fl1 += f == 1
        if not h:
            nulls += 1
            print("0x%02X null flag=%d" % (i, f)); continue
        k = idx[h]; a2 = ins[k + 1][1]
        stub = a2.startswith("ret") and ins[k][1] in ("xor eax,eax", "mov eax,0x3")
        st += stub
        print("0x%02X 0x%08X flag=%d %s" % (i, h, f, ("stub " + ins[k][1]) if stub else "body"))
    print("# opcodes", n, "null", nulls, "stubs", st, "flag=1", fl1)
    refs = [(a, t) for a, t in ins if re.search(r"0x6e0d1[c-f]\b|0x6e0d[2-9a-f][0-9a-f]\b|0x6e0[e-f][0-9a-f]{2}\b", t)]
    print("# code references inside the table past its first handler word:", len(refs), refs[:8])
    print("# references to its base:", [("0x%08X" % a, t) for a, t in ins if "0x6e0d18" in t])


def cmd_dead(d, ins):
    tr = set()
    for label, a, uses in traced(d, ins):
        for u in uses:
            if u[1] >= 0:
                tr.add(u[1])
    n = 0
    for x in rows(d):
        if x[6] not in tr:
            o = x[6]
            p = re.compile(r"\[[^\]]*\+0x%x\]|^(add|sub) e[a-ds][xpi],0x%x$" % (o, o))
            print("-%-12s off=0x%03X type=%d no traced use; raw hits at that offset in any addressing form: %d"
                  % (x[4], o, x[5], sum(bool(p.search(t)) for _, t in ins)))
            n += 1
    print("# rows with no traced reader or writer:", n, "of", COUNT)


def main():
    exe, sec = sys.argv[1], sys.argv[2]
    d = open(exe, "rb").read()
    if sec == "table":
        return cmd_table(d)
    ins = disasm(exe)
    if sec == "compare":
        cmps = dict(STRCMP)
        for x in sys.argv[3:]:
            cmps[int(x, 16)] = "cmp"
        return cmd_compare(d, ins, cmps)
    {"fields": cmd_fields, "disp": cmd_disp, "args": cmd_args, "options": cmd_options, "handlers": cmd_handlers, "scmd": cmd_scmd, "packets": cmd_packets,
     "dead": cmd_dead, "strings": cmd_strings}[sec](d, ins)


main()

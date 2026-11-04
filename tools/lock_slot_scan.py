"""ADR-0029 rule (a)'s kept scan: after a call of an import slot, does any code read EAX, ECX or EDX before writing it?

Static. No game, no emulator. objdump's Intel listing of the pinned image, read by a small use/def table.

Reach, two sets. EXECUTED: the functions the family's kept cases run, from `tools/ghidra.sh emucover` on the kept `.cases` and
`.mem` (re/ghidra_scripts/EmuCover.java: `P` lines): from the root, through each direct call instruction some case executed.
The cases have no other input, so for them "can reach" and "did" are one set; every path of those functions is still walked,
executed or not, and each read is marked with whether a case executed it. STATIC: the same descent through every direct call,
executed or not: `call rel32`, `jmp rel32`, jcc, fall-through and each switch table (`jmp [r*4 + table]`), a superset, kept as
what another declared state could add. Indirect calls and unresolved jumps are not followed; they are listed and counted.

Sites. Every call of a slot: `call [slot]`, `jmp [slot]` (a tail call), and `call r` where `mov r, [slot]` reaches it.

Walk. From the instruction after a site, with EAX, ECX, EDX (byte by byte, so `mov al, 1` leaves the upper bytes unwritten)
and the flags marked unwritten, every path is followed until all are written:
- into a direct callee, and back to that call's return;
- from a `ret` with no callee open, to every direct call of the function within the set (in EXECUTED, the call instructions
  a case executed); `ret` of the root is the case's end: EAX there is an output, ECX and EDX are not compared by a checker;
- through another site of a lock slot, which writes nothing (the stand-in is `ret n`);
- another import ends the path: stdcall leaves the three registers undefined, and nothing in the import reads them.
An indirect call or an unresolved jump with something still unwritten ends the path as OPEN, not as a pass. A mnemonic the
table does not hold, with a watched register as an operand, counts as a read (fails closed).

Two verdicts per site of EXECUTED. RULE: rule (a)'s, the walk confined to the set: a direct call to a function outside it ends
the path, printed as EXIT with what is still unwritten. STRICT: the same walk carried into those callees too, which no case
enters. A read STRICT finds outside the set is printed and counted, not dropped.

Usage: python3 -I tools/lock_slot_scan.py run --dir D     D holds cover/drop.out; writes slots.txt, sites-*.txt, closure-*.txt,
                                                          controls.txt, summary.txt, manifest.txt
       python3 -I tools/lock_slot_scan.py check --dir D   (regenerates and compares byte for byte)
"""
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(HERE, "..", "workspace", "install", "app", "game.exe")
PINNED = "631066c1649c4ea9"
BASE = 0x400000

ENTER, LEAVE, BADCODE = 0x006CC218, 0x006CC214, 0x006CC34C
LOCKS = (ENTER, LEAVE)
ROOTS = {"drop": 0x00555DA0}
ALLOC_LO, ALLOC_HI = 0x00409770, 0x0040A080   # the range the ADR's review scan named: compared, not assumed

# masks: 4 bits per register (low byte, second byte, upper half twice), one for the flags
REG = {}
for i, (e, x, l, h) in enumerate((("eax", "ax", "al", "ah"), ("ecx", "cx", "cl", "ch"), ("edx", "dx", "dl", "dh"))):
    REG[e], REG[x], REG[l], REG[h] = 0xF << (4 * i), 0x3 << (4 * i), 0x1 << (4 * i), 0x2 << (4 * i)
FLAGS = 1 << 12
ALL = 0xFFF | FLAGS
NAMES = ((0xF, "EAX"), (0xF0, "ECX"), (0xF00, "EDX"), (FLAGS, "FLAGS"))
TOKEN = re.compile(r"\b(eax|ecx|edx|ax|cx|dx|al|ah|cl|ch|dl|dh)\b")

WRITE = {"mov", "movzx", "movsx", "lea", "movd", "movq", "movss", "movsd", "movaps", "movups", "movdqa", "movdqu", "movapd",
         "cvttss2si", "cvttsd2si", "cvtss2si", "cvtsd2si", "cvtsi2sd", "cvtsi2ss", "cvtss2sd", "cvtsd2ss", "pop", "movlps", "movhps",
         "movlpd", "movhpd", "pmovmskb", "movmskps", "movmskpd"}
RMW = {"add", "sub", "and", "or", "xor", "adc", "sbb", "shl", "shr", "sar", "sal", "rol", "ror", "rcl", "rcr", "inc", "dec", "neg", "not",
       "xadd", "bswap", "shld", "shrd", "xchg", "cmpxchg", "bts", "btr", "btc", "bsf", "bsr"}
READ = {"cmp", "test", "push", "bt", "call", "jmp", "ucomiss", "ucomisd", "comiss", "comisd"}
NOREG = {"nop", "leave", "fwait", "wait", "cld", "std", "clc", "stc", "cmc", "sfence", "lfence", "mfence", "emms", "pause", "pushf",
         "pushfd", "popf", "popfd", "enter", "fnclex", "fninit"}
FLAG_WRITE = {"add", "sub", "and", "or", "xor", "cmp", "test", "neg", "adc", "sbb", "imul", "mul", "div", "idiv", "bt", "bsf", "bsr", "comiss",
              "comisd", "ucomiss", "ucomisd", "fcomi", "fcomip", "fucomi", "fucomip", "sahf", "popf", "popfd", "cmpxchg", "xadd", "scas", "cmps"}
PREFIX = {"rep", "repz", "repe", "repnz", "repne", "lock", "cs", "ds", "es", "fs", "gs", "ss", "data16", "addr16", "notrack", "bnd"}
STRING = {"movs", "stos", "lods", "scas", "cmps"}


def masks(text):
    m = 0
    for t in TOKEN.findall(text):
        m |= REG[t]
    return m


def split_ops(s):
    return [o.strip() for o in s.split(",")] if s.strip() else []


def is_mem(o):
    return "[" in o or re.search(r"\b[c-gs]s:", o) is not None


def is_imm(o):
    return re.fullmatch(r"-?(0x)?[0-9a-f]+", o) is not None


def effects(mn, ops, rep=False):
    """(reads, writes, unknown) as masks. Flags are in both masks."""
    r, w, unk = 0, 0, False
    for o in ops:
        if is_mem(o):
            r |= masks(o)
    plain = [o if not is_mem(o) else "" for o in ops]
    if mn.startswith("set"):
        return r | FLAGS, w | masks(plain[0]), False
    if mn.startswith("cmov"):
        return r | FLAGS | masks(plain[0]) | masks(plain[1]), w | masks(plain[0]), False
    if mn.startswith("j") and mn not in ("jmp", "jecxz", "jcxz"):
        return r | FLAGS, w, False
    if mn in ("jecxz", "jcxz", "loop", "loope", "loopne"):
        return r | REG["ecx"], w | REG["ecx"] if mn.startswith("loop") else w, False
    if mn in STRING:
        if rep:
            r |= REG["ecx"]
            w |= REG["ecx"]
        if mn in ("stos", "scas"):
            r |= REG["eax"]
        if mn == "lods":
            w |= REG["eax"]
        if mn in ("scas", "cmps"):
            w |= FLAGS
        return r, w, False
    if mn in ("cdq", "cwd"):
        return r | REG["eax"], w | REG["edx"], False
    if mn == "cwde":
        return r | REG["ax"], w | REG["eax"], False
    if mn == "cbw":
        return r | REG["al"], w | REG["ax"], False
    if mn == "sahf":
        return r | REG["ah"], w | FLAGS, False
    if mn == "lahf":
        return r | FLAGS, w | REG["ah"], False
    if mn in ("fnstsw", "fstsw"):
        return r, w | (masks(plain[0]) if plain and plain[0] else 0), False
    if mn == "rdtsc":
        return r, w | REG["eax"] | REG["edx"], False
    if mn == "cpuid":
        return r | REG["eax"] | REG["ecx"], w | REG["eax"] | REG["ecx"] | REG["edx"], False
    if mn in ("mul", "idiv", "div") or (mn == "imul" and len(ops) == 1):
        r |= masks(plain[0]) | REG["eax"]
        if mn in ("div", "idiv"):
            r |= REG["edx"]
        return r, w | REG["eax"] | REG["edx"] | FLAGS, False
    if mn == "imul":
        if len(ops) == 2:
            return r | masks(plain[0]) | masks(plain[1]), w | masks(plain[0]) | FLAGS, False
        return r | masks(plain[1]), w | masks(plain[0]) | FLAGS, False
    if mn == "pushad" or mn == "pusha":
        return r | 0xFFF, w, False
    if mn == "popad" or mn == "popa":
        return r, w | 0xFFF, False
    if mn in NOREG:
        return (r | FLAGS if mn in ("pushf", "pushfd", "cmc") else r), (w | FLAGS if mn in ("popf", "popfd") else w), False
    if mn in ("xor", "sub", "sbb") and len(ops) == 2 and ops[0] == ops[1] and masks(plain[0]):
        return (FLAGS if mn == "sbb" else 0), masks(plain[0]) | FLAGS, False          # the zero idiom: no read of the register
    if mn == "or" and len(ops) == 2 and plain[0] and ops[1] == "0xffffffff":
        return r, w | masks(plain[0]) | FLAGS, False                                 # or r, -1
    if mn == "and" and len(ops) == 2 and plain[0] and ops[1] == "0x0":
        return r, w | masks(plain[0]) | FLAGS, False                                 # and r, 0
    if mn in WRITE:
        return r | sum_masks(plain[1:]), w | (masks(plain[0]) if plain else 0), False
    if mn in RMW:
        r |= sum_masks(plain)
        w |= masks(plain[0])
        if mn in ("adc", "sbb", "rcl", "rcr"):
            r |= FLAGS
        if mn in FLAG_WRITE or (mn in ("shl", "shr", "sar", "sal") and is_imm(ops[-1]) and int(ops[-1], 16) != 0):
            w |= FLAGS
        if mn in ("xchg", "xadd"):
            w |= sum_masks(plain[1:])
        if mn == "cmpxchg":
            r |= REG["eax"]
            w |= REG["eax"]
        return r, w, False
    if mn in READ:
        r |= sum_masks(plain)
        if mn in FLAG_WRITE:
            w |= FLAGS
        return r, w, False
    if mn.startswith("f") or mn.startswith("p") or mn in ("ret", "int3", "hlt", "emms", "movnti"):
        # x87 and packed instructions name no general register as a plain operand, or they fall through to unknown below
        if not sum_masks(plain):
            return r, w | (FLAGS if mn in FLAG_WRITE else 0), False
    if sum_masks(plain):
        return r | sum_masks(plain), w, True                                         # fails closed
    return r, w, not (mn in ("cvtdq2ps", "cvtps2pd", "addss", "subss", "mulss", "divss", "addsd", "subsd", "mulsd", "divsd", "xorps",
                             "andps", "orps", "xorpd", "sqrtss", "sqrtsd", "shufps", "unpcklps"))


def sum_masks(ops):
    m = 0
    for o in ops:
        m |= masks(o)
    return m


class Listing:
    """addr -> (next addr, mnemonic, operand text, rep prefix). A linear sweep, then a local re-decode where flow enters elsewhere."""

    def __init__(self, exe=None, text=None, data=None, sections=None):
        self.exe, self.ins, self.data, self.sections = exe, {}, data, sections or []
        if exe:
            with open(exe, "rb") as f:
                self.data = f.read()
            self.sections = pe_sections(self.data)
            self.parse(subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", exe], capture_output=True, text=True, check=True).stdout)
        if text:
            self.parse(text)

    LINE = re.compile(r"^\s*([0-9a-f]+):\s+(.*)$")

    def parse(self, text, overwrite=False):
        pending = None
        for line in text.splitlines():
            m = self.LINE.match(line)
            if not m:
                continue
            addr = int(m.group(1), 16)
            body = m.group(2).split("<")[0].strip()
            if pending is not None and pending in self.ins and self.ins[pending][0] is None:
                self.ins[pending] = (addr,) + self.ins[pending][1:]
            if overwrite and addr in self.ins:
                pending = None
                continue
            f = body.split(None)
            rep = False
            while f and f[0] in PREFIX:
                rep = rep or f[0].startswith("rep")
                f = f[1:]
            mn = f[0] if f else "(bad)"
            self.ins[addr] = (None, mn, " ".join(f[1:]), rep)
            pending = addr

    def get(self, a):
        if a in self.ins and self.ins[a][0] is not None:
            return self.ins[a]
        if self.exe and self.in_text(a):
            out = subprocess.run(["objdump", "-d", "-M", "intel", "--no-show-raw-insn", "--start-address=%#x" % a, "--stop-address=%#x" % (a + 0x40), self.exe],
                                 capture_output=True, text=True, check=True).stdout
            local = Listing()
            local.parse(out)
            for k, v in local.ins.items():
                if v[0] is not None and k not in self.ins:
                    self.ins[k] = v
                elif v[0] is not None and self.ins[k][0] is None:
                    self.ins[k] = v
        return self.ins.get(a)

    def in_text(self, a):
        return any(s[3] and s[0] <= a < s[0] + s[1] for s in self.sections)

    def word(self, va):
        for s in self.sections:
            if s[0] <= va < s[0] + s[1]:
                o = va - s[0] + s[2]
                if o + 4 <= len(self.data):
                    return struct.unpack_from("<I", self.data, o)[0]
        return None


def pe_sections(d):
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    n = struct.unpack_from("<H", d, pe + 6)[0]
    opt = struct.unpack_from("<H", d, pe + 20)[0]
    out = []
    for i in range(n):
        o = pe + 24 + opt + 40 * i
        vs, va, rs, rp, _, _, _, _, ch = struct.unpack_from("<IIIIIIHHI", d, o + 8)
        out.append((BASE + va, max(vs, rs), rp, bool(ch & 0x20)))
    return out


def pe_imports(d):
    """slot address -> (dll, name), by the PE's own import directory."""
    secs = pe_sections(d)

    def off(rva):
        for va, sz, rp, _ in secs:
            if va - BASE <= rva < va - BASE + sz:
                return rva - (va - BASE) + rp
        raise ValueError(hex(rva))

    def cstr(o):
        return d[o:d.index(b"\0", o)].decode("ascii")
    pe = struct.unpack_from("<I", d, 0x3C)[0]
    rva = struct.unpack_from("<I", d, pe + 24 + 96 + 8)[0]
    out, o = {}, off(rva)
    while True:
        ilt, _, _, name, iat = struct.unpack_from("<IIIII", d, o)
        if not name:
            return out
        dll = cstr(off(name))
        t, s = off(ilt or iat), BASE + iat
        while True:
            v = struct.unpack_from("<I", d, t)[0]
            if not v:
                break
            out[s] = (dll, "#%d" % (v & 0xFFFF) if v >> 31 else cstr(off(v) + 2))
            t += 4
            s += 4
        o += 20


def target(ops):
    m = re.fullmatch(r"0x([0-9a-f]+)", ops.split()[0]) if ops else None
    return int(m.group(1), 16) if m else None


def slot_of(ops):
    m = re.fullmatch(r"(?:DWORD PTR )?ds:0x([0-9a-f]+)", ops)
    return int(m.group(1), 16) if m else None


def switch_targets(L, a, ops, n=512):
    m = re.search(r"\[[a-z]+\*4\+0x([0-9a-f]+)\]", ops)
    if not m:
        return None
    t, out = int(m.group(1), 16), []
    for i in range(n):
        v = L.word(t + 4 * i)
        if v is None or not L.in_text(v) or abs(v - a) > 0x8000:
            break
        out.append(v)
    return out


class Graph:
    def __init__(self, L, imports):
        self.L, self.imports = L, imports
        self.members, self.callers, self.indirect, self.bad = {}, {}, {}, {}

    def body(self, entry):
        """the instructions of a function: fall-through, jcc, jmp rel32 (a tail jump joins the body), switch tables."""
        if entry in self.members:
            return self.members[entry]
        seen, stack, ind, bad, calls = set(), [entry], [], [], []
        while stack:
            a = stack.pop()
            if a in seen:
                continue
            i = self.L.get(a)
            if i is None:
                bad.append(a)
                continue
            seen.add(a)
            nx, mn, ops, _ = i
            if mn in ("ret", "retf", "int3", "hlt", "ud2", "iret", "iretd"):
                continue
            if mn == "(bad)":
                bad.append(a)
                continue
            if mn == "jmp":
                t = target(ops)
                if t is not None:
                    stack.append(t)
                    continue
                if slot_of(ops) in self.imports:
                    continue
                sw = switch_targets(self.L, a, ops)
                if sw:
                    stack.extend(sw)
                else:
                    ind.append(a)
                continue
            if mn.startswith("j") or mn.startswith("loop"):
                t = target(ops)
                if t is not None:
                    stack.append(t)
            elif mn == "call":
                t = target(ops)
                if t is not None:
                    calls.append((a, t))
                elif slot_of(ops) not in self.imports:
                    ind.append(a)
            stack.append(nx)
        self.members[entry] = dict(seen=seen, calls=calls, indirect=ind, bad=bad)
        return self.members[entry]

    def closure(self, roots, executed=None):
        seen, stack = set(), list(roots)
        while stack:
            e = stack.pop()
            if e in seen:
                continue
            seen.add(e)
            stack.extend(t for a, t in self.body(e)["calls"] if executed is None or a in executed)
        return seen


def slot_regs(L, imports):
    """`call r` -> the slots a `mov r, [slot]` delivers to it, by a forward walk inside the function."""
    out = {}
    for a, (nx, mn, ops, _) in list(L.ins.items()):
        if mn != "mov" or nx is None:
            continue
        ol = split_ops(ops)
        if len(ol) != 2 or ol[0] not in ("eax", "ecx", "edx", "ebx", "esi", "edi", "ebp"):
            continue
        s = slot_of(ol[1])
        if s not in imports:
            continue
        reg, seen, stack = ol[0], set(), [nx]
        while stack:
            p = stack.pop()
            if p in seen:
                continue
            seen.add(p)
            i = L.get(p)
            if i is None:
                continue
            n2, m2, o2, _ = i
            if m2 in ("ret", "retf", "int3", "hlt", "(bad)"):
                continue
            if m2 == "call":
                if o2 == reg:
                    out.setdefault(p, set()).add(s)
                if reg in ("eax", "ecx", "edx"):
                    continue
                stack.append(n2)
                continue
            if m2 == "jmp":
                t = target(o2)
                if o2 == reg:
                    out.setdefault(p, set()).add(s)
                elif t is not None:
                    stack.append(t)
                continue
            ops2 = split_ops(o2)
            if ops2 and ops2[0] == reg and m2 not in READ:
                continue
            if m2.startswith("j") or m2.startswith("loop"):
                t = target(o2)
                if t is not None:
                    stack.append(t)
            stack.append(n2)
    return out


def sites_of(L, regs, slot):
    out = []
    for a, i in L.ins.items():
        if i[1] in ("call", "jmp") and slot_of(i[2]) == slot:
            out.append((a, i[1] + " [slot]"))
    for a, ss in regs.items():
        if slot in ss:
            out.append((a, "%s %s" % (L.ins[a][1], L.ins[a][2])))
    return sorted(out)


class Walker:
    def __init__(self, L, G, imports, regs, stand_in, roots, scope=None, executed=None, confine=False):
        self.L, self.G, self.imports, self.regs, self.stand_in, self.roots = L, G, imports, regs, stand_in, set(roots)
        self.scope, self.confine, self.exits = scope, confine, {}
        self.entries_of, self.calls_to = {}, {}
        for e in scope or ():
            b = G.body(e)
            for a in b["seen"]:
                self.entries_of.setdefault(a, set()).add(e)
            for a, t in b["calls"]:
                if executed is None or a in executed:
                    self.calls_to.setdefault(t, set()).add(L.get(a)[0])

    def is_stand_in(self, a, i):
        if slot_of(i[2]) in self.stand_in:
            return True
        return bool(self.regs.get(a, set()) & self.stand_in)

    def is_import_call(self, a, i):
        return slot_of(i[2]) in self.imports or a in self.regs

    def walk(self, a0, live0=ALL, limit=200000):
        """first reads, as a dict addr -> (mask, instruction); opens (addr, mask, why); and the end states."""
        reads, opens, root_end, steps = {}, {}, {}, 0
        seen, work = set(), [(a0, live0, ())]
        while work:
            a, live, st = work.pop()
            if not live:
                continue
            key = (a, live, st)
            if key in seen:
                continue
            seen.add(key)
            steps += 1
            if steps > limit:
                opens[a] = (live, "step limit")
                break
            i = self.L.get(a)
            if i is None or i[1] == "(bad)":
                opens[a] = (live, "undecoded")
                continue
            nx, mn, ops, rep = i
            r, w, unk = effects(mn, split_ops(ops), rep)
            hit = r & live
            if hit:
                old = reads.get(a, (0, "", False))
                reads[a] = (old[0] | hit, "%s %s" % (mn, ops), unk)
                # go on: one read is a finding, and the other registers still need their own answer
                live &= ~hit
            live &= ~w
            if mn in ("ret", "retf", "iret", "iretd"):
                self.ret(a, live, st, work, root_end, opens)
                continue
            if mn in ("int3", "hlt", "ud2"):
                continue
            if mn == "call":
                t = target(ops)
                if self.is_stand_in(a, i):
                    work.append((nx, live, st))
                elif t is not None and self.confine and t not in self.scope:
                    if live:
                        self.exits[a] = (self.exits.get(a, (0, t))[0] | live, t)
                elif t is not None:
                    if len(st) >= 24:
                        opens[a] = (live, "call depth")
                    else:
                        work.append((t, live, st + (nx,)))
                elif self.is_import_call(a, i):
                    continue
                elif live:
                    opens[a] = (live, "indirect call")
                continue
            if mn == "jmp":
                t = target(ops)
                if self.is_stand_in(a, i):
                    self.ret(a, live, st, work, root_end, opens)
                elif t is not None:
                    work.append((t, live, st))
                elif self.is_import_call(a, i):
                    continue
                else:
                    sw = switch_targets(self.L, a, ops)
                    if sw:
                        work.extend((x, live, st) for x in sw)
                    elif live:
                        opens[a] = (live, "indirect jump")
                continue
            if mn.startswith("j") or mn.startswith("loop"):
                t = target(ops)
                if t is not None:
                    work.append((t, live, st))
            work.append((nx, live, st))
        return reads, opens, root_end

    def ret(self, a, live, st, work, root_end, opens):
        if not live:
            return
        if st:
            work.append((st[-1], live, st[:-1]))
            return
        if self.scope is None:
            return                                # a walk with no scope ends at its own return (the entry control)
        es = self.entries_of.get(a, set())
        if not es:
            opens[a] = (live, "ret outside the reached set")
        for e in es:
            if e in self.roots:
                root_end[a] = root_end.get(a, 0) | live
            for r in self.calls_to.get(e, ()):
                work.append((r, live, ()))
            if e not in self.roots and not self.calls_to.get(e):
                opens[a] = (live, "no direct caller of %08x in the set" % e)


def mask_names(m):
    return "+".join(n for b, n in NAMES if m & b) or "-"


def scan(L, G, imports, regs, root, executed=None):
    clo = G.closure([root], executed)
    w = Walker(L, G, imports, regs, set(LOCKS), [root], scope=clo, executed=executed)
    confined = None if executed is None else Walker(L, G, imports, regs, set(LOCKS), [root], scope=clo, executed=executed, confine=True)
    inset = set(w.entries_of)
    lines, totals = [], dict(sites=0, fail=0, flagread=0, open=0, rootx=0, ran=0, rule_fail=0)
    ranstr = lambda a: "" if executed is None else (" executed" if a in executed else " not-executed")
    undec = sum(len(G.body(e)["bad"]) for e in clo)
    ind = sorted({a for e in clo for a in G.body(e)["indirect"]})
    in_range = 0
    for slot in LOCKS:
        for a, form in sites_of(L, regs, slot):
            if a not in inset:
                continue
            totals["sites"] += 1
            in_range += ALLOC_LO <= a < ALLOC_HI
            totals["ran"] += executed is not None and a in executed
            i = L.get(a)
            if i[1] == "jmp":
                reads, opens, ends = {}, {}, {}
                w.ret(a, ALL, (), _Push(reads, opens, ends, w), ends, opens)
            else:
                reads, opens, ends = w.walk(i[0])
            rule_fail, exits = False, {}
            if confined is not None:
                confined.exits = {}
                r2, _, e2 = confined.walk(i[0]) if i[1] != "jmp" else ({}, {}, {})
                rule_fail = any(v[0] & 0xFFF for v in r2.values()) or any(v & 0xF for v in e2.values())
                exits = dict(confined.exits)
                totals["rule_fail"] += rule_fail
            vol = {k: v for k, v in reads.items() if v[0] & 0xFFF}
            flg = {k: v for k, v in reads.items() if v[0] & FLAGS}
            eax_end = any(v & 0xF for v in ends.values())
            totals["fail"] += bool(vol) or eax_end
            totals["flagread"] += bool(flg)
            totals["open"] += bool(opens)
            totals["rootx"] += eax_end
            verdict = "FAIL" if vol or eax_end else ("OPEN" if opens else "pass")
            if confined is not None:
                verdict = "rule=%s strict=%s" % ("FAIL" if rule_fail else "pass", verdict)
            lines.append("SITE %08x %s %s %s %s%s" % (a, "Enter" if slot == ENTER else "Leave", form.replace(" ", "_"), verdict,
                                                     "reads=%d opens=%d flags=%d" % (len(vol), len(opens), len(flg)), ranstr(a)))
            for k in sorted(vol):
                lines.append("  READ %08x %s %s%s%s" % (k, mask_names(vol[k][0] & 0xFFF), vol[k][1], " (unknown mnemonic)" if vol[k][2] else "", ranstr(k)))
            for k in sorted(flg):
                lines.append("  FLAGREAD %08x %s%s" % (k, flg[k][1], ranstr(k)))
            for k in sorted(opens):
                lines.append("  OPEN %08x %s %s%s" % (k, mask_names(opens[k][0]), opens[k][1], ranstr(k)))
            for k in sorted(exits):
                lines.append("  EXIT call %08x to %08x live %s%s" % (k, exits[k][1], mask_names(exits[k][0]), ranstr(k)))
            for k in sorted(ends):
                lines.append("  ROOTRET %08x live %s" % (k, mask_names(ends[k])))
    image_range = sum(ALLOC_LO <= a < ALLOC_HI for slot in LOCKS for a, _ in sites_of(L, regs, slot))
    head = ["ROOT %08x functions=%d instructions=%d indirect=%d undecoded=%d sites=%d sites_executed=%d sites_in_%08x_%08x=%d of_image=%d rule_fail=%d strict_fail=%d open=%d flagread=%d rootret_eax=%d"
            % (root, len(clo), len(inset), len(ind), undec, totals["sites"], totals["ran"], ALLOC_LO, ALLOC_HI, in_range, image_range, totals["rule_fail"], totals["fail"], totals["open"], totals["flagread"], totals["rootx"])]
    head += ["INDIRECT %08x %s %s" % (a, L.get(a)[1], L.get(a)[2]) for a in ind]
    return head + lines, totals, clo


class _Push:
    """a `jmp [slot]` site acts as the stand-in's `ret`: walk from each return with a fresh worklist."""

    def __init__(self, reads, opens, ends, w):
        self.reads, self.opens, self.ends, self.w = reads, opens, ends, w

    def append(self, item):
        r, o, e = self.w.walk(item[0], item[1])
        self.reads.update(r)
        self.opens.update(o)
        self.ends.update(e)


def slot_control(L, G, imports, regs):
    """every import slot, every site in the image, each walked inside its own function and its direct callers' return only."""
    w = Walker(L, G, imports, regs, set(), [], scope=None)
    out = []
    for s in sorted(imports):
        sites = sites_of(L, regs, s)
        if not sites:
            continue
        n, ra, rc, rd = 0, 0, 0, 0
        for a, _ in sites:
            i = L.get(a)
            if i[1] != "call":
                continue
            n += 1
            reads, _, _ = w.walk(i[0])
            m = 0
            for v in reads.values():
                m |= v[0]
            ra += bool(m & 0xF)
            rc += bool(m & 0xF0)
            rd += bool(m & 0xF00)
        out.append("IMPORT %08x %s!%s calls=%d read_eax=%d read_ecx=%d read_edx=%d" % (s, imports[s][0], imports[s][1], n, ra, rc, rd))
    return out


def entry_control(L, G, imports, regs, clo):
    """each function of the reached set from its entry: reads of ECX or EDX before a write are register arguments, so the walker must see them."""
    w = Walker(L, G, imports, regs, set(), [], scope=None)
    c = dict(n=0, eax=0, ecx=0, edx=0)
    for e in sorted(clo):
        if L.get(e) is None:
            continue
        reads, _, _ = w.walk(e, 0xFFF)
        m = 0
        for v in reads.values():
            m |= v[0]
        c["n"] += 1
        c["eax"] += bool(m & 0xF)
        c["ecx"] += bool(m & 0xF0)
        c["edx"] += bool(m & 0xF00)
    return "ENTRY functions=%d read_eax_first=%d read_ecx_first=%d read_edx_first=%d" % (c["n"], c["eax"], c["ecx"], c["edx"])


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rule_b_site(L, G, imports, regs, site):
    """rule (b): what the code after the IsBadCodePtr call reads of EAX, ECX, EDX before writing them, inside its function."""
    w = Walker(L, G, imports, regs, set(), [], scope=None)
    reads, opens, _ = w.walk(L.get(site)[0], 0xFFF)
    out = ["RULEB site %08x slot %08x" % (site, BADCODE)]
    out += ["  READ %08x %s %s" % (k, mask_names(reads[k][0]), reads[k][1]) for k in sorted(reads)]
    out += ["  OPEN %08x %s %s" % (k, mask_names(opens[k][0]), opens[k][1]) for k in sorted(opens)]
    return out


def rule_c_dispatch(L, d):
    """rule (c), on the kept output of `dispatch`: each pass stops at the call instruction, with the opcode's table row on the stack."""
    meta_path, out_path = (os.path.join(d, "..", "..", "r60c", "emu", "dispatch." + x) for x in ("meta", "out"))
    with open(meta_path, encoding="ascii") as f:
        metas = json.load(f)
    n = same = wrong = 0
    with open(out_path, encoding="ascii") as f:
        lines = f.read().splitlines()
    for i, x in enumerate(lines):
        p = x.split()
        if len(p) > 4 and p[0] == "C" and p[3] == "OBS":
            assert int(p[4], 16) == 0x0054D7DC
            pushed = struct.unpack("<I", bytes.fromhex(lines[i + 1].split()[1])[:4])[0]
            op = metas[int(p[1]) - 1]["op"]
            n += 1
            same += pushed == L.word(0x006E0D18 + 8 * op)
            wrong += pushed == L.word(0x006E0D18 + 8 * (op + 1))
    return "RULEC dispatch stops_at_0054d7dc=%d pushed_is_the_row=%d control_next_row_matches=%d" % (n, same, wrong)


def spec_slots(d):
    """which kept memory specs write an import slot: the families rule (d) names."""
    out = []
    for run in ("r60c", "r55c"):
        base = os.path.join(d, "..", "..", run, "emu")
        for n in sorted(os.listdir(base)):
            if n.endswith(".mem"):
                with open(os.path.join(base, n), encoding="ascii") as f:
                    hits = [" ".join(x.split()) for x in f if re.search(r"\b006cc[0-9a-f]{3}\b", x)]
                out.append("SPEC %s/%s import_slot_writes=%d %s" % (run, n, len(hits), "; ".join(hits)))
    return out


def same_output(cover_out, kept):
    """the coverage run's C, D, A, R, W lines against the kept EmuBoundary output, byte for byte."""
    with open(cover_out, encoding="ascii") as f:
        a = [x for x in f if not x.startswith("P ")]
    with open(kept, encoding="ascii") as f:
        return a == f.readlines()


def cover(path):
    with open(path, encoding="ascii") as f:
        return {int(x[2:], 16) for x in f if x.startswith("P ")}


def generate(exe, d):
    h = sha(exe)
    if not h.startswith(PINNED):
        raise SystemExit("not the pinned image: " + h[:16])
    L = Listing(exe=exe)
    imports = pe_imports(L.data)
    regs = slot_regs(L, imports)
    G = Graph(L, imports)
    files = {}
    raw = []
    for s in LOCKS + (BADCODE,):
        dll, name = imports[s]
        needle = struct.pack("<I", s)
        text_hits = data_hits = 0
        for va, sz, rp, ex in L.sections:
            blob = L.data[rp:rp + sz]
            c = 0
            p = blob.find(needle)
            while p >= 0:
                c += 1
                p = blob.find(needle, p + 1)
            if ex:
                text_hits += c
            else:
                data_hits += c
        decoded = sum(1 for i in L.ins.values() if ("0x%x" % s) in i[2])
        sites = sites_of(L, regs, s)
        form = {}
        for _, f in sites:
            k = f.split()[0] + (" [slot]" if "[slot]" in f else " r")
            form[k] = form.get(k, 0) + 1
        raw.append("SLOT %08x %s!%s raw_in_exec=%d raw_elsewhere=%d decoded_operands=%d sites=%d forms=%s"
                   % (s, dll, name, text_hits, data_hits, decoded, len(sites), ",".join("%s:%d" % kv for kv in sorted(form.items()))))
    raw.append("STANDIN 0066a250 bytes=%s" % L.data[0x0066A250 - L.sections[0][0] + L.sections[0][2]:][:3].hex())
    raw.append("STANDIN 004bad70 bytes=%s" % L.data[0x004BAD70 - L.sections[0][0] + L.sections[0][2]:][:10].hex())
    files["slots.txt"] = "\n".join(raw) + "\n"
    summary = ["image sha256 " + h, "tool sha256 " + sha(os.path.abspath(__file__))] + raw
    for fam, root in ROOTS.items():
        executed = cover(os.path.join(d, "cover", fam + ".out"))
        summary.append("COVER %s instructions=%d equal_to_kept_output=%s" % (fam, len(executed), same_output(os.path.join(d, "cover", fam + ".out"), os.path.join(d, "..", "..", "r60c", "emu", fam + ".out"))))
        for tier, ex in (("executed", executed), ("static", None)):
            lines, t, clo = scan(L, G, imports, regs, root, ex)
            files["sites-%s-%s.txt" % (fam, tier)] = "\n".join(lines) + "\n"
            summary.append("%s %s %s" % (fam, tier.upper(), lines[0]))
            files["functions-%s-%s.txt" % (fam, tier)] = "".join("%08x\n" % e for e in sorted(clo))
            summary.append(tier.upper() + " " + entry_control(L, G, imports, regs, clo))
    summary += spec_slots(d)
    summary += rule_b_site(L, G, imports, regs, 0x00543E73)
    summary.append(rule_c_dispatch(L, d))
    files["controls.txt"] = "\n".join(slot_control(L, G, imports, regs)) + "\n"
    files["summary.txt"] = "\n".join(summary) + "\n"
    return files


def write(d, files):
    os.makedirs(d, exist_ok=True)
    for n, t in files.items():
        with open(os.path.join(d, n), "w", encoding="ascii") as f:
            f.write(t)
    every = []
    for top, _, names in os.walk(d):
        every += [os.path.relpath(os.path.join(top, n), d) for n in names]
    with open(os.path.join(d, "manifest.txt"), "w", encoding="ascii") as f:
        for n in sorted(x for x in every if x != "manifest.txt"):
            f.write("%s  %s\n" % (sha(os.path.join(d, n)), n))


def main():
    a = sys.argv[1:]
    if len(a) != 3 or a[0] not in ("run", "check") or a[1] != "--dir":
        raise SystemExit(__doc__)
    files = generate(EXE, a[2])
    if a[0] == "run":
        write(a[2], files)
        print(files["summary.txt"], end="")
        return
    bad = 0
    for n, t in files.items():
        with open(os.path.join(a[2], n), encoding="ascii") as f:
            if f.read() != t:
                print("DIFF", n)
                bad += 1
    print("check", "ok" if not bad else "differs", len(files))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

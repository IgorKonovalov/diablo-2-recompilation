#!/usr/bin/env python3
"""Plan 0052 Phase 2 (second run): a resumable model of an AI decision, past its first boundary (ADR-0015, ADR-0021).

    python3 -I tools/ai_resume.py check LOG [LOG ...] [--rows 6,28] [--out FILE]   # resume every decision at each boundary

The think function of a decision is executed from its entry, as code, by a small x86 interpreter over the pinned
game.exe (read through objdump, Intel syntax). What the logger recorded is known: the unit (type, class, mode, seed, +0xC4),
the AI control, the head record, the MonStats `aip`/`Skill`/`aidel` bytes, the AiCtx, the game's difficulty and frame, the
target's type, class, id, mode and position. Every other byte is unknown, and an unknown value is carried as None. A branch
on an unknown flag forks the state; both successors live on. A call to a boundary function (the 136 of tools/gdb/ai.py,
ADR-0021) is not executed: the model offers the call (function, call site, ECX, EDX, stack words, the unit seed, the AI
control words) to the logged boundary list, and a logged call matches when it equals one of the offered calls in every word
the model knows. The call then *returns the logged result*: EAX, the unit seed after the call, the control words, +0xC4 and
the blocks the arguments point at (the AIR lines of logger rev 4), and execution resumes from the surviving states. A call
that is neither a boundary nor on the list of callees that are executed (RNG and the position getters, `EXEC`) is opaque:
EAX, ECX, EDX and the memory it is passed a pointer to become unknown. When the logged boundaries are used up the decision
must be able to return without another boundary call (if the logger did not cap it at 16 calls).

What this proves, and what not: every logged boundary call, with its words, is a call the game's code can make from the
logged inputs and the earlier logged results; the model is the code, not a reading of it, so a mismatch is a wrong
interpreter, a wrong logged input or a game that did not run this code. It does not prove which of several offered
calls the code takes when an unknown value decides (the log shows the one it took), and it assumes opaque callees leave
the known memory unchanged except through their pointer arguments. A decision that cannot be resumed says why (the `STOP`
reasons: unsupported instruction, unresolved call target, state limit, no logged result, capped log).
Stdlib and objdump only.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

EXE = os.path.join(ROOT, "workspace", "runtime", "game", "game.exe")
M32 = 0xFFFFFFFF
MUL = 0x6AC690C5
STK_TOP = 0x7FF00000
RET_SENTINEL = 0x7FFF0000
PATH_U = 0x7A100000     # synthetic blocks (their addresses are not compared with the live ones)
PATH_T = 0x7A200000
THINK_WINDOWS = ((0x005B14E0, 0x005B1650), (0x005E0000, 0x00600000), (0x0058F0D0, 0x0058F130), (0x005DE830, 0x005DE8C0),
                 (0x005DF850, 0x005DFC00))
NESTED = ()
# callees that are executed rather than treated as opaque: RNG_Range, RNG_RangeB, the unit position getters, the AI
# distance, the two helpers whose windows the logger covers (0x005DE830, 0x005DF850)
EXEC = (0x0045C390, 0x0045C3E0, 0x0045ADF0, 0x0045AE20, 0x005DC530, 0x006488C0, 0x00648900, 0x005DE830, 0x005DF850)
# a callee inside these windows is executed too: its own calls to boundary functions are logged (the logger's return-address
# windows), so an opaque helper there would make its logged calls appear from nowhere
EXEC_WINDOWS = ((0x005E0000, 0x00600000), (0x005DE830, 0x005DE8C0), (0x005DF850, 0x005DFC00))
MAX_STATES = 96
MAX_STEPS = 6000
LOOP_LIMIT = 120


def u32(v):
    return None if v is None else v & M32


def s32(v):
    return None if v is None else (v & M32) - (1 << 32 if v & 0x80000000 else 0)


def seedval(txt):
    a, b = txt.split(":")
    return int(a, 16), int(b, 16)


# ------------------------------------------------------------------------------------------------------ the code
class Code:
    """Instruction text of the pinned image: {addr: (length, mnemonic, [operand text])}, loaded by objdump on demand
    (a window of 0x1000 bytes at a time), plus the `ret N` of a function. `inject` replaces objdump (the no-game tests)."""

    def __init__(self, exe=EXE, inject=None):
        self.exe, self.ins, self.loaded, self.retn = exe, {}, set(), {}
        if inject:
            self.ins.update(inject)
            self.loaded = None

    def _load(self, a):
        """Decode from `a`, which execution reached as an instruction start, to the first instruction that ends the flow
        (ret, an unconditional jmp, int3): later bytes may be data, and a sweep from another start would desynchronise."""
        if self.loaded is None or a in self.loaded:
            return
        out = subprocess.run(["objdump", "-d", "-M", "intel", "--start-address=0x%x" % a, "--stop-address=0x%x" % (a + 0x200),
                              self.exe], capture_output=True, text=True).stdout
        last = None
        got = []
        new = set()           # the instructions this load added (a continuation line extends only those)
        ended = False
        for ln in out.splitlines():
            m = re.match(r"\s*([0-9a-f]+):\t([0-9a-f ]+?)\s*\t(.*)", ln)
            if not m:
                c = re.match(r"\s*([0-9a-f]+):\t([0-9a-f ]+?)\s*$", ln)     # the bytes objdump wraps after seven
                if c and last is not None and last in new:
                    n, mn, ops = self.ins[last]
                    self.ins[last] = (n + len(c.group(2).split()), mn, ops)
                continue
            ad = int(m.group(1), 16)
            ins = self._parse(len(m.group(2).split()), m.group(3))
            if ad not in self.ins:
                self.ins[ad] = ins
                new.add(ad)
            got.append(ad)
            last = ad
            if ins[1] in ("ret", "retn", "jmp", "int3"):
                ended = True
                break
        if not ended and got:           # the window cut the last instruction short: do not keep that decode
            if got[-1] != a:
                if got[-1] in new:
                    del self.ins[got[-1]]
                got.pop()
        self.loaded.update(got)

    @staticmethod
    def _parse(n, text):
        text = text.split("#")[0].strip()
        parts = text.split(None, 1)
        mn = parts[0]
        if mn in ("rep", "repz", "repnz", "lock") and len(parts) > 1:
            return (n, mn + " " + parts[1].split()[0], [])
        ops = []
        if len(parts) > 1:
            depth, cur = 0, ""
            for ch in parts[1]:
                if ch == "[":
                    depth += 1
                if ch == "]":
                    depth -= 1
                if ch == "," and depth == 0:
                    ops.append(cur.strip())
                    cur = ""
                else:
                    cur += ch
            ops.append(cur.strip())
        return (n, mn, ops)

    def at(self, a):
        if a not in self.ins:
            self._load(a)
        return self.ins.get(a)

    def ret_imm(self, fn):
        """The `ret N` byte count of the function at fn (the first `ret` met from its start), None when not found."""
        if fn in self.retn:
            return self.retn[fn]
        a, r = fn, None
        for _ in range(900):
            i = self.at(a)
            if i is None:
                break
            if i[1] in ("ret", "retn"):
                r = int(i[2][0], 16) if i[2] else 0
                break
            a += i[0]
        self.retn[fn] = r
        return r


# ------------------------------------------------------------------------------------------------------ registers
R32 = ("eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi")
R16 = {"ax": "eax", "cx": "ecx", "dx": "edx", "bx": "ebx", "sp": "esp", "bp": "ebp", "si": "esi", "di": "edi"}
R8L = {"al": "eax", "cl": "ecx", "dl": "edx", "bl": "ebx"}
R8H = {"ah": "eax", "ch": "ecx", "dh": "edx", "bh": "ebx"}
SIZES = {"BYTE": 1, "WORD": 2, "DWORD": 4}


class State:
    def __init__(self):
        self.r = {k: None for k in R32}
        self.f = {"ZF": None, "SF": None, "CF": None, "OF": None}
        self.m = {}
        self.eip = 0
        self.steps = 0
        self.visits = {}
        self.calls = []             # the boundary calls this path has met: (fn, ra)
        self.prot = set()           # the bytes of pushed return addresses and saved EBPs: an opaque callee's blocks skip them

    def copy(self):
        s = State()
        s.r, s.f, s.m, s.eip, s.steps = dict(self.r), dict(self.f), dict(self.m), self.eip, self.steps
        s.visits, s.calls, s.prot = dict(self.visits), list(self.calls), set(self.prot)
        return s

    def key(self):
        return (self.eip, tuple(self.r[k] for k in R32), tuple(self.f.values()), frozenset(self.m.items()))

    # memory (little endian; None when any byte is unknown)
    def rd(self, a, n):
        if a is None:
            return None
        v = 0
        for k in range(n):
            b = self.m.get((a + k) & M32)
            if b is None:
                return None
            v |= b << (8 * k)
        return v

    def wr(self, a, n, v):
        if a is None:
            return
        for k in range(n):
            if v is None:
                self.m.pop((a + k) & M32, None)
            else:
                self.m[(a + k) & M32] = (v >> (8 * k)) & 0xFF

    def forget(self, a, n):
        if a is None:
            return
        for k in range(n):
            if (a + k) & M32 not in self.prot:
                self.m.pop((a + k) & M32, None)


class Stop(Exception):
    pass


def parse_op(t):
    """-> ("r", name, size) | ("i", value) | ("m", size, base, index, scale, disp)"""
    t = t.strip()
    sz = None
    m = re.match(r"(BYTE|WORD|DWORD) PTR (.*)", t)
    if m:
        sz, t = SIZES[m.group(1)], m.group(2)
    if t.startswith("["):
        inner = t[1:t.index("]")]
        rest = t[t.index("]") + 1:]
        base = index = None
        scale, disp = 1, 0
        for sign, tok in re.findall(r"([+-]?)\s*([^+-]+)", inner):
            tok = tok.strip()
            s = -1 if sign == "-" else 1
            mm = re.match(r"(e[a-z]{2})\*(\d)$", tok)
            if mm:
                index, scale = mm.group(1), int(mm.group(2))
            elif tok in R32:
                if base is None:
                    base = tok
                else:
                    index = tok
            elif tok.startswith("0x"):
                disp += s * int(tok, 16)
            else:
                raise Stop("operand " + t)
        if rest.strip():
            raise Stop("operand " + t)
        return ("m", sz or 4, base, index, scale, disp)
    if t in R32:
        return ("r", t, 4)
    if t in R16:
        return ("r", R16[t], 2)
    if t in R8L:
        return ("r", R8L[t], 1)
    if t in R8H:
        return ("r", R8H[t], -1)
    if t.startswith("0x") or re.match(r"^-?\d+$", t):
        return ("i", int(t, 0))
    raise Stop("operand " + t)


def mask(n):
    return (1 << (8 * n)) - 1


def sign(v, n):
    return bool(v & (1 << (8 * n - 1)))


def alu(op, a, b, n, cf_in=None):
    """-> (result, {flags}) for add sub adc sbb and or xor cmp test with unknown propagation (None)."""
    if a is None or b is None or (op in ("adc", "sbb") and cf_in is None):
        if op == "xor" and a is None and b is None:
            pass
        return None, {"ZF": None, "SF": None, "CF": None, "OF": None}
    mk = mask(n)
    a &= mk
    b &= mk
    fl = {"CF": False, "OF": False}
    if op in ("add", "adc"):
        c = cf_in if op == "adc" else 0
        t = a + b + c
        r = t & mk
        fl["CF"] = t > mk
        fl["OF"] = sign(~(a ^ b) & (a ^ r), n)
    elif op in ("sub", "sbb", "cmp"):
        c = cf_in if op == "sbb" else 0
        t = a - b - c
        r = t & mk
        fl["CF"] = t < 0
        fl["OF"] = sign((a ^ b) & (a ^ r), n)
    elif op in ("and", "test"):
        r = a & b
    elif op == "or":
        r = a | b
    else:
        r = a ^ b
    fl["ZF"] = r == 0
    fl["SF"] = sign(r, n)
    return r, fl


CONDS = {"je": "ZF", "jne": "!ZF", "js": "SF", "jns": "!SF", "jb": "CF", "jae": "!CF", "jbe": "CF|ZF", "ja": "!CF&!ZF",
         "jl": "SF!=OF", "jge": "SF==OF", "jle": "ZF|SF!=OF", "jg": "!ZF&SF==OF", "jz": "ZF", "jnz": "!ZF", "jc": "CF",
         "jnc": "!CF", "jnae": "CF", "jnb": "!CF", "jna": "CF|ZF", "jnbe": "!CF&!ZF", "jnge": "SF!=OF", "jnl": "SF==OF",
         "jng": "ZF|SF!=OF", "jnle": "!ZF&SF==OF"}


def cond_value(name, f):
    """True, False, or None (unknown) for a conditional jump over the flags."""
    e = CONDS[name]
    def g(k):
        return f[k]
    if e in ("ZF", "SF", "CF"):
        return g(e)
    if e in ("!ZF", "!SF", "!CF"):
        v = g(e[1:])
        return None if v is None else not v
    if e == "CF|ZF":
        a, b = g("CF"), g("ZF")
        return True if (a or b) else (False if (a is False and b is False) else None)
    if e == "!CF&!ZF":
        a, b = g("CF"), g("ZF")
        return False if (a or b) else (True if (a is False and b is False) else None)
    s, o = g("SF"), g("OF")
    if e == "SF!=OF":
        return None if s is None or o is None else s != o
    if e == "SF==OF":
        return None if s is None or o is None else s == o
    z = g("ZF")
    if e == "ZF|SF!=OF":
        if z:
            return True
        if z is None or s is None or o is None:
            return None
        return s != o
    if e == "!ZF&SF==OF":
        if z:
            return False
        if z is None or s is None or o is None:
            return None
        return s == o
    return None


class Machine:
    """Runs a State until it calls a boundary function, returns from the think function, or stops."""

    def __init__(self, code, bnd, invert=False, windows=THINK_WINDOWS):
        self.code, self.bnd, self.invert, self.windows = code, set(bnd), invert, windows

    # ---- operands
    def ea(self, st, op):
        _, sz, base, index, scale, disp = op
        a = disp
        if base:
            if st.r[base] is None:
                return None
            a += st.r[base]
        if index:
            if st.r[index] is None:
                return None
            a += st.r[index] * scale
        return a & M32

    def read(self, st, op):
        if op[0] == "i":
            return op[1] & M32
        if op[0] == "r":
            v = st.r[op[1]]
            if v is None:
                return None
            if op[2] == 4:
                return v
            if op[2] == 2:
                return v & 0xFFFF
            if op[2] == 1:
                return v & 0xFF
            return (v >> 8) & 0xFF
        return st.rd(self.ea(st, op), op[1])

    def write(self, st, op, v):
        if op[0] == "r":
            old = st.r[op[1]]
            if v is None:
                st.r[op[1]] = None if op[2] == 4 else None
            elif op[2] == 4:
                st.r[op[1]] = v & M32
            elif old is None:
                st.r[op[1]] = None
            elif op[2] == 2:
                st.r[op[1]] = (old & ~0xFFFF & M32) | (v & 0xFFFF)
            elif op[2] == 1:
                st.r[op[1]] = (old & ~0xFF & M32) | (v & 0xFF)
            else:
                st.r[op[1]] = (old & ~0xFF00 & M32) | ((v & 0xFF) << 8)
        else:
            st.wr(self.ea(st, op), op[1], v)

    def opsize(self, op, other=None):
        if op[0] in ("r", "m"):
            return 1 if (op[0] == "r" and op[2] == -1) else op[2 if op[0] == "r" else 1]
        return 4

    def push(self, st, v):
        sp = None if st.r["esp"] is None else (st.r["esp"] - 4) & M32
        st.r["esp"] = sp
        st.wr(sp, 4, v)

    def pop(self, st):
        sp = st.r["esp"]
        v = st.rd(sp, 4)
        st.r["esp"] = None if sp is None else (sp + 4) & M32
        return v

    # ---- one instruction; returns a list of successor states (fork) or the event
    def step(self, st):
        ins = self.code.at(st.eip)
        if ins is None:
            raise Stop("no code at %08x" % st.eip)
        n, mn, ops = ins
        nxt = st.eip + n
        st.steps += 1
        if st.steps > MAX_STEPS:
            raise Stop("step limit")
        p = [parse_op(o) for o in ops] if mn not in ("call", "jmp") and not mn.startswith("j") else None
        if mn in ("mov",):
            self.write(st, p[0], self.read(st, p[1]))
        elif mn in ("movzx", "movsx"):
            v = self.read(st, p[1])
            ns = self.opsize(p[1])
            if v is not None and mn == "movsx":
                v = (v - (1 << (8 * ns))) if sign(v, ns) else v
            self.write(st, p[0], u32(v) if v is not None else None)
        elif mn == "lea":
            self.write(st, p[0], self.ea(st, p[1]))
        elif mn == "push":
            self.push(st, self.read(st, p[0]) if p[0][0] != "i" else p[0][1] & M32)
            if p[0] == ("r", "ebp", 4) and st.r["esp"] is not None:
                st.prot.update(range(st.r["esp"], st.r["esp"] + 4))
        elif mn == "pop":
            self.write(st, p[0], self.pop(st))
        elif mn in ("add", "sub", "adc", "sbb", "and", "or", "xor", "cmp", "test"):
            sz = self.opsize(p[0])
            if mn == "xor" and p[0] == p[1]:
                a = b = 0
            else:
                a, b = self.read(st, p[0]), self.read(st, p[1])
                if p[1][0] == "i" and b is not None:
                    b &= mask(sz) if p[1][1] >= 0 else mask(sz)
            r, fl = alu(mn, a, b, sz, (1 if st.f["CF"] else 0) if st.f["CF"] is not None else None)
            if mn in ("and", "or", "xor", "test") and a is not None and b is not None:
                fl["CF"] = fl["OF"] = False
            if mn == "and" and (a == 0 or b == 0) and r is None:
                r, fl = 0, {"ZF": True, "SF": False, "CF": False, "OF": False}
            st.f.update(fl)
            if mn not in ("cmp", "test"):
                self.write(st, p[0], r)
        elif mn in ("inc", "dec"):
            sz = self.opsize(p[0])
            a = self.read(st, p[0])
            cf = st.f["CF"]
            r, fl = alu("add" if mn == "inc" else "sub", a, 1, sz)
            fl["CF"] = cf
            st.f.update(fl)
            self.write(st, p[0], r)
        elif mn == "neg":
            sz = self.opsize(p[0])
            a = self.read(st, p[0])
            r, fl = alu("sub", 0, a, sz)
            if a is not None:
                fl["CF"] = a != 0
            st.f.update(fl)
            self.write(st, p[0], r)
        elif mn == "not":
            a = self.read(st, p[0])
            self.write(st, p[0], None if a is None else (~a) & mask(self.opsize(p[0])))
        elif mn in ("shl", "sal", "shr", "sar"):
            sz = self.opsize(p[0])
            a = self.read(st, p[0])
            c = self.read(st, p[1]) if len(p) > 1 else 1
            if a is None or c is None:
                st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
                self.write(st, p[0], None)
            else:
                c &= 31
                if c:
                    mk = mask(sz)
                    if mn in ("shl", "sal"):
                        cf = bool((a << c) & (mk + 1)) if c <= 8 * sz else False
                        r = (a << c) & mk
                    elif mn == "shr":
                        cf = bool((a >> (c - 1)) & 1)
                        r = a >> c
                    else:
                        sv = a - (1 << (8 * sz)) if sign(a, sz) else a
                        cf = bool((sv >> (c - 1)) & 1)
                        r = (sv >> c) & mk
                    st.f.update({"ZF": r == 0, "SF": sign(r, sz), "CF": cf, "OF": None})
                    self.write(st, p[0], r)
        elif mn == "mul":
            sz = self.opsize(p[0])
            a, b = st.r["eax"], self.read(st, p[0])
            if sz != 4:
                raise Stop("mul size")
            if a is None or b is None:
                st.r["eax"] = st.r["edx"] = None
                st.f.update({"CF": None, "OF": None})
            else:
                t = a * b
                st.r["eax"], st.r["edx"] = t & M32, (t >> 32) & M32
                st.f.update({"CF": st.r["edx"] != 0, "OF": st.r["edx"] != 0})
        elif mn == "imul":
            if len(p) == 1:
                a, b = s32(st.r["eax"]), s32(self.read(st, p[0]))
                if a is None or b is None:
                    st.r["eax"] = st.r["edx"] = None
                else:
                    t = a * b
                    st.r["eax"], st.r["edx"] = t & M32, (t >> 32) & M32
            else:
                a = s32(self.read(st, p[1] if len(p) == 2 else p[1]))
                b = s32(self.read(st, p[0])) if len(p) == 2 else s32(self.read(st, p[2]))
                self.write(st, p[0], None if a is None or b is None else (a * b) & M32)
            st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
        elif mn in ("div", "idiv"):
            a, d, b = st.r["eax"], st.r["edx"], self.read(st, p[0])
            if a is None or d is None or b is None or b == 0 or self.opsize(p[0]) != 4:
                st.r["eax"] = st.r["edx"] = None
            else:
                if mn == "div":
                    t = (d << 32) | a
                    q, r = divmod(t, b)
                else:
                    t = s32(d) * (1 << 32) + a
                    bs = s32(b)
                    q = abs(t) // abs(bs) * (1 if (t < 0) == (bs < 0) else -1)
                    r = t - q * bs
                st.r["eax"], st.r["edx"] = q & M32, r & M32
            st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
        elif mn == "cdq":
            a = st.r["eax"]
            st.r["edx"] = None if a is None else (M32 if a & 0x80000000 else 0)
        elif mn == "xchg":
            a, b = self.read(st, p[0]), self.read(st, p[1])
            self.write(st, p[0], b)
            self.write(st, p[1], a)
        elif mn.startswith("set"):
            cc = "j" + mn[3:]
            v = cond_value(cc, st.f) if cc in CONDS else None
            self.write(st, p[0], None if v is None else int(v))
        elif mn in ("nop", "int3", "cld", "std"):
            pass
        elif mn.startswith("j"):
            if mn == "jmp":
                tgt = ops[0]
                if tgt.startswith("0x"):
                    st.eip = int(tgt, 16)
                    return [st]
                raise Stop("indirect jmp %s at %08x" % (tgt, st.eip))
            if mn not in CONDS:
                raise Stop("jcc %s" % mn)
            v = cond_value(mn, st.f)
            if self.invert and v is not None:        # the negative control: a wrong map, every known branch reversed
                v = not v
            tgt = int(ops[0], 16)
            if v is not None:
                st.eip = tgt if v else nxt
                return [st]
            a, b = st.copy(), st
            a.eip, b.eip = tgt, nxt
            e = CONDS[mn]
            for s2, taken in ((a, True), (b, False)):
                if e in ("ZF", "SF", "CF"):
                    s2.f[e] = taken
                elif e in ("!ZF", "!SF", "!CF"):
                    s2.f[e[1:]] = not taken
            return [a, b]
        elif mn == "call":
            return self.do_call(st, ops[0], nxt)
        elif mn in ("ret", "retn"):
            ra = self.pop(st)
            if ops:
                st.r["esp"] = None if st.r["esp"] is None else (st.r["esp"] + int(ops[0], 16)) & M32
            st.eip = ra if ra is not None else -1
            if ra is None:
                raise Stop("unknown return address")
            return [st]
        else:
            raise Stop("unsupported %s %s at %08x" % (mn, ",".join(ops), st.eip))
        st.eip = nxt
        return [st]

    def do_call(self, st, tgt, ra):
        if tgt.startswith("0x"):
            fn = int(tgt, 16)
        else:
            op = parse_op(tgt)
            fn = self.read(st, op)
            if fn is None:
                raise Stop("unresolved call target %s at %08x" % (tgt, st.eip))
        in_win = any(lo <= ra < hi for lo, hi in self.windows)
        if fn in self.bnd and in_win:
            st.eip = ra
            raise Event(st, fn, ra)
        if fn in EXEC or any(lo <= fn < hi for lo, hi in EXEC_WINDOWS):
            self.push(st, ra)
            if st.r["esp"] is not None:
                st.prot.update(range(st.r["esp"], st.r["esp"] + 4))
            st.eip = fn
            return [st]
        # opaque: the result and the registers a callee may use become unknown, the memory its pointer arguments name
        n = self.code.ret_imm(fn)
        if n is None:
            raise Stop("opaque callee %08x: no ret found" % fn)
        sp = st.r["esp"]
        words = [st.rd(sp + 4 * k, 4) if sp is not None else None for k in range(n // 4)]
        for v in [st.r["ecx"], st.r["edx"]] + words:
            if v is not None and (STK_TOP - 0x4000) <= v < STK_TOP + 0x10:
                # a block on the stack: a local of the running function (below its EBP) up to 64 bytes, else 16; the saved
                # words and return addresses are never cleared (st.prot)
                bp = st.r["ebp"]
                st.forget(v, min(64, bp - v) if bp is not None and v < bp else 16)
        st.r["eax"] = st.r["ecx"] = st.r["edx"] = None
        st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
        st.r["esp"] = None if sp is None else (sp + n) & M32
        st.eip = ra
        return [st]

    def run(self, st0):
        """-> (events, returns, stops): every way the state can reach a boundary call, return from the function, or stop."""
        work, events, rets, stops, seen = [st0], [], [], [], set()
        while work:
            st = work.pop()
            try:
                while True:
                    if st.eip == RET_SENTINEL:
                        rets.append(st)
                        break
                    c = st.visits.get(st.eip, 0) + 1
                    st.visits[st.eip] = c
                    if c > LOOP_LIMIT:
                        raise Stop("loop limit at %08x" % st.eip)
                    out = self.step(st)
                    if len(out) == 2:
                        k = out[0].key(), out[1].key()
                        for s2 in out:
                            kk = s2.key()
                            if kk in seen:
                                continue
                            seen.add(kk)
                            work.append(s2)
                        break
                    st = out[0]
            except Event as ev:
                events.append(ev)
            except Stop as e:
                stops.append(str(e))
            if len(work) + len(events) > MAX_STATES * 4:
                stops.append("state limit")
                break
        return events, rets, stops


class Event(Exception):
    def __init__(self, st, fn, ra):
        self.st, self.fn, self.ra = st, fn, ra


# ------------------------------------------------------------------------------------------------ decision models
def init_state(aid):
    """The state at the think function's entry from an AID line: the memory the logger recorded, everything else unknown."""
    st = State()
    g, u, cx = aid["g"], aid["u"], aid["cx"]
    ctl, md, ms, hp = aid["ctlp"], aid["mdp"], aid["ms"], aid["hp"]
    cw = aid["ctx"]
    # unit
    st.wr(u, 4, 1)
    st.wr(u + 4, 4, aid["c"] & M32)
    st.wr(u + 0x0C, 4, aid["id"])
    st.wr(u + 0x10, 4, aid["m"])
    st.wr(u + 0x14, 4, md)
    s0, s1 = seedval(aid["s"])
    st.wr(u + 0x20, 4, s0)
    st.wr(u + 0x24, 4, s1)
    st.wr(u + 0x2C, 4, PATH_U)
    st.wr(PATH_U + 2, 2, aid["x"])
    st.wr(PATH_U + 6, 2, aid["y"])
    st.wr(u + 0xC4, 4, aid["c4"])
    st.wr(md + 0x28, 4, ctl)
    st.wr(md + 0x54, 4, aid["md"])
    for k, b in enumerate(bytes.fromhex(aid["ctl"])):
        st.m[ctl + k] = b
    if hp and aid.get("head"):
        for k, b in enumerate(bytes.fromhex(aid["head"])):
            st.m[hp + k] = b
    # MonStats row: ai, aidel/aidist, aip, skills
    st.wr(ms + 0x1E, 2, aid["ai"] & 0xFFFF)
    st.wr(ms + 0x4F, 1, aid["ad"][0])
    st.wr(ms + 0x52, 1, aid["ad"][1])
    for k, b in enumerate(bytes.fromhex(aid["aip"])):
        st.m[ms + 0x56 + k] = b
    for k, b in enumerate(bytes.fromhex(aid["sk"])):
        st.m[ms + 0x170 + k] = b
    # game
    st.wr(g + 0x6D, 1, aid["diff"])
    st.wr(g + 0xA8, 4, aid["fr"])
    # the AiCtx
    for k, w in enumerate(cw):
        st.wr(cx + 4 * k, 4, w)
    # the target
    t = aid.get("t")
    if cw[2] and t:
        tg = cw[2]
        st.wr(tg, 4, t[0])
        st.wr(tg + 4, 4, t[1] & M32)
        st.wr(tg + 0x0C, 4, t[2])
        st.wr(tg + 0x10, 4, t[3])
        if t[4] is not None:
            st.wr(tg + 0x2C, 4, PATH_T)
            st.wr(PATH_T + 2, 2, t[4])
            st.wr(PATH_T + 6, 2, t[5])
    # the call: ECX game, EDX unit, [esp + 4] the AiCtx, return address
    st.r.update({"ecx": g, "edx": u, "esp": STK_TOP})
    st.wr(STK_TOP, 4, RET_SENTINEL)
    st.prot.update(range(STK_TOP, STK_TOP + 8))
    st.wr(STK_TOP + 4, 4, cx)
    st.eip = aid["th"]
    return st


def offered(ev, aid, nargs=6):
    """The words of an offered boundary call, None where the model does not know them. Only the callee's own stack
    arguments (its `ret N`) are words of the call; the logger's other stack words are whatever lay above them."""
    st = ev.st
    sp = st.r["esp"]
    args = [(st.rd(sp + 4 * k, 4) if sp is not None else None) if k < nargs else None for k in range(6)]
    u = aid["u"]
    ctl = aid["ctlp"]
    return {"fn": ev.fn, "ra": ev.ra, "ecx": st.r["ecx"], "edx": st.r["edx"], "a": args,
            "s": (st.rd(u + 0x20, 4), st.rd(u + 0x24, 4)), "c": [st.rd(ctl + 0x14 + 4 * k, 4) for k in range(3)],
            "c4": st.rd(u + 0xC4, 4)}


def synthetic(v):
    return v is not None and (0x7A000000 <= v < 0x7B000000 or 0x7FE00000 <= v < 0x80000000)


def match(off, b):
    """The differences between an offered call and a logged AIB line (an empty list: the logged call is this one)."""
    d = []
    if off["fn"] != b["fn"]:
        d.append("fn")
    if off["ra"] != b["ra"]:
        d.append("ra")
    for nm in ("ecx", "edx"):
        if off[nm] is not None and not synthetic(off[nm]) and off[nm] != b[nm]:
            d.append(nm)
    for k, v in enumerate(off["a"]):
        if v is not None and not synthetic(v) and v != b["a"][k]:
            d.append("arg%d" % k)
    if off["s"][0] is not None and off["s"][1] is not None and "%08x:%08x" % off["s"] != b["s"]:
        d.append("seed")
    for k, v in enumerate(off["c"]):
        if v is not None and v != b["c"][k]:
            d.append("c%d" % k)
    if off["c4"] is not None and off["c4"] != b["c4"]:
        d.append("c4")
    return d


def apply_result(m, ev, b, r, aid):
    """The state after the logged call returned: EAX, the seed, the control words, +0xC4 and the argument blocks from AIR."""
    st = ev.st.copy()
    n = m.code.ret_imm(ev.fn)
    if n is None:
        raise Stop("boundary %08x: no ret found" % ev.fn)
    u, ctl = aid["u"], aid["ctlp"]
    sp = st.r["esp"]
    st.r["esp"] = (sp + n) & M32
    st.r["eax"] = r["eax"]
    st.r["ecx"] = st.r["edx"] = None
    st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
    s0, s1 = seedval(r["s"])
    st.wr(u + 0x20, 4, s0)
    st.wr(u + 0x24, 4, s1)
    for k in range(3):
        st.wr(ctl + 0x14 + 4 * k, 4, r["c"][k])
    st.wr(u + 0xC4, 4, r["c4"])
    for i, blk in (r.get("bl") or {}).items():
        a = ev.st.rd(sp + 4 * int(i), 4)            # the pointer the model passed (its own stack, not the live address)
        if a is None:
            continue
        before = (b.get("b") or {}).get(i)
        for k, w in enumerate(blk):
            if before is not None and before[k] == w:
                continue                             # a word the callee did not change is not an output
            if any((a + 4 * k + j) in st.prot for j in range(4)):
                continue
            st.wr(a + 4 * k, 4, w)
    st.eip = ev.ra
    return st


class Result:
    def __init__(self):
        self.matched = 0          # logged boundary calls matched
        self.offers = []          # per matched call: the number of distinct (fn, ra) the model offered
        self.status = "ok"        # ok, mismatch, stop
        self.why = ""
        self.end = None           # True: the model reaches the return with no further call; False: it cannot
        self.nlog = 0


def top_level(dec):
    """The logged boundary calls the think function itself made: a logged call that lies between another call's AIB line and
    its AIR line was made inside that callee (a boundary function whose body is in the logger's windows, MonsterOwner, a
    search) and is not offered by the model, which does not execute boundary functions."""
    spans = [(b["n"], dec["air"][b["n"]]["n"]) for b in dec["aib"] if b["n"] in dec["air"]]
    return [b for b in dec["aib"] if not any(lo < b["n"] < hi for lo, hi in spans)]


def check_decision(m, dec):
    """Resume one decision (a tools/ai.py parse() record) at each logged boundary. -> Result."""
    res = Result()
    aid = dec["aid"]
    log = top_level(dec)
    res.nlog = len(log)
    try:
        states = [init_state(aid)]
    except (KeyError, ValueError) as e:
        res.status, res.why = "stop", "input %r" % (e,)
        return res
    for i, b in enumerate(log):
        evs = []
        stops = []
        for st in states:
            e, r, s = m.run(st)
            evs += e
            stops += s
        if not evs:
            res.status = "stop" if stops else "mismatch"
            res.why = "boundary %d: %s" % (i + 1, stops[0] if stops else "the model has no further call (logged %08x@%08x)" % (b["fn"], b["ra"]))
            return res
        offs = [(ev, offered(ev, aid, min(6, (m.code.ret_imm(ev.fn) or 24) // 4))) for ev in evs]
        res.offers.append(len({(o["fn"], o["ra"]) for _, o in offs}))
        ok = [(ev, o) for ev, o in offs if not match(o, b)]
        if not ok and stops:       # a path the model could not follow may be the one the game took: inconclusive
            res.status = "stop"
            res.why = "boundary %d: a path was not followed (%s); logged %08x@%08x not among the %d offered" % (
                i + 1, stops[0], b["fn"], b["ra"], len(offs))
            return res
        if not ok:
            near = min(offs, key=lambda x: len(match(x[1], b)))
            res.status = "mismatch"
            res.why = "boundary %d: logged %08x@%08x; closest offered %08x@%08x differs in %s (%d offered)" % (
                i + 1, b["fn"], b["ra"], near[1]["fn"], near[1]["ra"], ",".join(match(near[1], b)), len(offs))
            return res
        r = dec["air"].get(b["n"])
        if r is None:
            res.status, res.why = "stop", "boundary %d: no AIR line (call site not armed)" % (i + 1)
            return res
        try:
            nxt = [apply_result(m, ev, b, r, aid) for ev, o in ok]
        except Stop as e:
            res.status, res.why = "stop", str(e)
            return res
        dedup = {}
        for s in nxt:
            dedup[s.key()] = s
        states = list(dedup.values())[:MAX_STATES]
        res.matched += 1
    if len(dec["aib"]) >= dec.get("bmax", 48):
        res.status, res.why = "stop", "capped: the logger keeps %d boundary calls per decision" % dec.get("bmax", 48)
        return res
    # the logged boundaries are used up and the event ended: some state must return with no further call
    reach = 0
    stops = []
    for st in states:
        e, r, s = m.run(st)
        reach += len(r)
        stops += s
    res.end = reach > 0
    if not res.end:
        res.status = "stop" if stops else "mismatch"
        res.why = ("after boundary %d: %s" % (len(log), stops[0])) if stops else \
            "after boundary %d: the model offers another call, the decision ended" % len(log)
    return res


# ------------------------------------------------------------------------------------------------------------ CLI
def bnd_set():
    import re as _re
    src = open(os.path.join(HERE, "gdb", "ai.py")).read()
    m = _re.search(r"BND = \((.*?)\n    \)", src, _re.S)
    return set(int(x, 16) for x in _re.findall(r"0x[0-9A-F]{8}", m.group(1)))


def run_resume(paths, rows=None, controls=False, code=None, machine_cls=Machine):
    import ai
    code = code or Code()
    decs = []
    for p in paths:
        r = ai.parse(p)
        for d in r["dec"]:
            if rows is None or d["aid"]["ai"] in rows:
                decs.append(d)
    runs = [("resume", False, 0)]
    if controls:
        runs += [("invert", True, 0), ("seed", False, 1)]
    out, results = [], {}
    for name, inv, seedshift in runs:
        m = machine_cls(code, bnd_set(), invert=inv)
        per = {}
        for d in decs:
            if seedshift:
                d = dict(d, aid=dict(d["aid"], s="%08x:%08x" % ai.step(ai.seedval(d["aid"]["s"]))))
            r = check_decision(m, d)
            e = per.setdefault((d["aid"]["ai"], d["aid"]["th"]), {"n": 0, "ok": 0, "mis": 0, "stop": {}, "matched": 0,
                                                                     "past": 0, "amb": 0, "steps": 0, "end": 0,
                                                                     "seqs": {}, "name": ""})
            e["n"] += 1
            e["matched"] += r.matched
            e["past"] += max(0, r.matched - 1)
            e["amb"] += sum(1 for k in r.offers[1:] if k > 1)
            e["steps"] += max(0, len(r.offers) - 1)
            e["end"] += 1 if r.end else 0
            if r.status == "ok":
                e["ok"] += 1
            elif r.status == "mismatch":
                e["mis"] += 1
                e.setdefault("ex", []).append((os.path.basename(d["log"]), d["aid"]["n"], r.why))
            else:
                key = r.why.split(":")[0] if r.why.startswith("boundary") else r.why
                key = re.sub(r"boundary \d+", "boundary k", key)
                key = re.sub(r"[0-9a-f]{8}", "ADDR", key)
                e["stop"][key] = e["stop"].get(key, 0) + 1
            seq = tuple((b["fn"], b["ra"]) for b in d["aib"][:4])
            e["seqs"][seq] = e["seqs"].get(seq, 0) + 1
        results[name] = per
    return decs, results


def report(decs, results):
    L = []
    per = results["resume"]
    L.append("RESUME decisions=%d" % len(decs))
    tot = {"n": 0, "ok": 0, "mis": 0, "matched": 0, "past": 0}
    for key in sorted(per, key=lambda k: (k[0] is None, k[0] or 0, k[1] or 0)):
        e = per[key]
        for k in tot:
            tot[k] += e[k]
        stops = sum(e["stop"].values())
        L.append("RROW %s th=%08x decisions=%d resumed_ok=%d mismatches=%d stopped=%d boundaries_matched=%d past_first=%d "
                 "ambiguous_steps=%d/%d distinct_logged_prefixes4=%d" % (
                     key[0], key[1] or 0, e["n"], e["ok"], e["mis"], stops, e["matched"], e["past"], e["amb"], e["steps"],
                     len(e["seqs"])))
        for why, n in sorted(e["stop"].items(), key=lambda kv: -kv[1])[:4]:
            L.append("RSTOP %s th=%08x %d x %s" % (key[0], key[1] or 0, n, why))
        for ex in e.get("ex", [])[:3]:
            L.append("RMISMATCH %s n=%d row=%s %s" % (ex[0], ex[1], key[0], ex[2]))
    L.append("RTOTAL decisions=%d resumed_ok=%d mismatches=%d boundaries_matched=%d past_first=%d" % (
        tot["n"], tot["ok"], tot["mis"], tot["matched"], tot["past"]))
    for name in ("invert", "seed"):
        if name in results:
            c = results[name]
            n = sum(e["n"] for e in c.values())
            f = sum(e["mis"] for e in c.values())
            ok = sum(e["ok"] for e in c.values())
            L.append("RCONTROL %s decisions=%d mismatches=%d still_ok=%d rows_not_separated=%s" % (
                name, n, f, ok, ",".join(str(k[0]) for k in sorted(c, key=lambda k: k[0] or 0)
                                         if c[k]["mis"] == 0 and c[k]["matched"] > 0)))
    return "\n".join(L) + "\n"


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    paths, rows, out, controls = [], None, None, False
    a, k = argv[1:], 0
    while k < len(a):
        if a[k] == "--rows":
            rows = set(int(x) for x in a[k + 1].split(","))
            k += 2
        elif a[k] == "--out":
            out = a[k + 1]
            k += 2
        elif a[k] == "--controls":
            controls = True
            k += 1
        else:
            paths.append(a[k])
            k += 1
    decs, results = run_resume(paths, rows, controls)
    text = report(decs, results)
    if out:
        open(out, "w").write(text)
    print(text, end="")
    bad = sum(e["mis"] for e in results["resume"].values())
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

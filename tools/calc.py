#!/usr/bin/env python3
"""The calc formula compiler and evaluator (plan 0035 Phase 1, docs/findings/data/0005-calc.md).

    python3 -I tools/calc.py compile <excel-dir> [--show N] [--list]
    python3 -I tools/calc.py text <excel-dir> <context> <formula>
    python3 -I tools/calc.py eval <excel-dir> <context> <formula|hex:BYTES|offset> [--skill S|--missile M --lvl L] [name=value ...]
    python3 -I tools/calc.py dis <excel-dir> <context> <hex:BYTES|offset>

<context> is skills (skills and skilldesc formulas), missiles or items: it chooses the function-name list and the
identifier lookup the game passes to the compiler (the callbacks of 0x00611BD0/0x00611C70, 0x006619A0, 0x00631530).

compile  recompiles every formula cell of skills.txt, skilldesc.txt, missiles.txt and misc/weapons/armor.txt with a
         model of fn:CALC_Compile@0x006C1AE0 and checks it against the stock files: the s32 offset each record
         holds (from the column's descriptor offset), the bytes at that offset in the *code.bin pool, and the pool
         itself rebuilt by appending every compiled cell in record order (fn:sub_006118B0_CalcPoolAppend@0x006118B0).
         The last line is `SURVEY calc cells= blank= mismatches= pool_bytes= pool_mismatch= ...`. Exit 0 only with
         no mismatch.
text     compiles one formula and prints its bytes and the disassembly.
eval     compiles (or takes the bytes after hex:) and evaluates with the model of fn:CALC_Eval@0x006C0BC0. Variables
         are given as code=value (lvl=5, par1=10); a function call as fn(a,b)=value (skill(54,40)=3); min and max
         are computed (they are pure); an unset variable or call is an error. Values are int32.
dis      disassembles bytes, or the expression at an offset of the context's pool (skills -> skillscode.bin).

Stdlib only. Read-only.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402

MAXOUT = 0x400      # the cell callbacks' output buffer (0x00611BD0: local 1024 bytes, limit 0x400)
STACK = 0x40        # operator stack (compiler) and value stack (evaluator) depth

# Precedence table at 0x006FC874, indexed by opcode 0x00..0x16.
PREC = [0x17, 0x01, 0x02, 0x03, 0x09, 0x09, 0x09, 0x09, 0x09, 0x09, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F, 0x0F,
        0x11, 0x11, 0x13, 0x13, 0x14, 0x15, 0x16]
# Operand count by opcode (0x006C1820, table at 0x006C1880): op 1 asks the context, ops 0x0A-0x14 take 2,
# 0x15 takes 1, 0x16 takes 3, anything else 0.
ARITY = {**{op: 2 for op in range(0x0A, 0x15)}, 0x15: 1, 0x16: 3}

OPNAME = {0x00: "end", 0x01: "call", 0x02: "(", 0x04: "var8", 0x05: "var16", 0x06: "var32", 0x07: "const8",
          0x08: "const16", 0x09: "const32", 0x0A: "<", 0x0B: ">", 0x0C: "<=", 0x0D: ">=", 0x0E: "==", 0x0F: "!=",
          0x10: "+", 0x11: "-", 0x12: "*", 0x13: "/", 0x14: "^", 0x15: "neg", 0x16: "?:"}

# Formula columns per table, in descriptor order: (column, field offset, pool). From the descriptors the
# loaders build (skills/skilldesc 0x00613F80, missiles 0x00661B20, items ITEMS_LoadItemTables 0x006315D0),
# every entry of type 0x19 whose callback is one of the four calc cell callbacks.
COLUMNS = {
    "missiles": [("SrvCalc1", 0x80), ("CltCalc1", 0x84), ("SHitCalc1", 0x88), ("CHitCalc1", 0x8C),
                 ("DmgCalc1", 0x90), ("DmgSymPerCalc", 0xE0), ("EDmgSymPerCalc", 0x118)],
    "skills": [("prgcalc1", 0x38), ("prgcalc2", 0x3C), ("prgcalc3", 0x40), ("auralencalc", 0x60),
               ("aurarangecalc", 0x64)] + [("aurastatcalc%d" % k, 0x64 + 4 * k) for k in range(1, 7)]
              + [("passivecalc%d" % k, 0xA0 + 4 * k) for k in range(1, 6)] + [("petmax", 0xC0)]
              + [("sumsk%dcalc" % k, 0xCC + 4 * k) for k in range(1, 6)]
              + [("cltcalc1", 0x114), ("cltcalc2", 0x118), ("cltcalc3", 0x11C), ("perdelay", 0x128),
                 ("skpoints", 0x170), ("delay", 0x190), ("calc1", 0x138), ("calc2", 0x13C), ("calc3", 0x140),
                 ("calc4", 0x144), ("ToHitCalc", 0x1A0), ("DmgSymPerCalc", 0x1D8), ("EDmgSymPerCalc", 0x210),
                 ("ELenSymPerCalc", 0x224)],
    "skilldesc": [("ddam calc1", 0x18), ("ddam calc2", 0x1C), ("p1dmmin", 0x24), ("p1dmmax", 0x30),
                  ("p2dmmin", 0x28), ("p2dmmax", 0x34), ("p3dmmin", 0x2C), ("p3dmmax", 0x38)]
                 + [c for k in range(1, 7) for c in (("desccalca%d" % k, 0x94 + 4 * k),
                                                     ("desccalcb%d" % k, 0xD8 + 4 * k))]
                 + [c for k in range(1, 5) for c in (("dsc2calca%d" % k, 0xAC + 4 * k),
                                                     ("dsc2calcb%d" % k, 0xF0 + 4 * k))]
                 + [c for k in range(1, 8) for c in (("dsc3calca%d" % k, 0xBC + 4 * k),
                                                     ("dsc3calcb%d" % k, 0x100 + 4 * k))],
    "items": [("len", 0xB0), ("calc1", 0xA4), ("calc2", 0xA8), ("calc3", 0xAC), ("spelldesccalc", 0xB8)],
}
# table -> (txt tables in compile order, record size, pool file, context)
TABLES = [
    ("missiles", ["missiles"], 420, "misscode", "missiles"),
    ("skills", ["skills"], 0x23C, "skillscode", "skills"),
    ("skilldesc", ["skilldesc"], 288, "skilldesccode", "skills"),
    ("items", ["weapons", "armor", "misc"], 424, "itemscode", "items"),
]


def s32(v):
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


# ---------------------------------------------------------------- name tables (compile-time lookups)

class Names:
    """The links the identifier callbacks search: EXCEL_FindName (name, case-insensitive, first row wins) over
    skills/missiles/itemstatcost, EXCEL_FindCode (4-byte code) over the skillcalc/misscalc code lists."""

    def __init__(self, excel_dir):
        self.dir = excel_dir
        self.cache = {}

    def _col(self, table, col):
        h, rows = excel_bin.read_txt(excel_bin.find_file(self.dir, table, ".txt"))
        i = h.index(col)
        return [r[i] for r in rows]

    def names(self, table, col):
        key = ("n", table, col)
        if key not in self.cache:
            out = {}
            for i, v in enumerate(self._col(table, col)):
                out.setdefault(v.lower(), i)
            self.cache[key] = out
        return self.cache[key]

    def codes(self, table):
        key = ("c", table)
        if key not in self.cache:
            out = {}
            for i, v in enumerate(self._col(table, "code")):
                out.setdefault(code4(v), i)
            self.cache[key] = out
        return self.cache[key]

    def find_name(self, table, col, name):
        return self.names(table, col).get(name[:31].lower(), -1)

    def find_code(self, table, name):
        return self.codes(table).get(code4(name), -1)

    def code_names(self, table):
        return self._col(table, "code")


def code4(name):
    """0x00611760: the first four characters, a NUL and everything after it replaced by spaces."""
    out = ""
    for ch in name[:4]:
        out += ch
    return (out + "    ")[:4]


# ---------------------------------------------------------------- contexts (the compiler callbacks)

class Context:
    """fn_lookup: name -> index or -1 (case-insensitive _strnicmp(name, fn, 0x20) chain);
    fn_arity: index -> operand count (None: the compiler's default 2);
    ident: (name, prev_op, prev_arg) -> (value, flag) — flag 1 makes a constant, 0 a variable."""
    functions = []
    arity3 = ()
    has_arity = True

    def __init__(self, names):
        self.n = names

    def fn_lookup(self, name):
        for i, f in enumerate(self.functions):
            if name.lower() == f:
                return i
        return -1

    def fn_arity(self, idx):
        return 3 if idx in self.arity3 else 2


class SkillsContext(Context):
    """Skills and skilldesc: fn 0x00611930, arity 0x006119E0, ident 0x006119F0."""
    name = "skills"
    functions = ["min", "max", "rand", "skill", "miss", "stat", "sklvl"]
    arity3 = (6,)
    pool = "skillscode"
    varlist = "skillcalc"

    def ident(self, name, prev_op, prev_arg):
        n = self.n
        if prev_op == 1 and 3 <= prev_arg <= 6:
            if prev_arg in (3, 6):
                r = n.find_name("skills", "skill", name)
                if r >= 0:
                    return r, 1
                return n.find_code("skillcalc", name), 0
            if prev_arg == 4:
                r = n.find_name("missiles", "Missile", name)
                if r >= 0:
                    return r, 1
                return n.find_code("misscalc", name), 0
            r = n.find_name("itemstatcost", "Stat", name)
            if r >= 0:
                return r, 1
            if name.lower() == "base":
                return 1, 0
            if name.lower() == "mod":
                return 2, 0
            return 0, 0              # "accr" is compared, but the result is not used
        return n.find_code("skillcalc", name), 0


class MissilesContext(Context):
    """Missiles: fn 0x00661800, no arity callback (2), ident 0x00661880."""
    name = "missiles"
    functions = ["min", "max", "rand", "skill", "miss"]
    has_arity = False
    pool = "misscode"
    varlist = "misscalc"

    def fn_arity(self, idx):
        return 2

    def ident(self, name, prev_op, prev_arg):
        n = self.n
        if prev_op == 1 and prev_arg == 3:
            r = n.find_name("skills", "skill", name)      # the 2-byte skills code list (DataTables+0x70)
            if r >= 0:
                return r, 1
            return n.find_code("skillcalc", name), 0
        if prev_op == 1 and prev_arg == 4:
            r = n.find_name("missiles", "Missile", name)
            if r >= 0:
                return r, 1
            return n.find_code("misscalc", name), 0
        return n.find_code("misscalc", name), 0


class ItemsContext(Context):
    """Items (weapons/armor/misc): fn 0x00631430, arity 0x00631490 (always 2), ident 0x006314A0."""
    name = "items"
    functions = ["min", "max", "rand", "stat"]
    pool = "itemscode"
    varlist = None

    def fn_arity(self, idx):
        return 2

    def ident(self, name, prev_op, prev_arg):
        if prev_op == 1 and prev_arg == 3:
            r = self.n.find_name("itemstatcost", "Stat", name)
            if r >= 0:
                return r, 1
            if name.lower() == "base":
                return 1, 0
            if name.lower() == "mod":
                return 2, 0
        return 0, 0


CONTEXTS = {"skills": SkillsContext, "missiles": MissilesContext, "items": ItemsContext}


# ---------------------------------------------------------------- tokenizer (0x006C11C0)

T_LP, T_RP, T_COMMA, T_PLUS, T_MINUS, T_MUL, T_DIV, T_QUEST, T_COLON, T_POW = range(10)
T_LE, T_LT, T_GT, T_GE, T_EQ, T_NE = 10, 11, 12, 13, 14, 15
T_NUM, T_VAR, T_FN = 0x10, 0x11, 0x12
SINGLE = {"(": T_LP, ")": T_RP, ",": T_COMMA, "+": T_PLUS, "-": T_MINUS, "*": T_MUL, "/": T_DIV, "?": T_QUEST,
          ":": T_COLON, "^": T_POW}


def _isspace(c):
    return c in " \t\n\v\f\r"


def _isdigit(c):
    return "0" <= c <= "9"


def _isalpha(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z")


def _isalnum(c):
    return _isalpha(c) or _isdigit(c)


def next_token(s, p, ctx, st):
    """-> (new position, token, value), or (None, None, None) at the end (NUL or an unknown character).
    s is NUL-terminated. st is the compiler state (the identifier callback sees the operator-stack top)."""
    while s[p] != "\0" and (_isspace(s[p]) or s[p] == '"'):
        p += 1
    c = s[p]
    if _isdigit(c):
        v = ord(c) - 0x30
        while _isdigit(s[p + 1]):
            v = s32(v * 10 + ord(s[p + 1]) - 0x30)
            p += 1
        return p + 1, T_NUM, v
    if c == "'":
        name = s[p + 1]
        p += 2
        while s[p] != "\0":
            if s[p] == "'":
                p += 1
                break
            name += s[p]
            p += 1
        name = name.split("\0", 1)[0][:255]
        r, flag = ctx.ident(name, *st.top())
        if r >= 0:
            return p, (T_NUM if flag else T_VAR), r
        return p, T_NUM, 0
    if _isalpha(c):
        name = c
        p += 1
        while _isalnum(s[p]):
            name += s[p]
            p += 1
        name = name[:255]
        while s[p] != "\0" and _isspace(s[p]):
            p += 1
        if s[p] == "(":
            r = ctx.fn_lookup(name)
            if r >= 0:
                return p + 1, T_FN, r
        r, flag = ctx.ident(name, *st.top())
        if r >= 0:
            return p, (T_NUM if flag else T_VAR), r
        return p, T_NUM, 0
    if c in SINGLE:
        return p + 1, SINGLE[c], 0
    if c == "<":
        return (p + 2, T_LE, 0) if s[p + 1] == "=" else (p + 1, T_LT, 0)
    if c == ">":
        return (p + 2, T_GE, 0) if s[p + 1] == "=" else (p + 1, T_GT, 0)
    if c == "!" and s[p + 1] == "=":
        return p + 2, T_NE, 0
    if c == "=" and s[p + 1] == "=":
        return p + 2, T_EQ, 0
    if c == ".":
        name = s[p + 1]
        p += 2
        while _isalnum(s[p]):
            name += s[p]
            p += 1
        name = name.split("\0", 1)[0][:255]
        r, _flag = ctx.ident(name, *st.top())
        if r >= 0:
            return p, T_NUM, r
    return None, None, None


# ---------------------------------------------------------------- compiler (0x006C1AE0)

class CompileError(Exception):
    pass


class State:
    """The compiler state block (ebp-0x14C): operator bytes +0x000, their arguments +0x040, count +0x140,
    value depth +0x144."""

    def __init__(self):
        self.ops = []
        self.args = []
        self.depth = 0

    def top(self):
        # with an empty stack the callback reads the byte before the block: the token byte, zeroed before
        # each tokenizer call
        if not self.ops:
            return 0, 0
        return self.ops[-1], self.args[-1]


def _arity(op, arg, ctx_arity):
    if op == 1:
        return ctx_arity(arg) if ctx_arity else 2
    return ARITY.get(op, 0)


def _emit_const(out, v, depth_state, opbase=7):
    """0x006C19C0 (constants 07/08/09) and 0x006C1A50 (variables 04/05/06)."""
    v = s32(v)
    if -0x80 <= v < 0x80:
        if len(out) >= MAXOUT:
            raise CompileError("full")
        out += bytes([opbase, v & 0xFF])
    elif -0x8000 <= v < 0x8000:
        if len(out) + 3 >= MAXOUT:
            raise CompileError("full")
        out += bytes([opbase + 1]) + struct.pack("<h", v)
    else:
        if len(out) + 5 >= MAXOUT:
            raise CompileError("full")
        out += bytes([opbase + 2]) + struct.pack("<i", v)
    depth_state.depth += 1


def _operator(out, st, op):
    """0x006C18A0: pop and emit while the top binds at least as tightly, then push op (not 3 or 0x17);
    op 0 ends the expression with a 00 byte."""
    while st.ops:
        top = st.ops[-1]
        if top == 1 or op == 1 or top >= 0x17 or PREC[top] < op:
            break
        n = _arity(top, 0, None)
        if st.depth < n:
            raise CompileError("stack underflow at %s" % OPNAME.get(top, top))
        if len(out) >= MAXOUT:
            raise CompileError("full")
        out.append(top)
        st.ops.pop()
        st.args.pop()
        st.depth += 1 - n
    if op in (0x17, 3):
        return
    if op == 0:
        if not out:
            raise CompileError("empty")
        if len(out) >= MAXOUT:
            raise CompileError("full")
        out.append(0)
        return
    if len(st.ops) >= STACK:
        raise CompileError("operator stack full")
    st.ops.append(op)
    st.args.append(0)


OP_OF_TOKEN = {T_PLUS: 0x10, T_MUL: 0x12, T_DIV: 0x13, T_POW: 0x14, T_LE: 0x0C, T_LT: 0x0A, T_GT: 0x0B,
               T_GE: 0x0D, T_EQ: 0x0E, T_NE: 0x0F}


def compile_expr(text, ctx):
    """Bytes the game stores for one cell, or None where the cell gets -1 (compile failure or empty)."""
    s = text + "\0\0\0"
    st = State()
    out = bytearray()
    operand = False     # [ebp-0x154]: the last token was an operand (number, variable, function name)
    has_var = False     # [ebp-0x15C]: a variable or a function call occurred; else the result is folded
    p = 0
    try:
        while True:
            p, tok, val = next_token(s, p, ctx, st)
            if p is None:
                break
            if tok == T_LP:
                if len(st.ops) >= STACK:
                    raise CompileError("operator stack full")
                st.ops.append(2)
                st.args.append(0)
            elif tok == T_RP:
                if not st.ops:
                    raise CompileError("unbalanced )")
                while True:
                    top = st.ops[-1]
                    if top == 2:
                        break
                    n = _arity(top, st.args[-1], ctx.fn_arity if ctx.has_arity else None)
                    if st.depth < n:
                        raise CompileError("stack underflow at %s" % OPNAME.get(top, top))
                    if len(out) >= MAXOUT:
                        raise CompileError("full")
                    st.depth += 1 - n
                    out.append(top)
                    if top == 1:
                        if len(out) >= MAXOUT:
                            raise CompileError("full")
                        out.append(st.args[-1] & 0xFF)
                        break
                    st.ops.pop()
                    st.args.pop()
                    if not st.ops:
                        raise CompileError("unbalanced )")
                if not st.ops or st.ops[-1] not in (1, 2):
                    raise CompileError("unbalanced )")
                st.ops.pop()
                st.args.pop()
            elif tok == T_COMMA:
                _operator(out, st, 3)
            elif tok == T_MINUS:
                _operator(out, st, 0x11 if operand else 0x15)
                operand = False
            elif tok in OP_OF_TOKEN:
                _operator(out, st, OP_OF_TOKEN[tok])
                operand = False
            elif tok == T_QUEST:
                _operator(out, st, 0x16)
            elif tok == T_COLON:
                _operator(out, st, 0x17)
            elif tok == T_NUM:
                _emit_const(out, val, st, 7)
                operand = True
            elif tok == T_VAR:
                _emit_const(out, val, st, 4)
                operand = True
                has_var = True
            elif tok == T_FN:
                operand = True
                has_var = True
                if len(st.ops) >= STACK:
                    raise CompileError("operator stack full")
                st.ops.append(1)
                st.args.append(val)
        _operator(out, st, 0)
    except CompileError:
        return None
    if not has_var:
        v = evaluate(bytes(out), None)
        out = bytearray()
        st2 = State()
        try:
            _emit_const(out, v, st2, 7)
            _operator(out, st2, 0)
        except CompileError:
            return None
    return bytes(out)


# ---------------------------------------------------------------- evaluator (0x006C0BC0)

class EvalError(Exception):
    pass


def evaluate(code, env, length=None):
    """Value of the expression at code[0:]. env: None (the compile-time fold: no variable reader, no
    functions) or an object with var(index) and call(fn, a, b, c, argc) and nfuncs/argc(fn)."""
    if length is None:
        length = len(code)
    if length <= 0:
        return 0
    st = []

    def pop():
        return st.pop() if st else 0

    def push(v):
        if len(st) < STACK:
            st.append(s32(v))

    p = 0
    while p < length:
        op = code[p]
        p += 1
        if op in (4, 5, 6):
            if env is None:
                return 0
            n = {4: 1, 5: 2, 6: 4}[op]
            if p >= length:
                return 0
            idx = code[p] if op == 4 else struct.unpack_from({5: "<h", 6: "<i"}[op], code, p)[0]
            push(env.var(idx))
            p += n
        elif op in (7, 8, 9):
            if p >= length:
                return 0
            n = {7: 1, 8: 2, 9: 4}[op]
            push(struct.unpack_from({7: "<b", 8: "<h", 9: "<i"}[op], code, p)[0])
            p += n
        elif op == 1:
            fn = code[p]
            p += 1
            if env is None or fn >= env.nfuncs:
                push(0)
                continue
            argc = env.argc(fn)
            if argc == 3:
                c = pop()
                b = pop()
                a = pop()
            elif argc == 2:
                c = 0
                b = pop()
                a = pop()
            elif argc == 1:
                a, b, c = pop(), 0, 0
            elif argc == 0:
                a = b = c = 0
            else:
                push(0)
                continue
            push(env.call(fn, a, b, c, argc))
        elif 0x0A <= op <= 0x14:
            a = pop()               # the top: right operand
            b = pop()
            if op == 0x0A:
                r = int(b < a)
            elif op == 0x0B:
                r = int(b > a)
            elif op == 0x0C:
                r = int(b <= a)
            elif op == 0x0D:
                r = int(b >= a)
            elif op == 0x0E:
                r = int(b == a)
            elif op == 0x0F:
                r = int(b != a)
            elif op == 0x10:
                r = b + a
            elif op == 0x11:
                r = b - a
            elif op == 0x12:
                r = b * a
            elif op == 0x13:
                if a == 0:
                    r = 0
                else:       # idiv: truncation toward zero
                    q = abs(b) // abs(a)
                    r = q if (b < 0) == (a < 0) else -q
            else:
                if a <= 0:
                    r = 1
                else:
                    r = b
                    for _ in range(a - 1):
                        r = s32(r * b)
            push(r)
        elif op == 0x15:
            push(-pop())
        elif op == 0x16:
            a = pop()
            b = pop()
            cond = pop() if st else 0
            push(b if cond != 0 else a)
        else:       # 0x00, 0x02, 0x03 and anything above 0x16 end the expression
            return st.pop() if st else 0
    return 0


# ---------------------------------------------------------------- disassembly

def disasm(code, ctx=None, names=None):
    out = []
    p = 0
    while p < len(code):
        op = code[p]
        p += 1
        if op in (4, 5, 6, 7, 8, 9):
            n = {4: 1, 5: 2, 6: 4, 7: 1, 8: 2, 9: 4}[op]
            fmt = {4: "<B", 5: "<h", 6: "<i", 7: "<b", 8: "<h", 9: "<i"}[op]
            v = struct.unpack_from(fmt, code, p)[0]
            p += n
            if op <= 6 and ctx is not None and ctx.varlist and names is not None:
                vl = names.code_names(ctx.varlist)
                out.append("var %s" % (vl[v] if 0 <= v < len(vl) else v))
            elif op <= 6:
                out.append("var %d" % v)
            else:
                out.append(str(v))
        elif op == 1:
            fn = code[p]
            p += 1
            fname = ctx.functions[fn] if ctx is not None and fn < len(ctx.functions) else str(fn)
            out.append("call %s" % fname)
        else:
            out.append(OPNAME.get(op, "op%02X" % op))
            if op == 0:
                break
    return " ".join(out)


# ---------------------------------------------------------------- compile check over the stock files

def cmd_compile(excel_dir, show=5, list_all=False):
    names = Names(excel_dir)
    totals = dict(cells=0, blank=0, compiled=0, failed=0, mismatches=0, pool_bytes=0, pool_mismatch=0)
    per_pool = {}
    shown = 0
    opcodes = set()
    for table, txts, size, pool, cname in TABLES:
        ctx = CONTEXTS[cname](names)
        with open(excel_bin.find_file(excel_dir, pool, ".bin"), "rb") as fh:
            stock = fh.read()
        rebuilt = bytearray()
        cols = COLUMNS[table]
        t_cells = t_bad = 0
        for txt in txts:
            header, rows = excel_bin.read_txt(excel_bin.find_file(excel_dir, txt, ".txt"))
            recs, rsize = excel_bin.read_bin(excel_bin.find_file(excel_dir, txt, ".bin"))
            assert rsize == size and len(recs) == len(rows), (txt, rsize, len(recs), len(rows))
            lower = [h.lower() for h in header]
            # EXCEL_ParseTxt walks a row's cells in .txt column order, then the descriptor entries the .txt lacks in
            # descriptor order (EXCEL_MapColumns appends them): data/0005 § 9.
            present = sorted((c for c in cols if c[0].lower() in lower), key=lambda c: lower.index(c[0].lower()))
            ordered = present + [c for c in cols if c[0].lower() not in lower]
            for ri, (row, rec) in enumerate(zip(rows, recs)):
                for col, off in ordered:
                    stored = struct.unpack_from("<i", rec, off)[0]
                    ci = lower.index(col.lower()) if col.lower() in lower else None
                    cell = row[ci] if ci is not None else None
                    totals["cells"] += 1
                    t_cells += 1
                    code = compile_expr(cell, ctx) if cell else None
                    if cell is None or cell == "":
                        totals["blank"] += 1
                        want = -1
                    elif code is None:
                        totals["failed"] += 1
                        want = -1
                    else:
                        totals["compiled"] += 1
                        want = len(rebuilt)
                        rebuilt += code
                        p = 0
                        while p < len(code):
                            op = code[p]
                            opcodes.add(op)
                            p += 1 + {1: 1, 4: 1, 5: 2, 6: 4, 7: 1, 8: 2, 9: 4}.get(op, 0)
                    ok = stored == want
                    if ok and code is not None:
                        ok = stock[stored:stored + len(code)] == code
                    if not ok:
                        totals["mismatches"] += 1
                        t_bad += 1
                        if list_all or shown < show:
                            shown += 1
                            got = stock[stored:stored + len(code or b"") + 4] if stored >= 0 else b""
                            print("MISMATCH %s row %d %s: %r -> %s (want off %d), stock off %d %s" % (
                                txt, ri, col, cell, (code or b"").hex(), want, stored, got.hex()))
        pm = 0 if bytes(rebuilt) == stock else 1
        totals["pool_bytes"] += len(stock)
        totals["pool_mismatch"] += pm
        per_pool[pool] = (t_cells, t_bad, len(rebuilt), len(stock), pm)
        print("%-14s %-9s cells=%d mismatches=%d rebuilt=%d stock=%d pool %s" % (
            pool, table, t_cells, t_bad, len(rebuilt), len(stock), "identical" if not pm else "DIFFERS"))
    print("opcodes seen: %s" % " ".join("%02X" % o for o in sorted(opcodes)))
    print("SURVEY calc " + " ".join("%s=%d" % kv for kv in totals.items()) + " opcodes=%d" % len(opcodes))
    return 0 if totals["mismatches"] == 0 and totals["pool_mismatch"] == 0 else 1


# ---------------------------------------------------------------- eval / text / dis

def _dimret(lvl, a, b):
    """0x00645B20: a + (lvl*110/(lvl+6)) * (b-a) / 100, capped at b (C division, truncation toward zero)."""
    def cdiv(x, y):
        q = abs(x) // abs(y)
        return q if (x < 0) == (y < 0) else -q
    r = cdiv(s32(cdiv(s32(lvl * 110), lvl + 6) * (b - a)), 100) + a
    return b if r > b else r


class Env:
    """Evaluation inputs. With --skill/--lvl (skills context) or --missile/--lvl (missiles context) the variables
    that only read the table row and the level are computed (SKILLS_CalcVar 0x00646460 cases 0-16, 21, 22, 42,
    54-72 and toht without ToHitCalc; MISS_CalcVar 0x0064B340 cases 0-18, 28-42); everything that reads the unit
    must be given."""

    def __init__(self, ctx, names, assigns, excel_dir=None, row=None, lvl=None):
        self.ctx = ctx
        self.vars = {}
        self.calls = {}
        self.row = row
        self.lvl = lvl
        self.rec = None
        self.pool = None
        if row is not None and ctx.name in ("skills", "missiles"):
            table, size = ("skills", 0x23C) if ctx.name == "skills" else ("missiles", 420)
            recs, rsize = excel_bin.read_bin(excel_bin.find_file(excel_dir, table, ".bin"))
            assert rsize == size
            self.rec = recs[row]
            with open(excel_bin.find_file(excel_dir, "skillscode", ".bin"), "rb") as fh:
                self.pool = fh.read()
        vl = names.code_names(ctx.varlist) if ctx.varlist else []
        self.varnames = vl
        for k, v in assigns.items():
            if "(" in k:
                fn, args = k.split("(", 1)
                args = tuple(int(a) for a in args.rstrip(")").split(",") if a.strip())
                self.calls[(fn.lower(), args)] = int(v)
            elif k.lstrip("-").isdigit():
                self.vars[int(k)] = int(v)
            else:
                self.vars[vl.index(k) if k in vl else int(k)] = int(v)
        self.nfuncs = len(ctx.functions)

    def argc(self, fn):
        return self.ctx.fn_arity(fn)

    def var(self, idx):
        if idx in self.vars:
            return self.vars[idx]
        v = None
        if self.rec is not None:
            v = (self._skill_var if self.ctx.name == "skills" else self._miss_var)(idx)
        if v is None:
            name = self.varnames[idx] if 0 <= idx < len(self.varnames) else idx
            raise EvalError("variable %s not given" % name)
        return s32(v)

    def _i(self, off, fmt="<i"):
        return struct.unpack_from(fmt, self.rec, off)[0]

    def _skill_var(self, idx):
        lvl = self.lvl
        par = [self._i(0x148 + 4 * k) for k in range(8)]
        if idx <= 7:
            a, b = par[idx & 6], par[(idx & 6) + 1]
            if idx & 1:
                if idx != 7 and lvl < 1:       # dm78 (0x0064651F) calls 0x00645B20 without the level test
                    return 0
                return _dimret(lvl, a, b)
            return 0 if lvl < 1 else a + (lvl - 1) * b
        if idx <= 15:
            return par[idx - 8]
        if idx == 16:
            return lvl
        if idx == 20:
            if lvl < 1:
                return 0
            if self._i(0x1A0) == -1:
                return (lvl - 1) * self._i(0x19C) + self._i(0x198)
            return self._recurse(self._i(0x1A0, "<I"))
        if idx in (21, 22, 42):
            if lvl < 1:
                return 0
            m = self._i(0x18C, "<h") * (lvl - 1) + self._i(0x18A, "<h")
            if idx == 22:
                q = abs(m * 25) // 2
                m = q if m >= 0 else -q
            m = s32(m << (self._i(0x188, "<B") & 31))
            return m if idx == 42 else m >> 8
        fields = {54: 0x60, 55: 0x138, 56: 0x13C, 57: 0x140, 58: 0x144, 59: 0x64, 71: 0xC0, 72: 0x170}
        fields.update({60 + k: 0x68 + 4 * k for k in range(6)})
        fields.update({66 + k: 0xA4 + 4 * k for k in range(5)})
        if idx in fields:
            return self._recurse(self._i(fields[idx], "<I"))
        return None

    def _miss_var(self, idx):
        lvl = self.lvl
        offs = [0x38, 0x3C, 0x40, 0x44, 0x48, 0x58, 0x5C, 0x60, 0x64, 0x68, 0x4C, 0x50, 0x54, 0x6C, 0x70, 0x74,
                0x78, 0x7C]
        if idx < 18:
            return self._i(offs[idx])
        if idx == 18:
            return lvl
        if idx == 28:
            return self._i(0x98, "<h") * lvl + self._i(0x96, "<h")
        if 29 <= idx <= 42:
            a_off, b_off = [(0x38, 0x3C), (0x40, 0x44), (0x58, 0x5C), (0x60, 0x64), (0x4C, 0x50), (0x6C, 0x70),
                            (0x78, 0x7C)][(idx - 29) // 2]
            a, b = self._i(a_off), self._i(b_off)
            return (lvl - 1) * b + a if (idx - 29) % 2 == 0 else _dimret(lvl, a, b)
        return None

    def _recurse(self, off):
        """A field holding a skillscode offset is evaluated in the same context (0x006465F0 tail); -1 -> 0."""
        if off >= len(self.pool):
            return 0
        return evaluate(self.pool[off:], self, len(self.pool) - off)

    def call(self, fn, a, b, c, argc):
        name = self.ctx.functions[fn]
        args = (a, b, c)[:argc]
        if (name, args) in self.calls:
            return self.calls[(name, args)]
        if name == "min":
            return a if a < b else b
        if name == "max":
            return a if a > b else b
        raise EvalError("%s%r not given" % (name, args))


def _code_arg(arg, ctx, excel_dir):
    if arg.startswith("hex:"):
        return bytes.fromhex(arg[4:])
    if arg.isdigit():
        with open(excel_bin.find_file(excel_dir, ctx.pool, ".bin"), "rb") as fh:
            data = fh.read()
        off = int(arg)
        end = off
        while end < len(data):
            op = data[end]
            end += 1 + {1: 1, 4: 1, 5: 2, 6: 4, 7: 1, 8: 2, 9: 4}.get(op, 0)
            if op == 0:
                break
        return data[off:end]
    return compile_expr(arg, ctx)


def main(argv):
    if len(argv) < 2 or argv[0] not in ("compile", "text", "eval", "dis"):
        print(__doc__)
        return 2
    cmd, excel_dir = argv[0], argv[1]
    if cmd == "compile":
        show = 5
        if "--show" in argv:
            show = int(argv[argv.index("--show") + 1])
        return cmd_compile(excel_dir, show, "--list" in argv)
    names = Names(excel_dir)
    ctx = CONTEXTS[argv[2]](names)
    code = _code_arg(argv[3], ctx, excel_dir)
    if code is None:
        print("compile failed: the cell would hold -1")
        return 1
    print("bytes: %s" % code.hex(" "))
    print("dis:   %s" % disasm(code, ctx, names))
    if cmd == "eval":
        rest = argv[4:]
        row = lvl = None
        for opt in ("--skill", "--missile"):
            if opt in rest:
                i = rest.index(opt)
                key = rest[i + 1]
                if key.lstrip("-").isdigit():
                    row = int(key)
                elif opt == "--skill":
                    row = names.find_name("skills", "skill", key)
                else:
                    row = names.find_name("missiles", "Missile", key)
                del rest[i:i + 2]
        if "--lvl" in rest:
            i = rest.index("--lvl")
            lvl = int(rest[i + 1])
            del rest[i:i + 2]
        assigns = dict(a.split("=", 1) for a in rest)
        try:
            env = Env(ctx, names, assigns, excel_dir, row, lvl)
            if lvl is not None and ctx.name in ("skills", "missiles"):
                env.vars.setdefault(16 if ctx.name == "skills" else 18, lvl)
            print("value: %d" % evaluate(code, env))
        except EvalError as exc:
            print("error: %s" % exc)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

# gdb Python logger for plan 0035 Phase 2 (the calc evaluator at run time): docs/findings/data/0005-calc.md § 10.
# Sourced by tools/gdb/calc.gdb. One line per event, "TAG {json}". Addresses refer to the pinned game.exe (image base
# 0x400000). Every line carries "th" (the gdb thread number); the evaluator recurses (a variable or a function call
# can evaluate another formula), so the events of one thread nest: CE ... CX brackets one evaluation, CV ... CVR one
# variable read and CF ... CFR one function call, and an inner CE ... CX sits between a CV/CF and its CVR/CFR.
#
#   CE   0x006C0BC0 CALC_Eval entry: code ([esp+4]), len ([esp+8]), varFn ([esp+0xC]), funcs ([esp+0x10]), nFuncs
#        ([esp+0x14]), ctx ([esp+0x18]) and its first four dwords, the return address ([esp]) and the caller's
#        return address ([ebp+4]); the pool the code lies in (DataTables +0x40 skillscode, +0x4C skilldesccode,
#        +0x60 misscode, +0x98 itemscode) and the offset in it; the code bytes walked to their end (at most 256);
#        for a context whose first dword is a unit, that unit's type, class and seed (Unit+0x20)
#   CV   the variable reader calls 0x006C0C28 (04, u8 operand), 0x006C0C5C (05, s16), 0x006C0C8F (06, s32): the index
#        (ECX); CVR at the next instruction: the value (EAX)
#   CF   the function calls 0x006C0D5C (argc 3) and 0x006C0D9B (argc 2, 1, 0): the function index (ESI), its pointer
#        (funcs[ESI].fn), a (ECX), b (EDX), c ([esp]); for rand (0x00643700, 0x00627B70: the unit seed; 0x0064B720:
#        ctx+0x20) the seed it draws on; CFR at the next instruction: the value (EAX) and the seed again. The division
#        case (0x006C0ED1) jumps to 0x006C0D9D to push its quotient, so a CVR/CFR is logged only when ESP matches a
#        pending read or call of the same thread (ESP + 8 for a call: the callee pops c and ctx)
#   CX   the returns 0x006C0BD7 (len <= 0), 0x006C1145 (0), 0x006C1161 (top of the stack): the value (EAX)
#
# CALC_MAX (environment, default 0 = no limit): stop logging after that many CE lines (the breakpoints are disabled).
import json
import os
import struct

import gdb


def _calc_main():
    inf = gdb.selected_inferior()
    DT = 0x0096BC30
    POOLS = (("skillscode", 0x40), ("skilldesccode", 0x4C), ("misscode", 0x60), ("itemscode", 0x98))
    RAND = {0x00643700: "unit", 0x00627B70: "unit", 0x0064B720: "ctx"}
    W = {1: 1, 4: 1, 5: 2, 6: 4, 7: 1, 8: 2, 9: 4}
    cap = int(os.environ.get("CALC_MAX", "0") or 0)
    count = {"ce": 0}
    bps = []

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def sreg(n):
        v = reg(n)
        return v - (1 << 32) if v & 0x80000000 else v

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))

    def sd(p):
        return "%08x:%08x" % struct.unpack("<II", mem(p, 8))

    def walk(code, n):
        n = min(n, 256)
        if n <= 0:
            return ""
        b = mem(code, n)
        p = 0
        while p < n:
            op = b[p]
            p += 1 + W.get(op, 0)
            if op in (0, 2, 3) or op > 0x16:
                break
        return b[:min(p, n)].hex()

    def on_ce():
        if cap and count["ce"] >= cap:
            for bp in bps:
                bp.enabled = False
            gdb.write("CALC cap %d reached, logging off\n" % cap)
            return
        count["ce"] += 1
        esp = reg("esp")
        code, ln, varfn, funcs, nf, ctx = struct.unpack("<IiIIiI", mem(esp + 4, 24))
        d = {"code": code, "len": ln, "var": varfn, "funcs": funcs, "nf": nf, "ctx": ctx, "ra": u32(esp)}
        try:
            d["ra2"] = u32(reg("ebp") + 4)
        except gdb.MemoryError:
            d["ra2"] = None
        pool = off = None
        for name, o in POOLS:
            base, size = struct.unpack("<II", mem(DT + o, 8))
            if base and base <= code < base + size:
                pool, off = name, code - base
                break
        d["pool"], d["off"] = pool, off
        d["bytes"] = walk(code, ln)
        if ctx:
            c = list(struct.unpack("<iiii", mem(ctx, 16)))
            d["c"] = c
            u = c[0] & 0xFFFFFFFF
            if u and varfn != 0x0064B6E0:
                d["u"] = {"type": u32(u), "cls": s32(u + 4), "id": u32(u + 0x0C), "seed": sd(u + 0x20)}
            elif varfn == 0x0064B6E0:
                for key, v in (("u", c[0]), ("owner", c[1])):
                    v &= 0xFFFFFFFF
                    if v:
                        d[key] = {"type": u32(v), "cls": s32(v + 4), "id": u32(v + 0x0C)}
        emit("CE", d)

    def on_cx():
        emit("CX", {"v": sreg("eax")})

    pending = {}   # thread -> [(kind, esp expected after the call returns)]

    def on_cv(kind):
        def f():
            pending.setdefault(thn(), []).append(("v", reg("esp")))
            emit("CV", {"op": kind, "i": sreg("ecx")})
        return f

    def after(kind):
        p = pending.get(thn())
        if p and p[-1] == (kind, reg("esp")):
            p.pop()
            return True
        return False

    def on_cvr():
        if after("v"):
            emit("CVR", {"v": sreg("eax")})

    rand_seed = {}

    def on_cf(argc3):
        def f():
            esp, ebp = reg("esp"), reg("ebp")
            fi = reg("esi")
            funcs = u32(ebp + 0x14)
            fn = u32(funcs + 8 * fi)
            d = {"f": fi, "fn": fn, "argc": u32(funcs + 8 * fi + 4), "a": sreg("ecx"), "b": sreg("edx"),
                 "c": s32(esp), "site": 3 if argc3 else 2}
            if fn in RAND:
                ctx = u32(esp + 4)
                sp = None
                if ctx:
                    sp = (u32(ctx) + 0x20) if RAND[fn] == "unit" else ctx + 0x20
                rand_seed[thn()] = sp
                d["seedp"] = sp
                d["seed"] = sd(sp) if sp and RAND[fn] == "unit" else None
            pending.setdefault(thn(), []).append(("f", esp + 8))
            emit("CF", d)
        return f

    def on_cfr():
        # 0x006C0D9D is also the push tail the division case jumps to (0x006C0ED1): only the return of a pending
        # call (the callee pops its two stack arguments, so ESP is 8 above its value at the call) is a CFR
        if not after("f"):
            return
        d = {"v": sreg("eax")}
        sp = rand_seed.pop(thn(), None)
        if sp:
            try:
                d["seed"] = sd(sp)
            except gdb.MemoryError:
                pass
        emit("CFR", d)

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            bps.append(self)

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR calc %r\n" % (e,))
            return False

    Bp(0x006C0BC0, on_ce)
    for a in (0x006C0BD7, 0x006C1145, 0x006C1161):
        Bp(a, on_cx)
    for a, k in ((0x006C0C28, 4), (0x006C0C5C, 5), (0x006C0C8F, 6)):
        Bp(a, on_cv(k))
        Bp(a + 2, on_cvr)
    Bp(0x006C0D5C, on_cf(True))
    Bp(0x006C0D5E, on_cfr)
    Bp(0x006C0D9B, on_cf(False))
    Bp(0x006C0D9D, on_cfr)
    gdb.write("CALC logger armed%s\n" % (" (cap %d)" % cap if cap else ""))


_calc_main()

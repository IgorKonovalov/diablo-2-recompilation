"""Plan 0066 Phase 1, batch S2c: exhaustive static scans with a second tool for the class-c rows of skills/README,
skills/catalogue, skills/dispatch and skills/missiles. No game, no Ghidra.

Usage:
  python3 -I tools/skills_s2c.py <section> [<section> ...]
  python3 -I tools/skills_s2c.py all

Tools, as tools/quests_s3c.py (whose helpers this file imports): every reference scan three ways (raw-byte rel32 and
abs32, objdump's linear listing, r2 re-decoding each site); an instruction claimed at a site is decoded by objdump and
by r2 and both must agree (`site()`); call arguments by two walkers (objdump and r2). Table cells are read twice: the
plain .txt reader of quests_s3c (`tab`) and the compiled .bin through tools/excel_bin.py (`binrecs`). A count line
carries `bad=` (an observation against the statement the row tests, or a tool disagreement).

Sections (inventory rows: R = skills-README.md, C = skills-catalogue.md, D = skills-dispatch.md, M = skills-missiles.md):
  tables   D18 D19 D20 M9 M10 M11 M12 M13 C3: the function tables' extents, bounds and readers; the collide types; the
           direction table; the circle tables
  s16      M51 M93 C36: the five signed function-number tests and every Missiles row's function numbers
  entries  C4 C10 C12 C25: the hit and damage entries' `ret N`; the do entries' tails into mdo 1, 3 and 7
  data     M68 M39 M43 M44 C25 D58 D74 D76 D108 C67 C87 C90 C98 C99: full-table checks (Missiles, Skills, States,
           MonStats, ItemStatCost), .txt against .bin
  consts   D21 D22 D23 D24 D187 D68: the delay state 121 and its unit event, state 114, the periodic floor, the charge cap
  calls    D42 D46 D48 D195 D60 C80 D81 D194 D82 D151 D157 D98 C53 M2 M58 R17: callers and their arguments
  bits     D56 D57 D185 D193 C58 C14 D76 D88: the Unit+0xC4 bit-6 stores and clears, the skill-row flag-bit readers,
           the packet +0x65 byte stores, the missile +0x... bit 0 pair
  more     the rest (filled per row)
  totals   plan 0066's class totals over the per-spec inventory files
Stdlib, objdump and r2. Read-only.
"""
import collections
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import quests_s3c as Q  # noqa: E402
import sweep_s4b as S  # noqa: E402
import sweep2_s4cd as T  # noqa: E402

BAD = collections.Counter()
SECTIONS = collections.OrderedDict()


def section(name):
    def deco(f):
        SECTIONS[name] = f
        return f
    return deco


def out(sec, name, **kv):
    bad = kv.pop("bad", 0)
    BAD[sec] += bad
    print("S2c %s %s %s bad=%d" % (sec, name, " ".join("%s=%s" % (k, kv[k]) for k in sorted(kv)), bad))


note = Q.note
nm = Q.nm


def A():
    return S.asm()


# ------------------------------------------------------------------------------------------------ helpers
def dword(va):
    return S.dword(va)


def sdword(va):
    v = S.dword(va)
    return v - (1 << 32) if v & 0x80000000 else v


def norm_ops(s):
    """One spelling for objdump's and r2's operands: lower case, no size words, no spaces, `ds:0x..` as `[0x..]`,
    a whole decimal operand as hex."""
    s = (s or "").lower()
    for w in ("dword ptr ", "byte ptr ", "word ptr ", "dword ", "byte ", "word "):
        s = s.replace(w, "")
    s = s.replace(" ", "")
    s = re.sub(r"ds:(0x[0-9a-f]+)", r"[\1]", s)
    s = s.replace("ds:", "").replace("*1+", "+").replace("*1]", "]")
    s = re.sub(r"([+-])(\d+)\]", lambda m: "%s%s]" % (m.group(1), hex(int(m.group(2)))), s)
    return ",".join(hex(int(t)) if t.isdigit() else t for t in s.split(","))


def site(va):
    """(objdump text, r2 text, agree) for the instruction at va, normalised."""
    o = A().at(va)
    r = Q.r2_many([va])[va]
    ot = "%s %s" % (o[0], norm_ops(o[1])) if o else "?"
    rt = "%s %s" % (r[0], norm_ops(r[1])) if r else "?"
    rt = rt.replace("movsx ", "movsx ").replace("retn", "ret")
    return ot.strip(), rt.strip(), ot.strip() == rt.strip()


def site_line(sec, label, vas, want=None):
    """Decode each va twice; bad when the two disagree or the objdump text does not match `want` (regex list)."""
    bad = 0
    txt = []
    for k, va in enumerate(vas):
        ot, rt, ag = site(va)
        ok = ag
        if want is not None and not re.search(want[k], ot):
            ok = False
        bad += 0 if ok else 1
        txt.append("0x%08X %s%s" % (va, ot, "" if ag else "  [r2: %s]" % rt))
    out(sec, label, sites=len(vas), bad=bad)
    for t in txt:
        note(t)
    return bad


def listing(lo, hi):
    return [(va, mn, ops or "") for va, (mn, ops) in A().range(lo, hi)]


def fn_body(entry):
    import sweep2_s7a as W
    vas, calls, icalls = W.body2(A(), entry)
    return sorted(vas), calls, icalls


def rets(entry):
    """The `ret` operands met in a function's recursive-descent body (objdump)."""
    vas, _, _ = fn_body(entry)
    r = set()
    for va in vas:
        mn, ops = A().ins[va]
        if mn in ("ret", "retn"):
            r.add(T.imm(ops) if ops else 0)
    return r


def calls_to(target):
    raw, od, r2s = Q.refs(target, ("call",))
    return raw, od, r2s


def jmps_to(target):
    raw, od, r2s = Q.refs(target, ("jmp",))
    return raw, od, r2s


def args(site_va, n):
    """(objdump args, r2 args, agree), arg 0 first."""
    return Q.push_args(site_va, n)


def resolve(site_va, v):
    return Q.resolve(site_va, v)


# ------------------------------------------------------------------------------------------------ tables
@section("tables")
def sec_tables():
    sec = "tables"
    # D18: the start table
    bad = site_line(sec, "D18 start-table bound", [0x0056F75D, 0x0056F761, 0x0056F76A],
                    [r"cmp ax,0x5b", r"jge", r"mov eax,\[edx\*4\+0x732140\]"])
    starts = [dword(0x00732140 + 4 * i) for i in range((0x007322B0 - 0x00732140) // 4)]
    nz = [i for i, v in enumerate(starts) if v]
    out(sec, "D18 start-table extent", slots=len(starts), bound=0x5B, nonnull=len(nz), max_nonnull=max(nz),
        slot_0x5b=hex(starts[0x5B]), abs32=len(Q.raw_abs(0x00732140)), bad=int(max(nz) >= 0x5B))
    for s, a in Q.raw_abs(0x00732140):
        note("reader 0x%08X %s: %s" % (a, nm(a), site(a - 3 if s else a)[0]))
    # D19: the do table
    site_line(sec, "D19 do-table bounds", [0x0056F911, 0x0056D7E8, 0x005D542C],
              [r"cmp ax,0xbf", r"cmp ax,0xbf", r"cmp eax,\[0x6e1274\]"])
    dos = [dword(0x007322B0 + 4 * i) for i in range((0x007325B0 - 0x007322B0) // 4)]
    nz = [i for i, v in enumerate(dos) if v]
    out(sec, "D19 do-table extent", slots=len(dos), count_var=hex(dword(0x006E1274)), nonnull=len(nz),
        max_nonnull=max(nz), abs32=len(Q.raw_abs(0x007322B0)), bad=int(max(nz) >= 0xBF or dword(0x006E1274) != 0xBF))
    for s, a in Q.raw_abs(0x007322B0):
        note("reader at 0x%08X %s" % (a, nm(a)))
    # D20: the stat-event table
    site_line(sec, "D20 stat-event bound", [0x0056E746, 0x0056E749, 0x0056E74B],
              [r"cmp eax,0x31", r"ja ", r"mov eax,\[eax\*4\+0x7325b0\]"])
    ev = [dword(0x007325B0 + 4 * i) for i in range(0x32)]
    nz = [i for i, v in enumerate(ev) if v]
    nxt = dword(0x007325B0 + 4 * 0x32)
    out(sec, "D20 stat-event entries", slots=0x32, nonnull=len(nz), ids="%d..%d" % (min(nz), max(nz)),
        contiguous=int(nz == list(range(1, 32))), abs32=len(Q.raw_abs(0x007325B0)), bad=int(nz != list(range(1, 32))))
    note("ids 1..31 -> %s" % " ".join("%d:%s" % (i, nm(ev[i]).split("_", 2)[-1]) for i in nz))
    note("the dword after slot 0x31: 0x%08X" % nxt)
    # M9-M11: the missile tables
    for row, lab, base, cntva, want, readers in (
            ("M9", "do", 0x0073C768, 0x0073C71C, 53, [(0x005ADBFE, r"cmp eax,\[0x73c71c\]")]),
            ("M10", "hit", 0x0073C840, 0x0073C83C, 71, [(0x005ADA19, r"cmp eax,\[0x73c83c\]"),
                                                         (0x005AE0A7, r"cmp eax,\[0x73c83c\]"),
                                                         (0x005AE112, r"cmp eax,\[0x73c83c\]"),
                                                         (0x005B02DB, r"cmp eax,\[0x73c83c\]")]),
            ("M11", "damage", 0x0073C960, 0x0073C95C, 31, [(0x005AE164, r"cmp eax,\[0x73c95c\]")])):
        n = dword(cntva)
        ents = [dword(base + 4 * i) for i in range(n)]
        after = dword(base + 4 * n)
        cnt_refs = Q.raw_abs(cntva)
        rbad = site_line(sec, "%s %s-table count compares" % (row, lab), [v for v, _ in readers], [w for _, w in readers])
        out(sec, "%s %s table" % (row, lab), count=n, want=want, entry0=hex(ents[0]),
            nonnull=sum(1 for e in ents if e), count_refs=len(cnt_refs), readers=len(readers),
            next_dword=hex(after), bad=int(n != want or len(cnt_refs) != len(readers)))
    # M12: collide types
    ct = [(dword(0x0073C720 + 8 * i), dword(0x0073C724 + 8 * i)) for i in range(9)]
    out(sec, "M12 collide types", entries=len(ct), span="0x0073C720..0x%08X" % (0x0073C720 + 72),
        next_is_do_table=int(0x0073C720 + 72 == 0x0073C768), abs32=len(Q.raw_abs(0x0073C720)),
        bad=int(0x0073C720 + 72 != 0x0073C768))
    for i, (f, m) in enumerate(ct):
        note("type %d: filter 0x%08X %s, mask 0x%04X" % (i, f, nm(f) if f else "none", m))
    site_line(sec, "M12 reader", [0x005AE303, 0x005AE30B], [r"cmp \[esi\*8\+0x73c720\],0x0", r"lea eax,\[esi\*8\+0x73c720\]"])
    # M13: the direction table
    site_line(sec, "M13 PathDirection index", [0x0064FCD3, 0x0064FCD7, 0x0064FCDD, 0x0064FCE0, 0x0064FCE7],
              [r"imul eax,eax,0x7f", r"idiv edi", r"lea edx,\[eax\+eax\*2\]", r"\[edx\*4\+0x6eb7e8\]", r"\[edx\*4\+0x6eb7e0\]"])
    rows = [(sdword(0x006EB7E0 + 12 * i), sdword(0x006EB7E4 + 12 * i), sdword(0x006EB7E8 + 12 * i)) for i in range(129)]
    out(sec, "M13 g_PathDirTable", entries=128, first=rows[0], last=rows[127], beyond=rows[128],
        abs32=len(Q.raw_abs(0x006EB7E0)) + len(Q.raw_abs(0x006EB7E4)) + len(Q.raw_abs(0x006EB7E8)))
    # C3: the circle tables
    xs = [sdword(0x006E2B78 + 4 * i) for i in range(64)]
    ys = [sdword(0x006E2A78 + 4 * i) for i in range(64)]
    r2 = [x * x + y * y for x, y in zip(xs, ys)]
    site_line(sec, "C3 reader (mod 64)", [0x005AF106, 0x005AF116, 0x005AF11D],
              [r"and eax,0x8000003f", r"mov edx,\[eax\*4\+0x6e2b78\]", r"mov ecx,\[eax\*4\+0x6e2a78\]"])
    out(sec, "C3 circle tables", n=64, x_span="0x006E2B78..0x006E2C78", y_span="0x006E2A78..0x006E2B78",
        r2_min=min(r2), r2_max=max(r2), r_min="%.2f" % min(r2) ** .5, r_max="%.2f" % max(r2) ** .5,
        readers=len(Q.raw_abs(0x006E2B78)) + len(Q.raw_abs(0x006E2A78)), bad=int(not (28 ** 2 <= min(r2) and max(r2) <= 31 ** 2)))
    import math
    tr = [(int(30 * math.cos(2 * math.pi * i / 64)), int(30 * math.sin(2 * math.pi * i / 64))) for i in range(64)]
    miss = [i for i in range(64) if tr[i] != (xs[i], ys[i])]
    out(sec, "C3 against trunc(30 cos, 30 sin) of i/64 turns", points=64, equal=64 - len(miss),
        differ=" ".join("%d:(%d,%d)/(%d,%d)" % ((i,) + (xs[i], ys[i]) + tr[i]) for i in miss) or "-")
    note("first points: %s" % ", ".join("(%d,%d)" % p for p in list(zip(xs, ys))[:8]))


# ------------------------------------------------------------------------------------------------ s16
@section("s16")
def sec_s16():
    sec = "s16"
    tests = (("hit", 0x005ADA0D, 0xE, 0x73C83C), ("hit", 0x005AE09B, 0xE, 0x73C83C), ("hit", 0x005AE106, 0xE, 0x73C83C),
             ("hit", 0x005B02CF, 0xE, 0x73C83C), ("damage", 0x005AE158, 0x10, 0x73C95C), ("do", 0x005ADBEE, 0xC, 0x73C71C))
    for kind, va, off, cnt in tests:
        ins = listing(va, va + 0x20)[:6]
        want = [r"movzx eax,\[e..\+%s\]" % hex(off), r"test ax,ax", r"jle ", r"movsx eax,ax",
                r"cmp eax,\[%s\]" % hex(cnt), r"jge "]
        site_line(sec, "M51 %s test at 0x%08X (%s)" % (kind, va, nm(va)), [v for v, _, _ in ins], want)
        prev = [x for x in listing(va - 0x30, va)][-4:]
        note("before: " + "; ".join("%s %s" % (mn, norm_ops(o)) for _, mn, o in prev))
    # every row's three function words, read twice
    h, txt = Q.tab("missiles")
    b = Q.binrecs("missiles")
    big = collections.defaultdict(list)
    diff = 0
    for i, r in enumerate(b):
        for col in ("pSrvDoFunc", "pSrvHitFunc", "pSrvDmgFunc"):
            v = r.get(col) or 0
            if v > 0x7FFF:
                big[col].append((i, txt[i]["Missile"], v, v - 0x10000, txt[i].get(col)))
            t = txt[i].get(col, "")
            if t.strip().lstrip("-").isdigit() and int(t) != (v if v <= 0x7FFF else v - 0x10000) and not (t == "" and v == 0):
                diff += 1
    out(sec, "M51 Missiles rows above 0x7FFF", rows=len(b), txt_rows=len(txt), hit=len(big["pSrvHitFunc"]),
        damage=len(big["pSrvDmgFunc"]), do=len(big["pSrvDoFunc"]), txt_bin_numeric_differ=diff,
        bad=int(len(b) != len(txt) or [x[0] for x in big["pSrvHitFunc"]] != [568] or big["pSrvDmgFunc"] or big["pSrvDoFunc"] or diff))
    for col, lst in big.items():
        for i, n, v, sv, t in lst:
            note("%s row %d %s: %d (s16 %d), .txt cell %r" % (col, i, n, v, sv, t))


# ------------------------------------------------------------------------------------------------ entries
MDO1, MDO1_THUNK, MDO3, MDO7 = 0x005AE1F0, 0x005B0BC0, 0x005AE480, 0x005AE780
COOKIE = 0x00681A48     # the stack-cookie check; it keeps eax


def after_call(va):
    """What a function returns after the call or jmp at va: 'tail' (jmp), 'result' (eax unwritten up to a ret),
    'const N', or 'other'. Linear objdump walk, unconditional jmps followed, at most 16 instructions."""
    mn, ops = A().ins[va]
    if mn == "jmp":
        return "tail"
    cur = A().next_va(va)
    cookie = False
    for _ in range(16):
        mn, ops = A().ins[cur]
        o = norm_ops(ops)
        if mn in ("ret", "retn"):
            return "result after the cookie check" if cookie else "result"
        if mn == "jmp":
            t = S.branch_target(ops)
            if t is None:
                return "other"
            cur = t
            continue
        if mn.startswith("j"):
            return "branch"
        if mn == "mov" and o.startswith("eax,"):
            v = o.split(",")[1]
            return "const %d" % int(v, 16) if v.startswith("0x") else "eax<-" + v
        if mn in ("xor", "sub") and o == "eax,eax":
            return "const 0"
        if mn == "lea" and o.startswith("eax,") or mn in ("inc", "dec", "add", "or", "and") and o.startswith("eax"):
            return "eax<-%s %s" % (mn, o)
        if mn == "call" and S.branch_target(ops or "") == COOKIE:
            cookie = True
        elif mn == "call":
            return "call"
        cur = A().next_va(cur)
    return "other"


@section("entries")
def sec_entries():
    sec = "entries"
    # C4: the hit and damage entries' ret
    for lab, base, n, want in (("hit", 0x0073C840, 71, 4), ("damage", 0x0073C960, 31, 8)):
        ents = sorted(set(dword(base + 4 * i) for i in range(n)) - {0})
        rr = {e: rets(e) for e in ents}
        r2pop = {e: T.callee_pop(e) for e in ents}
        badl = [e for e in ents if rr[e] != {want} or r2pop[e] != want]
        out(sec, "C4 %s entries ret" % lab, slots=n, distinct=len(ents), want="ret %d" % want,
            all_rets_objdump=sum(1 for e in ents if rr[e] == {want}), first_ret_r2=sum(1 for e in ents if r2pop[e] == want),
            bad=len(badl))
        for e in badl:
            note("0x%08X %s: objdump rets %s, r2 first ret %s" % (e, nm(e), sorted(rr[e]), r2pop[e]))
    # C10, C12: the do entries' tails
    raw = S.image()[0][S.va_off(0x005B0BC0):S.va_off(0x005B0BC0) + 5]
    tgt = (0x005B0BC0 + 5 + struct.unpack("<i", raw[1:5])[0]) & 0xFFFFFFFF
    out(sec, "C10 entry 1", entry=hex(dword(0x0073C768 + 4)), byte0=hex(raw[0]), jmp_target=hex(tgt),
        r2=Q.r2_text(0x005B0BC0), bad=int(dword(0x0073C768 + 4) != 0x005B0BC0 or raw[0] != 0xE9 or tgt != MDO1))
    names = {MDO1: "mdo1", MDO1_THUNK: "mdo1", MDO3: "mdo3", MDO7: "mdo7"}
    summary = {}
    for n in range(2, 53):
        e = dword(0x0073C768 + 4 * n)
        if not e:
            continue
        vas, calls, _ = fn_body(e)
        tails = []
        for va in vas:
            mn, ops = A().ins[va]
            if mn in ("call", "jmp"):
                t = S.branch_target(ops or "")
                if t in names:
                    r2t = Q.r2_many([va])[va]
                    ok = r2t and Q.r2_target(r2t[1]) == t
                    tails.append("%s@0x%08X:%s%s" % (names[t], va, after_call(va), "" if ok else "!r2"))
        consts = sorted(set(after_call(va) for va in vas if A().ins[va][0] in ("ret", "retn")) - {"result"})
        k2 = sum(1 for va in vas if A().ins[va][0] == "mov" and norm_ops(A().ins[va][1]) == "eax,0x2")
        summary[n] = (e, tails, k2)
    for n, (e, tails, k2) in summary.items():
        note("mdo %d 0x%08X %s: %s; mov eax,2 x%d" % (n, e, nm(e), ", ".join(tails) or "no mdo 1/3/7", k2))
    s9a = [n for n in summary if 2 <= n <= 18]
    no1 = [n for n in s9a if not any(t.startswith("mdo1") and (t.endswith(":tail") or ":result" in t) for t in summary[n][1])]
    want9b = {20: "mdo1", 30: "mdo1", 32: "mdo7", 34: "mdo3"}
    b9 = []
    for n, m in want9b.items():
        ts = [t for t in summary.get(n, (0, [], 0))[1] if t.startswith(m)]
        if not ts or (n in (20, 30) and not all(t.endswith(":const 1") for t in ts)) or (n in (32, 34) and not all(t.endswith(":tail") or t.endswith(":result") for t in ts)):
            b9.append(n)
    other9b = [n for n in summary if n >= 19 and n not in want9b and summary[n][1]]
    out(sec, "C10 9a entries ending in mdo 1", entries=len(s9a), without=" ".join(map(str, no1)) or "-", bad=len(no1))
    extra = [n for n in range(37, 53) if dword(0x0073C768 + 4 * n)]
    note("non-null do entries above 36: %s" % (" ".join("%d:0x%08X" % (n, dword(0x0073C768 + 4 * n)) for n in extra) or "-"))
    out(sec, "C10 9b entries 20, 30 (1 after mdo 1), 32 (mdo 7), 34 (mdo 3)", failed=" ".join(map(str, b9)) or "-",
        other_9b_with_tail=" ".join(map(str, other9b)) or "-", bad=len(b9))
    e6 = summary.get(6)
    out(sec, "C12 mdo 6 after: mdo 1", entry=hex(e6[0]), tails=" ".join(e6[1]),
        bad=int(not any(t.startswith("mdo1") for t in e6[1])))
    # C25: entry 24 is entry 23's function
    e23, e24 = dword(0x0073C768 + 4 * 23), dword(0x0073C768 + 4 * 24)
    out(sec, "C25 entries 23 and 24", e23=hex(e23), e24=hex(e24), abs_23=len(Q.raw_abs(0x005AF790)),
        bad=int(e23 != e24 or e23 != 0x005AF790))


# ------------------------------------------------------------------------------------------------ data
def num(v):
    v = (v or "").strip()
    return int(v) if v.lstrip("-").isdigit() else None


@section("data")
def sec_data():
    sec = "data"
    hm, mt = Q.tab("missiles")
    mb = Q.binrecs("missiles")
    # M68 and C25: the used function numbers, both readers
    for col, lim, want in (("pSrvDoFunc", 53, 34), ("pSrvHitFunc", 71, 49), ("pSrvDmgFunc", 31, 13)):
        tb = sorted(set(r.get(col) or 0 for r in mb) - {0})
        used = [v for v in tb if 0 < v < lim]
        tt = sorted(set(num(r.get(col)) for r in mt) - {None, 0})
        out(sec, "M68 %s used" % col, distinct_bin=len(tb), in_table=len(used), want=want,
            txt_numeric=len([v for v in tt if 0 < v < lim]), unused=" ".join(str(n) for n in range(1, lim) if n not in used),
            bad=int(len(used) != want))
    do24 = [i for i, r in enumerate(mb) if r.get("pSrvDoFunc") == 24]
    out(sec, "C25 rows naming mdo 24", rows=len(do24), bad=len(do24))
    # M39 M43 M44: CollideType counts
    cnt = collections.Counter(r.get("CollideType") or 0 for r in mb)
    cntt = collections.Counter(num(r.get("CollideType")) or 0 for r in mt)
    out(sec, "M39/M43/M44 CollideType rows", by_type=" ".join("%d:%d" % kv for kv in sorted(cnt.items())),
        txt_same=int(cnt == cntt), type0=cnt[0], type4=cnt[4], type6=cnt[6],
        bad=int(cnt[0] != 301 or cnt[4] != 0 or cnt[6] != 24 or cnt != cntt))
    # Skills
    hs, st = Q.tab("skills")
    sb = Q.binrecs("skills")

    def miss(v):
        return v not in (None, 0xFFFF, -1) and v < len(mb)
    only = [i for i, r in enumerate(sb) if miss(r.get("srvmissile")) and not r.get("srvdofunc")]
    abc = [i for i, r in enumerate(sb) if not miss(r.get("srvmissile")) and not r.get("srvdofunc") and
           any(miss(r.get(c)) for c in ("srvmissilea", "srvmissileb", "srvmissilec"))]
    out(sec, "D58 srvmissile with no srvdofunc", rows=len(only), want=48, has_36_251_25=int({36, 251, 25} <= set(only)),
        abc_only_no_do=" ".join(map(str, abc)), bad=int(len(only) != 48 or abc != [307, 325] or not {36, 251, 25} <= set(only)))
    txt_only = [i for i, r in enumerate(st) if r["srvmissile"] and r["srvdofunc"] in ("", "0")]
    note(".txt reader: %d rows with a srvmissile cell and no srvdofunc" % len(txt_only))
    per = [i for i, r in enumerate(sb) if r.get("periodic")]
    sm = [i for i, r in enumerate(sb) if r.get("startmana")]
    rp = [i for i, r in enumerate(sb) if r.get("repeat")]
    pt = [i for i, r in enumerate(st) if r["periodic"] == "1"]
    smt = [i for i, r in enumerate(st) if r["startmana"] not in ("", "0")]
    rpt = [i for i, r in enumerate(st) if r["repeat"] == "1"]
    out(sec, "D74/D76 periodic, startmana, repeat rows", periodic=" ".join("%d:%s" % (i, st[i]["skill"]) for i in per),
        startmana=" ".join("%d:%s" % (i, st[i]["skill"]) for i in sm), repeat=" ".join(map(str, rp)),
        txt_same=int((pt, smt, rpt) == (per, sm, rp)),
        bad=int(per != [57, 277] or sm != rp or len(sm) != 3 or set(sm) & set(per) or (pt, smt, rpt) != (per, sm, rp)))
    # D108: who registers the handlers
    hi, it = Q.tab("itemstatcost")
    ib = Q.binrecs("itemstatcost")
    isc = sorted(set(v for r in ib for c in ("itemeventfunc1", "itemeventfunc2") for v in [r.get(c)] if v))
    isct = sorted(set(num(r[c]) for r in it for c in ("itemeventfunc1", "itemeventfunc2") if num(r[c])))
    sk = collections.defaultdict(set)
    for c in ("auraeventfunc1", "auraeventfunc2", "auraeventfunc3", "passiveeventfunc"):
        for r in st:
            if num(r[c]):
                sk[c].add(num(r[c]))
    skall = sorted(set().union(*sk.values()))
    want_isc = [6, 7, 8, 9, 10] + list(range(13, 22)) + [28, 29, 30, 31]
    want_sk = [1, 2, 3, 4, 5] + list(range(22, 28))
    none = [n for n in range(1, 32) if n not in isc and n not in skall]
    out(sec, "D108 handler registration", itemstatcost=",".join(map(str, isc)), skills=",".join(map(str, skall)),
        named_by_none=",".join(map(str, none)), isc_txt_same=int(isc == isct),
        bad=int(isc != want_isc or skall != want_sk or none != [11, 12] or isc != isct))
    for c, v in sk.items():
        note("Skills %s: %s" % (c, sorted(v)))
    # C67: STATES_Load's list and the States rows with flag bit 16
    # g_DataTables (0x0096BC30) + 0x17C / + 0x180: the list do 121 reads (0x005C89D0, 0x005C89B3)
    w = [(va, mn, o) for va, mn, o in listing(0x00618100, 0x00618C58)
         if (norm_ops(o).startswith("edi,") and mn not in ("cmp", "test")) or (mn in ("pop", "xchg") and "edi" in o)]
    v = int(norm_ops(w[0][2]).split(",")[1], 16) if len(w) == 1 and w[0][1] == "mov" else "edi?"
    note("writes of edi in STATES_Load before 0x00618C58: %s" % "; ".join("0x%08X %s %s" % x for x in w))
    site_line(sec, "C67 STATES_Load list call", [0x00618C4D, 0x00618C4E, 0x00618C53, 0x00618C58, 0x005C89D0, 0x005C89B3],
              [r"push edi", r"mov edx,0x96bdb0", r"mov ecx,0x96bdac", r"call 0x611dc0", r"mov eax,\[eax\+0x17c\]",
               r"cmp \[eax\+0x180\],bx"])
    site_line(sec, "C67 StatesListByFlag bit test", [0x00611E16, 0x00611E19, 0x00611E20, 0x00611E26, 0x00611E35],
              [r"and ebx,0x7", r"lea ebx,\[ebx\*4\+0x6ce268\]", r"sar ecx,0x3", r"lea ecx,\[ecx\+edx\+0x10\]", r"test \[ebx\],dl"])
    a, b, ag = args(0x00618C58, 1)
    hs2, sst = Q.tab("states")
    sbn = Q.binrecs("states")
    dis = [i for i, r in enumerate(sbn) if r.get("disguise")]
    dist = [i for i, r in enumerate(sst) if r.get("disguise") == "1"]
    out(sec, "C67 the list's bit and its rows", pushed=a, pushed_r2=b, edi=v, list_addr="0x96BC30+0x17C", rows=" ".join("%d:%s" % (i, sst[i]["state"]) for i in dis),
        txt_same=int(dis == dist), bad=int(v != 16 or dis != dist or not {139, 140} <= set(dis)))
    # C87: the maggot spawn joins
    hmo, mo = Q.tab("monstats")
    mob = Q.binrecs("monstats")
    ids = {r["Id"]: i for i, r in enumerate(mo)}
    sm_rows = [(i, r["Id"], r["spawn"], r["spawnmode"], [r["Skill%d" % k] for k in range(1, 6) if r["Skill%d" % k]])
               for i, r in enumerate(mo) if r["Id"].startswith("sandmaggot")]
    ok15 = all(mo[ids["sandmaggot%d" % k]]["spawn"] == "maggotegg%d" % k and mo[ids["sandmaggot%d" % k]]["spawnmode"] == "S1"
               for k in range(1, 6))
    binsp = [mob[i].get("spawn") for i, *_ in sm_rows]
    out(sec, "C87 sandmaggot spawn rows", rows=len(sm_rows), one_to_five_hold=int(ok15),
        bin_spawn_ids=",".join(map(str, binsp)), bad=int(not ok15))
    for i, n, sp, mode, sks in sm_rows:
        note("%d %s: spawn %s (%s), skills %s" % (i, n, sp, mode, sks))
    users = collections.defaultdict(list)
    for i, r in enumerate(mo):
        for k in range(1, 9):
            v2 = r.get("Skill%d" % k, "")
            if v2 in ("MaggotEgg", "MagottLay", "Nest", "EvilHutSpawner"):
                users[v2].append(r["Id"])
    for k2, v2 in users.items():
        note("MonStats rows using %s: %s" % (k2, " ".join(v2)))
    o8 = {156: ("srvmissilea", ""), 183: ("srvmissile", ""), 202: ("srvmissile", ""), 336: ("srvmissilea", "rogue1")}
    o8bad = [i for i, (c, w) in o8.items() if st[i][c] != w]
    out(sec, "C87 O8 rows 156, 183, 202, 336", names=" ".join(st[i]["skill"].replace(" ", "_") for i in o8),
        rogue1_in_missiles=int(any(r["Missile"] == "rogue1" for r in mt)), bad=len(o8bad))
    # C90: P4's joins
    p4 = [(193, "srvstfunc", "53"), (193, "srvdofunc", "152"), (193, "srvmissilea", "diablight"), (285, "Param5", "40"),
          (285, "Param6", ""), (212, "srvdofunc", "112"), (66, "skill", "Amplify Damage"), (72, "skill", "Weaken"),
          (82, "skill", "Life Tap"), (87, "skill", "Decrepify"), (91, "skill", "Lower Resist")]
    p4bad = [(i, c, st[i][c], w) for i, c, w in p4 if st[i][c] != w]
    out(sec, "C90 P4 cells", cells=len(p4), bad=len(p4bad))
    for x in p4bad:
        note("row %d %s: %r, want %r" % x)
    note("row 91 Param7 %r; row 212 Param5..7 %r %r %r" % (st[91]["Param7"], st[212]["Param5"], st[212]["Param6"], st[212]["Param7"]))
    # C98, C99: Q6's joins
    stid = {r["state"]: i for i, r in enumerate(sst)}
    mm = [r.get("code") for r in Q.tab("monmode")[1]]
    q6 = [(301, "srvmissilea", "", sb[301].get("srvmissilea") == 0xFFFF), (301, "srvdofunc", "134", True),
          (330, "aurastate", "attached", stid.get("attached") == 143 and sst[143]["srvactivefunc"] == "147"),
          (295, "auratargetstate", "bloodlust", stid.get("bloodlust") == 141), (295, "calc1", "par1", st[295]["Param1"] == "65"),
          (295, "summon", "suicideminion1", ids.get("suicideminion1") == 461),
          (295, "summode", "S1", mm.index("S1") == 8), (300, "summon", "painworm1", ids.get("painworm1") == 551)]
    q6bad = [(i, c, st[i][c], w, ok) for i, c, w, ok in q6 if st[i][c] != w or not ok]
    out(sec, "C98/C99 Q6 cells", cells=len(q6), bad=len(q6bad))
    for x in q6bad:
        note("row %d %s: %r, want %r (join %s)" % x)


# ------------------------------------------------------------------------------------------------ consts
def fn_calls(entry):
    """[(site, target)] of a function's direct calls, objdump body, site order."""
    _, calls, _ = fn_body(entry)
    return sorted(calls)


def call_args_line(sec, label, entry, targets, n):
    """Every call of `targets` inside a function, with n arguments by both walkers."""
    rows, bad = [], 0
    for va, t in fn_calls(entry):
        if t in targets:
            a, b, ag = args(va, n)
            bad += 0 if ag else 1
            rows.append("0x%08X %s(%s)%s" % (va, nm(t), ", ".join(a or []), "" if ag else " [r2 %s]" % b))
    out(sec, label, calls=len(rows), bad=bad)
    for r in rows:
        note(r)
    return rows


STATE_FNS = {0x006256B0, 0x006252D0, 0x00639DB0, 0x00639DF0, 0x00639E30}


@section("consts")
def sec_consts():
    sec = "consts"
    allfn = set(t for t in STATE_FNS)
    # D21, D68, D187: the delay state's writer and reader
    w = call_args_line(sec, "D21 SetDelayState state calls", 0x0056EF90, allfn | {0x005417D0}, 2)
    r = call_args_line(sec, "D21 DelayOk state calls", 0x006478F0, allfn, 2)
    out(sec, "D21 state 121 pair", writer_state_args=sum(1 for x in w if "(121" in x or ", 121" in x),
        reader_state_args=sum(1 for x in r if ", 121" in x or "(121" in x),
        bad=int(not any(", 121" in x or "(121" in x for x in r) or sum(1 for x in w if "121" in x) < 3))
    ue = [x for x in call_args_line(sec, "D68 SetDelayState unit-event calls", 0x0056EF90, {0x005417D0, 0x00541720}, 3)]
    # D22: state 114 by an exhaustive scan of `push 0x72` before a state call
    sites = []
    for va, (mn, ops) in A().ins.items():
        if mn == "call" and S.branch_target(ops or "") in STATE_FNS:
            a, b, ag = args(va, 2)
            if a and "114" in a[:2]:
                sites.append((va, nm(S.branch_target(ops)), a, ag))
    out(sec, "D22 state 114 calls (.text, every call of the five state functions)", calls=len(sites),
        owners=" ".join(sorted(set(nm(v).split("+")[0] for v, *_ in sites))), bad=sum(1 for *_, ag in sites if not ag))
    for va, f, a, ag in sorted(sites):
        note("0x%08X %s %s(%s)" % (va, nm(va), f, ", ".join(a)))
    # D23: the periodic floor
    site_line(sec, "D23 QueuePeriodic floor", [0x0056CDF7, 0x0056CDFE, 0x0056CE01, 0x0056CE03, 0x0056CEC7, 0x0056CECE, 0x0056CED1, 0x0056CED3],
              [r"call 0x646ca0", r"cmp ecx,0x5", r"jg 0x56ce08", r"mov ecx,0x5", r"call 0x646ca0", r"cmp ecx,0x5", r"jg 0x56ced8", r"mov ecx,0x5"])
    # D24: the charge cap
    site_line(sec, "D24 AddProgressiveCharge cap", [0x005D340F, 0x005D3414, 0x005D3417, 0x005D341A, 0x005D341C, 0x005D3421, 0x005D342A],
              [r"call 0x625d00", r"lea ecx,\[eax\+0x1\]", r"cmp ecx,0x3", r"jle 0x5d3421", r"mov ecx,0x3", r"cmp eax,ecx", r"call 0x627150"])
    a, b, ag = args(0x005D342A, 3)
    a2, b2, ag2 = args(0x005D340F, 2)
    out(sec, "D24 read and write the same stat", read=a2, write=a, bad=int(not (ag and ag2 and a2[:2] == a[:1] + a[1:2]) and a2[1] != a[1]))


# ------------------------------------------------------------------------------------------------ calls
SRVDO, ITEMCAST, CAST_UNIT, CAST_XY = 0x0056F7F0, 0x005FDA80, 0x005FDCA0, 0x005FDD60


def caller_list(sec, label, target, want=None):
    r = Q.ref_line(sec, label, target, want=want)
    BAD[sec] += Q.BAD.pop("S2c-" + sec, 0)
    return r


@section("calls")
def sec_calls():
    sec = "calls"
    Q.BAD.clear()
    # D42: SKILLS_CanUse's callers and the monster path
    cu = Q.ref_line(sec, "D42 SKILLS_CanUse callers", 0x00647960)
    import sweep2_s7a as W
    mon = {0x005DEAD0: "MonAiUseSkill", 0x005A75C0: "MonModeStartSkill", 0x005A7C20: "MonSetMode", 0x005A7670: "MonAttackFrame",
           0x0056FAF0: "SKILLS_StartUsedSkill", 0x0056FC50: "SKILLS_DoUsedSkill"}
    G = W.graph2(list(mon))
    hit = 0x00647960 in G
    out(sec, "D42 direct-call closure from the monster mode path", roots=len(mon), functions=len(G),
        reaches_canuse=int(hit), icalls=sum(len(v[4]) for v in G.values() if v))
    direct = [v for v in cu if T.owner(v)[0] in mon]
    out(sec, "D42 callers inside the monster mode path's own functions", callers=len(direct), bad=len(direct))
    if hit:
        e, chain = 0x00647960, []
        while e is not None:
            chain.append(nm(e))
            e = G[e][1]
        note("path: " + " <- ".join(chain))
    # D46: the four refusals
    for va in (0x0056FB49, 0x0056FC41, 0x0056F6DB, 0x0056F8AE):
        a, b, ag = args(va, 5)
        a = [Q.resolve(va, x) if x == "eax" else x for x in a]
        g = [x for x in listing(va - 0x20, va) if x[1] == "cmp" and norm_ops(x[2]).endswith(",0x0") or x[1] == "cmp" and norm_ops(x[2]) == "[esi],eax"]
        out(sec, "D46 refusal 0x%08X" % va, target=nm(S.branch_target(A().ins[va][1])), args=",".join(map(str, a)), walkers_agree=int(ag),
            type_test=";".join("%s %s" % (m, norm_ops(o)) for _, m, o in g), bad=int(not ag))
    site_line(sec, "D46 0x0056FC41's eax is 0 (eax = ebx, ebx tested non-zero away)", [0x0056FC29, 0x0056FC32, 0x0056FC34],
              [r"mov ebx,eax", r"test ebx,ebx", r"jne 0x56fc46"])
    # D48 / D195: the ally test
    site_line(sec, "D48 StartUsedSkill gate and call", [0x0056FBB2, 0x0056FBB8, 0x0056FBBB, 0x0056FBC4],
              [r"mov cl,\[0x6ce270\]", r"test \[edi\+0x7\],cl", r"jne 0x56fbcd", r"call 0x554d20"])
    site_line(sec, "D48 SkillAllyTest bit test", [0x00554D56, 0x00554D59, 0x00554D62, 0x00554D68, 0x00554D6B],
              [r"mov ecx,\[ebp\+0xc\]", r"call 0x45c4b0", r"mov cl,\[0x6ce270\]", r"test \[eax\+0x7\],cl", r"je 0x554dd0"])
    site_line(sec, "D48 the same skill: edi = row(ebx) in StartUsedSkill, row([ebp+0xc] = the pushed ebx) in the test",
              [0x0056FB94, 0x0056FB96, 0x0056FB9C, 0x0056FBC0, 0x0045C4C4, 0x0045C4CA],
              [r"mov edi,ebx", r"imul edi,edi,0x23c", r"add edi,\[eax\+0xb98\]", r"push ebx", r"imul eax,eax,0x23c", r"add eax,\[ecx\+0xb98\]"])
    wr = [x for x in listing(0x0056FB9C, 0x0056FBC0) if norm_ops(x[2]).startswith("ebx,") or x[1] == "pop"]
    out(sec, "D48 ebx unwritten between the row and the push", writes=len(wr), bad=len(wr))
    tail = listing(0x00554DD0, 0x00554DE0)
    out(sec, "D48 SkillAllyTest 0x00554DD0", code="; ".join("%s %s" % (m, norm_ops(o)) for _, m, o in tail[:4]),
        bad=int(not any(m == "xor" and norm_ops(o) == "eax,eax" for _, m, o in tail[:3])))
    Q.ref_line(sec, "D48 SkillAllyTest callers", 0x00554D20)
    # D60, C80: SKILLS_SrvDo's callers and the effect argument (stack arg 4: id, lvl, pay, item, effect)
    sd = Q.ref_line(sec, "D60 SKILLS_SrvDo callers", SRVDO)
    nz = []
    for va in sd:
        a, b, ag = args(va, 5)
        eff = Q.resolve(va, a[4]) if a and len(a) > 4 else None
        effi = int(eff) if isinstance(eff, int) or (isinstance(eff, str) and eff.isdigit()) else eff
        if effi != 0:
            nz.append(va)
        note("0x%08X %s: args %s, effect %s%s" % (va, nm(va), a, effi, "" if ag else " [r2 %s]" % b))
    site_line(sec, "D60 0x0056FD34's eax is 0 (UnitIsDead's result, non-zero branched away)", [0x0056FD20, 0x0056FD25, 0x0056FD27, 0x0056FD2C, 0x0056FD2D],
              [r"call 0x5541b0", r"test eax,eax", r"jne 0x56fd50", r"push eax", r"push eax"])
    nz = [v for v in nz if v != 0x0056FD34]
    out(sec, "D60 callers with a non-zero or variable effect", callers=len(sd), nonzero=" ".join(nm(v) for v in nz),
        bad=int(len(sd) != 8 or [nm(v).split("+")[0] for v in nz] != ["ITEMSKILL_Cast"]))
    # D81, D194, D82: the effect flag from ITEMSKILL_Cast's callers (its 10th stack arg, [ebp+0x2c])
    site_line(sec, "D81 ITEMSKILL_Cast passes [ebp+0x2c] as SrvDo's effect", [0x005FDC1E, 0x005FDC24], [r"mov ecx,\[ebp\+0x2c\]", r"push ecx"])
    ic = Q.ref_line(sec, "D81 ITEMSKILL_Cast callers", ITEMCAST)
    for va in ic:
        a, b, ag = args(va, 10)
        note("0x%08X %s: arg 10 %s (r2 %s)" % (va, nm(va), a[9] if a and len(a) > 9 else None, b[9] if b and len(b) > 9 else None))
    rows = []
    for tgt, k in ((CAST_UNIT, 2), (CAST_XY, 3)):
        for va in Q.ref_line(sec, "D81 %s callers" % nm(tgt), tgt):
            a, b, ag = args(va, k + 1)
            v = Q.resolve(va, a[k]) if a and len(a) > k else None
            rows.append((va, nm(va), v, ag))
    for va, n, v, ag in rows:
        note("0x%08X %s: effect argument %s%s" % (va, n, v, "" if ag else " [walkers differ]"))
    # five callers take the effect push from a block before a branch (the linear walkers stop at the other path's ret):
    # each push is decoded twice and the path from it to the call has no other push of that slot
    shared = {0x005C065A: (0x005C0626, 0), 0x005C0751: (0x005C0718, 0), 0x005BF1D7: (0x005BF1A1, 0),
              0x005C0584: (0x005C054E, 1), 0x005C0558: (0x005C054E, 1)}
    site_line(sec, "D81 the shared effect pushes", sorted(set(p for p, _ in shared.values())),
              [r"push 0x1" if p == 0x005C054E else r"push 0x0" for p in sorted(set(p for p, _ in shared.values()))])
    rows = [(va, n, shared[va][1] if va in shared else v, ag) for va, n, v, ag in rows]
    for va, n, v, ag in rows:
        note("resolved 0x%08X %s: effect %s" % (va, n, v))
    site_line(sec, "D81 handler 20's branch on ItemTgtDo (Skills +0x07 bit 5)", [0x005C051E, 0x005C0524, 0x005C0527, 0x005C0530, 0x005C054E],
              [r"mov cl,\[0x6ce27c\]", r"test \[eax\+0x7\],cl", r"je 0x5c0549", r"push 0x0", r"push 0x1"])
    hi, it = Q.tab("itemstatcost")
    for f in (20, 21, 30):
        note("ItemStatCost rows with event func %d: %s" % (f, " ".join("%s(%s/%s)" % (r["Stat"], r["itemevent1"], r["itemevent2"]) for r in it
                                                                    if f in (num(r["itemeventfunc1"]), num(r["itemeventfunc2"])))))
    ones = [n for _, n, v, _ in rows if v not in (0, "0")]
    out(sec, "D81 the item-cast callers' effect argument", callers=len(rows),
        nonzero=" ".join(ones), bad=int(any(not n.startswith("sub_005C0470_StatEv20") for n in ones)))
    # D151: MonAttackStats
    Q.ref_line(sec, "D151 MonAttackStats callers", 0x005A4F50)
    call_args_line(sec, "D151 MonSkillAttackDo's calls", 0x005D9C80, {0x005A4F50, 0x005A5490, 0x0057D4F0}, 1)
    # D157: SkillWeaponWear
    Q.ref_line(sec, "D157 SkillWeaponWear callers", 0x005DAA40)
    out(sec, "D157 ImpaleHit's direct calls in order", calls=len(fn_calls(0x005DAB40)))
    note(", ".join("0x%08X %s" % (va, nm(t)) for va, t in fn_calls(0x005DAB40)))
    # D98: the mastery bonus
    Q.ref_line(sec, "D98 SKILLS_GetMasteryBonus callers", 0x00645830)
    # C53: 0x005C2FF0 and the paladin entries
    Q.ref_line(sec, "C53 0x005C2FF0 callers", 0x005C2FF0)
    pal_st = [29, 31, 35, 36, 37]
    pal_do = [64, 65, 66, 67, 73, 79, 80, 81, 82, 150]
    roots = [dword(0x00732140 + 4 * i) for i in pal_st] + [dword(0x007322B0 + 4 * i) for i in pal_do]
    roots = [r for r in roots if r]
    G = W.graph2(roots)
    out(sec, "C53 paladin entries' closure", roots=len(roots), functions=len(G), reaches_0x005C2FF0=int(0x005C2FF0 in G),
        bad=int(0x005C2FF0 in G))
    # M2: MissileCreateAt
    Q.ref_line(sec, "M2 MissileCreateAt callers", 0x0056EDE0)
    # M58: MissileEndHit
    Q.ref_line(sec, "M58 MissileEndHit references", 0x005AD9D0, kinds=("call", "jmp", "jcc"))
    # R17: SkillMissileCreate's to-hit
    site_line(sec, "R17 SkillMissileCreate to-hit", [0x0056ED84, 0x0056ED87, 0x0056ED89, 0x0056ED8B, 0x0056ED8E, 0x0056ED97, 0x0056ED9E],
              [r"cmp \[esi\],0x1", r"jne 0x56eda1", r"push 0x0", r"push 0x13", r"call 0x625480", r"or \[ebp-0x5c\],0x1000",
               r"mov \[ebp-0x14\],eax"])
    k = [va for va, m, o in listing(0x0056ECB0, 0x0056EDE0) if "0x1000" in o or "ebp-0x14" in o]
    out(sec, "R17 to-hit flag and +0x48 writes in SkillMissileCreate", sites=len(k), bad=int(k != [0x0056ED97, 0x0056ED9E]))
    BAD[sec] += sum(Q.BAD.values())
    Q.BAD.clear()


# ------------------------------------------------------------------------------------------------ main
def main(argv):
    secs = argv[1:]
    if not secs:
        print(__doc__)
        return 2
    if secs == ["all"]:
        secs = list(SECTIONS)
    for s in secs:
        print("== %s" % s)
        SECTIONS[s]()
    print("S2c total bad=%d %s" % (sum(BAD.values()), " ".join("%s=%d" % kv for kv in sorted(BAD.items()))))
    return 1 if sum(BAD.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

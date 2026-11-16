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
  bits     (part 2) D56 D57 D185 D193 C58 C14 D76 D95 D88: the Unit+0xC4 bit-6 sets, clears and readers, the monster
           mode records, the do-150 closure, the MissileData+0x28 pair, the Skills +0x05 flag-bit readers, the packet
           +0x65 byte stores
  more     (part 2) D1 D2 D25 D50 D137 C57 C74 C75 C108 M5 M23 M25 M48 R22 M70 M94 R24: the skill packets, noCost, the
           prevent-heal hook, Smite's mode, the knockback pushes, the rings' step, the spiral, useAmmo, the creators, the
           0x40 marks, ExplosionMissile, BuildDamage's reads, the two critical chains
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


# ------------------------------------------------------------------------------------------------ part 2: bits
def bit6_sites():
    """(sets, clears) of Unit+0xC4 bit 6 in objdump's whole .text: `or [r+0xc4], 0x40`, `and [r+0xc4], ~0x40`."""
    sets, clrs = [], []
    for va, (mn, ops) in sorted(A().ins.items()):
        o = norm_ops(ops)
        if "+0xc4]" not in o or not o.split(",")[0].endswith("+0xc4]"):
            continue
        if mn == "or" and o.endswith(",0x40"):
            sets.append(va)
        elif mn == "and" and o.endswith(",0xffffffbf"):
            clrs.append(va)
    return sets, clrs


def r2_bit6_count(vas, want):
    """r2 re-decodes each site; the count of agreeing decodes."""
    dec = Q.r2_many(vas)
    return sum(1 for v in vas if dec[v] and norm_ops(dec[v][1]).split(",")[-1] == want and dec[v][0] in ("or", "and"))


def other_c4_writes():
    """Every other write to a `+0xC4` dword in the server range (0x00540000..0x00680000) whose immediate or register
    operand could clear bit 6: `and` with an immediate that has bit 6 clear, any `mov`, `and`/`xor` with a register."""
    w = []
    for va, (mn, ops) in sorted(A().ins.items()):
        o = norm_ops(ops)
        if not (0x00540000 <= va < 0x00680000) or not o.split(",")[0].endswith("+0xc4]"):
            continue
        src = o.split(",")[-1]
        if mn == "and" and src.startswith("0x") and not int(src, 16) & 0x40:
            w.append((va, mn, o))
        elif mn in ("mov", "xor") or (mn == "and" and not src.startswith("0x")):
            w.append((va, mn, o))
    return w


def body_set(entry):
    return set(fn_body(entry)[0])


def closure_hits(roots, sites):
    import sweep2_s7a as W
    G = W.graph2(roots)
    where = {}
    for e, v in G.items():
        if v:
            for x in v[2]:
                where.setdefault(x, e)
    hits = [s for s in sites if s in where]
    paths = []
    for h in hits:
        e, ch = where[h], []
        while e is not None:
            ch.append(nm(e))
            e = G[e][1]
        paths.append("0x%08X: %s" % (h, " <- ".join(ch)))
    return G, hits, paths, sum(len(v[4]) for v in G.values() if v)


MODE_REC = 0x006E2260  # g_MonModeRecords: 16-byte records {start, frame, end, flag}


@section("bits")
def sec_bits():
    sec = "bits"
    Q.BAD.clear()
    sets, clrs = bit6_sites()
    r2s, r2c = r2_bit6_count(sets, "0x40"), r2_bit6_count(clrs, "0xffffffbf")
    own = sorted(set(nm(v).split("+")[0] for v in sets))
    out(sec, "D56/D185 Unit+0xC4 bit-6 sets and clears (.text, objdump; r2 re-decodes each)", sets=len(sets),
        sets_r2=r2s, clears=len(clrs), clears_r2=r2c, set_owners=len(own),
        set_client_range=sum(1 for v in sets if v < 0x00540000), clear_client_range=sum(1 for v in clrs if v < 0x00540000),
        bad=int(len(sets) != 124 or len(clrs) != 17 or r2s != 124 or r2c != 17))
    note("set owners: " + " ".join(own))
    for v in clrs:
        note("clear 0x%08X %s" % (v, nm(v)))
    w = other_c4_writes()
    out(sec, "D56 other server-range writes of a +0xC4 dword that could clear bit 6", sites=len(w))
    for va, mn, o in w:
        note("0x%08X %s %s %s" % (va, nm(va), mn, o))
    site_line(sec, "D56 SKILLS_SrvDo sets the bit once its missile row exists", [0x0056F97D, 0x0056F982, 0x0056F984, 0x0056F98A],
              [r"call 0x46ace0", r"test eax,eax", r"je 0x56fa3d", r"or \[edi\+0xc4\],0x40"])
    site_line(sec, "D56/D57 the AI's set before MonSetMode", [0x005DEAFF, 0x005DEB08, 0x005DEB33],
              [r"call 0x620210", r"or \[esi\+0xc4\],0x40", r"call 0x5a7c20"])
    # readers: `mov r, [x+0xc4]; shr r, 6`
    vas = sorted(A().ins)
    idx = {v: i for i, v in enumerate(vas)}
    rd = []
    for va in vas:
        mn, ops = A().ins[va]
        o = norm_ops(ops)
        if mn == "mov" and o.split(",")[-1].endswith("+0xc4]"):
            m2, o2 = A().ins[vas[idx[va] + 1]]
            if m2 == "shr" and norm_ops(o2).endswith(",0x6"):
                rd.append(va)
    srv = [v for v in rd if 0x00540000 <= v < 0x00680000]
    out(sec, "D56 bit-6 readers (mov [x+0xC4]; shr 6)", sites=len(rd), server_range=len(srv))
    for v in srv:
        note("0x%08X %s" % (v, nm(v)))
    site_line(sec, "D56 PlrModeSkillFrame: bit 6 set skips the do; else code 1 or 2 runs it",
              [0x005804C2, 0x005804C8, 0x005804CB, 0x005804CE, 0x005804D3, 0x005804D6, 0x005804D8, 0x005804DB, 0x005804E2],
              [r"mov ecx,\[esi\+0xc4\]", r"shr ecx,0x6", r"and ecx,0x1", r"jne 0x5804e7", r"cmp eax,0x1", r"je 0x5804dd",
               r"cmp eax,0x2", r"jne 0x5804e7", r"call 0x56fc50"])
    # the monster mode records
    recs = []
    for m in range(0, 21):
        s, f = dword(MODE_REC + 16 * m), dword(MODE_REC + 16 * m + 4)
        recs.append((m, s, f))
    r2w = Q.r2_words(MODE_REC, 21 * 4) if hasattr(Q, "r2_words") else None
    agree = r2w is not None and all(r2w[4 * m] == s and r2w[4 * m + 1] == f for m, s, f in recs)
    sk = [m for m, s, f in recs if s == 0x005A75C0]
    out(sec, "D57 g_MonModeRecords start and frame words (python and r2)", r2_agree=int(agree),
        modes_with_MonModeStartSkill=" ".join(map(str, sk)), mode14_start="0x%08X" % recs[14][1], mode14_frame=nm(recs[14][2]),
        bad=int(not agree or recs[14][1] != 0x005A7870 or recs[14][2] != 0x005A8670))
    note("frames of the MonModeStartSkill modes: " + " ".join("%d:%s" % (m, nm(f)) for m, s, f in recs if s == 0x005A75C0))
    site_line(sec, "D57 the mode-14 start: SetMode(14), clear bit 6, tail-jump to SKILLS_StartUsedSkill",
              [0x005A7875, 0x005A787B, 0x005A7884, 0x005A7891],
              [r"push 0xe", r"call 0x553570", r"and \[esi\+0xc4\],0xffffffbf", r"jmp 0x56faf0"])
    st = [dword(0x00732140 + 4 * i) for i in range(0x5B)]
    G, hits, paths, ic = closure_hits([0x005A75C0], clrs)
    out(sec, "D57 MonModeStartSkill's direct-call closure against the 17 clears", functions=len(G), icalls=ic, hits=len(hits),
        bad=len(hits))
    G, hits, paths, ic = closure_hits([0x005A75C0] + [x for x in st if x], clrs)
    out(sec, "D57 the same closure with every start-table entry as a root", functions=len(G), icalls=ic, hits=len(hits))
    for p in paths:
        note(p)
    Q.ref_line(sec, "D57 SKILLS_DoUsedSkill callers", 0x0056FC50)
    site_line(sec, "D57 MonSeqFrame: +0x4E = 4 runs the do untested; else bit 6 clear and code 1 or 2",
              [0x005A86ED, 0x005A86F1, 0x005A86F5, 0x005A86FD, 0x005A8703, 0x005A8706, 0x005A8709, 0x005A870B, 0x005A8710, 0x005A871A],
              [r"movzx eax,\[esi\+0x4e\]", r"cmp eax,0x4", r"je 0x5a8715", r"mov ecx,\[esi\+0xc4\]", r"shr ecx,0x6", r"and ecx,0x1",
               r"jne 0x5a871f", r"cmp eax,0x1", r"cmp eax,0x2", r"call 0x56fc50"])
    site_line(sec, "D57 MonAttackFrame: skill flag bit 0 clear or no step end runs the do with no bit-6 test",
              [0x005A7694, 0x005A7697, 0x005A76AB, 0x005A76AE, 0x005A76DF, 0x005A76E3],
              [r"test bl,0x1", r"je 0x5a76df", r"cmp eax,0x2", r"jne 0x5a76df", r"mov edx,esi", r"call 0x56fc50"])
    site_line(sec, "D57 MonAttackFrame's bit-6 test is behind `mode = 14`",
              [0x005A76C9, 0x005A76CD, 0x005A76CF, 0x005A76D5, 0x005A76DD, 0x005A76FA, 0x005A76FE],
              [r"cmp \[esi\+0x10\],0xe", r"jne 0x5a76fa", r"mov eax,\[esi\+0xc4\]", r"shr eax,0x6", r"je 0x5a76e8",
               r"cmp \[esi\+0x4e\],0x1", r"je 0x5a76df"])
    # C58: Smite
    sm = [v for v in body_set(0x005CE9F0) if "+0xc4]" in norm_ops(A().ins[v][1])]
    out(sec, "C58 do 150's own body: +0xC4 operands", sites=len(sm), bad=len(sm))
    G, hits, paths, ic = closure_hits([0x005CE9F0], sets)
    out(sec, "C58 do 150's direct-call closure against the 124 sets", functions=len(G), icalls=ic, hits=len(hits))
    for p in paths:
        note(p)
    # C14: do 10 and mdo 7
    site_line(sec, "C14 do 10: esi = the target unit, unwritten to the store",
              [0x005DB71B, 0x005DB720, 0x005DB798], [r"call 0x553540", r"mov \[ebp-0x10\],eax", r"mov esi,\[ebp-0x10\]"])
    wr = [x for x in listing(0x005DB79B, 0x005DB7F3) if (norm_ops(x[2]).startswith("esi,") and x[1] not in ("test", "cmp"))
          or (x[1] == "pop" and x[2] == "esi")]
    out(sec, "C14 esi writes between 0x005DB798 and the test", writes=len(wr), bad=len(wr))
    site_line(sec, "C14 do 10 writes 1 with a target, 2 without, through MISSDATA_SetSeedLow",
              [0x005DB7E8, 0x005DB7F3, 0x005DB7F5, 0x005DB7F7, 0x005DB7FB, 0x005DB7FD, 0x005DB7FE],
              [r"call 0x59fa30", r"test esi,esi", r"je 0x5db7fb", r"push 0x1", r"push 0x2", r"push ebx", r"call 0x64a710"])
    site_line(sec, "C14 SetSeedLow and GetSeedLow: the same MissileData+0x28 (unit+0x14)",
              [0x0064A71F, 0x0064A729, 0x0064A73F, 0x0064A746],
              [r"mov eax,\[eax\+0x14\]", r"mov \[eax\+0x28\],ecx", r"mov eax,\[eax\+0x14\]", r"mov eax,\[eax\+0x28\]"])
    site_line(sec, "C14 mdo 7 tests bit 0 of it", [0x005AE800, 0x005AE801, 0x005AE806, 0x005AE808],
              [r"push esi", r"call 0x64a730", r"test al,0x1", r"je 0x5ae882"])
    Q.ref_line(sec, "C14 MISSDATA_SetSeedLow callers (other writers of +0x28)", 0x0064A710)
    # D76 / D95: the Skills +0x05 flag bits
    srcs = skills_row_fns()
    for lab, mask, bit in (("D76 repeat (+0x05 bit 3)", 0x006CE274, 3), ("D95 Kick (+0x05 bit 1)", 0x006CE26C, 1)):
        rows = mask_tests(mask)
        out(sec, lab + " mask-form tests of [r+0x5]", sites=len(rows), server_range=sum(1 for v, *_ in rows if v >= 0x00540000),
            in_fn_with_skills_row=" ".join("0x%08X" % r[0] for r in rows if r[0] >= 0x00540000 and r[1] in srcs))
        for v, e, o, rt, src in rows:
            note("0x%08X %s test %s (r2 %s) skills_row_source=%d; row from %s" % (v, nm(v), o, rt, int(e in srcs), src))
    site_line(sec, "D76 MissileDoFrame's tested row is a Missiles row (stride 0x1A4, base +0xB64)", [0x005ADBD9, 0x005ADBDF, 0x005ADBE6, 0x005ADC43],
              [r"imul eax,eax,0x1a4", r"add eax,\[ecx\+0xb64\]", r"mov ebx,eax", r"test \[ebx\+0x5\],cl"])
    imm = imm_flag_tests()
    out(sec, "D76/D95 immediate forms (test/and [r+5] bit 3 or 1, [r+4] bit 11 or 9)", sites=len(imm),
        in_fn_with_skills_row=sum(1 for v, e, o in imm if e in srcs), bad=sum(1 for v, e, o in imm if e in srcs and v >= 0x00540000))
    site_line(sec, "D95 GetPhysMax's test", [0x00647D30, 0x00647D38], [r"mov al,\[0x6ce26c\]", r"test \[esi\+0x5\],al"])
    for t in (0x00647BC0, 0x00647D00):
        cs = Q.ref_line(sec, "D95 %s callers" % nm(t), t)
        var = []
        for s in cs:
            a, b, ag = args(s, 2)
            if a and len(a) > 1 and not a[1].isdigit() and T.owner(s)[0] != 0x005D54B0:
                var.append(s)
        out(sec, "D95 %s sites with a variable skill id, KickPhysDamage's apart" % nm(t), sites=len(var), bad=int(len(var) != 15))
    Q.ref_line(sec, "D95 SkillKickDamage callers", 0x00644C20, want=[0x00647D41])
    Q.ref_line(sec, "D95 SkillKickPhysDamage callers", 0x005D54B0)
    Q.ref_line(sec, "D95 DragonTalonHit callers", 0x005D5880)
    sd = [dword(0x00732140 + 4 * 2), dword(0x007322B0 + 4 * 2)]
    G, hits, paths, ic = closure_hits(sd, [s for t in (0x00647BC0, 0x00647D00) for s in Q.refs(t)[2]])
    out(sec, "D95 start 2 and do 2's direct-call closure against the GetPhysMin/Max sites", roots=" ".join(nm(x) for x in sd),
        functions=len(G), icalls=ic, hits=len(hits))
    for p in paths:
        note(p)
    hs, st_ = Q.tab("skills")
    sb = Q.binrecs("skills")
    kick = [i for i, r in enumerate(sb) if r.get("Kick")]
    kt = [i for i, r in enumerate(st_) if r.get("Kick") == "1"]
    out(sec, "D95 Kick rows (.bin, .txt)", bin=" ".join(map(str, kick)), txt=" ".join(map(str, kt)),
        bad=int(kick != [1, 255, 270, 275] or kick != kt))
    # D88: the EType stores
    ety = etype_stores()
    out(sec, "D88 byte stores of a Skills +0x1DC read (whole .text)", stores=len(ety),
        packet_base_found=sum(1 for *_, b in ety if b), bad=int(len(ety) != 15 or not all(b for *_, b in ety)))
    for va, st_va, o, e, b in ety:
        note("0x%08X -> 0x%08X %s in %s (symbol owner 0x%08X); packet base within -0x180..+0x100: %s" % (va, st_va, o, nm(st_va), e, b))
    rowsn = {"Concentrate": None, "Berserk": None, "Vengeance": None, "Power Strike": None}
    for i, r in enumerate(st_):
        if r.get("skill") in rowsn:
            rowsn[r["skill"]] = (i, r.get("EType"), sb[i].get("EType"), r.get("calc4"))
    out(sec, "D88 the named rows' EType (.txt, .bin) and calc4", rows=" | ".join("%s %s" % kv for kv in rowsn.items()),
        bad=int(any(v is None or not v[1] for v in rowsn.values())))
    BAD[sec] += sum(Q.BAD.values())
    Q.BAD.clear()


def skills_row_fns():
    """Functions (by re/symbols.csv owner) that make a Skills row: SKILLS_GetRecord, a 0x23C stride, the +0xB98 base."""
    s = set()
    for va, (mn, ops) in A().ins.items():
        o = norm_ops(ops)
        if (mn == "call" and S.branch_target(ops or "") == 0x0045C4B0) or (mn == "imul" and "0x23c" in o) or "+0xb98]" in o:
            s.add(T.owner(va)[0])
    return s


def mask_tests(mask):
    """`mov r8, [mask]` followed within four instructions by `test [x+0x5], r8`: (test va, owner, objdump, r2)."""
    vas = sorted(A().ins)
    idx = {v: i for i, v in enumerate(vas)}
    tag = "[0x%x]" % mask
    rows = []
    for va in vas:
        if tag in norm_ops(A().ins[va][1]):
            for j in range(idx[va] + 1, idx[va] + 5):
                m2, o2 = A().ins[vas[j]]
                if m2 == "test" and "+0x5]" in norm_ops(o2):
                    ot, rt, ag = site(vas[j])
                    src = "?"
                    for k in range(idx[va] - 1, idx[va] - 13, -1):
                        mk, ok = A().ins[vas[k]]
                        if mk in ("call", "imul"):
                            so, sr, sa = site(vas[k])
                            src = "0x%08X %s%s%s" % (vas[k], so, "" if sa else " [r2 %s]" % sr,
                                                     " (%s)" % nm(S.branch_target(ok)) if mk == "call" else "")
                            break
                    rows.append((vas[j], T.owner(va)[0], ot if ag else ot + " [r2 differs]", rt, src))
                    break
    return rows


def imm_flag_tests():
    r = []
    for va, (mn, ops) in A().ins.items():
        o = norm_ops(ops)
        m = re.search(r"\+0x([45])\],0x([0-9a-f]+)$", o)
        if mn in ("test", "and", "bt") and m:
            off, v = int(m.group(1), 16), int(m.group(2), 16)
            if (off == 5 and v & 0xA) or (off == 4 and v & 0xA00):
                r.append((va, T.owner(va)[0], o))
    return sorted(r)


def etype_stores():
    vas = sorted(A().ins)
    idx = {v: i for i, v in enumerate(vas)}
    res = []
    for va in vas:
        mn, ops = A().ins[va]
        o = norm_ops(ops)
        if mn == "mov" and o.split(",")[-1].endswith("+0x1dc]") and re.match(r"[abcd]l,", o):
            reg = o.split(",")[0]
            for j in range(idx[va] + 1, idx[va] + 4):
                m2, o2 = A().ins[vas[j]]
                o2 = norm_ops(o2)
                if m2 == "mov" and o2.endswith("," + reg) and o2.startswith("[ebp-"):
                    k = int(re.match(r"\[ebp-(0x[0-9a-f]+)\]", o2).group(1), 16)
                    base = "[ebp-0x%x]" % (k + 0x65)
                    e = T.owner(vas[j])[0]
                    b = [v for v, m3, o3 in listing(vas[j] - 0x180, vas[j] + 0x100) if base in norm_ops(o3)]
                    ot, rt, ag = site(vas[j])
                    res.append((va, vas[j], ot if ag else ot + " [r2 " + rt + "]", e,
                                "%s at %s" % (base, ",".join("0x%08X" % x for x in b[:2])) if b else None))
                    break
    return res


# ------------------------------------------------------------------------------------------------ part 2: more
PKT = 0x006E0D18  # g_SrvPacketTable: 8-byte records {handler, flag}


@section("more")
def sec_more():
    sec = "more"
    Q.BAD.clear()
    # D1 D2 D25: the skill packets
    py = [(dword(PKT + 8 * i), dword(PKT + 8 * i + 4)) for i in range(0x12)]
    rw = Q.r2_words(PKT, 2 * 0x12)
    agree = all(rw[2 * i] == py[i][0] for i in range(0x12))
    out(sec, "D1/D2/D25 g_SrvPacketTable 0x05..0x11 (python and r2)", r2_agree=int(agree), bad=int(not agree))
    want = {5: ("L", "XY", None), 6: ("L", "U", "1"), 7: ("L", "U", "0"), 0xC: ("R", "XY", None), 0xD: ("R", "U", "1"),
            0xE: ("R", "U", "0")}
    alt = {8: 5, 9: 6, 0xA: 7, 0xF: 0xC, 0x10: 0xD, 0x11: 0xE}
    LS, RS, RXY, RU, SXY, SU, SET = 0x00620190, 0x006201D0, 0x005496F0, 0x00549830, 0x00549AD0, 0x00549BA0, 0x00627260
    bad = 0
    for i in range(5, 0x12):
        h = py[i][0]
        cl = fn_calls(h)
        ts = [t for _, t in cl]
        tx = ", ".join(nm(t) for t in ts)
        if i in want:
            side, form, walk = want[i]
            ok = (LS if side == "L" else RS) in ts and (RXY if form == "XY" else RU) in ts and (SXY if form == "XY" else SU) in ts
            st = [va for va, t in cl if t == SET]
            a = args(st[0], 3)[0] if st else None
            ok = ok and a is not None and a[1] == "328"
            if walk is not None:
                su = [va for va, t in cl if t == SU][0]
                ok = ok and args(su, 4)[0][3] == walk
            note("0x%02X %s: %s; stat set %s%s" % (i, nm(h), tx, a, "" if walk is None else ", walk %s" % walk))
        elif i in alt:
            tgt = py[alt[i]][0]
            ok = tgt in ts and (RXY if alt[i] in (5, 0xC) else RU) in ts and (LS if i < 0xC else RS) in ts
            note("0x%02X %s: %s (-> 0x%02X)" % (i, nm(h), tx, alt[i]))
        else:
            ok = not ts and not [v for v in fn_body(h)[0] if A().ins[v][0] == "mov" and norm_ops(A().ins[v][1]).startswith("[")]
            note("0x%02X %s: no call, no store" % (i, nm(h)))
        bad += 0 if ok else 1
    out(sec, "D1/D2/D25 handlers: side, form, stat 328, walk, re-read", handlers=0x11 - 5 + 1, bad=bad)
    site_line(sec, "D25 left and right entries: SkillList+0x08 and +0x0C", [0x006201B9, 0x00643953],
              [r"mov ecx,\[eax\+0xa8\]", r"mov eax,\[ecx\+0x8\]"])
    rsk = [v for v in fn_body(0x006201D0)[0] if A().ins[v][0] == "call"]
    for v in rsk:
        t = S.branch_target(A().ins[v][1])
        if t and t not in (0x00408090, 0x00408A60, 0x00681E09):
            note("GetRightSkill calls %s" % nm(t))
            for x in listing(t, t + 0x30):
                if x[1] == "mov" and norm_ops(x[2]).startswith("eax,[ecx+"):
                    site_line(sec, "D25 the right entry's read", [x[0]], [r"mov eax,\[ecx\+0xc\]"])
                    break
    site_line(sec, "D25 the location form: 5 bytes, x u16 +1, y u16 +3", [0x005496F9, 0x00549734, 0x00549739],
              [r"cmp \[ebp\+0xc\],0x5", r"movzx eax,\[ebx\+0x3\]", r"movzx edi,\[ebx\+0x1\]"])
    site_line(sec, "D25 the unit form: 9 bytes, type u32 +1 below 6, guid u32 +5", [0x00549833, 0x00549855, 0x00549859, 0x0054985C, 0x0054985F],
              [r"cmp \[ebp\+0xc\],0x9", r"mov ebx,\[eax\+0x5\]", r"mov esi,\[eax\+0x1\]", r"cmp esi,0x6", r"jb 0x54986c"])
    # D50: noCost
    cs = Q.ref_line(sec, "D50 SKILLS_SrvStart callers", 0x0056F640)
    one = []
    for s in cs:
        a, b, ag = args(s, 3)
        note("0x%08X %s noCost %s%s" % (s, nm(s), a[2] if a and len(a) > 2 else None, "" if ag else " [r2 %s]" % b))
        if a and len(a) > 2 and a[2] != "0":
            one.append(nm(s).split("+")[0])
    out(sec, "D50 callers passing a non-zero noCost", callers=len(cs), nonzero=" ".join(one), bad=int(one != ["ITEMSKILL_Cast"]))
    # D137: PreventHealHook
    site_line(sec, "D137 the hook's tests and its block", [0x0057D81A, 0x0057D823, 0x0057D825, 0x0057D82C, 0x0057D834, 0x0057D838,
                                                          0x0057D83B, 0x0057D840, 0x0057D842, 0x0057D847, 0x0057D879, 0x0057D880,
                                                          0x0057D88A, 0x0057D891],
              [r"cmp \[edi\],0x0", r"mov eax,\[esi\]", r"cmp eax,0x1", r"push 0x75", r"test eax,eax", r"mov eax,\[esi\+0x4\]",
               r"cmp eax,0x2c0", r"jl 0x57d849", r"cmp eax,0x2c5", r"jle 0x57d896", r"mov \[ebp-0x14\],0x1d4c0",
               r"mov \[ebp-0x10\],0x1f", r"mov \[ebp-0x8\],0x34", r"call 0x56e970"])
    site_line(sec, "D137 ToHitRoll: edi = ebx, esi = [ebp-0xc] at the hook's call", [0x0057DB7B, 0x0057DB7E, 0x0057DB80],
              [r"mov esi,\[ebp-0xc\]", r"mov edi,ebx", r"call 0x57d810"])
    # C57: Smite's monster branch
    site_line(sec, "C57 Smite's monster branch: mode 5 to MonAttackStats, the test's word kept",
              [0x005CEBB6, 0x005CEBBD, 0x005CEBE4, 0x005CEBE9, 0x005CEBEB, 0x005CEBA8, 0x005CEBB0, 0x005CEBB4],
              [r"mov edx,0x5", r"call 0x5a4f50", r"call 0x57ec10", r"test al,0x1", r"mov \[ebp-0x84\],ax", r"call 0x57ec10",
               r"or ax,0x1", r"jmp 0x5cebe9"])
    site_line(sec, "C57 MonAttackStats: edx is the mode, 5 tested first, then 7..8",
              [0x005A4F5B, 0x005A5015, 0x005A5018, 0x005A501B, 0x005A5021, 0x005A5026, 0x005A50D0, 0x005A5042, 0x005A5084],
              [r"mov \[ebp-0x24\],edx", r"mov eax,\[ebp-0x24\]", r"cmp eax,0x5", r"je 0x5a50b9", r"cmp eax,0x6", r"cmp eax,0x8",
               r"push 0x10", r"push 0x20", r"push 0x8"])
    # C74 C75: the knockback level difference
    for lab, ent, tgt, pushes, rr in (("C74 do 42", 0x005D5A30, 0x005D5A74, [0x005D5AE3, 0x005D5AF4], "edi"),
                                       ("C75 do 33", 0x005D3140, 0x005D31A3, [0x005D31D8, 0x005D31E2], "ebx")):
        site_line(sec, "%s: target from UNIT_GetTargetUnit" % lab, [{0x005D5A74: 0x005D5A6F, 0x005D31A3: 0x005D3196}[tgt], tgt], [r"call 0x553540", r"mov %s,eax" % rr])
        site_line(sec, "%s: both stat-12 reads push the target" % lab, pushes, [r"push %s" % rr] * 2)
        ws = [v for v in fn_body(ent)[0] if norm_ops(A().ins[v][1]).startswith(rr + ",") and A().ins[v][0] in ("mov", "lea", "xchg")
              and tgt < v < pushes[1]]
        out(sec, "%s: %s writes between the target and the second push" % (lab, rr), writes=len(ws), bad=len(ws))
        call_args_line(sec, "%s stat reads" % lab, ent, {0x00625480}, 3)
    site_line(sec, "C74 the difference: s1 + [ebp+0xc] (the level) - s2", [0x005D5AFC, 0x005D5AFF, 0x005D5B01],
              [r"mov ecx,\[ebp\+0xc\]", r"add esi,ecx", r"sub esi,eax"])
    site_line(sec, "C75 the difference", [0x005D31EA, 0x005D31ED, 0x005D31EF], [r"mov edx,\[ebp\+0xc\]", r"add esi,edx", r"sub esi,eax"])
    # C108: the rings' step
    for lab, ent, ld, lp in (("prg 37 ring", 0x005D4150, 0x005D43A1, 0x005D4605), ("prg 143 ring", 0x005D4870, None, 0x005D4D25)):
        ed = [(v, A().ins[v][0], norm_ops(A().ins[v][1])) for v in fn_body(ent)[0] if "edi" in norm_ops(A().ins[v][1])]
        out(sec, "C108 %s: every edi operand" % lab, sites=len(ed),
            tests=sum(1 for _, m, o in ed if m in ("test", "cmp") or (m.startswith("j"))), bad=sum(1 for _, m, o in ed if m in ("test", "cmp")))
        for v, m, o in ed:
            note("0x%08X %s %s" % (v, m, o))
        site_line(sec, "C108 %s loop" % lab, [lp, lp + 2, lp + 4, lp + 0x68, lp + 0x6A, lp + 0x70] if ent == 0x005D4150 else
                  [lp, lp + 2, lp + 4, lp + 0x75, lp + 0x77, lp + 0x7D],
                  [r"add edi,edi", r"add edi,edi", r"xor esi,esi", r"add esi,edi", r"cmp esi,0x100", r"jl "])
    for prg, ring in ((0x005D4E70, 0x005D4150), (0x005D4F40, 0x005D4870)):
        call_args_line(sec, "C108 %s's ring call (8 stack args, the calc last)" % nm(prg), prg, {ring}, 8)
    # M5: types 4, 10, 14
    import sweep2_s7a as W
    G = W.graph2([0x0067A140])
    mem = [v for v in fn_body(0x0067A140)[0] if "[" in A().ins[v][1] and not re.search(r"\[(ebp|esp)", norm_ops(A().ins[v][1]))]
    out(sec, "M5 PathPlanSpiral: closure and non-stack memory operands", functions=len(G),
        callees=" ".join(nm(e) for e in G if e != 0x0067A140), mem=len(mem))
    for v in mem:
        ot, rt, ag = site(v)
        note("0x%08X %s%s" % (v, ot, "" if ag else " [r2 %s]" % rt))
    # M23: useAmmo
    shared = {0x0056F524: 0x0056F4F7, 0x0056F614: 0x0056F5E7, 0x0056FA29: 0x0056F9FD, 0x005CE08B: 0x005CE050,
              0x005CE18B: 0x005CE150, 0x005D8952: 0x005D892F}
    site_line(sec, "M23 the shared useAmmo pushes", sorted(shared.values()),
              [r"push 0x%d" % (0 if p in (0x0056F9FD, 0x005CE050, 0x005CE150) else 1) for p in sorted(shared.values())])
    vals = {}
    for t in (0x0056ECB0, 0x0056EE90):
        for s in Q.ref_line(sec, "M23 %s callers" % nm(t), t):
            a, b, ag = args(s, 8)
            v = a[7] if a and len(a) > 7 else None
            if s in shared:
                v = "1" if shared[s] not in (0x0056F9FD, 0x005CE050, 0x005CE150) else "0"
            vals[s] = v
            note("0x%08X %s useAmmo %s (pad entry 0x%08X)" % (s, nm(s), v, T.pad_entry(s)))
    ones = sorted(s for s, v in vals.items() if v == "1")
    out(sec, "M23 useAmmo values", sites=len(vals), ones=len(ones), zeros=sum(1 for v in vals.values() if v == "0"),
        unresolved=sum(1 for v in vals.values() if v not in ("0", "1")), bad=int(len(vals) != 33 or len(ones) != 14))
    mon = [s for s in ones if 0x005A0000 <= s < 0x005A8000]
    hold = []
    for s in mon:
        for e in (0x005A2620, 0x005A2840, 0x005A2C20, 0x005A3F30, 0x005A6D50, 0x005A6FF0):
            if s in body_set(e):
                hold.append(e)
                break
    out(sec, "M23 the monster sites' recursive-descent bodies", sites=len(mon), bodies=len(set(hold)),
        entries=" ".join("0x%08X" % e for e in hold))
    site_line(sec, "M23 SKILL_AttackDo: 27 (magicarrow) takes the 0 site", [0x0056F0B6, 0x0056F0BB, 0x0056F0BE, 0x0056F0C6],
              [r"call 0x645f00", r"cmp eax,0x1b", r"je 0x56f0e9", r"push 0x1"])
    site_line(sec, "M23 Throw and Left Hand Throw: item type 38 takes the lob", [0x0056F4EB, 0x0056F4F0, 0x0056F501, 0x0056F510, 0x0056F524],
              [r"push 0x26", r"call 0x629bb0", r"je 0x56f517", r"call 0x56ee90", r"call 0x56ecb0"])
    site_line(sec, "M23 the player-owner gates", [0x0056EDA1, 0x0056EDA7, 0x0056EDB0, 0x0056EF44, 0x0056EF4A, 0x0056EF53, 0x0056C406],
              [r"cmp \[ebp\+0x24\],0x0", r"cmp \[esi\],0x0", r"call 0x56c3f0", r"cmp \[ebp\+0x24\],0x0", r"cmp \[esi\],0x0",
               r"call 0x56c3f0", r"cmp \[edi\],0x0"])
    # M25: MissileCreate's callers
    mc = Q.ref_line(sec, "M25 MissileCreate callers", 0x0059FA30)
    own = collections.Counter(nm(s).split("+")[0] for s in mc)
    outside = [s for s in mc if s not in body_set(T.owner(s)[0])]
    out(sec, "M25 the sites' owners", sites=len(mc), symbol_owners=len(own), sites_outside_their_owner_body=len(outside),
        item_owners=" ".join(n for n in own if n.startswith(("ITEM", "INV"))) or "none")
    note("owners: " + " ".join("%s:%d" % kv for kv in sorted(own.items())))
    # M48 / R22: the 0x40 marks
    import csv
    coll = [(int(r[0], 16), r[2]) for r in csv.reader(open(os.path.join(HERE, "..", "re", "symbols.csv")))
            if r and r[0].startswith("0x") and r[2].startswith("COLL_")]
    found = []
    for e, n in coll:
        for s in Q.refs(e)[2]:
            a, b, ag = args(s, 5)
            if a and any(x.isdigit() and int(x) & 0x40 and int(x) < 0x10000 for x in a):
                found.append((s, n, a, ag))
    out(sec, "M48 calls of the COLL_ functions with a constant mask holding 0x40", coll_functions=len(coll), sites=len(found),
        server_range=sum(1 for s, *_ in found if s >= 0x00540000))
    for s, n, a, ag in found:
        note("0x%08X %s %s(%s)%s" % (s, nm(s), n, ", ".join(a), "" if ag else " [walkers differ]"))
    site_line(sec, "M48 HitUnit's unmark (push before the size calls)", [0x005AE1B1, 0x005AE1CB], [r"push 0x40", r"call 0x64eba0"])
    site_line(sec, "M48 MissileCreate: a Collision row's path mark mask is 0x40", [0x0059FD54, 0x0059FD5B, 0x0059FD5D, 0x0059FD61, 0x0059FD64],
              [r"cmp \[edx\+0x184\],0x0", r"je 0x59fd61", r"push 0x40", r"push 0x0", r"call 0x648c30"])
    pm = Q.ref_line(sec, "M48 PATH_SetMarkMask callers", 0x00648C30)
    pv = []
    for s in pm:
        a, b, ag = args(s, 2)
        if a and len(a) > 1 and (not a[1].isdigit() or int(a[1]) & 0x40):
            pv.append("0x%08X %s %s" % (s, nm(s), a[1]))
    note("callers with a variable or 0x40 mask: " + "; ".join(pv))
    ct = [(dword(0x0073C720 + 8 * i), dword(0x0073C724 + 8 * i)) for i in range(9)]
    out(sec, "M48 g_MissileCollideTypes masks holding 0x40", types=" ".join(str(i) for i, (f, m) in enumerate(ct) if m & 0x40))
    # M70: ExplosionMissile (+0x016)
    mrow = set()
    for va, (mn, ops) in A().ins.items():
        o = norm_ops(ops)
        if (mn == "call" and S.branch_target(ops or "") == 0x0046ACE0) or (mn == "imul" and "0x1a4" in o) or "+0xb64]" in o:
            mrow.add(T.owner(va)[0])
    w16 = []
    for va, (mn, ops) in sorted(A().ins.items()):
        o = norm_ops(ops)
        if re.search(r"\+0x16\]", o) and "word" in (ops or "").lower() and (
                (mn in ("mov", "movzx", "movsx") and not o.startswith("[")) or mn in ("cmp", "test")):
            w16.append(va)
    srv = [v for v in w16 if 0x00540000 <= v < 0x00680000]
    out(sec, "M70 word operands at +0x16 (objdump), server range, in a function that makes a Missiles row", sites=len(w16),
        server_range=len(srv), server_in_missile_row_fn=sum(1 for v in srv if T.owner(v)[0] in mrow),
        client_in_missile_row_fn=" ".join("0x%08X" % v for v in w16 if v < 0x00540000 and T.owner(v)[0] in mrow),
        bad=sum(1 for v in srv if T.owner(v)[0] in mrow))
    site_line(sec, "M70 the server-range sites, decoded twice", srv, None)
    # M94: BuildDamage
    G = W.graph2([0x005A89A0])
    out(sec, "M94 MISSILE_BuildDamage's closure", functions=len(G), icalls=sum(len(v[4]) for v in G.values() if v),
        item_or_owner=" ".join(nm(e) for e in G if re.search(r"ITEM|INV|Owner|Weapon", nm(e))) or "none")
    rows = call_args_line(sec, "M94 BuildDamage's stat reads", 0x005A89A0, {0x00625480, 0x00625500, 0x006253B0, 0x005A8910}, 2)
    out(sec, "M94 every read on esi", reads=len(rows), not_esi=sum(1 for r in rows if "(esi," not in r), bad=sum(1 for r in rows if "(esi," not in r))
    ws = [v for v in fn_body(0x005A89A0)[0] if norm_ops(A().ins[v][1]).startswith("esi,") and A().ins[v][0] in ("mov", "lea", "xchg")]
    out(sec, "M94 esi writes in BuildDamage", writes=" ".join("0x%08X" % v for v in ws), bad=int(ws != [0x005A89B9]))
    site_line(sec, "M94 esi is the first stack argument; HitUnit pushes edi there", [0x005A89B9], [r"mov esi,\[ebp\+0x8\]"])
    call_args_line(sec, "M94 HitUnit's BuildDamage call", 0x005ADF10, {0x005A89A0}, 1)
    call_args_line(sec, "M94 MissileElemRoll's stat reads", 0x005A8910, {0x00625480}, 1)
    ents = sorted(set(dword(0x0073C960 + 4 * i) for i in range(31)) - {0})
    G2 = W.graph2(ents)
    out(sec, "M94 the damage-table entries' closure (the remainder)", entries=len(ents), functions=len(G2),
        icalls=sum(len(v[4]) for v in G2.values() if v), owner_fns=" ".join(nm(e) for e in G2 if "Owner" in nm(e)))
    # R24: the two critical chains
    Q.ref_line(sec, "R24 MissileCritRoll references", 0x0064A850, kinds=("call", "jmp", "jcc"))
    Q.ref_line(sec, "R24 MissileDamageBlock references", 0x0064B860, kinds=("call", "jmp", "jcc"))
    G3 = W.graph2([0x0057B7D0])
    out(sec, "R24 COMBAT_BuildDamage's closure", functions=len(G3), icalls=sum(len(v[4]) for v in G3.values() if v),
        reaches_MissileCritRoll=int(0x0064A850 in G3), reaches_MissileDamageBlock=int(0x0064B860 in G3),
        bad=int(0x0064A850 in G3 or 0x0064B860 in G3))
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

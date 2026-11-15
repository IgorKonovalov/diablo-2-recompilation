"""Plan 0066 batch S5b (combat): static second sources for the 24 class-c rows. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s5b.py <section> [<section> ...]
  python3 -I tools/sweep2_s5b.py all

Sections (the inventory rows each serves are in the check names):
  callers   raw-byte call/abs32 scans (tools/xrefscan.py) of the named functions, each site decoded by r2; r2 reads of
            the branches and pushes the rows name (README 3, 8; to-hit 2, 13, 19; delivery 1, 26, 29, 38, 54, 65, 66)
  stats     the stat ids pushed to the stat readers in the to-hit, damage and reduction functions (objdump bodies, r2
            for the pushes), and the reduction table at 0x00732980 read with r2 (to-hit 4, damage 2, reductions 1)
  stores    store scans over the objdump listing: packet +0x38/+0x3C/+0x40 and +0x65/+0x68 in every function that
            hands a packet to COMBAT_BuildDamage or COMBAT_ResolveAndQueue, the callers' zeroing of the packet
            (README 4's remainder), the EType loads, the item-flag writers against 0x0062A4E0, the MonLvlStats /
            MonAttackStats output pair (damage 17, 27, 32; to-hit 21)
  tables    full-table checks over the excel .txt tables (States meleeonly and row 54, Skills ItemEffect,
            srvprgfunc1-3 / prgstack, the event columns of Skills and ItemStatCost, MonStats noRatio x El)
            (README 8; to-hit 19; damage 19, 32; delivery 20, 21, 38)
  closures  the direct-call closures of the 31 stat-event handlers (g_StatEventFuncs, read with r2) and of the
            item-target helpers 3, 4 and 0x0056E390, walked over the objdump listing with every code pointer an
            instruction takes as an immediate added as an edge; draws = inline LCG sites (objdump and r2's own byte
            search) and calls of the RNG primitives (delivery 50, 51; damage 19's handler 3)

Each section prints `S5b <section> <check> key=value ...` lines and detail lines; `bad=` counts an observation that
contradicts the statement the check tests. Stdlib only, plus objdump (through tools/sweep_s4b.py) and r2. Read-only.
The record is findings/combat/0001 § "Plan 0066 batch S5b".
"""
import collections
import re
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402
import sweep2_s4cd as T  # noqa: E402

S.RNG_FNS.setdefault(0x00472280, "RNG_RangeOffset")
S.RNG_FNS.setdefault(0x004BC500, "RNG_RandLoHi")


class Rep(T.Rep):
    def done(self):
        if "bad" not in self.c:
            self.c["bad"] += 0
        print("S5b %s %s %s" % (self.sec, self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return self.c["bad"]


def nm(va):
    e, n = T.owner(va)
    return n if e == va else "%s+0x%X" % (n, va - e)


def r2ins(va):
    """r2's decoding of the one instruction at va: (mnemonic, operands)."""
    for ln in T.r2("pd 1 @ 0x%x" % va).splitlines():
        m = T.R2_LINE.match(ln)
        if m and int(m.group(1), 16) == va:
            return m.group(2), m.group(3)
    return None, None


def call_sites(tgt):
    """Raw-byte call sites of tgt, each confirmed by r2's decoding as `call tgt`; (sites, abs32 refs, r2 mismatches)."""
    rel, calls, ab = T.raw(tgt)
    bad = [s for s in calls if r2ins(s) != ("call", "0x%x" % tgt)]
    return calls, ab, bad, len(rel) - len(calls)


KNOWN_ENTRIES = (0x005D8B10,)   # skills/0001 § 11, skills/0003 § 12: the helper of do 75


def entry_of(site):
    """The function entry whose objdump body holds site: the symbol's, else the int3-padding guess."""
    A = S.asm()
    e = T.owner(site)[0]
    if site in S.body(A, e)[0]:
        return e
    for k in KNOWN_ENTRIES:   # entries the findings name that neither the symbols nor int3 padding give
        if k < site < k + 0x400 and site in S.body(A, k)[0]:
            return k
    p = T.pad_entry(site)
    if p and site in S.body(A, p)[0]:
        return p
    # a function that follows the previous one's `ret` with no padding: the nearest such start whose body holds site
    for va, (mn, ops) in reversed(list(A.range(site - 0x400, site))):
        if mn.startswith("ret"):
            a = A.next_va(va)
            if a and site in S.body(A, a)[0]:
                return a
    return None


# ============================================================================================================ callers
def chk_callers():
    bad = 0
    A = S.asm()

    # README 3: the callers of COMBAT_MeleeHitTest
    r = Rep("callers", "readme3_meleehittest_callers")
    calls, ab, mism, other = call_sites(0x0057EC10)
    r.add("call_sites", len(calls)); r.add("abs32", len(ab)); r.add("r2_mismatch", len(mism)); r.add("other_rel", other)
    fns = collections.OrderedDict()
    for s in calls:
        fns.setdefault(T.owner(s)[1], []).append(s)
    r.add("functions", len(fns))
    if 0x005C7712 not in calls or ab or mism or other:
        r.add("bad")
    for n, ss in fns.items():
        r.note("%s: %s" % (n, " ".join("0x%08X" % s for s in ss)))
    bad += r.done()

    # README 8: SKILL_AttackDo's meleeonly branch and UNIT_HasStateFlag's set table
    r = Rep("callers", "readme8_meleeonly_branch")
    want = {0x0056F19A: ("push", "0x26"), 0x0056F19C: ("push", "esi"), 0x0056F19D: ("call", "0x63a7b0"),
            0x0056F1A4: ("je", "0x56f1bc"), 0x0056F1AE: ("call", "0x56c2d0"), 0x0056F1B9: ("ret", "8"),
            0x0056F1CE: ("call", "0x5d5220"), 0x0056F1DA: ("call", "0x57d4f0"),
            0x0063A7BD: ("cmp", "ecx, 0x27"), 0x0063A7C9: ("mov", "ebx, dword [edx + ecx*4 + 0xcc]"),
            0x0063A7D0: ("call", "0x63a130"), 0x00618C12: ("mov", "dword [esi*4 + 0x96bcfc], ecx"),
            0x00618C19: ("call", "0x611d60"), 0x00618C27: ("cmp", "esi, 0x28"),
            0x00611D82: ("lea", "esi, [edx + esi + 0x10]")}
    for va, w in sorted(want.items()):
        got = r2ins(va)
        r.add("ins")
        if got != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, got, w))
    calls, ab, mism, other = call_sites(0x0056C2D0)
    r.add("deliver_meleeonly_callers", len(calls))
    if calls != [0x0056F1AE] or ab:
        r.add("bad")
    r.note("DataTables at [0x744304] = 0x%08X; set 38 at +0xCC + 4*38 = 0x%08X" % (S.dword(0x00744304), 0x0096BCFC + 4 * 38))
    bad += r.done()

    # to-hit 2: ToHitRoll / DefenceRoll / AvoidRoll callers
    r = Rep("callers", "tohit2_missile_tohit_defence")
    exp = {0x0057D9B0: {0x0057ECCD, 0x005AE06F, 0x005A88FB}, 0x0057DFB0: {0x0057ECE8, 0x005AD806, 0x0056BA0D},
           0x0057DD60: {0x0057DFC8, 0x0057DFEA, 0x0057E072}}
    for tgt, ws in exp.items():
        calls, ab, mism, other = call_sites(tgt)
        r.add("sites_%s" % T.owner(tgt)[1], len(calls))
        if set(calls) != ws or ab or mism:
            r.add("bad")
        for s in calls:
            r.note("%s <- 0x%08X in %s (entry 0x%08X)" % (T.owner(tgt)[1], s, nm(s), entry_of(s) or 0))
    # the unnamed function at 0x005A88E0 that holds 0x005A88FB: no caller and no pointer
    calls, ab, mism, other = call_sites(0x005A88E0)
    r.add("fn_005A88E0_callers", len(calls)); r.add("fn_005A88E0_abs32", len(ab))
    r.add("fn_005A88E0_jmp", other)
    if calls or ab or other or T.pad_entry(0x005A88FB) != 0x005A88E0:
        r.add("bad")
    bad += r.done()

    # to-hit 13: the two other attack-rating computations
    r = Rep("callers", "tohit13_other_ar")
    calls, ab, mism, other = call_sites(0x00583740)
    r.add("arcalc_calls", len(calls)); r.add("arcalc_abs32", len(ab))
    if calls != [0x00583893] or ab or T.owner(0x00583893)[0] != 0x00583840:
        r.add("bad")
    c2, ab2, _, o2 = call_sites(0x00583840)
    r.add("shrine_statvalue_calls", len(c2)); r.add("shrine_statvalue_abs32", len(ab2))
    for s in c2:
        r.note("SHRINE_StatValue <- 0x%08X in %s" % (s, nm(s)))
    c3, ab3, _, o3 = call_sites(0x004E9040)
    r.add("client_calls", len(c3)); r.add("client_jmps", o3); r.add("client_abs32", len(ab3))
    if c3 or o3 or ab3 != [0x0072D80C]:
        r.add("bad")
    tbl = S.dwords(0x0072D7FC, 5)
    r.note("the pointer at 0x0072D80C sits in a .rdata run of client functions: %s" % " ".join("0x%08X" % x for x in tbl))
    for v in tbl:
        if not (0x004E0000 <= v < 0x004F0000):
            r.add("bad")
    refs = [(0x0072D7FC + 4 * k, s) for k in range(-1, 6) for s in T.raw(0x0072D7FC + 4 * k)[2]]
    r.add("abs32_refs_to_the_run", len(refs))
    for a, s in refs:
        r.note("0x%08X referenced at 0x%08X (int3-padding entry 0x%08X)" % (a, s, T.pad_entry(s) or 0))
        if not (0x004E0000 <= s < 0x004F0000):
            r.add("bad")
    bad += r.done()

    # to-hit 19: the range-test call and the state-54 test in COMBAT_MeleeHitTest
    r = Rep("callers", "tohit19_range_and_state54")
    for va, w in ((0x0057ECA6, ("call", "0x622c40")), (0x0057ED2C, ("push", "0x36")), (0x0057ED2E, ("push", "edi")),
                  (0x0057ED2F, ("call", "0x639df0")), (0x0057ED38, ("or", "ebx, 4")), (0x0057EC97, ("call", "0x622870"))):
        got = r2ins(va)
        r.add("ins")
        if got != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, got, w))
    bad += r.done()

    # delivery 1, 29: COMBAT_GetHit -> sub_0057CCB0_UnitKilled, and the drop path's direct calls
    r = Rep("callers", "delivery1_29_unitkilled")
    for va, w in ((0x0057D001, ("test", "al, 2")), (0x0057D003, ("je", "0x57d01d")), (0x0057D00F, ("call", "0x57ccb0"))):
        got = r2ins(va)
        r.add("ins")
        if got != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, got, w))
    calls, ab, mism, other = call_sites(0x0057CCB0)
    r.add("unitkilled_calls", len(calls)); r.add("unitkilled_abs32", len(ab))
    if 0x0057D00F not in calls or ab or mism:
        r.add("bad")
    r.note("UnitKilled <- " + " ".join("0x%08X(%s)" % (s, T.owner(s)[1]) for s in calls))
    for tgt in (0x005A6600, 0x005A6830, 0x005A6FF0):
        c, a, _, o = call_sites(tgt)
        r.add("calls_%s" % T.owner(tgt)[1], len(c)); r.add("abs32_%s" % T.owner(tgt)[1], len(a))
        r.note("%s <- calls %s abs32 %s" % (T.owner(tgt)[1], ["0x%08X(%s)" % (s, T.owner(s)[1]) for s in c],
                                             ["0x%08X" % x for x in a]))
    bad += r.done()

    # delivery 26: UNIT_AddEvent's head insert and UNIT_DispatchEvent's walk
    r = Rep("callers", "delivery26_event_list")
    for va, w in ((0x005C0B1E, ("mov", "ecx, dword [esi + 0x90]")), (0x005C0B27, ("mov", "dword [eax + 0x1c], ecx")),
                  (0x005C0B3D, ("mov", "dword [ecx + 0x18], eax")), (0x005C0B40, ("mov", "dword [esi + 0x90], eax")),
                  (0x005C0C4B, ("mov", "esi, dword [eax + 0x90]")), (0x005C0C6E, ("mov", "edi, dword [esi + 0x1c]")),
                  (0x005C0C8E, ("call", "eax")), (0x005C0C96, ("mov", "edi, dword [esi + 0x1c]"))):
        got = r2ins(va)
        r.add("ins")
        if got != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, got, w))
    calls, ab, mism, other = call_sites(0x005C0AD0)
    r.add("addevent_calls", len(calls)); r.add("addevent_abs32", len(ab))
    r.note("UNIT_AddEvent <- " + " ".join("0x%08X(%s)" % (s, T.owner(s)[1]) for s in calls))
    # the walk's continuation: after the handler, the loop goes on with the saved +0x1C (next, older)
    vas, cl, ic = S.body(A, 0x005C0C30)
    nxt = sorted(va for va in vas if "+0x1c]" in A.ins[va][1])
    r.note("DispatchEvent reads of +0x1C: %s" % " ".join("0x%08X %s %s" % (v, A.ins[v][0], A.ins[v][1]) for v in nxt))
    stores90 = [va for va in vas if A.ins[va][0] == "mov" and "+0x90]," in A.ins[va][1]]
    r.add("dispatch_head_stores", len(stores90))
    r.note("DispatchEvent stores to +0x90 (unlinking the head): %s" % " ".join("0x%08X" % v for v in stores90))
    bad += r.done()

    # delivery 38: the record's +0x0C from the item-stat registrar and the handler's arguments
    r = Rep("callers", "delivery38_handler_args")
    for va, w in ((0x0055B81E, ("mov", "edi, dword [ebp + 0xc]")), (0x0055B823, ("shr", "ebx, 0x10")),
                  (0x0055B883, ("movsx", "ecx, word [ebx + 0x4c]")), (0x0055B887, ("movsx", "edx, word [ebx + 0x48]")),
                  (0x0055B893, ("push", "edi")), (0x0055B897, ("call", "0x56e740")),
                  (0x0056E74B, ("mov", "eax, dword [eax*4 + 0x7325b0]")), (0x0056E75B, ("mov", "esi, dword [ebp + 0x18]")),
                  (0x0056E764, ("mov", "eax, dword [ebp + 0xc]")), (0x0056E76C, ("call", "0x5c0ad0")),
                  (0x005C0AF7, ("mov", "edx, dword [ebp + 0xc]")), (0x005C0B0D, ("mov", "byte [eax], cl")),
                  (0x005C0B12, ("mov", "dword [eax + 0xc], edx")), (0x005C0B1B, ("mov", "dword [eax + 0x14], edx")),
                  (0x005C0C73, ("mov", "ecx, dword [esi + 0x10]")), (0x005C0C7C, ("mov", "ecx, dword [esi + 0xc]")),
                  (0x005C0C80, ("mov", "ecx, dword [ebp + 0x10]")), (0x005C0C84, ("mov", "ecx, dword [ebp + 0xc]")),
                  (0x005C0C88, ("push", "eax")), (0x0057C7C6, ("push", "ebx")), (0x0057C7C7, ("mov", "edx, 6")),
                  (0x0057C7CC, ("call", "0x5c0c30")), (0x0057C7DB, ("push", "edi")), (0x0057C7DC, ("push", "esi")),
                  (0x0057C7DD, ("push", "ebx")), (0x0057C7DE, ("mov", "edx, 5")), (0x0057C7E3, ("call", "0x5c0c30")),
                  (0x0057C6C8, ("mov", "esi, dword [ebp + 8]")), (0x0057C6CC, ("mov", "ebx, edx")),
                  (0x0057C6DC, ("mov", "edi, dword [ebp + 0x10]"))):
        got = r2ins(va)
        r.add("ins")
        if got != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, got, w))
    r.note("g_StatEventFuncs[14..16] = %s" % " ".join("0x%08X" % x for x in S.dwords(0x007325B0 + 4 * 14, 3)))
    calls, ab, mism, other = call_sites(0x0056E740)
    r.add("addstatevent_calls", len(calls)); r.add("addstatevent_abs32", len(ab))
    r.note("AddStatEvent <- " + " ".join("0x%08X(%s)" % (s, T.owner(s)[1]) for s in calls))
    bad += r.done()

    # delivery 20, 54, 66: the item effect flag
    r = Rep("callers", "delivery20_54_66_effect_flag")
    sd, sab, smm, so = call_sites(0x0056F7F0)
    r.add("srvdo_calls", len(sd)); r.add("srvdo_abs32", len(sab)); r.add("srvdo_jmps", so)
    pop = T.callee_pop(0x0056F7F0)
    r.add("srvdo_ret_bytes", pop)
    for s in sd:
        p = T.pushes_before(s, want=5) or []
        fifth = p[4] if len(p) > 4 else None
        r.note("SrvDo <- 0x%08X %s fifth word %s (pushes %s)" % (s, nm(s), fifth, p[:5]))
        if s == 0x005FDC2F:
            continue
        if fifth not in ("0", "eax"):
            r.add("bad")
    # 0x0056FD34's fifth word is EAX after `test eax, eax; jne`
    for va, w in ((0x0056FD25, ("test", "eax, eax")), (0x0056FD27, ("jne", "0x56fd50")), (0x0056FD2C, ("push", "eax"))):
        if r2ins(va) != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
    for tgt in (0x005FDA80, 0x005FDCA0, 0x005FDD60):
        c, a, mm, o = call_sites(tgt)
        r.add("calls_%s" % T.owner(tgt)[1], len(c)); r.add("abs32_%s" % T.owner(tgt)[1], len(a))
        r.add("jmps_%s" % T.owner(tgt)[1], o)
        if a or o:
            r.add("bad")
        r.note("%s <- %s" % (T.owner(tgt)[1], " ".join("0x%08X(%s)" % (s, nm(s)) for s in c)))
    # the effect word each caller of ItemCastAtUnit / ItemCastAtXY pushes first (read by r2 at the push)
    eff = {0x005BF1A1: "0", 0x005BF21C: "0", 0x005C0530: "0", 0x005C054E: "1", 0x005C0626: "0", 0x005C0718: "0"}
    for va, v in sorted(eff.items()):
        got = r2ins(va)
        r.add("effect_pushes")
        if got != ("push", v):
            r.add("bad"); r.note("0x%08X r2 %s, want push %s" % (va, got, v))
        else:
            r.note("effect push 0x%08X %s: push %s" % (va, nm(va), v))
    # ItemTgtDo: 0x005C0530's branch is the ItemTgtDo one (the cast with ECX the other unit)
    bad += r.done()

    # delivery 65: the three SKILLS_PayCost calls never read the return
    r = Rep("callers", "delivery65_paycost_return")
    calls, ab, mism, other = call_sites(0x0056BFE0)
    r.add("calls", len(calls)); r.add("abs32", len(ab))
    if calls != [0x0056F7AA, 0x0056FA7A, 0x005D6B48] or ab:
        r.add("bad")
    for s in calls:
        for end in eax_after(s):
            r.add("path_end_" + end[1])
            r.note("0x%08X: path ends at 0x%08X (%s) %s %s" % (s, end[0], end[1], end[2], end[3]))
            if end[1] == "READ":
                r.add("bad")
            if end[1] == "call":
                t = S.branch_target(end[3])
                ce = eax_at_entry(t) if t else "indirect"
                r.note("    callee 0x%08X %s: eax at entry %s" % (t or 0, T.owner(t)[1] if t else "?", ce))
                if ce != "not read":
                    r.add("bad")
    bad += r.done()
    return bad


REG_A = re.compile(r"\b(eax|ax|al|ah)\b")
REG_AHI = re.compile(r"\b(eax|ax|ah)\b")


def eax_after(site):
    """The paths after the call at site, walked over the objdump listing until EAX is written whole, read, a call or a
    ret; `mov al, imm/mem` makes the low byte clean (a later read of AL alone is not a read of the return)."""
    A = S.asm()
    out, seen = [], set()
    work = [(A.next_va(site), False)]
    while work:
        va, lowclean = work.pop()
        while va is not None and va not in seen:
            seen.add(va)
            mn, ops = A.at(va)
            parts = [p.strip() for p in ops.split(",")] if ops else []
            dst = parts[0] if parts else ""
            if mn == "mov" and dst == "al" and not REG_A.search(",".join(parts[1:])):
                lowclean = True
                va = A.next_va(va)
                continue
            regs = REG_AHI if lowclean else REG_A
            if mn == "xor" and len(parts) == 2 and parts[0] == parts[1] == "eax":
                out.append((va, "write", mn, ops)); break
            if mn in ("mov", "lea", "movzx", "movsx", "pop") and dst == "eax" and not REG_A.search(",".join(parts[1:])):
                out.append((va, "write", mn, ops)); break
            if any(regs.search(p) for p in parts) and mn not in ("call",):
                out.append((va, "READ", mn, ops)); break
            if mn == "call":
                out.append((va, "call", mn, ops)); break
            if mn.startswith("ret"):
                out.append((va, "ret", mn, ops)); break
            if mn == "jmp":
                va = S.branch_target(ops)
                continue
            if mn.startswith("j"):
                t = S.branch_target(ops)
                if t is not None:
                    work.append((t, lowclean))
            va = A.next_va(va)
    return out


def eax_at_entry(fn):
    """Whether a callee reads EAX before writing it, along its first straight-line block up to a call or branch."""
    A = S.asm()
    va = fn
    for _ in range(40):
        mn, ops = A.at(va)
        parts = [p.strip() for p in ops.split(",")] if ops else []
        if mn in ("mov", "lea", "movzx", "movsx", "pop") and parts and parts[0] == "eax" \
                and not REG_A.search(",".join(parts[1:])):
            return "not read"
        if mn == "xor" and parts == ["eax", "eax"]:
            return "not read"
        if any(REG_A.search(p) for p in parts):
            return "read at 0x%08X" % va
        if mn == "call" or mn.startswith("j") or mn.startswith("ret"):
            return "not read"
        va = A.next_va(va)
    return "not read"


# ============================================================================================================== stats
READERS = {0x00625480: "GetUnitStat", 0x006253B0: "GetUnitBaseStat", 0x00625500: "UnitGetStat",
           0x00625420: "StatListGetStat", 0x00625350: "StatListGetBaseStat", 0x00624F60: "StatListGetValue",
           0x00624ED0: "StatListGetBaseValue", 0x00625D00: "StatListGetBaseStatJ", 0x00625560: "UnitStatDelta",
           0x006261D0: "StatListGetEntries", 0x0057A8E0: "COMBAT_RollElemStat"}
LAYER_FIRST = {0x00625480, 0x006253B0, 0x00625500, 0x00625420, 0x00625350, 0x00625D00, 0x00625560}


def window_paths(win):
    """The straight paths through a window of (va, (mn, ops)) in address order: a conditional jump to an address in
    the window forks, a `jmp` to one jumps; a jump that leaves the window ends that path (dropped)."""
    idx = {va: i for i, (va, _) in enumerate(win)}
    paths, work = [], [(0, [])]
    while work:
        i, acc = work.pop()
        while i < len(win):
            va, (mn, ops) = win[i]
            acc = acc + [(va, mn, ops)]
            if mn == "jmp" or (mn.startswith("j") and mn != "jmp"):
                t = S.branch_target(ops)
                if mn == "jmp":
                    if t in idx and idx[t] > i:
                        i = idx[t]
                        continue
                    acc = None
                    break
                if t in idx and idx[t] > i:
                    work.append((idx[t], list(acc)))
            i += 1
        if acc is not None:
            paths.append(acc)
    return paths


# EAX at a COMBAT_RollElemStat call computed from a register the window does not set (r2-asserted in chk_stats)
EAX_SITES = {0x0057BA7E: 61}


def stat_ids(roots):
    """{stat id: [sites]} and unresolved sites, over the objdump bodies of roots. Per reader call, each straight
    path through the instructions between the previous call of the body and the site gives the stat id as the
    second-to-last push (args pushed last first: (unit, stat, ...)); COMBAT_RollElemStat's ids are its last two
    pushes (arg 0 the maximum, arg 1 the mastery, -1 none) and EAX (`mov eax, imm`). -1 is never a stat id."""
    A = S.asm()
    ids, unres = collections.defaultdict(list), []
    for e in roots:
        vas, calls, icalls = S.body(A, e)
        vs = sorted(vas)
        cs = sorted([s for s, _ in calls] + list(icalls))
        for s, t in calls:
            if t not in READERS:
                continue
            prev = max([c for c in cs if c < s] + [vs[0] - 1])
            win = [(va, A.ins[va]) for va in vs if prev < va < s]
            st = set()
            paths = window_paths(win)
            if not paths:   # every path left the window: the linear listing
                paths = [[(va, mn, ops) for va, (mn, ops) in win]]
            for path in paths:
                pushes = [ops for va, mn, ops in path if mn == "push"]
                if t == 0x0057A8E0:
                    cand = [T.imm(x) for x in pushes[-2:]]
                    cand += [T.imm(ops.split(",")[1]) for va, mn, ops in path if mn == "mov" and ops.startswith("eax,0x")]
                    if s in EAX_SITES:
                        cand.append(EAX_SITES[s])
                else:
                    cand = [T.imm(pushes[-2])] if len(pushes) >= 2 else []
                st |= set(v for v in cand if v is not None and v != 0xFFFFFFFF and v < 0x400)
            if not st:
                unres.append((s, READERS[t], e, [ops for va, (mn, ops) in win if mn == "push"]))
            for v in st:
                ids[v].append(s)
    return ids, unres


def ranges(*rs):
    out = set()
    for r in rs:
        if isinstance(r, tuple):
            out |= set(range(r[0], r[1] + 1))
        else:
            out.add(r)
    return out


def chk_stats():
    bad = 0
    sets = [
        ("tohit4", [0x0057D9B0, 0x0057D8A0, 0x00622560, 0x0057DFB0, 0x0057DD60, 0x0057DCA0, 0x00622720, 0x006223F0,
                    0x0057EC10, 0x00622D00],
         ranges(2, 12, 16, 171, 19, 20, 31, 32, 33, 115, 116, 119, 123, 124, 179, 182, 325, 338, 339, 340, 348),
         {325: "the caller's arPct (SKILL_AttackDo)"}),
        ("damage2", [0x0057B7D0, 0x0057B420, 0x0057A8E0, 0x0057A880, 0x0057B660, 0x0057B6A0],
         ranges(0, 2, 17, 18, (21, 25), (48, 59), (60, 66), 101, 103, 104, 106, 111, (120, 122), 141, 180, 315, 326,
                (329, 332), 357, 337), {}),
        ("reductions1", [0x0057C1E0, 0x0057BF80, 0x0057BE00, 0x0057BF10, 0x0057C060, 0x0057C140, 0x005AD730],
         ranges(34, 35, (36, 46), 110, 118, 153, (142, 149), 327, (333, 336)), {}),
    ]
    for name, roots, spec, outside in sets:
        r = Rep("stats", name)
        ids, unres = stat_ids(roots)
        found = set(ids)
        if name == "reductions1":
            rows = resist_table()
            for row in rows:
                for v in row[1:6]:
                    if v != 0xFFFFFFFF:
                        found.add(v)
                        ids[v].append(0x00732980)
            r.add("table_rows", len(rows))
            for row in rows:
                r.note("table row: offset 0x%02X resist %s max %s pierce %s absorb %s/%s" % tuple(
                    [row[0]] + ["-" if v == 0xFFFFFFFF else str(v) for v in row[1:6]]))
        missing = sorted(spec - found)
        extra = sorted(found - spec)
        r.add("spec_ids", len(spec)); r.add("found_ids", len(found)); r.add("unresolved_sites", len(unres))
        r.add("missing", len(missing)); r.add("extra", len(extra))
        for v in sorted(found):
            r.note("stat %3d at %s" % (v, " ".join("0x%08X" % s for s in sorted(set(ids[v])))))
        for v in missing:
            r.note("in the spec, not found here: %d (%s)" % (v, outside.get(v, "?")))
            if v not in outside:
                r.add("bad")
        for v in extra:
            r.note("found, not in the spec's list: %d at %s" % (v, " ".join("0x%08X(%s)" % (s, nm(s)) for s in ids[v])))
        for s, rd, e, p in unres:
            r.note("unresolved: 0x%08X %s in %s pushes %s" % (s, rd, T.owner(e)[1], p))
        bad += r.done()
    r = Rep("stats", "damage2_eax61")
    for va, w in ((0x0057BA55, ("mov", "ecx, dword [ebp - 4]")), (0x0057BA58, ("cmp", "ecx, 1")),
                  (0x0057BA5E, ("jne", "0x57baf8")), (0x0057BA7B, ("lea", "eax, [ecx + 0x3c]")),
                  (0x0057BA7E, ("call", "0x57a8e0"))):
        r.add("ins")
        if r2ins(va) != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
    bad += r.done()
    # to-hit 4's 325: SKILL_AttackDo pushes it before its stat read
    r = Rep("stats", "tohit4_325_in_attackdo")
    ids, unres = stat_ids([0x0056F070])
    r.add("sites_325", len(ids.get(325, [])))
    r.note("SKILL_AttackDo stat 325 at %s" % " ".join("0x%08X" % s for s in ids.get(325, [])))
    if not ids.get(325):
        r.add("bad")
    bad += r.done()
    return bad


def resist_table():
    """The 12 rows of g_DamageResistTable (11 dwords each) read with r2: (field offset, resist, max, pierce,
    absorb percent, absorb flat)."""
    words = []
    for ln in T.r2("pxw %d @ 0x00732980" % (12 * 11 * 4)).splitlines():
        m = re.match(r"^0x[0-9a-f]+\s+((?:0x[0-9a-f]{8}\s*)+)", ln)
        if m:
            words += [int(x, 16) for x in m.group(1).split()]
    rows = [words[11 * k:11 * k + 11] for k in range(12)]
    return [(w[0], w[1], w[2], w[3], w[4], w[5]) for w in rows]


# ============================================================================================================= stores
MEM = re.compile(r"\[ebp-0x([0-9a-f]+)\]")
PTRST = re.compile(r"\[(e[a-z]{2})\+0x(38|3c|40|65|68)\]")


POINTER_PACKETS = {
    0x0057DBF0: "COMBAT_ResolveAndQueue's own build takes its caller's packet (the callers are the rows above)",
    0x005D54B0: "sub_005D54B0_SkillKickPhysDamage takes the packet of its three callers (listed below)",
    0x005D7C40: "sub_005D7C40_BladeShieldAreaCb copies 0x1C dwords from the block of sub_005D7CE0_BladeShieldArea",
}


def packet_functions():
    """{entry: [(site, target)]} for every call of COMBAT_BuildDamage and COMBAT_ResolveAndQueue."""
    fn = collections.OrderedDict()
    for tgt in (0x0057B7D0, 0x0057DBF0):
        calls, ab, mism, other = call_sites(tgt)
        for s in calls:
            fn.setdefault(entry_of(s), []).append((s, tgt))
    # sub_005D7C40_BladeShieldAreaCb copies its packet (`rep movsd`, 0x1C dwords) from the block its registrar
    # sub_005D7CE0_BladeShieldArea builds and hands to SKILLS_ForUnitsInRange (0x005D7DF7): that registrar too
    fn.setdefault(0x005D7CE0, []).append((0x005D7DF7, 0x0056B7E0))
    return fn


def frame_stores(e, offs):
    """Stores into [ebp-Y] with Y = X - off for a frame base X the body takes with lea; and stores [reg+off]."""
    A = S.asm()
    vas, calls, icalls = S.body(A, e)
    leas, stores, ptr = set(), [], []
    for va in sorted(vas):
        mn, ops = A.ins[va]
        dst = ops.split(",")[0]
        m = MEM.search(ops)
        if mn == "lea" and m:
            leas.add(int(m.group(1), 16))
        elif mn not in ("cmp", "test", "push", "lea") and "[ebp-" in dst and "," in ops:
            stores.append((va, mn, ops, int(MEM.search(dst).group(1), 16)))
        pm = PTRST.search(dst)
        if mn not in ("cmp", "test", "push", "lea") and pm and int(pm.group(2), 16) in offs and "," in ops:
            ptr.append((va, mn, ops))
    hits = [(b, off, va, mn, ops) for b in sorted(leas) for off in offs for va, mn, ops, y in stores if b - y == off]
    return leas, hits, ptr, vas, calls


def chk_stores():
    bad = 0
    A = S.asm()
    fn = packet_functions()

    # README 4 (remainder): every caller's packet is a zeroed frame block of 0x70 bytes or more
    r = Rep("stores", "readme4_zeroing")
    for e, sites in fn.items():
        vas, calls, icalls = S.body(A, e)
        zero = []
        for s, t in calls:
            if t == 0x00681EF0:
                p = T.pushes_before(s, entry=e, want=3)
                zero.append((s, p))
        leas = sorted(int(MEM.search(A.ins[va][1]).group(1), 16) for va in vas
                      if A.ins[va][0] == "lea" and MEM.search(A.ins[va][1]))
        ok = [z for z in zero if z[1] and len(z[1]) == 3 and z[1][1] in ("0", "eax") and T.imm(z[1][2]) is not None
              and T.imm(z[1][2]) >= 0x70]
        kind = "zeroed" if ok else "pointer"
        if ok and ok[0][1][1] == "eax":
            # do 67: memset(&packet, EAX, 0x70) with EAX 0 after `test eax, eax; jne` (0x005CFBE5-0x005CFBE7)
            kind = "zeroed_eax0"
            if ok[0][0] != 0x005CFBF7 or r2ins(0x005CFBE5) != ("test", "eax, eax") or r2ins(0x005CFBE7)[0] != "jne" \
                    or r2ins(0x005CFBEF) != ("push", "eax"):
                r.add("bad")
        if kind == "pointer" and e not in POINTER_PACKETS:
            r.add("bad")
        r.add(kind)
        r.note("%s 0x%08X %s sites %s memset %s leas %s" % (kind, e, T.owner(e)[1],
                                                             " ".join("0x%08X%s" % (s, "B" if t == 0x0057B7D0 else "R") for s, t in sites),
                                                             ["0x%08X %s" % (s, p) for s, p in zero], [hex(x) for x in leas]))
    for e, why in POINTER_PACKETS.items():
        r.note("pointer packet 0x%08X %s: %s" % (e, T.owner(e)[1], why))
    for e in (0x005D54B0, 0x005D7C40):
        c, a, mm, o = call_sites(e)
        r.note("  0x%08X <- calls %s abs32 %s" % (e, ["0x%08X(%s)" % (x, nm(x)) for x in c], ["0x%08X" % x for x in a]))
    for va, w in ((0x005D7C52, ("mov", "ecx, 0x1c")), (0x005D7C57, ("lea", "edi, [ebp - 0x78]")),
                  (0x005D7C5A, ("rep", "movsd dword es:[edi], dword [esi]"))):
        if r2ins(va) != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
    bad += r.done()

    # damage 17: writers of +0x38/+0x3C/+0x40 in those functions and their direct callees
    for name, offs in (("damage17_drain_fields", (0x38, 0x3C, 0x40)), ("damage27_conv_fields", (0x65, 0x68))):
        r = Rep("stores", name)
        callees = collections.defaultdict(set)
        for e, sites in fn.items():
            leas, hits, ptr, vas, calls = frame_stores(e, offs)
            last = max(s for s, _ in sites)
            for s, t in calls:
                if s < last and t not in (0x0057B7D0, 0x0057DBF0):
                    callees[t].add(e)
            for b, off, va, mn, ops in hits:
                first_build = min([s for s, t in sites if t == 0x0057B7D0] or [last])
                r.add("frame_store")
                r.note("0x%08X %s: base -0x%X +0x%X 0x%08X %s %s (%s the first build/queue call 0x%08X)" % (
                    e, T.owner(e)[1], b, off, va, mn, ops, "before" if va < first_build else "after", first_build))
            for va, mn, ops in ptr:
                r.add("ptr_store_in_caller")
                r.note("0x%08X %s: pointer store 0x%08X %s %s" % (e, T.owner(e)[1], va, mn, ops))
        r.add("functions", len(fn)); r.add("callees", len(callees))
        if offs[0] == 0x38:
            # start 60's adds come after `+0x00 |= 2`, and ResolveAndQueue builds only when bit 2 is clear
            for va, w in ((0x005D15EF, ("mov", "eax, dword [ebp - 0x78]")), (0x005D15F2, ("or", "eax, 2")),
                          (0x005D15F5, ("mov", "dword [ebp - 0x78], eax")), (0x0057DC28, ("test", "byte [ebx], 2")),
                          (0x0057DC2B, ("jne", "0x57dc3c")), (0x0057DC37, ("call", "0x57b7d0"))):
                r.add("ins")
                if r2ins(va) != w:
                    r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
        for t in sorted(callees):
            leas, hits, ptr, vas, calls = frame_stores(t, offs)
            for va, mn, ops in ptr:
                r.add("ptr_store_in_callee")
                r.note("callee 0x%08X %s: 0x%08X %s %s" % (t, T.owner(t)[1], va, mn, ops))
        bad += r.done()

    # damage 27: the EType byte loads and where each goes
    r = Rep("stores", "damage27_etype_loads")
    loads = [(va, mn, ops) for va, (mn, ops) in sorted(A.ins.items())
             if "+0x1dc]" in ops and "BYTE PTR" in ops and mn in ("mov", "movzx", "movsx")]
    r.add("loads", len(loads))
    for va, mn, ops in loads:
        reg = ops.split(",")[0].strip()
        nxt, st = A.next_va(va), None
        for _ in range(6):
            m2, o2 = A.ins[nxt]
            if m2 == "mov" and o2.endswith("," + reg) and "PTR" in o2.split(",")[0]:
                st = (nxt, o2)
                break
            nxt = A.next_va(nxt)
        if st and st[1].startswith("BYTE PTR [ebp-"):
            e = entry_of(va)
            y = int(MEM.search(st[1]).group(1), 16)
            leas = frame_stores(e, ())[0] if e else set()
            base = [b for b in leas if b - y == 0x65]
            r.add("byte_store_to_frame")
            if not base:
                r.add("bad")
            r.note("0x%08X %s -> 0x%08X %s: packet base %s, in %s" % (va, ops, st[0], st[1],
                                                                     ["-0x%X" % b for b in base], nm(va)))
    bad += r.done()

    # to-hit 21: the writers of item flags 0x100 and 0x4000 against 0x0062A4E0's test
    r = Rep("stores", "tohit21_item_flags")
    for va, w in ((0x0062A4F8, ("mov", "eax, dword [eax + 0x18]")), (0x0062A4FB, ("and", "eax, 0x100")),
                  (0x0062A50E, ("mov", "eax, dword [eax + 0x18]")), (0x0062A511, ("and", "eax, 0x4000"))):
        if r2ins(va) != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
    calls, ab, mism, other = call_sites(0x006280D0)
    r.add("setflag_calls", len(calls)); r.add("setflag_abs32", len(ab))
    for s in calls:
        p = T.pushes_before(s, want=3) or []
        mask = T.imm(p[1]) if len(p) > 1 else None
        setv = p[2] if len(p) > 2 else None
        if mask in (0x100, 0x4000):
            r.add("mask_%x_set_%s" % (mask, setv))
            r.note("0x%08X %s mask 0x%X set %s" % (s, nm(s), mask, setv))
        elif mask is None:
            r.add("mask_register")
            r.note("0x%08X %s mask %s set %s (register)" % (s, nm(s), p[1] if len(p) > 1 else None, setv))
    direct = [(va, mn, ops) for va, (mn, ops) in sorted(A.ins.items())
              if mn in ("or", "and", "mov") and re.search(r"\[e[a-z]{2}\+0x18\]", ops.split(",")[0])
              and any(S.has_imm(ops, v) for v in (0x100, 0x4000, 0xFFFFFEFF, 0xFFFFBFFF))]
    r.add("direct_imm_stores_at_0x18", len(direct))
    for va, mn, ops in direct:
        r.note("direct 0x%08X %s %s in %s" % (va, mn, ops, nm(va)))
    bad += r.done()

    # damage 32: MonLvlStats' El branch writes and MonAttackStats' El reads of the zeroed output
    r = Rep("stores", "damage32_monlvlstats_el")
    want = {0x00653BBC: ("test", "byte [ebp + 0x18], 0x40"), 0x00653BC8: ("test", "byte [edi + 0xc], cl"),
            0x00653BD5: ("mov", "dword [ebx + 0x24], edx"), 0x00653BE0: ("mov", "dword [ebx + 0x28], ecx"),
            0x00653BE3: ("jmp", "0x653c25"), 0x00653C0B: ("mov", "dword [ebx + 0x2c], eax"),
            0x00653C1F: ("mov", "dword [ebx + 0x30], eax"), 0x00653C2D: ("mov", "dword [ebx + 0x34], edx"),
            0x005A5245: ("push", "0x38"), 0x005A5247: ("lea", "edx, [ebp - 0x74]"), 0x005A524D: ("call", "0x681ef0"),
            0x005A5258: ("lea", "eax, [ebp - 0x74]"), 0x005A527A: ("call", "0x6538a0"),
            0x005A5286: ("mov", "ecx, dword [ebp - 0x48]"), 0x005A5289: ("mov", "edx, dword [ebp - 0x40]"),
            0x005A528C: ("mov", "ebx, dword [ebp - 0x44]")}
    for va, w in sorted(want.items()):
        r.add("ins")
        if r2ins(va) != w:
            r.add("bad"); r.note("0x%08X r2 %s, want %s" % (va, r2ins(va), w))
    r.note("noRatio mask byte 0x006CE270 = 0x%02X (MonStats +0x00C bit 2)" % (S.dword(0x006CE270) & 0xFF))
    vas, calls, icalls = S.body(A, 0x005A4F50)
    reads = sorted(va for va in vas if re.search(r"\[ebp-0x(50|4c)\]", A.ins[va][1]) and va > 0x005A527A)
    r.add("el_reads_of_0x24_0x28_after_el_call", len(reads))
    if reads:
        r.add("bad")
    bad += r.done()
    return bad


# ============================================================================================================= tables
def chk_tables():
    bad = 0
    st = S.tsv("states")
    r = Rep("tables", "readme8_tohit19_states")
    r.add("rows", len(st))
    mo = [(i, x["state"]) for i, x in enumerate(st) if x.get("meleeonly") == "1"]
    r.add("meleeonly_rows", len(mo))
    r.note("meleeonly = 1: %s" % mo)
    r.note("row 54: %s" % st[54]["state"])
    if mo != [(139, "wolf"), (140, "bear")] or st[54]["state"] != "uninterruptable":
        r.add("bad")
    bad += r.done()

    sk = S.tsv("skills")
    r = Rep("tables", "delivery20_itemeffect")
    r.add("rows", len(sk))
    vals = collections.Counter(x.get("ItemEffect") or "" for x in sk)
    for v, n in sorted(vals.items()):
        r.add("itemeffect_%s" % (v or "blank"), n)
    other = [(x["Id"], x["skill"], x["ItemEffect"]) for x in sk if x.get("ItemEffect") not in ("", "0", "1")]
    r.note("ItemEffect other than blank/0/1: %s" % other)
    if other != [("44", "Frost Nova", "36"), ("48", "Nova", "36"), ("53", "Chain Lightning", "151")]:
        r.add("bad")
    tgt = [(x["Id"], x["skill"], x.get("ItemTgtDo"), x.get("ItemTarget")) for x in sk if x.get("ItemTgtDo") not in ("", "0")]
    r.note("ItemTgtDo set: %s" % tgt)
    bad += r.done()

    r = Rep("tables", "delivery21_prg")
    rows = [(x["Id"], x["skill"], [x.get("srvprgfunc%d" % i) or "-" for i in (1, 2, 3)], x.get("prgstack") or "")
            for x in sk if any(x.get("srvprgfunc%d" % i) for i in (1, 2, 3))]
    r.add("rows", len(rows))
    for row in rows:
        r.note("%s" % (row,))
    want = [("259", "Fists of Fire", ["143", "38", "39"], "1"), ("269", "Claws of Thunder", ["-", "36", "37"], "1"),
            ("274", "Blades of Ice", ["-", "38", "39"], "1"), ("280", "Royal Strike", ["40", "143", "41"], "")]
    if rows != want:
        r.add("bad")
    bad += r.done()

    ev = [x.get("event") for x in S.tsv("events")]
    isc = S.tsv("itemstatcost")
    r = Rep("tables", "damage19_delivery38_events")
    r.note("events.txt: %s" % list(enumerate(ev)))
    regs = []
    for x in isc:
        for j in ("1", "2"):
            if x.get("itemevent" + j):
                regs.append(("ItemStatCost", x["ID"], x["Stat"], x["itemevent" + j], x["itemeventfunc" + j]))
    for x in sk:
        for c, f in (("auraevent1", "auraeventfunc1"), ("auraevent2", "auraeventfunc2"), ("auraevent3", "auraeventfunc3"),
                     ("auratgtevent", "auratgteventfunc"), ("passiveevent", "passiveeventfunc")):
            if x.get(c):
                regs.append(("Skills." + c, x["Id"], x["skill"], x[c], x.get(f)))
    r.add("registrations", len(regs))
    on3 = [g for g in regs if g[3] == ev[3]]
    r.add("on_event3_%s" % ev[3], len(on3))
    r.note("event 3 (%s): %s" % (ev[3], on3))
    if on3 != [("Skills.auraevent1", "50", "Shiver Armor", "attackedinmelee", "3")]:
        r.add("bad")
    cb = [g for g in regs if g[0] == "ItemStatCost" and g[1] in ("134", "135", "136")]
    r.note("stats 134-136: %s" % cb)
    if sorted((g[1], g[3], g[4]) for g in cb) != [("134", "domeleedamage", "14"), ("134", "domissiledamage", "14"),
                                                  ("135", "domeleedamage", "15"), ("135", "domissiledamage", "15"),
                                                  ("136", "domeleedamage", "16"), ("136", "domissiledamage", "16")]:
        r.add("bad")
    named = sorted(set(int(g[4]) for g in regs if g[4]))
    r.note("handler numbers named by a stock row: %s; not named: %s" % (named, [i for i in range(1, 32) if i not in named]))
    r.add("handlers_named", len(named))
    for g in regs:
        r.note("  %s" % (g,))
    bad += r.done()

    ms = S.tsv("monstats")
    r = Rep("tables", "damage32_noratio_el")
    nr = [(i, x["Id"]) for i, x in enumerate(ms) if x.get("noRatio") == "1"]
    el = [(i, x["Id"], [(x.get("El%dMode" % j), x.get("El%dType" % j)) for j in (1, 2, 3) if x.get("El%dMode" % j)])
          for i, x in enumerate(ms) if x.get("noRatio") == "1" and any(x.get("El%dMode" % j) for j in (1, 2, 3))]
    r.add("noratio_rows", len(nr)); r.add("noratio_with_el", len(el))
    r.note("noRatio rows with an El column: %s" % el)
    bad += r.done()
    return bad


# =========================================================================================================== closures
TEXT_LO, TEXT_HI = 0x00401000, 0x00401000 + 0x2CA5A1
HEX = re.compile(r"0x([0-9a-f]{6,8})\b")


def graph_cb(roots, stop=()):
    """The objdump walker's direct-call graph, plus an edge to every .text address an instruction of a body takes as
    an immediate (push/mov/lea of a code pointer: a callback)."""
    A = S.asm()
    out, q = collections.OrderedDict(), collections.deque()
    for r in roots:
        out[r] = None
        q.append((r, 0, None, "root"))
    while q:
        e, d, p, how = q.popleft()
        vas, calls, icalls = S.body(A, e)
        tg = set(t for _, t in calls)
        cbs = []
        for va in vas:
            mn, ops = A.ins[va]
            if mn in ("push", "mov", "lea") and "PTR" not in ops:
                for h in HEX.findall(ops):
                    v = int(h, 16)
                    if TEXT_LO <= v < TEXT_HI and v not in tg and A.at(v) is not None:
                        cbs.append((va, v))
        out[e] = (d, p, vas, calls, icalls, cbs, how)
        for t, kind in [(t, "call") for _, t in calls] + [(t, "cb") for _, t in cbs]:
            if t in S.RNG_FNS or t in stop or t in out:
                continue
            out[t] = None
            q.append((t, d + 1, e, kind))
    return out


def closure_report(rep, root, label, r2lcg, stop=()):
    A = S.asm()
    G = graph_cb([root], stop=stop)
    draws = {}
    for e, v in G.items():
        lcg, rc = S.rng_sites(A, v[2])
        r2in = sorted(x for x in r2lcg if x in v[2])
        if lcg or rc or r2in:
            draws[e] = (lcg, rc, r2in)
    ics = [(e, s) for e, v in G.items() for s in v[4]]
    imp = [x for x in ics if A.ins[x[1]][1].startswith("DWORD PTR ds:0x6cc")]
    game = [x for x in ics if x not in imp and 0x00450000 <= x[1] < 0x00681C00]   # below: Storm/Fog; above: CRT
    cb = sum(1 for v in G.values() if v[6] == "cb")
    stops = sorted(set(T.owner(t)[1] for e, v in G.items() for _, t in v[3] if t in stop))
    rep.note("%s 0x%08X: functions=%d callback_edges=%d draw_functions=%d indirect=%d (imports %d, game-range %d, "
             "other %d)%s" % (label, root, len(G), cb, len(draws), len(ics), len(imp), len(game),
                              len(ics) - len(imp) - len(game), (" stops reached: %s" % stops) if stops else ""))
    for e, (lcg, rc, r2in) in draws.items():
        ch = [e]
        while G[ch[-1]][1] is not None:
            ch.append(G[ch[-1]][1])
        rep.note("    draw in %s (lcg %s, rng %s, r2 lcg %s); path %s" % (
            T.owner(e)[1], ["0x%08X" % x for x in lcg], [n for _, n in rc], ["0x%08X" % x for x in r2in],
            " <- ".join("%s/%s" % (T.owner(x)[1], G[x][6]) for x in ch)))
    for e, s in game:
        rep.note("    game-range indirect 0x%08X %s %s in %s" % (s, A.ins[s][0], A.ins[s][1], nm(s)))
    return G, draws, game


def chk_closures():
    bad = 0
    hits, r2lcg = T.r2_lcg_sites()
    A = S.asm()
    olcg = set()
    for va, (mn, ops) in A.ins.items():
        if S.has_imm(ops, S.LCG_MUL):
            olcg.add(va)
    r = Rep("closures", "lcg_sites")
    r.add("r2_hits", len(hits)); r.add("r2_sites", len(r2lcg)); r.add("objdump_sites", len(olcg))
    r.add("r2_not_objdump", len(set(r2lcg) - olcg)); r.add("objdump_not_r2", len(olcg - set(r2lcg)))
    if set(r2lcg) != olcg:
        r.add("bad")
    bad += r.done()

    tbl = []
    for ln in T.r2("pxw 128 @ 0x007325b0").splitlines():
        m = re.match(r"^0x[0-9a-f]+\s+((?:0x[0-9a-f]{8}\s*)+)", ln)
        if m:
            tbl += [int(x, 16) for x in m.group(1).split()]
    r = Rep("closures", "delivery50_handlers")
    r.add("handlers", sum(1 for h in tbl if h))
    stop = {0x0057C6C0: "COMBAT_ApplyDamage", 0x0057CEE0: "COMBAT_GetHit"}
    clean = []
    for i, h in enumerate(tbl):
        if not h:
            continue
        vas, calls, ic = S.body(A, h)
        lcg, rc = S.rng_sites(A, vas)
        r.note("h%d 0x%08X %s own body: lcg %s rng %s" % (i, h, T.owner(h)[1], ["0x%08X" % x for x in lcg],
                                                           [n for _, n in rc]))
        G, draws, game = closure_report(r, h, "  h%d" % i, r2lcg, stop=set(stop))
        if not draws:
            clean.append(i)
    r.note("handlers whose closure (to COMBAT_ApplyDamage / COMBAT_GetHit) holds no draw: %s" % clean)
    if 28 not in clean:
        r.add("bad")
    for i in (2, 4, 5, 6, 10, 13, 17, 18, 19, 22, 23, 24, 25, 26, 27, 28, 29):
        r.add("spec_list_clean" if i in clean else "spec_list_with_draw_function")
    bad += r.done()

    r = Rep("closures", "delivery51_helpers")
    for root, label in ((0x005FD9C0, "helper3"), (0x005FDA10, "helper4"), (0x0056E390, "CorpsePickNear")):
        G, draws, game = closure_report(r, root, label, r2lcg)
        r.add("%s_functions" % label, len(G)); r.add("%s_draw_functions" % label, len(draws))
        r.add("%s_game_indirect" % label, len(game))
        if draws:
            r.add("bad")
    bad += r.done()
    return bad


SECTIONS = collections.OrderedDict([("callers", chk_callers), ("stats", chk_stats), ("stores", chk_stores),
                                    ("tables", chk_tables), ("closures", chk_closures)])


def main(argv):
    names = list(SECTIONS) if argv == ["all"] else argv
    if not names or any(n not in SECTIONS for n in names):
        print(__doc__)
        return 2
    total = 0
    for n in names:
        total += SECTIONS[n]()
    print("S5b total bad=%d" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

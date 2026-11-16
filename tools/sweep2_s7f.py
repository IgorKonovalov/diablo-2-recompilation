"""Plan 0066 batch S7f (sim/frame, path, drlg/lifecycle): constants, tables and writer/reader pairs read with a second
tool for the 35 class-c rows of the batch. No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s7f.py <section> [<section> ...]
  python3 -I tools/sweep2_s7f.py all

Sections (the inventory rows each check serves are in the check names):
  frame      frame 8-11 (g_ServerFps, the 0x006CAF10 initializer and the CRT table that calls it, g_GameSlots' loops,
             g_UnitTypeEventList), 23 (GameTick's seven calls), 27 (the net queue's pop and both appends), 29
             (g_SrvPacketTable 0x00..0x67 and the dispatch's switch), 44 (the four event tables and dispatches)
  path       path README 7 (the record's extent), 8 (the two masks' writers and readers in the path module), 11
             (MissileCreate's mask and Missiles.txt CollideType), 16 (Whirlwind's two immediates), 44 (PathSetType's
             server arguments), 67 (`Jump` in every excel table); path search 3 (g_DirOctant), 26 (the pass and try
             bounds, and the pass count over every h0, b1C), 27 (g_PathSearchTurnRows), 30 (tools/room_extent.py rerun
             against the kept a67 outputs), 35 (PathPlan's tail)
  lifecycle  lifecycle 38-46, 64, 77 (the inactive room, item and monster records: each field's writer against its
             reader), 57, 61-63 (SpecialModsApply's third argument, MinionRestore's handler calls, the handlers' flag
             tests), 70 (the room drivers' bit-0 test)

Each check reads its sites twice, in objdump's listing (tools/sweep_s4b.py) and in r2's decoding of the same address,
and compares both with the instruction the row's reading expects (operands normalised: case, spacing, `PTR`, `ds:`,
numbers as hex). Each section prints `S7f <section> <check> key=value ...` lines and detail lines; `bad=` counts an
observation that contradicts the statement the check tests, or a site where the two tools disagree. Stdlib only,
plus objdump and r2. Read-only. The records are the "Plan 0066 batch S7f" sections of findings/frame/0001,
path/0001 and drlg/0009.
"""
import collections
import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402
import sweep2_s4cd as T  # noqa: E402
import sweep2_s7a as A7  # noqa: E402


class Rep(T.Rep):
    def done(self):
        if "bad" not in self.c:
            self.c["bad"] += 0
        print("S7f %s %s %s" % (self.sec, self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return self.c["bad"]


NUM = re.compile(r"\b(0x[0-9a-f]+|\d+)\b")


ABS = re.compile(r"(?:(?:byte|word|dword|qword)\s*(?:ptr)?\s*)?(?:ds:(0x[0-9a-f]+)\b|\[(0x[0-9a-f]+)\])")


def norm(ops):
    """Operands in one form for both tools: lower case, no spaces, no `PTR`, an absolute memory operand as
    `[0x...]` without its size word (objdump writes `ds:0x...`, often with no size), numbers as hex."""
    s = (ops or "").lower()
    for k, v in imports().items():
        s = s.replace(k.replace("[", "[").lower(), v).replace(k.replace("[", "dword ["), "dword " + v)
    s = ABS.sub(lambda m: "[%s]" % (m.group(1) or m.group(2)), s)
    s = s.replace("ptr", "").replace(" ", "")
    return NUM.sub(lambda m: hex(int(m.group(1), 0)), s)


IMPORTS = {}


def imports():
    """r2's import names for the three import slots the checks call through, each checked against r2's `ii`."""
    if not IMPORTS:
        for ln in T.r2("ii").splitlines():
            m = re.match(r"^\s*\d+\s+(0x[0-9a-f]+)\s+\S+\s+FUNC\s+(\S+)\s+(\S+)", ln)
            if m and int(m.group(1), 16) in (0x006CC214, 0x006CC218, 0x006CC34C):
                IMPORTS["[sym.imp.%s_%s]" % (m.group(2).lower(), m.group(3).lower())] = "[%s]" % m.group(1)
    return IMPORTS


def expect(r, va, mn, *subs):
    """Both tools decode `mn` at va with every normalised substring in subs; bad otherwise."""
    A = S.asm()
    o = A.at(va)
    m2, o2 = A7.r2ins(va)
    ok = o is not None and o[0] == mn and m2 == mn and all(norm(x) in norm(o[1]) and norm(x) in norm(o2)
                                                             for x in subs)
    r.c["sites"] += 1
    if not ok:
        r.c["bad"] += 1
        r.note("MISMATCH 0x%08X want %s %s; objdump %s; r2 %s %s" % (va, mn, subs, o, m2, o2))
    return ok


def dw(va):
    return S.dword(va)


def sdw(va):
    v = S.dword(va)
    return v - (1 << 32) if v & 0x80000000 else v


def byte(va):
    return S.image()[0][S.va_off(va)]


def absx(t):
    """abs32 hits of t with the instruction that holds each (None outside .text)."""
    _, ab = A7.xref(t)
    return [(h, A7.abs_instr(h, t)) for h in ab]


def text_range(lo, hi):
    return list(S.asm().range(lo, hi))


def branch_into(lo, hi):
    """Every branch in .text (jcc, jmp, call) whose immediate target lies in (lo, hi]."""
    out = []
    for va, (mn, ops) in S.asm().ins.items():
        if mn.startswith("j") or mn == "call":
            m = re.match(r"^0x([0-9a-f]+)$", ops or "")
            if m and lo < int(m.group(1), 16) <= hi:
                out.append(va)
    return sorted(out)


# ================================================================================================== frame
def chk_frame():
    bad = 0
    # ---- frame 8: g_ServerFps
    r = Rep("frame", "row8_ServerFps")
    r.c["value"] = dw(0x00731014)
    r.c["bad"] += int(r.c["value"] != 25)
    calls, other, ab = A7.calls_of(0x0052DF80)
    r.c["setter_calls"], r.c["setter_jumps"], r.c["setter_abs"] = len(calls), len(other), len(ab)
    r.c["bad"] += len(calls) + len(other) + len(ab)
    hits = absx(0x00731014)
    r.c["word_refs"] = len(hits)
    for h, ins in hits:
        r.note("g_ServerFps ref 0x%08X %s %s" % (h, A7.nm(h), ins))
    stores = [h for h, ins in hits if ins and ins[1] == "mov" and ins[2].startswith("dword [0x731014]")]
    r.c["stores"] = len(stores)
    r.c["bad"] += int([T.pad_entry(h) for h in stores] != [0x0052DF80])
    expect(r, 0x0052DF8E, "mov", "[0x731014],ecx")
    bad += r.done()

    # ---- frame 9: the static initializer and the CRT table that calls it
    r = Rep("frame", "row9_FrameInterval")
    expect(r, 0x006CAF10, "mov", "eax,0x3e8")
    expect(r, 0x006CAF15, "cdq")
    expect(r, 0x006CAF16, "idiv", "[0x731014]")
    expect(r, 0x006CAF1C, "mov", "[0x883d60],eax")
    expect(r, 0x006CAF21, "ret")
    r.c["interval"] = 1000 // dw(0x00731014)
    r.c["bad"] += int(r.c["interval"] != 40)
    ptrs = absx(0x006CAF10)
    r.c["init_ptrs"] = len(ptrs)
    # the table the CRT init loop walks: esi from 0x006CC614 to edi 0x006CC720, each non-null dword called
    expect(r, 0x00681CDE, "mov", "esi,0x6cc614")
    expect(r, 0x00681CE5, "mov", "edi,0x6cc720")
    expect(r, 0x00681CEF, "mov", "eax,dword[esi]")
    expect(r, 0x00681CF5, "call", "eax")
    expect(r, 0x00681CF7, "add", "esi,0x4")
    expect(r, 0x00681CFA, "cmp", "esi,edi")
    r.c["bad"] += int(len(ptrs) != 1 or not (0x006CC614 <= ptrs[0][0] < 0x006CC720) or ptrs[0][1] is not None)
    r.note("0x006CAF10 held at 0x%08X (.rdata, the CRT_cinit table 0x006CC614..0x006CC720)" % ptrs[0][0])
    hits = absx(0x00883D60)
    for h, ins in hits:
        r.note("g_ServerFrameInterval ref 0x%08X %s %s" % (h, A7.nm(h), ins))
    st = sorted(T.pad_entry(h) for h, ins in hits if ins and ins[1] == "mov" and ins[2].startswith("dword [0x883d60]"))
    r.c["interval_stores"] = len(st)
    r.c["bad"] += int(st != [0x0052DF80, 0x006CAF10])
    bad += r.done()

    # ---- frame 10: g_GameSlots, 1024 dwords
    r = Rep("frame", "row10_GameSlots")
    A = S.asm()
    END = (0x00883D38, 0x00883D3C)
    for base in (0x00882D38, 0x00882D3C):
        for h, ins in absx(base):
            e = T.pad_entry(h)
            fn = [(va, mn, ops) for va, (mn, ops) in A.range(h - 7, h + 0x400) if va >= h - 1]
            kind = None
            if ins and "[0x882d38]" in ins[2].replace(" ", "") and ins[1] == "mov" and not ins[2].startswith("dword"):
                kind = "slot0_read"
            else:
                nxt = [x for x in fn if x[0] > h - 7][:4]
                if any(mn == "mov" and norm(ops) == "ecx,0x400" for va, (mn, ops) in A.range(h - 8, h)) and \
                        any(mn.startswith("rep") for va, mn, ops in nxt):
                    kind = "clear_1024"
                else:
                    for va, mn, ops in fn:
                        if T.pad_entry(va) != e:
                            break
                        if mn == "cmp" and any(norm(ops).endswith(",%s" % hex(b)) for b in END):
                            kind = "loop_to_%s" % norm(ops).split(",")[1]
                            break
            r.c[kind or "unclassified"] += 1
            r.note("0x%08X %-40s %s" % (h, A7.nm(h), kind))
    r.c["bad"] += r.c["unclassified"]
    # the end word itself is a separate variable: its two stores
    ends = [(h, ins) for h, ins in absx(0x00883D38) if ins and ins[1] == "mov" and ins[2].startswith("dword [0x883d38]")]
    r.c["end_word_stores"] = len(ends)
    r.note("stores to 0x00883D38: %s" % ", ".join("0x%08X %s" % (h, A7.nm(h)) for h, _ in ends))
    r.c["extent_dwords"] = (0x00883D38 - 0x00882D38) // 4
    r.c["bad"] += int(r.c["extent_dwords"] != 1024)
    bad += r.done()

    # ---- frame 11: g_UnitTypeEventList
    r = Rep("frame", "row11_UnitTypeEventList")
    vals = [sdw(0x006E0B9C + 4 * i) for i in range(6)]
    r.note("types 0..5 -> %s (dwords)" % vals)
    r.c["bad"] += int(vals != [0, 1, 3, 2, 4, -1])
    hits = absx(0x006E0B9C)
    owners = collections.OrderedDict()
    for h, ins in hits:
        owners.setdefault(T.pad_entry(h), []).append(h)
        r.c["bad"] += int(not (ins and re.search(r"\[e[a-z]{2}\*4 \+ 0x6e0b9c\]", ins[2])))
    r.c["reads"], r.c["functions"] = len(hits), len(owners)
    for e, hs in owners.items():
        r.note("reader 0x%08X %s: %s" % (e, T.owner(e)[1] if T.owner(e)[0] == e else "(unnamed)",
                                         ", ".join("0x%08X" % h for h in hs)))
    for k in (0x006E0B9D, 0x006E0B9E, 0x006E0BA0, 0x006E0BB0):
        r.c["bad"] += len(absx(k))
    bad += r.done()

    # ---- frame 23: GameTick's seven calls
    r = Rep("frame", "row23_GameTickCalls")
    seq = text_range(0x0052D8DF, 0x0052D90C)
    r.c["calls"] = sum(1 for va, (mn, ops) in seq if mn == "call")
    r.c["branches"] = sum(1 for va, (mn, ops) in seq if mn.startswith("j") or mn.startswith("ret"))
    r.c["bad"] += int(r.c["calls"] != 7) + r.c["branches"]
    for va, (mn, ops) in seq:
        m2, o2 = A7.r2ins(va)
        r.c["bad"] += int(m2 != mn)
    tgt = [ops for va, (mn, ops) in seq if mn == "call"]
    r.note("calls: %s" % ", ".join("%s %s" % (t, A7.nm(int(t, 16))) for t in tgt))
    into = branch_into(0x0052D8DF, 0x0052D907)
    r.c["branches_into"] = len(into)
    r.c["bad"] += len(into)
    bad += r.done()

    # ---- frame 27: the net queue
    r = Rep("frame", "row27_NetQueue")
    # pop: null context and index bound return -1; the head at [ctx+0x870][i] is taken under the lock at +0x854
    for va, mn, sub in ((0x006BEADB, "or", "eax,0xffffffff"), (0x006BEAE7, "cmp", "esi,dword[ebx+0x87c]"),
                        (0x006BEB06, "lea", "edi,[ebx+0x854]"), (0x006BEB0D, "call", "[0x6cc218]"),
                        (0x006BEB13, "mov", "eax,dword[ebx+0x870]"), (0x006BEB1C, "mov", "esi,dword[eax]"),
                        (0x006BEB20, "jne", "0x6beb33"), (0x006BEB2B, "or", "eax,0xffffffff"),
                        (0x006BEB33, "mov", "ecx,dword[esi+0x5bc]"), (0x006BEB39, "mov", "dword[eax],ecx"),
                        (0x006BEB3B, "mov", "edx,dword[ebx+0x874]"), (0x006BEB4C, "mov", "dword[eax],0x0"),
                        (0x006BEB53, "call", "[0x6cc214]"),
                        # append A: link 0, then the tail's link or the empty head, then the tail, under the lock
                        (0x006BF46C, "mov", "dword[esi+0x5bc],0x0"), (0x006BF48A, "call", "[0x6cc218]"),
                        (0x006BF493, "mov", "edx,dword[edi+0x874]"), (0x006BF4A6, "mov", "dword[eax+ecx*4],esi"),
                        (0x006BF4AB, "mov", "dword[eax+0x5bc],esi"), (0x006BF4BB, "mov", "dword[ecx+edx*4],esi"),
                        (0x006BF4BE, "call", "[0x6cc214]"),
                        # append B, the same shape
                        (0x006C0A5A, "mov", "dword[esi+0x5bc],0x0"), (0x006C0A7E, "call", "[0x6cc218]"),
                        (0x006C0A87, "mov", "eax,dword[edi+0x874]"), (0x006C0A9A, "mov", "dword[edx+ecx*4],esi"),
                        (0x006C0A9F, "mov", "dword[eax+0x5bc],esi"), (0x006C0AAE, "mov", "dword[eax+ecx*4],esi"),
                        (0x006C0AB8, "call", "[0x6cc214]"),
                        # the drain pops until -1, queues 0, 1, 2 from one context [0x00882D08]
                        (0x0052D004, "cmp", "eax,0xffffffff"), (0x0052D031, "cmp", "eax,0xffffffff"),
                        (0x0052D061, "cmp", "eax,0xffffffff"), (0x0052D043, "jmp", "0x52d020"),
                        (0x0052B2E1, "push", "0x1"), (0x0052B301, "push", "0x0"), (0x0052B321, "push", "0x2"),
                        (0x0052B2D9, "mov", "edx,dword[0x882d08]")):
        expect(r, va, mn, sub)
    imps = T.r2("ii~0x006cc21").strip().splitlines()
    r.note("imports: %s" % " | ".join(" ".join(x.split()[1:]) for x in imps))
    r.c["bad"] += int(not any("EnterCriticalSection" in x and "6cc218" in x for x in imps)) + \
        int(not any("LeaveCriticalSection" in x and "6cc214" in x for x in imps))
    # every access to the head, tail and link fields in the net module, by function
    acc = collections.defaultdict(list)
    for va, (mn, ops) in S.asm().range(0x006BE000, 0x006C1000):
        if re.search(r"\+0x(870|874|5bc)\]", ops or ""):
            acc[T.pad_entry(va)].append("0x%08X %s %s" % (va, mn, ops))
    r.c["field_functions"] = len(acc)
    for e in sorted(acc):
        r.note("0x%08X: %s" % (e, "; ".join(acc[e])))
    calls, other, ab = A7.calls_of(0x006BEAD0)
    r.c["pop_calls"] = len(calls)
    r.note("NetQueuePop callers: %s" % ", ".join("0x%08X %s" % (s, A7.nm(s)) for s in calls))
    bad += r.done()

    # ---- frame 29: g_SrvPacketTable and the mode-test switch
    r = Rep("frame", "row29_SrvPacketTable")
    for va, mn, sub in ((0x0054D756, "mov", "al,byte[eax]"), (0x0054D758, "test", "al,al"),
                        (0x0054D766, "cmp", "al,0x67"), (0x0054D768, "jae", "0x54d82a"),
                        (0x0054D772, "cmp", "dword[ebx*8+0x6e0d18],0x0"), (0x0054D788, "lea", "eax,[ebx-0x14]"),
                        (0x0054D78B, "cmp", "eax,0x52"), (0x0054D790, "movzx", "ecx,byte[eax+0x54d848]"),
                        (0x0054D797, "jmp", "[ecx*4+0x54d838]"), (0x0054D7A2, "cmp", "dword[esi+0x10],0x11"),
                        (0x0054D7B0, "call", "0x57eec0"), (0x0054D7DC, "call", "[0x6cc34c]"),
                        (0x0054D818, "call", "eax")):
        expect(r, va, mn, sub)
    r.c["bad"] += int([norm(x) for x in (A7.args(0x0054D7B0, 3) or [])] != ["0x1", "0x0", "0x0"])
    jt = [dw(0x0054D838 + 4 * i) for i in range(4)]
    idx = [byte(0x0054D848 + i) for i in range(0x53)]
    cls = {}
    for i, v in enumerate(idx):
        cls[i + 0x14] = {0x0054D7A8: "test", 0x0054D7C0: "skip", 0x0054D79E: "mode11"}.get(jt[v], "?")
    skip = sorted(k for k, v in cls.items() if v == "skip")
    mode = sorted(k for k, v in cls.items() if v == "mode11")
    r.note("jump table %s; skip %s; only in mode 0x11 %s" % ([hex(x) for x in jt], [hex(k) for k in skip],
                                                             [hex(k) for k in mode]))
    r.c["bad"] += int(skip != [0x14, 0x15, 0x3C, 0x43, 0x66]) + int(mode != [0x41]) + \
        sum(1 for v in cls.values() if v == "?")
    ent = [dw(0x006E0D18 + 8 * i) for i in range(0x67)]
    r.c["handlers"] = sum(1 for i in range(1, 0x67) if ent[i])
    nulls = [i for i in range(1, 0x67) if not ent[i]]
    r.note("null entries 0x01..0x66: %s; entry 0: %s" % ([hex(i) for i in nulls], hex(ent[0])))
    r.c["bad"] += sum(1 for i in range(1, 0x67) if ent[i] and not (0x401000 <= ent[i] < 0x6CB5A1))
    r.c["exceptions_with_handler"] = sum(1 for k in skip + mode if ent[k])
    r.note("second dwords: %s" % sorted(set(dw(0x006E0D18 + 8 * i + 4) for i in range(0x67))))
    # queue 1 is popped from the one context word, the pop's only caller of index 1
    r.c["pop1_calls"] = len(A7.calls_of(0x0052B2D0)[0])
    r.note("NetQueuePop1 callers: %s" % ", ".join("0x%08X %s" % (s, A7.nm(s)) for s in A7.calls_of(0x0052B2D0)[0]))
    bad += r.done()

    # ---- frame 44: the four event tables and dispatches
    r = Rep("frame", "row44_EventDispatch")
    tabs = (("player", 0x006E1810), ("monster", 0x006E2490), ("object", 0x006E19B0), ("item", 0x006E117C))
    for nmx, t in tabs:
        e = [dw(t + 4 * i) for i in range(15)]
        r.note("%s 0..14: %s" % (nmx, " ".join("%d:%s" % (i, ("%X" % x) if x else "0") for i, x in enumerate(e))))
        r.c["bad"] += int(e[14] != 0) + sum(1 for x in e if x and not (0x401000 <= x < 0x6CB5A1))
        refs = absx(t)
        r.c["%s_refs" % nmx] = len(refs)
        if nmx == "object":
            r.c["bad"] += int(e[12:15] != [0, 0, 0])
    for va, mn, sub in ((0x00581226, "cmp", "eax,0xe"), (0x00581229, "ja", "0x581242"),
                        (0x00581232, "test", "eax,eax"), (0x00581234, "je", "0x581242"),
                        (0x005A7F89, "cmp", "edi,0xe"), (0x005A7F90, "ja", "0x5a7fd8"),
                        (0x005A7FC6, "test", "eax,eax"), (0x005A7FC8, "je", "0x5a7fd8"),
                        (0x00586AD7, "mov", "eax,dword[ebx*4+0x6e19b0]"), (0x00586AE5, "call", "[0x6cc34c]"),
                        (0x00586B09, "call", "0x681e09"),
                        (0x00562DA7, "mov", "eax,dword[ebx*4+0x6e117c]"), (0x00562DB5, "call", "[0x6cc34c]"),
                        (0x00562DD9, "call", "0x681e09"),
                        (0x00540FB9, "movzx", "edx,byte[esi]"), (0x0054101D, "movzx", "ecx,byte[esi]"),
                        (0x005410B9, "movzx", "edx,byte[esi]"),
                        (0x005ADCC4, "call", "0x5adbb0"), (0x005ADCCA, "ret", "0x4")):
        expect(r, va, mn, sub)
    imp = T.r2("ii~0x006cc34c").strip()
    r.c["bad"] += int("IsBadCodePtr" not in imp)
    # the object and item dispatches read no kind bound: no cmp of the kind between entry and the table read
    for e, ld in ((0x00586AD0, 0x00586AD7), (0x00562DA0, 0x00562DA7)):
        r.c["bad"] += sum(1 for va, (mn, ops) in text_range(e, ld) if mn == "cmp")
    for d, runner in ((0x005ADCC0, "MissileEventsRun"), (0x00581220, "PlayerEventsRun"),
                      (0x005A7F80, "MonEventsRun"), (0x00586AD0, "ObjEventsRun"), (0x00562DA0, "ItemEventsRun")):
        c = A7.calls_of(d)[0]
        r.note("0x%08X called from %s" % (d, ", ".join("0x%08X %s" % (s, A7.nm(s)) for s in c)))
        r.c["bad"] += int(len(c) != 2 or any(runner not in A7.nm(s) for s in c))
    bad += r.done()
    return bad


# ================================================================================================== path
def chk_path():
    bad = 0
    A = S.asm()
    # ---- README 7: point slots and the record's extent
    r = Rep("path", "readme7_PointSlots")
    expect(r, 0x00649D17, "mov", "edx,0x200")
    expect(r, 0x00649D1C, "call", "0x40b430")
    expect(r, 0x00649D21, "push", "0x200")
    expect(r, 0x00649D2A, "call", "0x681ef0")
    r.c["slots"] = (0x1D4 - 0x9C) // 4
    r.c["bad"] += int(r.c["slots"] != 78)
    p1d4 = [(va, mn, ops) for va, (mn, ops) in A.range(0x00648000, 0x00651000) if "+0x1d4]" in (ops or "")]
    r.c["path_module_0x1D4_refs"] = len(p1d4)
    for x in p1d4:
        r.note("+0x1D4 in the path module: 0x%08X %s %s" % x)
    r.c["bad"] += int(len(p1d4) == 0)
    expect(r, 0x00648DA7, "cmp", "byte[eax+0x91],0x4e")
    bad += r.done()

    # ---- README 8: the two masks
    r = Rep("path", "readme8_TwoMasks")
    for va, mn, sub in ((0x00648C8A, "mov", "dword[esi+0x4c],ecx"), (0x00648C54, "mov", "ecx,dword[esi+0x4c]"),
                        (0x00648C6C, "mov", "ecx,dword[esi+0x4c]"), (0x00648C65, "call", "0x64eba0"),
                        (0x00648C7D, "call", "0x64ec10"), (0x00648CA9, "call", "0x64ea00"),
                        (0x00648CC3, "call", "0x64ea90"),
                        (0x00648CE9, "mov", "dword[ecx+0x50],eax"), (0x00648CD6, "mov", "eax,dword[eax+0x50]"),
                        (0x00649DB5, "mov", "dword[esi+0x4c],ebx"), (0x00649DB8, "mov", "dword[esi+0x50],ebx"),
                        (0x00649DCA, "mov", "dword[esi+0x4c],0x100"), (0x00649E73, "mov", "dword[esi+0x4c],0x80"),
                        (0x00649E7A, "mov", "dword[esi+0x50],0x1c09"), (0x00649E60, "mov", "dword[esi+0x50],0x804"),
                        (0x00649E4A, "mov", "dword[esi+0x50],eax"),
                        (0x00649A1E, "mov", "edx,dword[edi+0x50]"), (0x00649B3A, "mov", "ecx,dword[edi+0x50]")):
        expect(r, va, mn, sub)
    # the grid writers PATH_SetMarkMask feeds: what each pushes as its mask argument (the last push before the call)
    for c in (0x00648C65, 0x00648C7D, 0x00648CA9, 0x00648CC3):
        a = A7.args(c, 5)
        r.note("0x%08X -> %s args %s" % (c, A7.nm(int(A.at(c)[1], 16)), a))
    # stores to +0x4C / +0x50 in the PATH_ functions (0x00648000..0x0064A000): the setters and creation only
    st = collections.Counter()
    for va, (mn, ops) in A.range(0x00648000, 0x0064A000):
        m = re.match(r"^DWORD PTR \[e[a-z]{2}\+0x(4c|50)\],", ops or "")
        if m and mn in ("mov", "or", "and"):
            st[(m.group(1), T.owner(va)[0])] += 1
    for (off, e), n in sorted(st.items()):
        r.note("store +0x%s in 0x%08X %s: %d" % (off.upper(), e, T.owner(e)[1], n))
    r.c["bad"] += sum(n for (off, e), n in st.items() if e not in (0x00648C30, 0x00648CE0, 0x00649D00))
    bad += r.done()

    # ---- README 11: the missile's test mask
    r = Rep("path", "readme11_MissileMask")
    for va, mn, sub in ((0x0059FD6C, "movzx", "ecx,byte[eax+0x183]"), (0x0059FD73, "mov", "edx,dword[ecx*8+0x73c724]"),
                        (0x0059FD7A, "push", "edx"), (0x0059FD7B, "push", "edi"), (0x0059FD7C, "call", "0x648ce0")):
        expect(r, va, mn, sub)
    tab = [(dw(0x0073C720 + 8 * i), dw(0x0073C724 + 8 * i)) for i in range(9)]
    r.note("g_MissileCollideTypes: %s" % ", ".join("%d:(%X,%X)" % (i, f, m) for i, (f, m) in enumerate(tab)))
    rows = S.tsv("missiles")
    ct = collections.Counter(x["CollideType"] or "0" for x in rows)
    r.c["missile_rows"] = len(rows)
    r.note("CollideType: %s -> masks %s" % (sorted(ct.items()), {k: hex(tab[int(k)][1]) for k in ct}))
    r.c["bad"] += sum(n for k, n in ct.items() if not k.isdigit() or int(k) > 8)
    calls = A7.calls_of(0x00648CE0)[0]
    miss = [s for s in calls if 0x0059FA30 <= T.pad_entry(s) < 0x005B0000]
    r.c["setcollmask_calls"], r.c["missile_module_calls"] = len(calls), len(miss)
    r.note("PathSetCollMask in the missile module: %s" % ", ".join("0x%08X %s" % (s, A7.nm(s)) for s in miss))
    r.c["bad"] += int(miss != [0x0059FD7C])
    bad += r.done()

    # ---- README 16: Whirlwind's masks
    r = Rep("path", "readme16_WhirlwindMasks")
    expect(r, 0x005D9042, "push", "0xc01")
    expect(r, 0x005D9050, "call", "0x648ce0")
    expect(r, 0x005D90AE, "push", "0x401")
    expect(r, 0x005D90B4, "call", "0x648ce0")
    for m in (0xC01, 0x401):
        r.c["bad"] += int(m & (0x100 | 0x1000 | 0x2000) != 0)
    r.c["plan_has_0x800"], r.c["flight_has_0x800"] = int(bool(0xC01 & 0x800)), int(bool(0x401 & 0x800))
    r.note("pushes at the four Whirlwind PathSetCollMask calls: %s" % ", ".join(
        "0x%08X %s" % (s, A7.args(s, 2)) for s in calls if 0x005D8F50 <= s < 0x005D9460))
    bad += r.done()

    # ---- README 44: PathSetType's arguments on the server
    r = Rep("path", "readme44_MissilePathType")
    calls = A7.calls_of(0x00648CF0)[0]
    srv = [s for s in calls if s >= 0x00520000]
    r.c["calls"], r.c["server_calls"] = len(calls), len(srv)
    for s in srv:
        a = A7.args(s, 2)
        n = A7.nm(s)
        const = a is not None and re.match(r"^(0x[0-9a-f]+|\d+)$", a[1] or "")
        missile = "Miss" in n or "Hammer" in n
        r.c["const" if const else "register"] += 1
        if missile:
            r.c["missile_sites"] += 1
            r.c["bad"] += int(not const)
        r.note("0x%08X %-45s type %s%s" % (s, n, a[1] if a else None, "  (missile)" if missile else ""))
    bad += r.done()

    # ---- README 67: Jump in every excel table
    r = Rep("path", "readme67_Jump")
    hits = collections.Counter()
    for fn in sorted(os.listdir(S.EXCEL)):
        if not fn.lower().endswith(".txt"):
            continue
        r.c["tables"] += 1
        with open(os.path.join(S.EXCEL, fn), errors="replace") as f:
            rd = list(csv.reader(f, delimiter="\t"))
        for row in rd[1:]:
            for j, c in enumerate(row):
                if c.strip().lower() == "jump":
                    hits[(fn, rd[0][j] if j < len(rd[0]) else str(j))] += 1
    r.note("cells equal to Jump: %s" % dict(hits))
    r.c["bad"] += sum(n for (fn, col), n in hits.items() if (fn.lower(), col) != ("skills.txt", "skill"))
    st47 = [(x["skill"], x["Id"]) for x in S.tsv("skills") if x["srvstfunc"] == "47"]
    r.note("srvstfunc 47: %s" % st47)
    r.c["bad"] += int(st47 != [("Jump", "165")])
    bad += r.done()

    # ---- search 3: g_DirOctant
    r = Rep("path", "search3_DirOctant")
    o = [dw(0x006F1518 + 4 * i) for i in range(75)]
    r.c["values"] = len(o)
    r.c["bad"] += sum(1 for v in o if v > 7)
    r.note("distinct %s; column 0 %s" % (sorted(set(o)), [o[3 * i] for i in range(25)]))
    expect(r, 0x006794BC, "cmp", "dword[eax+0x8],0xff")
    expect(r, 0x006794C5, "push", "0x4c")
    bad += r.done()

    # ---- search 26: the pass and try bounds
    r = Rep("path", "search26_Bounds")
    for va, mn, sub in ((0x0067AC57, "cmp", "eax,0x10"), (0x0067AC69, "movzx", "eax,byte[edi+0x1c]"),
                        (0x0067AC7B, "movzx", "eax,byte[edi+0x1c]"), (0x0067ACAB, "call", "0x67a740"),
                        (0x0067ACB0, "add", "ebx,0x5"), (0x0067ACB7, "cmp", "dword[ebp-0x30d84],0x384"),
                        (0x0067ACD1, "cmp", "ebx,dword[ebp-0x4]"), (0x0067ACD4, "jl", "0x67ac90"),
                        (0x0067A77E, "cmp", "eax,0x2710"), (0x0067A786, "jg", "0x67a861")):
        expect(r, va, mn, sub)

    def passes(h0, b1c, t16):
        first = (h0 + (h0 >> 1)) if t16 else h0          # i16; h0 below 0x8000 here
        last = max(first, b1c)
        n, b = 0, first
        while True:
            n += 1
            b += 5
            if not b < last:
                return n
    mx = max(passes(h, b, t) for h in range(0, 600) for b in range(256) for t in (0, 1))
    r.c["max_passes"] = mx
    r.c["max_passes_h0_ge2"] = max(passes(h, b, t) for h in range(2, 600) for b in range(256) for t in (0, 1))
    r.c["bad"] += int(r.c["max_passes_h0_ge2"] != 51)
    bad += r.done()

    # ---- search 27: g_PathSearchTurnRows
    r = Rep("path", "search27_TurnRows")
    t = [dw(0x006F17D8 + 4 * i) for i in range(64)]
    zero0 = [k for k in range(8) if t[8 * k] == 0]
    r.note("rows: %s" % [t[8 * k:8 * k + 8] for k in range(8)])
    r.note("rows with entry 0 = 0: %s" % zero0)
    r.c["bad"] += int(zero0 != [0, 1, 2, 6, 7])
    expect(r, 0x0067AC41, "mov", "dword[ebp-0x14],0x6f17d8")
    bad += r.done()

    # ---- search 30: room_extent rerun against the kept a67 outputs
    r = Rep("path", "search30_RoomExtent")
    new = os.path.join(S.LOGS, "n66o", "s7f", "room_extent")
    old = os.path.join(S.LOGS, "a67")
    for f in ("report.txt", "levels.tsv", "lvlprest.tsv"):
        h = [hashlib.sha256(open(os.path.join(d, f), "rb").read()).hexdigest() for d in (new, old)]
        r.note("%s %s %s" % (f, h[0][:16], "equal" if h[0] == h[1] else "DIFFERS " + h[1][:16]))
        r.c["bad"] += int(h[0] != h[1])
    # the maze sizes from the .txt table, a second source beside lvlmaze.bin
    mz = [(int(x["SizeX"] or 0), int(x["SizeY"] or 0), x.get("Level") or x.get("Name")) for x in S.tsv("lvlmaze")]
    r.c["lvlmaze_rows"] = len(mz)
    r.note("LvlMaze.txt largest %s" % (max((a, b) for a, b, _ in mz),))
    side, rect = 12 * 5, 12 * 5 + 20
    r.c["room"], r.c["rect"], r.c["clear"] = side, rect, (rect + 6) ** 2
    pair = side + 5 * 5 + side
    r.c["pair_side"], r.c["pair_clear"] = pair, (pair + 6) ** 2
    r.c["bad"] += int((r.c["clear"], r.c["pair_side"], r.c["pair_clear"]) != (7396, 145, 22801))
    bad += r.done()

    # ---- search 35: PathPlan's tail has no count test above 78
    r = Rep("path", "search35_PlanTail")
    expect(r, 0x00649BAE, "call", "eax")
    expect(r, 0x00649BB8, "mov", "dword[edi+0x28],eax")
    seq = text_range(0x00649BA1, 0x00649C6F)
    cmps = [(va, ops) for va, (mn, ops) in seq if mn in ("cmp", "test")]
    for va, ops in cmps:
        r.note("0x%08X %s" % (va, ops))
    r.c["compares"] = len(cmps)
    r.c["bad"] += sum(1 for va, ops in cmps if re.search(r"0x4[de]\b", ops))
    bad += r.done()
    return bad


# ================================================================================================== lifecycle
PAIRS = [
    # (row, field, [(va, mnemonic, operand) ...] writers, [...] readers)
    ("38", "room record: x desc, y key, three heads, next", [
        (0x00541D8B, "mov", "edx,0x18"), (0x00541D9C, "mov", "dword[eax+0x8],ecx"),
        (0x00541D9F, "mov", "dword[eax+0xc],ecx"), (0x00541DA2, "mov", "dword[eax+0x10],ecx"),
        (0x00541DA5, "mov", "dword[eax],ebx"), (0x00541DA7, "mov", "dword[eax+0x4],edx"),
        (0x00541DAA, "mov", "dword[eax+0x14],esi"),
        (0x00542EA3, "mov", "edx,0x18"), (0x00542EC5, "mov", "dword[eax],ecx"),
        (0x00542ECA, "mov", "dword[eax+0x4],edx"), (0x00542ECD, "mov", "dword[eax+0x14],ebx")], [
        (0x00541D40, "mov", "ecx,dword[esi]"), (0x00541D42, "cmp", "ebx,ecx"), (0x00541D49, "cmp", "eax,dword[esi+0x4]"),
        (0x00541D50, "jg", "0x541d62"), (0x00541D54, "mov", "esi,dword[esi+0x14]"),
        (0x00542E83, "jg", "0x542e90"),
        (0x00541C37, "mov", "edx,dword[eax+0x8]"), (0x00541C3C, "mov", "dword[eax+0x8],ecx"),
        (0x005424D8, "mov", "ecx,dword[eax+0xc]"), (0x005424DE, "mov", "dword[eax+0xc],edi"),
        (0x00543069, "mov", "eax,dword[ebx+0x10]"), (0x0054306F, "mov", "dword[ebx+0x10],esi"),
        (0x0054193C, "mov", "eax,dword[edx+0x10]"), (0x00541944, "mov", "eax,dword[edx+0x8]"),
        (0x00542528, "mov", "ebx,dword[eax+0xc]")]),
    ("39", "item record: next, expiry, 0x00629F20(item), n, bytes", [
        (0x00541B34, "call", "0x629f20"), (0x00541B4C, "mov", "dword[ebp-0x40c],eax"),
        (0x00541B52, "mov", "dword[ebp-0x414],0x0"), (0x00541B3F, "push", "0x400"), (0x00541B5C, "call", "0x6313e0"),
        (0x00541B65, "mov", "word[ebp-0x408],ax"), (0x00541B6C, "call", "0x558a10"),
        (0x00541B8C, "mov", "dword[ebp-0x410],eax"), (0x00541B82, "add", "esi,0xf"), (0x00541BA6, "call", "0x6829c0")], [
        (0x0054199B, "movzx", "edi,word[ebx+0xc]"), (0x005419A6, "lea", "esi,[ebx+0xe]"), (0x005419AA, "call", "0x62e410"),
        (0x005419DB, "mov", "ebx,dword[ebx+0x4]"), (0x00541AD0, "mov", "eax,dword[esi+0x4]"),
        (0x00541AD5, "mov", "edi,dword[esi]")]),
    ("40", "monster record +0x18 flag 0x40", [
        (0x0054235A, "call", "0x573540"), (0x00542363, "or", "dword[edi+0x18],0x40")], [
        (0x00542934, "mov", "ecx,dword[ebx+0x18]"), (0x00542937, "and", "ecx,0x40"), (0x00542954, "call", "0x547ed0")]),
    ("41", "+0x1C group leader id", [
        (0x0054224B, "mov", "dword[edi+0x1c],0xffffffff"), (0x00542463, "call", "0x58f440"),
        (0x0054246B, "cmp", "eax,0xffffffff"), (0x00542470, "cmp", "dword[ebp-0x8],ebx"),
        (0x00542475, "mov", "dword[edi+0x1c],eax"),
        (0x0058F46C, "cmp", "dword[esi+0x30],0x1"), (0x0058F47D, "mov", "eax,dword[esi+0x2c]"),
        (0x0058F44E, "mov", "dword[edx],0xffffffff")], [
        (0x005427E7, "mov", "edx,dword[ebx+0x1c]"), (0x005427FB, "call", "0x58f4d0")]),
    ("42", "+0x20 AI control +0x34; +0x24 the path moved from AI control +0x38; +0x28 AI control's first dword", [
        (0x0058F4AF, "mov", "eax,dword[esi+0x34]"), (0x0058F4BB, "mov", "dword[esi+0x34],0x0"),
        (0x0054247B, "mov", "dword[edi+0x20],edx"),
        (0x0058F016, "mov", "eax,dword[eax+0x28]"), (0x0058F019, "add", "eax,0x38"),
        (0x00542093, "lea", "edx,[edi+0x24]"), (0x00542098, "call", "0x666120"),
        (0x00666120, "mov", "eax,dword[ecx]"), (0x00666122, "mov", "dword[edx],eax"),
        (0x00666124, "mov", "dword[ecx],0x0"),
        (0x005422C9, "mov", "ecx,dword[eax+0x28]"), (0x005422D0, "call", "0x5b0d60"),
        (0x005B0D60, "mov", "eax,dword[ecx]"), (0x005422D7, "mov", "dword[edi+0x28],eax")], [
        (0x005425D6, "mov", "edx,dword[ebx+0x20]"), (0x005427DD, "mov", "edx,dword[ebx+0x20]"),
        (0x00541E91, "lea", "edi,[ebx+0x24]"), (0x00541E94, "call", "0x58f000"), (0x00541EA2, "call", "0x666120"),
        (0x00542959, "mov", "edx,dword[ebx+0x24]"), (0x00542963, "call", "0x666130"),
        (0x00542862, "mov", "ecx,dword[ebx+0x28]"), (0x0054286B, "call", "0x5b0e00")]),
    ("43", "+0x2C monster data +0x58", [
        (0x005423EE, "call", "0x573520"), (0x005423F5, "mov", "dword[edi+0x2c],eax"),
        (0x00573533, "mov", "eax,dword[ecx+0x58]")], [
        (0x00542928, "mov", "ecx,dword[ebx+0x2c]"), (0x00542949, "mov", "edx,dword[ebp-0x20]"),
        (0x00542954, "call", "0x547ed0")]),
    ("44", "+0x30 name seed, +0x32 nine mods, +0x3C superunique id", [
        (0x005422DA, "call", "0x5a0140"), (0x005422DF, "mov", "word[edi+0x30],ax"),
        (0x005423F8, "call", "0x5a0120"), (0x00542404, "mov", "byte[edi+0x32],cl"),
        (0x0054243B, "mov", "byte[edi+0x3a],al"),
        (0x00542305, "call", "0x5a0180"), (0x0054230E, "or", "dword[edi+0x18],0x800"),
        (0x00542317, "call", "0x5a01e0"), (0x0054231C, "mov", "word[edi+0x3c],ax")], [
        (0x005426AF, "movzx", "eax,word[ebx+0x30]"), (0x00542676, "lea", "eax,[ebx+0x32]"),
        (0x00542696, "lea", "edx,[ebx+0x32]"), (0x005428A1, "lea", "edx,[ebx+0x32]"),
        (0x0054269A, "movzx", "edx,word[ebx+0x3c]"), (0x00541EC3, "cmp", "word[ebx+0x3c],0x6")]),
    ("45", "+0x4C, +0x50 AI parameters", [
        (0x0054202E, "mov", "dword[edi+0x4c],ecx"), (0x0054202B, "or", "dword[edi+0x50],edx"),
        (0x0054207F, "mov", "dword[edi+0x4c],ecx"), (0x00542085, "mov", "dword[edi+0x50],edx"),
        (0x00542133, "mov", "dword[edi+0x4c],eax")], [
        (0x00541E7D, "mov", "ecx,dword[ebx+0x4c]"), (0x00541E83, "mov", "edx,dword[ebx+0x50]"),
        (0x00541ECA, "cmp", "dword[ebx+0x4c],0x0"), (0x00541ED0, "cmp", "dword[ebx+0x50],0x0")]),
    ("46", "+0x58 next of the room's monster list", [
        (0x005424D8, "mov", "ecx,dword[eax+0xc]"), (0x005424DB, "mov", "dword[edi+0x58],ecx"),
        (0x005424DE, "mov", "dword[eax+0xc],edi")], [
        (0x00542563, "mov", "edx,dword[ebx+0x58]"), (0x00542A8D, "mov", "eax,dword[eax+0x58]")]),
    ("64", "+0x14 = unit +0xC8; bit 0x200 carried back", [
        (0x005424A1, "mov", "edx,dword[esi+0xc8]"), (0x005424AF, "mov", "dword[edi+0x14],edx")], [
        (0x005428F9, "mov", "eax,0x200"), (0x005428FE, "test", "dword[ebx+0x14],eax"),
        (0x00542901, "je", "0x542909"), (0x00542903, "or", "dword[esi+0xc8],eax")]),
    ("77", "the release at 0x00542098 and the restore's write back", [
        (0x00542089, "call", "0x58f000"), (0x0054208E, "cmp", "dword[eax],0x0"), (0x00542098, "call", "0x666120")], [
        (0x00541E99, "cmp", "dword[edi],0x0"), (0x00541E9E, "mov", "edx,eax"), (0x00541EA0, "mov", "ecx,edi"),
        (0x00541EA2, "call", "0x666120")]),
]


def chk_lifecycle():
    bad = 0
    A = S.asm()
    for row, what, wr, rd in PAIRS:
        r = Rep("lifecycle", "row%s" % row)
        r.note(what)
        for va, mn, sub in wr:
            if expect(r, va, mn, sub):
                r.c["writer_sites"] += 1
        for va, mn, sub in rd:
            if expect(r, va, mn, sub):
                r.c["reader_sites"] += 1
        if row == "39":
            # no reader of the item record's +0x08 in the restore pair
            rr = [va for va, (mn, ops) in list(A.range(0x00541990, 0x00541B10))
                  if re.search(r"\[e(?!bp)[a-z]{2}\+0x8\]", ops or "")]
            r.c["restore_reads_0x08"] = len(rr)
            r.note("+0x08 reads in InactiveItemRestoreOne/InactiveItemsRestore: %s" % ["0x%08X" % x for x in rr])
        if row == "44":
            pad = [va for lo, hi in ((0x005421A0, 0x005424F0), (0x005424F0, 0x00542AC0), (0x00541E20, 0x00541FE0))
                   for va, (mn, ops) in A.range(lo, hi) if re.search(r"\+0x3[bef]\]", ops or "")]
            r.c["padding_refs"] = len(pad)
            r.c["bad"] += len(pad)
        if row == "64":
            imm = [va for va, (mn, ops) in A.ins.items() if mn == "or" and
                   re.match(r"^DWORD PTR \[e[a-z]{2}\+0xc8\],0x[0-9a-f]+$", ops or "")
                   and int(ops.split(",")[1], 16) & 0x200]
            reg = [va for va, (mn, ops) in A.ins.items() if mn in ("or", "mov") and
                   re.match(r"^DWORD PTR \[e[a-z]{2}\+0xc8\],e[a-z]{2}$", ops or "")]
            r.c["imm_0x200_or_stores"], r.c["register_stores_0xC8"] = len(imm), len(reg)
            r.note("register or/mov stores to [reg+0xC8]: %s" % " ".join("0x%08X" % x for x in sorted(reg)))
        bad += r.done()

    # ---- 57, 61, 62, 63: the minions argument and the handler flag
    r = Rep("lifecycle", "row57_62_SpecialModsApplyArg3")
    for va, mn, sub in ((0x005A454E, "push", "0x0"), (0x005A4550, "push", "esi"), (0x005A4551, "push", "ebx"),
                        (0x005A4558, "call", "0x5a2120"), (0x005A2123, "cmp", "dword[ebp+0x10],0x0"),
                        (0x005A212D, "je", "0x5a213a"), (0x005A2135, "call", "0x5a0c00"),
                        (0x005A214D, "push", "0x1"), (0x005A21CA, "ret", "0xc")):
        expect(r, va, mn, sub)
    uses = [va for va, (mn, ops) in A.range(0x005A2120, 0x005A21CD) if "ebp+0x10" in (ops or "")]
    r.c["arg3_reads"] = len(uses)
    r.c["bad"] += int(uses != [0x005A2123])
    r.c["bad"] += int([norm(x) for x in (A7.args(0x005A4558, 3) or [])] != ["ebx", "esi", "0x0"])
    bad += r.done()

    r = Rep("lifecycle", "row61_63_MinionRestoreFlag0")
    for va, mn, sub in ((0x005A47DF, "or", "word[eax+0x16],0x10"), (0x005A47E4, "mov", "dword[ebp-0x10],0x1"),
                        (0x005A47EB, "mov", "dword[ebp-0xc],0x2"), (0x005A47F2, "mov", "dword[ebp-0x8],0x3"),
                        (0x005A47F9, "mov", "dword[ebp-0x4],0x4"), (0x005A4806, "mov", "eax,dword[edx*4+0x73c008]"),
                        (0x005A4811, "push", "0x0"), (0x005A4815, "call", "eax"), (0x005A481A, "cmp", "ebx,0x4"),
                        (0x005A4825, "mov", "eax,dword[edx*4+0x73c008]"), (0x005A4830, "push", "0x0"),
                        (0x005A4834, "call", "eax"), (0x005A4839, "cmp", "ebx,0x9"),
                        (0x005A0CE7, "cmp", "dword[ebp+0x8],0x0"), (0x005A0CEB, "je", "0x5a0d1a"),
                        (0x005A0CF0, "mov", "edx,0x6ac690c5"),
                        (0x005A138F, "cmp", "dword[ebp+0x8],0x0"), (0x005A1393, "je", "0x5a15eb")):
        expect(r, va, mn, sub)
    h = {i: dw(0x0073C008 + 4 * i) for i in (1, 2, 3, 4, 8, 27, 28)}
    r.note("handlers: %s" % {k: hex(v) for k, v in h.items()})
    r.c["bad"] += int(h[1] != 0x005A0CE0) + sum(int(h[k] != 0x005A1370) for k in (8, 27, 28))
    bad += r.done()

    # ---- 70: the drivers' bit-0 test
    r = Rep("lifecycle", "row70_DriverBit0")
    for va, mn, sub in ((0x0052D0FB, "test", "byte[esi+0x34],0x1"), (0x0052D0FF, "jne", "0x52d134"),
                        (0x0052D105, "call", "0x5559a0"), (0x0052D10E, "call", "0x542b40"),
                        (0x0052D117, "call", "0x552610"), (0x0052D120, "call", "0x54ec90"),
                        (0x0052D125, "or", "dword[esi+0x34],0x1"),
                        (0x0052D135, "call", "0x61a4d0"), (0x0052D13C, "jne", "0x52d14f"),
                        (0x0052D142, "call", "0x542b40"),
                        (0x0052D19B, "mov", "ebx,0x1"), (0x0052D1C9, "test", "byte[esi+0x34],bl"),
                        (0x0052D1CC, "jne", "0x52d1f7"), (0x0052D1D2, "call", "0x5559a0"),
                        (0x0052D1DB, "call", "0x542b40"), (0x0052D1E4, "call", "0x552610"),
                        (0x0052D1ED, "call", "0x54ec90"), (0x0052D1F8, "call", "0x61a4d0"),
                        (0x0052D1FF, "jne", "0x52d211"), (0x0052D205, "call", "0x542b40")):
        expect(r, va, mn, sub)
    # ebx is not written between 0x0052D19B and the test
    w = [va for va, (mn, ops) in A.range(0x0052D1A0, 0x0052D1C9) if (ops or "").startswith("ebx")]
    r.c["ebx_writes_between"] = len(w)
    r.c["bad"] += len(w)
    c = A7.calls_of(0x00542B40)[0]
    r.note("RoomInactiveUnitsRestore callers: %s" % ", ".join("0x%08X %s" % (s, A7.nm(s)) for s in c))
    bad += r.done()
    return bad


CHECKS = collections.OrderedDict([("frame", chk_frame), ("path", chk_path), ("lifecycle", chk_lifecycle)])


def main(argv):
    secs = list(CHECKS) if argv[1:] == ["all"] else argv[1:]
    bad = 0
    for s in secs:
        bad += CHECKS[s]()
    print("S7f total bad=%d" % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

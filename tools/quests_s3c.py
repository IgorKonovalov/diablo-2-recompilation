"""Plan 0066 Phase 1, batch S3c: exhaustive static scans with a second tool for the 51 class-c rows of quests/progression,
quests/travel and quests/README. No game, no Ghidra.

Usage:
  python3 -I tools/quests_s3c.py <section> [<section> ...]
  python3 -I tools/quests_s3c.py all

Tools. Every reference scan is taken three ways and compared: (1) a raw-byte pass over .text (the rel32 call/jmp/jcc
and abs32 rules of tools/xrefscan.py, one pass for every target), (2) objdump's linear listing (tools/sweep_s4b.py,
its `call 0x...` operands and its immediates), (3) r2, which re-decodes every site the first two name (one batched
r2 process per list of sites). A count line carries `agree=` (the three site sets equal) and `bad=` (an observation
against the statement the row tests). Call arguments are read twice: an objdump walk back from the call
(`push_args`, this file) and r2's (tools/sweep2_s4cd.pushes_before from the int3-padded entry).

Sections (inventory rows: P = quests-progression.md, T = quests-travel.md, R = quests-README.md):
  events    P1 P2 P35 P36 P37 P38 P45 P318: callers of the two dispatchers and of the raisers, the event index each
            caller stores at block +0x04, the direct slot calls `call [reg+0xA0+4e]` over all of .text
  record    P14 P19 P20 P68 P78 P124 P126 P229 P254 P28 P230: every call of QUESTRECORD_SetState / ClearState /
            ClearSteps / GetState, GameQuestSet / GameQuestGet, with its word and bit read by both walkers;
            per-word writer tables
  registry  P21-P33: g_QuestDescs (37 rows of 0x18) and the second table 0x0073188C (4 rows of 8) read by struct and
            by r2 `pxw`; every init's `+0xE0` store (objdump and r2)
  travel    T1 T30 T31 T33 T36 T78 T21 P314 P159 P321: UnitInteract case 2, the waypoint-record writers, the arrival
            list head, WaypointTravelCheck's calls, PlayerTickSet's callers, the collision map's dimension users
  act       P175 P319: readers of act +0x094, +0x484, +0x474 in the quest scripts' ranges
  misc      P6 P104 P316: NPC_MenuAction's switch, MissileCreateAt's callers' arguments, g_ObjInitFns
  data      P179 P302 R3 T56 T32 T30: a second DS1 parser (this file) over every .ds1, objgroup.txt, Levels.txt,
            SuperUniques.txt, Objects.txt Sync/FrameDelta, and the immediate scans for classes 567, 410, 377
Stdlib, objdump and r2. Read-only.
"""
import collections
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S  # noqa: E402
import sweep2_s4cd as T  # noqa: E402

EXE = S.EXE
BAD = collections.Counter()


def out(sec, name, **kv):
    bad = kv.pop("bad", 0)
    BAD[sec] += bad
    print("S3c %s %s %s bad=%d" % (sec, name, " ".join("%s=%s" % (k, kv[k]) for k in sorted(kv)), bad))


def note(s):
    print("  " + s)


def nm(va):
    e, n = T.owner(va)
    return n if e == va else "%s+0x%X" % (n, va - e)


# ------------------------------------------------------------------------------------------------ tool 1: raw bytes
_RAW = None


def raw_index():
    """{target: [(kind, site)]} for every rel32 call/jmp/jcc in executable sections (xrefscan.py's rules)."""
    global _RAW
    if _RAW is None:
        import xrefscan
        data = open(EXE, "rb").read()
        base, secs = xrefscan.sections(EXE)
        idx = collections.defaultdict(list)
        for s in secs:
            if not s["flags"] & xrefscan.IMAGE_SCN_MEM_EXECUTE:
                continue
            raw, rsize, va = s["raw"], min(s["rsize"], s["vsize"]), s["va"]
            blob = data[raw:raw + rsize]
            n = len(blob)
            for op, kind, ln in ((b"\xe8", "call", 5), (b"\xe9", "jmp", 5)):
                i = blob.find(op)
                while 0 <= i < n - 4:
                    rel = struct.unpack_from("<i", blob, i + 1)[0]
                    at = base + va + i
                    idx[(at + ln + rel) & 0xFFFFFFFF].append((kind, at))
                    i = blob.find(op, i + 1)
            i = blob.find(b"\x0f")
            while 0 <= i < n - 6:
                if 0x80 <= blob[i + 1] <= 0x8F:
                    rel = struct.unpack_from("<i", blob, i + 2)[0]
                    at = base + va + i
                    idx[(at + 6 + rel) & 0xFFFFFFFF].append(("jcc", at))
                i = blob.find(b"\x0f", i + 1)
        _RAW = idx
    return _RAW


def raw_abs(target):
    """abs32 occurrences of target in every section: [(section, va)]."""
    import xrefscan
    data = open(EXE, "rb").read()
    base, secs = xrefscan.sections(EXE)
    tb = struct.pack("<I", target)
    hits = []
    for s in secs:
        raw, rsize, va = s["raw"], min(s["rsize"], s["vsize"]), s["va"]
        blob = data[raw:raw + rsize]
        k = blob.find(tb)
        while k >= 0:
            hits.append((s["name"], base + va + k))
            k = blob.find(tb, k + 1)
    return hits


# ------------------------------------------------------------------------------------------------ tool 2: objdump
def A():
    return S.asm()


_OD_CALLS = None


def od_index():
    """{target: [(mnemonic, site)]} of every direct call/jmp/jcc operand in objdump's .text listing."""
    global _OD_CALLS
    if _OD_CALLS is None:
        idx = collections.defaultdict(list)
        for va, (mn, ops) in A().ins.items():
            if mn == "call" or mn.startswith("j"):
                t = S.branch_target(ops or "")
                if t is not None:
                    idx[t].append((mn, va))
        _OD_CALLS = idx
    return _OD_CALLS


# ------------------------------------------------------------------------------------------------ tool 3: r2
R2_LINE = re.compile(r"^\s*0x([0-9a-f]{8})\s+(\S+)\s*(.*?)\s*$")
_R2 = {}


def r2_many(vas):
    """{va: (mnemonic, operands)} from one r2 process decoding one instruction at each va."""
    need = [v for v in sorted(set(vas)) if v not in _R2]
    for k in range(0, len(need), 400):
        chunk = need[k:k + 400]
        cmd = ";".join("pd 1 @ 0x%x" % v for v in chunk)
        txt = subprocess.run(["r2", "-q", "-e", "scr.color=0", "-e", "asm.bytes=false", "-e", "asm.lines=false",
                              "-e", "asm.comments=false", "-e", "asm.xrefs=false", "-e", "asm.flags=false",
                              "-c", cmd, EXE], capture_output=True, text=True).stdout
        for ln in txt.splitlines():
            m = R2_LINE.match(ln)
            if m:
                _R2[int(m.group(1), 16)] = (m.group(2), m.group(3))
    return {v: _R2.get(v) for v in vas}


def r2_text(va):
    d = r2_many([va])[va]
    return "%s %s" % d if d else "?"


def r2_target(ops):
    return T.imm((ops or "").strip())


# ------------------------------------------------------------------------------------------------ references
def refs(target, kinds=("call",)):
    """The direct references of target by the three tools: (sites agreed, detail dict)."""
    raw = sorted(s for k, s in raw_index().get(target, []) if k in kinds or (k == "jcc" and "jcc" in kinds))
    od = sorted(s for mn, s in od_index().get(target, [])
                if (mn == "call" and "call" in kinds) or (mn == "jmp" and "jmp" in kinds)
                or (mn.startswith("j") and mn != "jmp" and "jcc" in kinds))
    dec = r2_many(sorted(set(raw) | set(od)))
    r2s = sorted(s for s, d in dec.items() if d and r2_target(d[1]) == target and
                 ((d[0] == "call" and "call" in kinds) or (d[0] == "jmp" and "jmp" in kinds) or
                  (d[0].startswith("j") and d[0] != "jmp" and "jcc" in kinds)))
    return raw, od, r2s


def ref_line(sec, label, target, want=None, kinds=("call",)):
    raw, od, r2s = refs(target, kinds)
    other = refs(target, tuple(k for k in ("call", "jmp", "jcc") if k not in kinds))
    ab = raw_abs(target)
    agree = int(raw == od == r2s)
    bad = 0
    if want is not None:
        bad = int(sorted(want) != r2s)
    out(sec, label, target="0x%08X" % target, raw=len(raw), objdump=len(od), r2=len(r2s), agree=agree,
        other_refs=len(other[0]) + len(other[1]), abs32=len(ab), bad=bad + (1 - agree))
    note("%s: %s" % (nm(target), ", ".join("0x%08X %s" % (s, nm(s)) for s in r2s)))
    for kd, s in sorted(set(other[0]) | set(other[1])):
        pass
    if other[0] or other[1]:
        note("other refs: %s" % ", ".join("0x%08X %s" % (s, nm(s)) for s in sorted(set(other[0]) | set(other[1]))))
    for secn, a in ab:
        note("abs32 in %s at 0x%08X (%s)" % (secn, a, nm(a) if secn == ".text" else "data"))
    return r2s


# ------------------------------------------------------------------------------------------------ argument walkers
REG32 = ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")


def od_listing(entry, site):
    return [(va, mn, ops or "") for va, (mn, ops) in A().range(entry, site + 1)]


def od_push_args(site, n, entry=None):
    """The first n stack arguments of the call at site from objdump's listing, walking back from the call over pushes
    (skipping the pushes consumed by intervening calls: their `ret N` from r2, or the `add esp, N` after)."""
    e = entry or T.pad_entry(site)
    ins = od_listing(e, site)
    if not ins or ins[-1][0] != site:
        return None
    res, skip = [], 0
    for va, mn, ops in reversed(ins[:-1]):
        if mn in ("ret",) or (mn == "sub" and ops.startswith("esp,")):
            break
        if mn == "add" and ops.startswith("esp,"):
            skip += (T.imm(ops.split(",")[1]) or 0) // 4
            continue
        if mn == "call":
            t = S.branch_target(ops)
            k = T.callee_pop(t) if t is not None else None
            skip += (k or 0) // 4
            continue
        if mn == "push":
            if skip:
                skip -= 1
            else:
                res.append(norm(ops))
                if len(res) >= n:
                    break
    return res


def norm(ops):
    """A common spelling for objdump's and r2's operands: lower case, no PTR, no spaces, hex immediates as ints."""
    s = (ops or "").lower().replace("dword ptr ", "").replace("byte ptr ", "").replace("word ptr ", "")
    s = s.replace("dword ", "").replace("byte ", "").replace("word ", "").replace(" ", "")
    m = re.match(r"^(?:0x([0-9a-f]+)|(\d+))$", s)
    if m:
        v = int(m.group(1), 16) if m.group(1) else int(m.group(2))
        if v >= 0xFFFFFF80 or v > 0xFFFFFFFF:
            v = v & 0xFFFFFFFF
        return str(v)
    return s


def r2_push_args(site, n):
    a = T.pushes_before(site, entry=T.pad_entry(site), want=n)
    return None if a is None else [norm(x) for x in a]


def push_args(site, n):
    """(objdump args, r2 args, agree)."""
    a, b = od_push_args(site, n), r2_push_args(site, n)
    return a, b, a == b


def reg_src(site, reg, entry=None):
    """The last objdump instruction before site (linear, from the padded entry) that writes reg: (va, mn, ops)."""
    e = entry or T.pad_entry(site)
    ins = od_listing(e, site)
    for k in range(len(ins) - 2, -1, -1):
        va, mn, ops = ins[k]
        dst = ops.split(",")[0].strip()
        if mn == "call" and reg in ("eax", "ecx", "edx"):
            return va, mn, ops
        if mn == "pop" and epilogue(ins, k):
            continue      # an earlier exit path's restore: the linear code after its ret keeps the register's value
        if dst == reg and mn not in ("cmp", "test", "push"):
            return va, mn, ops
    return None


def epilogue(ins, k):
    """True when the instruction at ins[k] is followed by a ret through pops and `mov esp, ebp` only."""
    for va, mn, ops in ins[k + 1:k + 7]:
        if mn == "ret":
            return True
        if mn == "pop" or (mn == "mov" and ops.replace(" ", "") == "esp,ebp") or mn == "leave":
            continue
        return False
    return False


def resolve(site, val, depth=0):
    """A pushed operand's value: an int, or the source text of the register it names (one step back)."""
    if val is None:
        return None
    if val.isdigit():
        return int(val)
    if val in REG32 and depth < 3:
        r = reg_src(site, val)
        if r is None:
            return "%s?" % val
        va, mn, ops = r
        src = norm(ops.split(",", 1)[1]) if "," in ops else norm(ops)
        if mn == "xor" and src == val:
            return 0
        if mn == "mov" and src.isdigit():
            return int(src)
        if mn == "mov" and src in REG32:
            return resolve(va, src, depth + 1)
        return "%s<-%s %s@0x%08X" % (val, mn, src, va)
    return val


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
    print("S3c total bad=%d %s" % (sum(BAD.values()), " ".join("%s=%d" % kv for kv in sorted(BAD.items()))))
    return 1 if sum(BAD.values()) else 0


SECTIONS = collections.OrderedDict()


def section(fn):
    SECTIONS[fn.__name__[4:]] = fn
    return fn


MEM = re.compile(r"\[([a-z]{3})(?:\+([a-z]{3})\*(\d))?([+-]0x[0-9a-f]+)?\]")


def memref(ops):
    """[(base, index, scale, disp)] of every memory operand in an objdump operand string."""
    res = []
    for m in MEM.finditer((ops or "").lower()):
        d = m.group(4)
        res.append((m.group(1), m.group(2), int(m.group(3) or 0), int(d, 16) if d else 0))
    return res


def expr(site, val, depth=0):
    """A backward expression for an operand at site (objdump, linear from the int3-padded entry): an int, `ret(T)` for
    a call's return, `arg(n)` for [ebp+8+4n], `[E+d]` for a load, `ecx@entry` etc. for a register the listing does not
    write; depth-limited to 7 steps ("..." beyond)."""
    if val is None:
        return "?"
    if depth > 7:
        return "..."
    v = norm(val)
    if v.isdigit():
        return int(v)
    if v in REG32:
        e = T.pad_entry(site)
        r = reg_src(site, v, entry=e)
        if r is None:
            return "%s@entry" % v
        va, mn, ops = r
        if mn == "call":
            import sweep2_s7a as S7
            k, _ = S7.zero_or_cmp(e, site, v)    # a tested return on a `jne` fall-through (r2's listing)
            if k is not None:
                return k
            t = S.branch_target(ops)
            return "ret(%s)" % (nm(t) if t else norm(ops))
        src = ops.split(",", 1)[1] if "," in ops else ""
        if mn == "xor" and norm(src) == v:
            return 0
        if mn in ("mov", "movzx", "movsx"):
            return expr(va, src, depth + 1)
        if mn == "lea":
            mr = memref(src)
            if mr:
                b, x, sc, d = mr[0]
                if x is None:
                    import sweep2_s7a as S7
                    k, _ = S7.zero_or_cmp(T.pad_entry(va), va, b)   # `cmp b, k; jne` fall-through (r2's listing)
                    if k is not None:
                        return k + d
                return "&(%s%+#x%s)" % (expr(va, b, depth + 1), d, "+%s*%d" % (x, sc) if x else "")
        if mn == "pop":
            return "pop@0x%08X" % va
        return "%s(%s)@0x%08X" % (mn, norm(src), va)
    mr = memref(v)
    if mr and len(mr) == 1:
        b, x, sc, d = mr[0]
        if b == "ebp" and x is None:
            if d >= 8:
                return "arg%d" % ((d - 8) // 4)
            # the last store to that local before site
            e = T.pad_entry(site)
            for va, mn, ops in reversed(od_listing(e, site)[:-1]):
                if mn == "mov" and memref(ops.split(",")[0]) == [("ebp", None, 0, d)]:
                    return expr(va, ops.split(",", 1)[1], depth + 1)
            return "local(%#x)" % (d & 0xFFFFFFFF)
        if x is None:
            return "[%s%+#x]" % (expr(site, b, depth + 1), d)
        return "[%s%+#x+%s*%d]" % (expr(site, b, depth + 1), d, x, sc)
    m = re.match(r"^\[?0x([0-9a-f]+)\]?$", v)
    if m:
        return "[0x%s]" % m.group(1)
    return v


# ================================================================================================== events
DISPATCH = {0x005438E0: "QUESTS_DispatchEvent", 0x005439A0: "QUESTS_DispatchUnitEvent"}
QUEST_CORE = (0x00543400, 0x00547200)   # the QUESTS_* core (re/symbols.csv: QUESTS_PlayerRecord .. WaypointArrivalAdd)


def block_event(site):
    """The event index a dispatcher call passes: EDI = lea [ebp-X] before the call, then the last store to
    [ebp-X+4] before it (objdump), re-decoded by r2."""
    e = T.pad_entry(site)
    ins = od_listing(e, site)
    lea = None
    for va, mn, ops in reversed(ins[:-1]):
        if mn == "lea" and ops.startswith("edi,"):
            lea = memref(ops)[0]
            break
        if ops.split(",")[0].strip() == "edi" and mn not in ("cmp", "test", "push"):
            return None, "edi from 0x%08X %s %s" % (va, mn, ops)
    if lea is None:
        return None, "no lea edi"
    base, _, _, disp = lea
    want = (base, None, 0, disp + 4)
    for va, mn, ops in reversed(ins[:-1]):
        if mn == "mov" and memref(ops.split(",")[0]) == [want]:
            v = norm(ops.split(",", 1)[1])
            r = r2_text(va)
            return (int(v) if v.isdigit() else v), "0x%08X %s / r2 %s" % (va, ops, r)
    return None, "no store to [%s%+#x]" % (base, disp + 4)


@section
def sec_events():
    raised = collections.defaultdict(list)
    for tgt, name in sorted(DISPATCH.items()):
        sites = ref_line("events", name, tgt)
        for s in sites:
            ev, how = block_event(s)
            raised[ev].append(s)
            note("0x%08X %s event=%s (%s)" % (s, nm(s), ev, how))
    note("events by index: %s" % ", ".join("%s: %s" % (k, " ".join("0x%08X" % s for s in v))
                                           for k, v in sorted(raised.items(), key=lambda kv: str(kv[0]))))
    # P1/P35/P36: the raisers of e4 and e5; P2/P37: QUESTS_MonsterDeathEvent; P38: QuestsInvItemEvent
    e4 = ref_line("events", "P1/P35 e4 raiser QUESTS_RaiseItemPlaced", 0x00543D80)
    e5 = ref_line("events", "P1/P36 e5 raiser QUESTS_RaiseItemDropped", 0x00543DB0)
    out("events", "P1 counts", e4=len(e4), e5=len(e5), bad=int(len(e4) != 7) + int(len(e5) != 1))
    md = ref_line("events", "P2/P37 QUESTS_MonsterDeathEvent", 0x00543A30, want=[0x0057CDD9])
    inv = ref_line("events", "P38 sub_00543BD0_QuestsInvItemEvent", 0x00543BD0)
    # P45: the two wrappers and the indices no caller passes
    w0 = ref_line("events", "P45 wrapper 0x00543CE0", 0x00543CE0, want=[])
    w6 = ref_line("events", "P45 wrapper 0x00543DE0", 0x00543DE0, want=[])
    live = {k for k, v in raised.items() if any(T.pad_entry(s) not in (0x00543CE0, 0x00543DE0) for s in v)}
    # the direct slot reads in the quest core: every memory operand with displacement 0xA0 + 4e, e = 0..14
    slots = collections.defaultdict(list)
    for va, (mn, ops) in A().range(*QUEST_CORE):
        for base, idx, sc, d in memref(ops):
            if 0xA0 <= d <= 0xD8 and (d - 0xA0) % 4 == 0 and base not in ("ebp", "esp"):
                slots[(d - 0xA0) // 4].append((va, mn, ops, idx))
    for e in sorted(slots):
        note("slot e%d (+0x%X): %s" % (e, 0xA0 + 4 * e, "; ".join("0x%08X %s %s %s" % (va, nm(va), mn, ops)
                                                                     for va, mn, ops, _ in slots[e])))
    r2d = r2_many([va for v in slots.values() for va, _, _, _ in v])
    disagree = [va for v in slots.values() for va, _, ops, _ in v
                if not r2d[va] or ("0x%x" % (0xA0 + 4 * ((memref(ops)[0][3] - 0xA0) // 4))) not in r2d[va][1]]
    direct = {e: v for e, v in slots.items() if any(i is None for *_, i in v)}
    out("events", "P45 live indices", live="+".join(str(k) for k in sorted(live, key=str)),
        dead_raised=sorted(set(raised) - live), slot_disp_reads=sum(len(v) for v in slots.values()),
        r2_disagree=len(disagree), direct_slots="+".join(str(e) for e in sorted(direct)),
        bad=len(disagree) + len({1, 6, 7, 12} & live) + len(w0) + len(w6))
    # P45, whole .text: an indirect call through a slot displacement, either `call [b+disp]` or a `mov r, [b+disp]`
    # whose register is called within the next 16 instructions with no write of it between (objdump; r2 re-decodes)
    ind = collections.defaultdict(list)
    order = A()._sorted or sorted(A().ins)
    A()._sorted = order
    for i, va in enumerate(order):
        mn, ops = A().ins[va]
        ops = ops or ""
        if mn == "call" and ops.startswith("DWORD PTR ["):
            for b, x, sc, d in memref(ops):
                if 0xA0 <= d <= 0xD8 and d % 4 == 0 and x is None:
                    ind[(d - 0xA0) // 4].append((va, va))
        elif mn == "mov" and ops.split(",")[0] in REG32 and "," in ops:
            mr = memref(ops.split(",", 1)[1])
            if mr and mr[0][1] is None and 0xA0 <= mr[0][3] <= 0xD8 and mr[0][3] % 4 == 0:
                r = ops.split(",")[0]
                for va2 in order[i + 1:i + 17]:
                    mn2, ops2 = A().ins[va2]
                    if mn2 == "call" and (ops2 or "").strip() == r:
                        ind[(mr[0][3] - 0xA0) // 4].append((va, va2))
                        break
                    if (ops2 or "").split(",")[0].strip() == r and mn2 not in ("cmp", "test", "push"):
                        break
    for e in sorted(ind):
        note("indirect call through +0x%X (e%d): %s" % (0xA0 + 4 * e, e, "; ".join(
            "0x%08X->0x%08X %s [r2 %s]" % (a, b, nm(a), r2_text(a)) for a, b in ind[e])))
    out("events", "P45 indirect slot calls over .text", **{"e%d" % e: len(v) for e, v in sorted(ind.items())})
    quest = sorted((a, b) for v in ind.values() for a, b in v if 0x00500000 <= a < 0x00680000)
    note("server-range (0x00500000-0x00680000) hits: %s" % ", ".join("0x%08X %s" % (a, nm(a)) for a, _ in quest))
    idx_reads = [(va, mn, ops) for va, (mn, ops) in A().ins.items()
                 if any(x is not None and sc == 4 and d == 0xA0 for b, x, sc, d in memref(ops))]
    note("indexed [b+x*4+0xa0] operands over .text: %s" % ", ".join("0x%08X %s" % (va, nm(va)) for va, _, _ in sorted(idx_reads)))
    out("events", "P45 server-range slot calls", n=len(quest), indexed_a0=len(idx_reads),
        bad=sum(1 for a, _ in quest if T.owner(a)[0] not in (0x005467E0, 0x00543BD0, 0x00546270)))
    # P318: QUESTS_HookMonster's callers
    hk = ref_line("events", "P318 QUESTS_HookMonster", 0x005436B0)
    out("events", "P318 owners", functions=len(set(T.pad_entry(s) for s in hk)), calls=len(hk),
        names="|".join(sorted(set(T.owner(s)[1] for s in hk))))


# ================================================================================================== record
REC_FNS = {0x0065C360: "SetState", 0x0065C3A0: "ClearState", 0x0065C3E0: "ClearSteps", 0x0065C310: "GetState"}
GQS, GQG = 0x00544720, 0x00544760


def func_bounds(va):
    """[entry, end) of the int3-padded function holding va (end: the next int3 pad after a ret)."""
    e = T.pad_entry(va)
    order = A()._sorted or sorted(A().ins)
    A()._sorted = order
    import bisect
    i = bisect.bisect_left(order, e)
    data = S.image()[0]
    while i < len(order):
        v = order[i]
        mn, _ = A().ins[v]
        if mn == "int3" or data[S.va_off(v)] == 0xCC:
            return e, v
        i += 1
    return e, order[-1]


def game_record_uses():
    """Every function reading the quest control (`[x+0x10f4]`), with the loads `[ctrl+0xc]` (the game record) a
    whole-function linear register taint finds (a register holding ctrl dies when written), and each such record
    register's uses up to its next write: pushes (with the call they feed) and stores through it."""
    res = []
    fns = sorted(set(T.pad_entry(va) for va, (mn, ops) in A().ins.items() if "+0x10f4]" in (ops or "")))
    for e in fns:
        lo, hi = func_bounds(e)
        ins = [(va, mn, ops or "") for va, (mn, ops) in A().range(lo, hi)]
        ctrl, rec = set(), {}
        found = []
        for k, (va, mn, ops) in enumerate(ins):
            dst = ops.split(",")[0].strip()
            src = ops.split(",", 1)[1] if "," in ops else ""
            if mn == "mov" and "+0x10f4]" in src and dst in REG32:
                ctrl.add(dst)
                rec.pop(dst, None)
                continue
            mr = memref(src)
            if mn == "mov" and dst in REG32 and mr and mr[0][0] in ctrl and mr[0][3] == 0xC and mr[0][1] is None:
                rec[dst] = va
                ctrl.discard(dst)
                uses = []
                for va2, mn2, ops2 in ins[k + 1:]:
                    d2 = ops2.split(",")[0].strip()
                    if mn2 == "push" and ops2.strip() == dst:
                        nxt = next(((v3, o3) for v3, m3, o3 in ins if v3 > va2 and m3 == "call"), None)
                        uses.append("push->call %s at 0x%08X" % (nm(S.branch_target(nxt[1]) or 0) if nxt else "?",
                                                               nxt[0] if nxt else 0))
                    elif any(b == dst for b, *_ in memref(d2)) and mn2 not in ("cmp", "test", "push"):
                        uses.append("store 0x%08X %s %s" % (va2, mn2, ops2))
                    elif mn2 == "mov" and ops2.split(",", 1)[-1].strip() == dst:
                        uses.append("copy 0x%08X %s %s" % (va2, mn2, ops2))
                    if d2 == dst and mn2 not in ("cmp", "test", "push"):
                        break
                    if mn2 == "call" and dst in ("eax", "ecx", "edx"):
                        break
                found.append((va, dst, uses))
                continue
            if dst in ctrl and mn not in ("cmp", "test", "push"):
                ctrl.discard(dst)
            if mn == "call":
                ctrl -= {"eax", "ecx", "edx"}
        res.append((e, found))
    return res


def word_bit(site, kind):
    """(word, bit, agree) of a record call: stack args 1 and 2 (GameQuestSet/Get: EDX and stack arg 0)."""
    if kind in ("GQS", "GQG"):
        r = reg_src(site, "edx")
        w = expr(site, "edx")
        a, b, ok = push_args(site, 1)
        r2e = T.r2_range(r[0], r[0] + 8)[0] if r else None
        ok2 = r is None or (r2e is not None and norm(r2e[2].split(",", 1)[-1]) == norm(r[2].split(",", 1)[-1]))
        return w, expr(site, a[0]) if a else "?", ok and ok2
    a, b, ok = push_args(site, 3)
    if not a or len(a) < 2:
        return "?", "?", False
    return expr(site, a[1]), (expr(site, a[2]) if len(a) > 2 else "-"), ok


@section
def sec_record():
    rows = []
    for t, name in sorted(REC_FNS.items()) + [(GQS, "GQS"), (GQG, "GQG")]:
        sites = ref_line("record", name, t)
        for s in sites:
            if name == "GetState" and s < 0x00500000:
                rows.append((name, s, "client", "client", True))
                continue
            w, b, ok = word_bit(s, name)
            rows.append((name, s, w, b, ok))
    dis = [r for r in rows if not r[4]]
    out("record", "args read twice", calls=len(rows), walkers_disagree=len(dis),
        client_getstate=sum(1 for r in rows if r[2] == "client"))
    for r in dis:
        a, b, _ = push_args(r[1], 3)
        note("disagree %s 0x%08X %s objdump=%s r2=%s" % (r[0], r[1], nm(r[1]), a, b))
    for r in rows:
        if r[2] != "client":
            print("  CALL %s 0x%08X %s word=%s bit=%s" % (r[0], r[1], nm(r[1]), r[2], r[3]))
    byw = collections.defaultdict(list)
    for r in rows:
        byw[r[2]].append(r)
    # A7 / P20 / P78 / P229 / P254: the writes per word immediate
    W = {"SetState", "ClearState", "ClearSteps", "GQS"}
    for w in (7, 15, 23, 28, 32, 33, 34, 41, 42, 43, 44, 45, 46, 47, 0, 9):
        ws = [r for r in byw.get(w, []) if r[0] in W]
        rs = [r for r in byw.get(w, []) if r[0] not in W]
        out("record", "word %d" % w, writes=len(ws), reads=len(rs),
            writers="|".join(sorted(set(T.owner(r[1])[1] for r in ws))) or "-",
            readers="|".join(sorted(set(T.owner(r[1])[1] for r in rs))) or "-")
        for r in ws:
            note("w%d %s 0x%08X %s bit=%s" % (w, r[0], r[1], nm(r[1]), r[3]))
    nonimm = [r for r in rows if r[2] != "client" and not isinstance(r[2], int)]
    out("record", "non-immediate words", n=len(nonimm), writes=sum(1 for r in nonimm if r[0] in W))
    for r in nonimm:
        note("%s 0x%08X %s word=%s bit=%s" % (r[0], r[1], nm(r[1]), r[2], r[3]))
    # P14: ClearState with bit 0
    c0 = [r for r in rows if r[0] == "ClearState" and r[3] == 0]
    out("record", "P14 ClearState bit 0", n=len(c0), sites=" ".join("0x%08X:w%s" % (r[1], r[2]) for r in c0))
    # P19: the game record's loads and uses
    for e, found in game_record_uses():
        for va, reg, uses in found:
            note("game record [ctrl+0xc] at 0x%08X %s -> %s: %s" % (va, nm(va), reg, "; ".join(uses) or "-"))
    return rows


# ================================================================================================== registry
DESCS, SECOND = 0x00731510, 0x0073188C
SPEC_ROWS = {  # quests/progression § B registry, as specified: row -> (quest object, act 0-based, word, init)
    0: (0, 0, 0, 0x0058FB80), 1: (1, 0, 1, 0x00590720), 2: (2, 0, 2, 0x00591210), 3: (3, 0, 3, 0x00591F70),
    4: (4, 0, 4, 0x005971B0), 5: (5, 0, 5, 0x00595920), 6: (6, 0, 6, 0x00596990), 7: (30, 0, 41, 0x00596C40),
    8: (7, 1, 8, 0x00598810), 9: (8, 1, 9, 0x00599340), 10: (9, 1, 10, 0x0059EB00), 11: (10, 1, 11, 0x0059EEA0),
    12: (11, 1, 12, 0x0059F2A0), 13: (12, 1, 13, 0x0059C280), 14: (13, 1, 14, 0x0059D5B0),
    15: (26, 1, 30, 0x0059E330), 16: (27, 1, 31, 0x0059E530), 17: (14, 2, 16, 0x005B7010),
    18: (15, 2, 17, 0x005B7E90), 19: (16, 2, 18, 0x005BDA30), 20: (17, 2, 19, 0x005B9850),
    21: (18, 2, 20, 0x005BAA70), 22: (19, 2, 21, 0x005BBEB0), 23: (20, 2, 22, 0x005BCDC0),
    24: (28, 2, 32, 0x005BD300), 25: (21, 3, 24, 0x005B3780), 26: (22, 3, 25, 0x005B42B0),
    27: (23, 3, 26, 0x005B54C0), 28: (24, 3, 27, 0x005B6610), 29: (25, 0, 29, 0x00596C40),
    30: (29, 3, 33, 0x005B6A70), 31: (31, 4, 35, 0x005876E0), 32: (32, 4, 36, 0x00588510),
    33: (33, 4, 37, 0x0058A410), 34: (34, 4, 38, 0x0058BB20), 35: (35, 4, 39, 0x0058CE30),
    36: (36, 4, 40, 0x0058E500),
}
SPEC_E0 = {7: 29, 24: 16, 29: 29}     # rows whose init writes +0xE0 other than the descriptor word (§ B registry)
SPEC_SECOND = [(37, 0, 0x0058FA20), (38, 1, 0x005985D0), (39, 2, 0x005B6E60), (40, 4, 0x0058EA50)]


def r2_words(va, n):
    txt = T.r2("pxw %d @ 0x%x" % (4 * n, va))
    vals = []
    for ln in txt.splitlines():
        parts = ln.split()
        if parts and parts[0].startswith("0x"):
            vals += [int(p, 16) for p in parts[1:5] if p.startswith("0x")]
    return vals[:n]


def init_e0(init):
    """The `+0xE0` stores in an init up to its first ret: [(va, value expr)] by objdump, each re-decoded by r2."""
    res = []
    for va, (mn, ops) in A().range(init, init + 0x400):
        if mn == "ret":
            break
        if mn == "mov" and memref((ops or "").split(",")[0]) and memref(ops.split(",")[0])[0][3] == 0xE0 \
                and memref(ops.split(",")[0])[0][1] is None:
            v = expr(va, ops.split(",", 1)[1])
            r = r2_many([va])[va]
            ok = r is not None and "0xe0]" in r[1]
            res.append((va, v, ok, "%s %s" % r if r else "?"))
    return res


@section
def sec_registry():
    import struct as st
    d = S.image()[0]
    b1 = bytes(d[S.va_off(DESCS):S.va_off(DESCS) + 37 * 0x18])
    w2 = r2_words(DESCS, 37 * 6)
    bad = 0
    for row in range(37):
        init, act, f2, flag, qid, word = st.unpack_from("<6I", b1, 0x18 * row)
        r2row = tuple(w2[6 * row:6 * row + 6])
        e0 = init_e0(init)
        e0v = [v for _, v, _, _ in e0]
        want = SPEC_ROWS[row]
        want_e0 = SPEC_E0.get(row, want[2])
        ok = (qid, act, word, init) == want and r2row == (init, act, f2, flag, qid, word) and e0v == [want_e0] \
            and all(o for _, _, o, _ in e0)
        bad += not ok
        print("  ROW %2d id=%2d act=%d word=%2d init=0x%08X f2=%d flag=%d r2=%s e0=%s %s" % (
            row, qid, act, word, init, f2, flag, "same" if r2row == (init, act, f2, flag, qid, word) else r2row,
            ["0x%08X=%s [r2 %s]" % (va, v, r) for va, v, o, r in e0], "ok" if ok else "MISMATCH"))
    n2 = len(SPEC_SECOND)
    b2 = bytes(d[S.va_off(SECOND):S.va_off(SECOND) + 8 * n2])
    w22 = r2_words(SECOND, 2 * n2)
    for k, (qid, act, init) in enumerate(SPEC_SECOND):
        i2, a2 = st.unpack_from("<2I", b2, 8 * k)
        e0 = init_e0(i2)
        ok = (i2, a2) == (init, act) and tuple(w22[2 * k:2 * k + 2]) == (i2, a2) and [v for _, v, _, _ in e0] == [42]
        bad += not ok
        print("  SECOND %d id=%d act=%d init=0x%08X e0=%s %s" % (k, qid, a2, i2, ["0x%08X=%s" % (va, v) for va, v, _, _ in e0],
                                                             "ok" if ok else "MISMATCH"))
    # the counts QUESTS_InitGame loops to: the dword after each table
    after1 = S.dword(DESCS + 37 * 0x18)
    after2 = S.dword(SECOND + 8 * n2)
    out("registry", "tables", rows=37, second=n2, count_after_main=after1, count_after_second=after2,
        bad=bad + int(after1 != 37) + int(after2 != 4))
    for c in (DESCS + 37 * 0x18, SECOND + 8 * n2):
        note("abs32 refs of 0x%08X: %s" % (c, ", ".join("%s 0x%08X %s" % (s, a, nm(a) if s == ".text" else "")
                                                       for s, a in raw_abs(c))))
    for c in (DESCS, SECOND):
        note("abs32 refs of 0x%08X: %s" % (c, ", ".join("%s 0x%08X %s [r2 %s]" % (
            s, a, nm(a) if s == ".text" else "", "") for s, a in raw_abs(c))))


# ================================================================================================== travel
QUEST_READERS = {0x0065C310: "QUESTRECORD_GetState", 0x00544760: "GameQuestGet", 0x00543520: "QUESTS_PlayerRecord",
                 0x00543640: "QUESTS_FindById"}


def calls_in(lo, hi):
    return [(va, S.branch_target(ops or "")) for va, (mn, ops) in A().range(lo, hi)
            if mn == "call" and S.branch_target(ops or "") is not None]


def reach(roots, stops=(), limit=4000):
    """Direct-call reach from roots (objdump call operands inside each function's int3-padded bounds): {fn: parent}."""
    par = {r: None for r in roots}
    todo = list(roots)
    while todo and len(par) < limit:
        f = todo.pop()
        if f in stops:
            continue
        lo, hi = func_bounds(f)
        for va, t in calls_in(lo, hi):
            if S.section_of(t) != ".text" if 0x00400000 <= t < 0x00800000 else True:
                continue
            if t not in par:
                par[t] = f
                todo.append(t)
    return par


def path(par, f):
    p = []
    while f is not None:
        p.append(nm(f))
        f = par[f]
    return " <- ".join(p)


def stores_disp(disp):
    """[(va, mn, ops)] of every objdump instruction writing a [base+disp] operand (no index)."""
    res = []
    for va, (mn, ops) in A().ins.items():
        d0 = (ops or "").split(",")[0]
        mr = memref(d0)
        if mr and mr[0][3] == disp and mr[0][1] is None and mn not in ("cmp", "test", "push", "call") \
                and not mn.startswith("j") and "," in (ops or ""):
            res.append((va, mn, ops))
    return sorted(res)


@section
def sec_travel():
    # T1: UnitInteract's switch, case 2, and the operate chain
    tab = S.dwords(0x00548E8C, 6)
    r2t = r2_words(0x00548E8C, 6)
    c2 = tab[2]
    nxt = min([x for x in tab if x > c2] + [0x00548E7B])
    cc = [(va, t) for va, t in calls_in(c2, nxt)]
    r2c = r2_many([va for va, _ in cc])
    out("travel", "T1 UnitInteract switch", jmp=r2_text(0x00548B12), table="0x00548E8C", case2="0x%08X" % c2,
        r2_same=int(tab == r2t), calls_case2=len(cc), bad=int(tab != r2t))
    for va, t in cc:
        note("case 2 call 0x%08X -> 0x%08X %s [r2 %s]" % (va, t, nm(t), "%s %s" % r2c[va]))
    ref_line("travel", "T1 callers of 0x00584540 (operate wrapper)", 0x00584540)
    ref_line("travel", "T1 OBJ_OperateDispatch", 0x00584420)
    note("table call: 0x00584504 %s ; 0x0058450E %s" % (r2_text(0x00584504), r2_text(0x0058450E)))
    note("distance test: 0x00548B6D %s ; 0x00548B70 %s" % (r2_text(0x00548B6D), r2_text(0x00548B70)))
    # T31: the arrival list head (objrgn +0x1110)
    hs = [(va, mn, ops) for va, (mn, ops) in A().ins.items() if any(d == 0x1110 and x is None
                                                                     for b, x, sc, d in memref(ops))]
    for va, mn, ops in sorted(hs):
        note("+0x1110 0x%08X %s %s %s [r2 %s]" % (va, nm(va), mn, ops, r2_text(va)))
    wr = [h for h in hs if memref(h[2].split(",")[0]) and mn != "cmp"]
    out("travel", "T31 arrival head +0x1110", operands=len(hs), writes=len([h for h in hs if memref(h[2].split(",")[0])]))
    ref_line("travel", "T31 WaypointArrivalAdd", 0x00547170, want=[0x00585108])
    # T33: waypoint record writers
    ref_line("travel", "T33 WAYPOINT_Set", 0x00660EC0)
    for t, n in ((0x00661030, "WAYPOINT_Load"), (0x00547F50, "PlayerWaypointRecord"), (0x00660E50, "WAYPOINT_IsSet")):
        ref_line("travel", "T33 %s" % n, t)
    # T36 / P314: WaypointTravelCheck's body and the waypoint paths' reach to the quest readers
    lo, hi = func_bounds(0x00549570)
    cs = calls_in(lo, hi)
    out("travel", "T36 WaypointTravelCheck", bounds="0x%08X-0x%08X" % (lo, hi), calls=len(cs),
        quest_calls=sum(1 for _, t in cs if t in QUEST_READERS), bad=sum(1 for _, t in cs if t in QUEST_READERS))
    for va, t in cs:
        note("call 0x%08X -> %s" % (va, nm(t)))
    for va, (mn, ops) in A().range(lo, hi):
        if mn == "cmp":
            note("cmp 0x%08X %s [r2 %s]" % (va, ops, r2_text(va)))
    for label, roots in (("P314 waypoint menu/travel", [0x00584E30, 0x0054C5D0, 0x00549570, 0x00584F60]),
                         ("P159/P321 Arcane portal init", [0x0059BA40]),
                         ("P314 waypoint init OBJINIT_Waypoint", [0x00547210])):
        hit = []
        seen = set()
        for r in roots:
            lo, hi = func_bounds(r)
            for va, t in calls_in(lo, hi):
                seen.add(t)
                if t in QUEST_READERS or t == GQG:
                    hit.append((va, r, t, 1))
                elif S.section_of(t) == ".text" and t not in (0x00408090, 0x00408A60, 0x00681E09):
                    lo2, hi2 = func_bounds(t)
                    for va2, t2 in calls_in(lo2, hi2):
                        seen.add(t2)
                        if t2 in QUEST_READERS or t2 == GQG:
                            hit.append((va2, t, t2, 2))
        out("travel", label, callees_depth2=len(seen), record_reads=sum(1 for h in hit if h[2] != 0x00543640),
            find_by_id=sum(1 for h in hit if h[2] == 0x00543640),
            bad=sum(1 for h in hit if h[2] != 0x00543640))
        for va, f, t, dep in hit:
            note("depth %d: 0x%08X in %s calls %s" % (dep, va, nm(f), nm(t)))
    # T78: PlayerTickSet and the stamp (player data +0x160)
    ref_line("travel", "T78 PlayerTickSet", 0x0055B720, want=[0x005A5F51])
    st = stores_disp(0x160)
    srv = [x for x in st if 0x00500000 <= x[0] < 0x00680000]
    out("travel", "T78 stores to +0x160 over .text", n=len(st), server_range=len(srv),
        bad=sum(1 for x in srv if T.pad_entry(x[0]) != 0x0055B720))
    for va, mn, ops in st:
        note("+0x160 store 0x%08X %s %s %s base=%s [r2 %s]" % (va, nm(va), mn, ops,
                                                               expr(va, memref(ops.split(",")[0])[0][0]), r2_text(va)))


# ================================================================================================== act
QUEST_NAME = re.compile(r"(QUESTS_|_A[1-5]Q\d|A1Intro|Quests|OBJINIT_Portal)")


@section
def sec_act():
    fns = [(int(l.split(",")[0], 16), l.split(",")[2]) for l in open(os.path.join(S.ROOT, "re", "symbols.csv"))
           if l.count(",") >= 3 and l.split(",")[1] == "func" and QUEST_NAME.search(l.split(",")[2])]
    hits = collections.defaultdict(list)
    for e, n in fns:
        lo, hi = func_bounds(e)
        for va, (mn, ops) in A().range(lo, hi):
            for b, x, sc, d in memref(ops):
                if d in (0x94, 0x484, 0x474) and x is None and b not in ("ebp", "esp"):
                    hits[d].append((va, n, mn, ops, expr(va, b)))
    out("act", "quest functions scanned", n=len(fns), d94=len(hits[0x94]), d484=len(hits[0x484]), d474=len(hits[0x474]))
    for d in (0x94, 0x484, 0x474):
        for va, n, mn, ops, b in hits[d]:
            note("+0x%X 0x%08X %s %s %s base=%s [r2 %s]" % (d, va, nm(va), mn, ops, b, r2_text(va)))
    for t, n in ((0x0061AEB0, "act +0x094 wrapper 0x0061AEB0"), (0x00642230, "act +0x094 getter 0x00642230")):
        ref_line("act", n, t)
    for d in (0x484, 0x474):
        ops_ = sorted((va, mn, ops) for va, (mn, ops) in A().ins.items()
                      if any(dd == d and x is None for b, x, sc, dd in memref(ops)))
        owners = collections.Counter(T.owner(va)[1] for va, _, _ in ops_)
        out("act", "+0x%X operands over .text" % d, n=len(ops_), functions=len(owners),
            quest=sum(v for k, v in owners.items() if QUEST_NAME.search(k)),
            bad=sum(v for k, v in owners.items() if QUEST_NAME.search(k)))
        note("owners: %s" % ", ".join("%s x%d" % kv for kv in sorted(owners.items())))
    # the level-27 bit: immediates 27 / 0x1B compared or pushed in the same functions
    l27 = []
    for e, n in fns:
        lo, hi = func_bounds(e)
        for va, (mn, ops) in A().range(lo, hi):
            if mn in ("cmp", "push", "mov") and re.search(r"(,|^)0x1b$", (ops or "").replace(" ", "")):
                l27.append((va, mn, ops))
    out("act", "immediate 27 in quest functions", n=len(l27))
    for va, mn, ops in l27:
        note("0x%08X %s %s %s" % (va, nm(va), mn, ops))


# ================================================================================================== misc
SERVICES = {0x00591790: "A1Q3_ImbueDone", 0x005877C0: "A5Q1_SocketDone", 0x0058BC00: "A5Q4_PersonalizeDone",
            0x0058FD50: "A1Q1_RespecDone", 0x0054B830: "NpcTravelMove"}


@section
def sec_misc():
    # P6: the service calls inside NPC_MenuAction
    lo, hi = func_bounds(0x00579D60)
    for t, n in sorted(SERVICES.items()):
        sites = ref_line("misc", "P6 %s" % n, t)
        out("misc", "P6 %s inside NPC_MenuAction" % n, calls=len(sites),
            inside=sum(1 for s in sites if lo <= s < hi), bad=int(not any(lo <= s < hi for s in sites)))
    sw = [(va, ops) for va, (mn, ops) in A().range(lo, hi) if mn == "jmp" and "*4+" in (ops or "")]
    for va, ops in sw:
        note("switch 0x%08X %s [r2 %s]" % (va, ops, r2_text(va)))
    # P104: MissileCreateAt's callers: ECX, EDX and five stack arguments; the callee's ret
    sites = ref_line("misc", "P104 MissileCreateAt", 0x0056EDE0)
    pop = T.callee_pop(0x0056EDE0)
    ok = 0
    for s in sites:
        a, b, ag = push_args(s, 5)
        ex = expr(s, "ecx")
        ed = expr(s, "edx")
        flag = a is not None and b is not None and len(a) == len(b) == 5 and all(
            x == y or (x.isdigit() and not y.isdigit() and y not in REG32 and "[" not in y) for x, y in zip(a, b))
        if flag and not ag:
            note("0x%08X: r2 prints an immediate by a flag name (%s for %s); counted as agreeing" % (
                s, [y for x, y in zip(a, b) if x != y], [x for x, y in zip(a, b) if x != y]))
        good = a is not None and len(a) == 5 and (ag or flag)
        ok += good
        note("0x%08X %s args objdump=%s r2=%s ecx=%s edx=%s" % (s, nm(s), a, b, ex, ed))
    out("misc", "P104 argument layout", callers=len(sites), five_args_agree=ok, callee_ret=pop,
        bad=int(pop != 20) + len(sites) - ok)
    # P316: g_ObjInitFns entries the spec names, and whether each reaches a quest reader directly
    base = 0x00731BC0
    d = S.dwords(base, 90)
    r2d = r2_words(base, 90)
    out("misc", "P316 g_ObjInitFns", entries=90, r2_same=int(d == r2d), bad=int(d != r2d))
    for k in (43, 44, 49, 50, 52, 55, 69, 79):
        f = d[k]
        lo, hi = func_bounds(f) if f else (0, 0)
        cs = [t for _, t in calls_in(lo, hi)]
        q = sorted(set(nm(t) for t in cs if t in QUEST_READERS or t == GQG))
        note("InitFn %d = 0x%08X %s; quest calls: %s" % (k, f, nm(f) if f else "-", ", ".join(q) or "-"))


if __name__ == "__main__":
    sys.exit(main(sys.argv))

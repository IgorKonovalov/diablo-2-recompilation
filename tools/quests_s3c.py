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
  (part 2)
  dataflow  P19: every `+0x10f4` displacement three ways; a may-taint walk over each function's control-flow graph from
            each quest-control load (C) and its `[C+0xc]` game-record loads (R), into callees to depth 3, and into the
            quest objects' `+0xE8` log-state callbacks; every write, store, push and register argument of C or R
  data      P179 P302 R3 T56 T32 T30: a second DS1 reader (this file) against tools/ds1.py over every .ds1; a plain
            .txt reader against the .bin through tools/excel_bin.py (MonPreset, LvlPrest, Levels, SuperUniques,
            Hireling, objgroup, Objects); every excel cell naming act2guard4; the immediates 377, 567, 410 three ways
  part2     P37 P316 P319 T21 T30: QUESTS_MonsterDeathEvent's forced list and UnitKilled's order; g_ObjInitFns[6];
            the level getters' level-27 calls and the quest functions' DRLG callees; the field-centre words and the
            expfield.d2 header; WAYPOINT_IndexFromLevel and WaypointOperate's references
  totals    plan 0066's class totals over the per-spec inventory files
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


# ================================================================================================== dataflow (P19)
CTRL_DISP = 0x10F4
NORET = {0x00681E09}             # the fatal exit every `[ctrl+0x8] == 0` test reaches (no return)
RMW = ("or", "and", "xor", "add", "sub", "inc", "dec", "not", "neg", "bts", "btr", "btc", "shl", "shr", "sar",
       "rol", "ror", "adc", "sbb", "xchg")
REC_KNOWN = {0x0065C360: "SetState", 0x0065C3A0: "ClearState", 0x0065C3E0: "ClearSteps", 0x0065C310: "GetState"}


def split_ops(ops):
    ops = ops or ""
    if "," in ops:
        d, s = ops.split(",", 1)
        return d.strip(), s.strip()
    return ops.strip(), ""


def slot_key(opnd):
    """A register name, or the text of an ebp/esp-based stack slot, or None."""
    o = norm(opnd)
    if o in REG32:
        return o
    m = memref(opnd)
    if m and m[0][0] in ("ebp", "esp") and m[0][1] is None:
        return "[%s%+#x]" % (m[0][0], m[0][3] if m[0][3] < 0x80000000 else m[0][3] - 0x100000000)
    return None


def kinds_of(src, st):
    k = slot_key(src)
    if k is not None and k in st:
        return st[k]
    m = memref(src)
    if m and m[0][1] is None:
        b, _, _, d = m[0]
        if d == CTRL_DISP and b not in ("ebp", "esp"):
            return frozenset("C")
        if d == 0xC and "C" in st.get(b, ()):
            return frozenset("R")
    return frozenset()


def df_succ(ins, k, lo, hi):
    va, mn, ops = ins[k]
    nxt = [ins[k + 1][0]] if k + 1 < len(ins) else []
    if mn == "ret":
        return []
    t = S.branch_target(ops) if (mn == "call" or mn.startswith("j")) else None
    if mn == "call":
        return [] if t in NORET else nxt
    if mn == "jmp":
        if t is not None:
            return [t] if lo <= t < hi else []
        m = S.JTAB.match(ops or "")
        if m:
            return S.switch_targets(A(), va, int(m.group(1), 16))
        return []
    if mn.startswith("j"):
        return ([t] if t is not None and lo <= t < hi else []) + nxt
    return nxt


def df_events(va, mn, ops, st):
    """The observations at one instruction, from the state before it."""
    ev = []
    dst, src = split_ops(ops)
    for pos, opnd in ((0, dst), (1, src)):
        for b, ix, sc, d in memref(opnd):
            ks = st.get(b, frozenset())
            if "R" in ks:
                write = (pos == 0 and mn not in ("cmp", "test", "push", "call", "jmp")) and (mn == "mov" or mn in RMW)
                ev.append(("REC-WRITE" if write else "REC-READ", va, mn, ops))
            if "C" in ks and d == 0xC and ix is None and pos == 0 and mn not in ("cmp", "test", "push"):
                ev.append(("RECPTR-STORE", va, mn, ops))
    if mn == "push":
        ks = kinds_of(dst, st) if slot_key(dst) else frozenset()
        for kd in sorted(ks):
            ev.append(("PUSH-" + kd, va, mn, ops))
    if mn == "call" or mn == "jmp":
        for r in ("ecx", "edx"):
            for kd in sorted(st.get(r, ())):
                ev.append(("REGARG-%s-%s" % (kd, r), va, mn, ops))
    if mn == "mov" and slot_key(dst) is None and memref(dst):
        for kd in sorted(kinds_of(src, st)):
            ev.append(("STORE-" + kd, va, mn, ops))
    return ev


def df_step(va, mn, ops, st):
    st = dict(st)
    dst, src = split_ops(ops)
    if mn == "mov":
        k = slot_key(dst)
        if k is not None:
            ks = kinds_of(src, st)
            if ks:
                st[k] = ks
            else:
                st.pop(k, None)
    elif mn == "call":
        for r in ("eax", "ecx", "edx"):
            st.pop(r, None)
    elif mn not in ("cmp", "test", "push") and not mn.startswith("j"):
        k = slot_key(dst)
        if k is not None and (k in REG32 or mn in RMW or mn in ("lea", "pop")):
            st.pop(k, None)
    return st


def dataflow(lo, hi, seeds=None, start=None):
    """May-taint over the CFG of [lo, hi) from start (default lo): C = the quest control (a load of `[x+0x10f4]`),
    R = the game record (a load of `[C+0xc]`). Calls kill eax/ecx/edx; the fatal exit has no successor. Returns the
    events at every instruction (from its fixpoint in-state), the instructions reached, and the branches leaving the
    range."""
    ins = fresh(lo, hi)
    at = {va: k for k, (va, _, _) in enumerate(ins)}
    if (start if start is not None else lo) not in at:
        return [("DESYNC", start or lo, "", "")], 0, len(ins), []
    k0 = at[start if start is not None else lo]
    IN = {k0: dict(seeds or {})}
    work = [k0]
    leave = set()
    while work:
        k = work.pop()
        va, mn, ops = ins[k]
        o = df_step(va, mn, ops, IN[k])
        for t in df_succ(ins, k, lo, hi):
            j = at.get(t)
            if j is None:
                leave.add((va, t))
                continue
            old = IN.get(j)
            new = dict(old or {})
            for key, ks in o.items():
                new[key] = new.get(key, frozenset()) | ks
            if old is None or new != old:
                IN[j] = new
                work.append(j)
        if mn == "jmp" and S.branch_target(ops) is not None and not (lo <= S.branch_target(ops) < hi):
            leave.add((va, S.branch_target(ops)))
    ev = []
    for k in sorted(IN):
        va, mn, ops = ins[k]
        ev += df_events(va, mn, ops, IN[k])
    return ev, len(IN), len(ins), sorted(leave)


_FRESH = {}


def fresh(lo, hi):
    """objdump's decoding of [lo, hi) started at lo (the global linear sweep can be out of step at an entry that
    follows data)."""
    if (lo, hi) not in _FRESH:
        _FRESH[(lo, hi)] = sorted((va, mn, ops or "") for va, (mn, ops) in S.parse_listing(S.objdump(lo, hi)).items())
    return _FRESH[(lo, hi)]


def fn_range(va):
    """[entry, end) for a walk through va: the entry is the nearer of the symbol's entry and the int3-padded guess
    (a 0xCC byte inside an instruction can fake a pad), the end the first int3 instruction after va."""
    e = T.owner(va)[0] or T.pad_entry(va)
    pe = T.pad_entry(va)
    if pe is not None and e is not None:
        e = min(e, pe)
    end = None
    for v, mn, ops in fresh(e, va + 0x4000):
        if v >= va and mn == "int3":
            end = v
            break
    return e, end


def next_call(va, hi):
    for v, (mn, ops) in A().range(va + 1, hi):
        if mn == "call":
            return v, S.branch_target(ops or "")
    return None, None


def arg_index(site, opnd):
    a = od_push_args(site, 8) or []
    n = norm(opnd)
    return a.index(n) if n in a else None


def log_state_callbacks():
    """(lo, hi, seeds) of every function stored at a quest object's +0xE8 by the 41 inits, and the default
    0x00543F90; seeds: the game record at [ebp+0x8] (stack argument 1 of the `call eax` at 0x005442AD/0x00546135)."""
    inits = sorted(set(v[3] for v in SPEC_ROWS.values()) | set(x[2] for x in SPEC_SECOND))
    fns, unresolved = set(), []
    for f in inits:
        lo, hi = fn_range(f)
        for va, (mn, ops) in A().range(lo, hi):
            d, src = split_ops(ops)
            m = memref(d)
            if mn == "mov" and m and m[0][3] == 0xE8 and m[0][0] not in ("ebp", "esp"):
                v = norm(src)
                v = int(v) if v.isdigit() else v
                if v in REG32:
                    r = reg_src(va, v, entry=lo)
                    if r and r[1] == "xor" and norm(split_ops(r[2])[1]) == v:
                        v = 0
                    elif r and r[1] == "mov" and norm(split_ops(r[2])[1]).isdigit():
                        v = int(norm(split_ops(r[2])[1]))
                    else:
                        v = "%s<-%s" % (v, r)
                if isinstance(v, int):
                    if v:
                        fns.add(v)
                else:
                    unresolved.append((va, ops, v))
    # every +0xE8 store in .text, for the scope line
    allst = [va for va, (mn, ops) in A().ins.items() if mn == "mov" and memref(split_ops(ops)[0]) and
             memref(split_ops(ops)[0])[0][3] == 0xE8 and memref(split_ops(ops)[0])[0][0] not in ("ebp", "esp")]
    inside = [va for va in allst if any(fn_range(f)[0] <= va < fn_range(f)[1] for f in inits)]
    out("dataflow", "P19 +0xE8 callbacks", inits=len(inits), functions=len(fns), unresolved=len(unresolved),
        e8_stores_text=len(allst), e8_stores_in_inits=len(inside), bad=len(unresolved))
    for va in sorted(set(allst) - set(inside)):
        note("+0xE8 store outside the inits: 0x%08X %s %s %s" % (va, nm(va), A().ins[va][0], A().ins[va][1]))
    for u in unresolved:
        note("unresolved +0xE8 store 0x%08X %s -> %s" % u)
    res = []
    for f in sorted(fns) + [0x00543F90]:
        lo, hi = fn_range(f)
        res.append((f, hi, (("[ebp+0x8]", frozenset("R")),) if f != 0x00543F90 else (), f))
    note("callbacks: %s" % " ".join("0x%08X" % f for f in sorted(fns)))
    return res


@section
def sec_dataflow():
    # (1) every +0x10f4 displacement: raw bytes (ModRM mod=10, disp32 = 0x10f4), objdump, r2
    data = S.image()[0]
    import xrefscan
    base, secs = xrefscan.sections(EXE)
    raw = set()
    for s in secs:
        if not s["flags"] & xrefscan.IMAGE_SCN_MEM_EXECUTE:
            continue
        blob = data[s["raw"]:s["raw"] + min(s["rsize"], s["vsize"])]
        k = blob.find(b"\xf4\x10\x00\x00")
        while k >= 0:
            raw.add(base + s["va"] + k)
            k = blob.find(b"\xf4\x10\x00\x00", k + 1)
    od = sorted(va for va, (mn, ops) in A().ins.items() if re.search(r"[+-]0x10f4\]", ops or ""))
    # an objdump site holds the displacement bytes somewhere inside its encoding
    od_disp = {}
    for va in od:
        nv = A().next_va(va)
        hit = [r for r in raw if va < r and r + 4 <= nv]
        od_disp[va] = hit
    unclaimed = sorted(r for r in raw if not any(r in h for h in od_disp.values()))
    dec = r2_many(od)
    r2s = sorted(v for v, d in dec.items() if d and re.search(r"[+-]0x10f4\]", d[1].lower().replace(" ", "")))
    ctrl = [va for va in od if not re.search(r"\[e[bs]p-0x10f4\]", A().ins[va][1] or "")]
    out("dataflow", "P19 +0x10f4 sites", objdump=len(od), r2=len(r2s), raw_disp32=len(raw),
        raw_unclaimed=len(unclaimed), stack_slots=len(od) - len(ctrl), ctrl_sites=len(ctrl),
        agree=int(od == r2s and all(len(od_disp[v]) == 1 for v in ctrl)),
        bad=int(od != r2s or not all(len(od_disp[v]) == 1 for v in ctrl)))
    for r in unclaimed:
        hold = max(v for v, _ in A().range(r - 15, r + 1))
        note("raw f4 10 00 00 at 0x%08X inside 0x%08X %s %s (not a +0x10f4 operand) [r2 %s]" % (
            r, hold, A().ins[hold][0], A().ins[hold][1], r2_text(hold)))
    stores = [va for va in ctrl if split_ops(A().ins[va][1])[0].find("0x10f4]") >= 0 and A().ins[va][0] == "mov"]
    for va in ctrl:
        note("site 0x%08X %s: %s %s [r2 %s]" % (va, nm(va), A().ins[va][0], A().ins[va][1], r2_text(va)))
    out("dataflow", "P19 stores to +0x10f4", n=len(stores), sites=" ".join("0x%08X" % v for v in stores))
    # the record's creation: QUESTRECORD_Alloc's return stored at ctrl +0xc in QUESTS_InitGame, nothing between
    seq = [(v, mn, o) for v, mn, o in fresh(0x00545F50, 0x00545F65)]
    for v, mn, o in seq:
        note("init 0x%08X %s %s [r2 %s]" % (v, mn, o, r2_text(v)))
    ok = [(mn, o) for v, mn, o in seq if v in (0x00545F57, 0x00545F5C)] == [
        ("call", "0x65c430"), ("mov", "DWORD PTR [ebx+0xc],eax")]
    out("dataflow", "P19 record creation", alloc_then_store=int(ok), bad=int(not ok))
    # (2) the CFG taint from every function holding a ctrl load; then the callees the C or R value reaches
    queue = []
    for va in ctrl:
        lo, hi = fn_range(va)
        queue.append((lo, hi, (), 0, va))
    # the quest objects' log-state callbacks (+0xE8), handed the game record as stack argument 1
    for lo, hi, sd, f in log_state_callbacks():
        queue.append((lo, hi, sd, 1, f))
    seen, allev = set(), []
    while queue:
        lo, hi, seeds, depth, start = queue.pop(0)
        key = (lo, seeds, start)
        if key in seen:
            continue
        seen.add(key)
        ev, reached, total, leave = dataflow(lo, hi, dict(seeds), start)
        note("WALK 0x%08X..0x%08X %s from 0x%08X depth=%d seeds=%s reached=%d/%d events=%d leave=%s" % (
            lo, hi, nm(lo), start or lo, depth, ",".join("%s:%s" % (k, "".join(sorted(v))) for k, v in seeds) or "-",
            reached, total, len(ev), " ".join("0x%08X->0x%08X" % x for x in leave) or "-"))
        for kind, va, mn, ops in ev:
            tgt = None
            if kind.startswith("PUSH-"):
                cs, tgt = next_call(va, hi)
            elif kind.startswith("REGARG"):
                cs, tgt = va, S.branch_target(ops)
            allev.append((kind, va, mn, ops, tgt, lo))
            note("  %s 0x%08X %s %s%s [r2 %s]" % (kind, va, mn, ops, " -> 0x%08X %s" % (tgt or 0, nm(tgt) if tgt else "?")
                                                  if tgt is not None or kind.startswith(("PUSH", "REGARG")) else "",
                                                  r2_text(va)))
            # follow a C or R value into its callee, unless the callee is a record function
            if depth >= 3 or tgt is None or tgt in REC_KNOWN:
                continue
            kd = kind.split("-")[1]
            if kind.startswith("PUSH-"):
                i = arg_index(cs, ops)
                if i is None:
                    note("    unresolved argument position at call 0x%08X" % cs)
                    continue
                sd = (("[ebp+%#x]" % (8 + 4 * i), frozenset(kd)),)
            else:
                sd = ((kind.split("-")[2], frozenset(kd)),)
            clo, chi = fn_range(tgt)
            queue.append((tgt, chi, sd, depth + 1, tgt))
    c = collections.Counter(k for k, *_ in allev)
    out("dataflow", "P19 events", functions=len(seen), **{k.replace("-", "_"): v for k, v in sorted(c.items())})
    w = [e for e in allev if e[0] in ("REC-WRITE", "RECPTR-STORE") or e[0].startswith("STORE")]
    for e in w:
        note("WRITE-LIKE %s 0x%08X %s %s %s in %s" % (e[0], e[1], nm(e[1]), e[2], e[3], nm(e[5])))
    recpush = collections.Counter(nm(e[4]) if e[4] else "?" for e in allev if e[0] in ("PUSH-R",) or
                                  e[0].startswith("REGARG-R"))
    out("dataflow", "P19 record handed to", **{re.sub(r"\W", "_", k): v for k, v in sorted(recpush.items())})


# ================================================================================================== data (part 2)
MERGED = os.path.join(S.ROOT, "workspace", "merged")
EXCEL = os.path.join(MERGED, "data", "global", "excel")
TILES = os.path.join(MERGED, "data", "global", "tiles")
DS1_OBJ_IDS = 0x00748AD8          # g_Ds1ObjectIds: 5 acts x 150 u32


def tab(table):
    """A plain reader of <table>.txt, independent of tools/excel_bin.py: (header, rows as dicts in record order).
    Lines split on LF, CR stripped, empty lines skipped, rows whose first cell is "Expansion" dropped (the compiled
    .bin has no record for them; docs/formats/excel-bin.md)."""
    raw = open(os.path.join(EXCEL, table + ".txt"), "rb").read().decode("latin-1")
    lines = [ln[:-1] if ln.endswith("\r") else ln for ln in raw.split("\n")]
    head = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln:
            continue
        c = ln.split("\t")
        if c[0] == "Expansion":
            continue
        rows.append({h: (c[i] if i < len(c) else "") for i, h in enumerate(head) if h not in ()})
    return head, rows


def binrecs(table):
    """The compiled records through tools/excel_bin.py and tools/excel_layouts.py: [{column: value}]."""
    import excel_bin
    recs, size = excel_bin.read_bin(os.path.join(EXCEL, table + ".bin"))
    lay = excel_bin.get_layout(table)
    out_ = []
    for r in recs:
        d = {}
        for f in lay["fields"]:
            try:
                d.setdefault(f.get("name", f.get("col")), excel_bin.decode_field(r, f))
            except Exception:  # noqa: BLE001 - a calc or string-table field this check does not need
                pass
        out_.append(d)
    return out_


def ds1_objects(data):
    """A second DS1 reader (docs/formats/ds1.md, written for this check): the header, the file list skipped, the cell
    layers skipped by count, then the object list. Returns (version, act, [(type, id, x, y, flags)], error)."""
    o = 0

    def i32():
        nonlocal o
        if o + 4 > len(data):
            raise ValueError("short")
        v = struct.unpack_from("<i", data, o)[0]
        o += 4
        return v
    try:
        ver, sx, sy = i32(), i32(), i32()
        act = i32() if ver >= 8 else 0
        tag = i32() if ver >= 10 else 0
        if ver >= 3:
            for _ in range(i32()):
                z = data.index(b"\0", o)
                o = z + 1
        if 9 <= ver <= 13:
            o += 8
        cells = (sx + 1) * (sy + 1)
        if ver >= 4:
            walls = i32()
            floors = i32() if ver >= 16 else 1
            layers = 2 * walls + floors + 1 + (1 if tag in (1, 2) else 0)
        else:
            layers = 5
        o += 4 * cells * layers
        objs = []
        if ver >= 2:
            for _ in range(i32()):
                t, i, x, y = i32(), i32(), i32(), i32()
                fl = i32() if ver >= 6 else 0
                objs.append((t, i, x, y, fl))
        return ver, min(act, 4), objs, None
    except ValueError as ex:
        return None, None, [], str(ex)


def ds1_map(ver, act, objs, mp, otab):
    """The game's unit mapping (docs/formats/ds1.md § Objects): type 1 (v >= 5) through the act's MonPreset list to
    (kind, index); type 2 (v >= 6) ids < 150 through g_Ds1ObjectIds, else id - 150; the act rewrites of six MonStats
    ids into objects at act index 2 and 4. Returns [(type, class-or-place, x, y)]."""
    res = []
    for t, i, x, y, fl in objs:
        if t == 1:
            if ver < 5:
                continue
            lst = mp.get(act + 1, [])
            pl = lst[i] if 0 <= i < len(lst) else None
            if pl and pl[0] == 1:
                cls = pl[1]
                if act == 2 and cls in (297, 366):
                    res.append((2, {297: 382, 366: 404}[cls], x, y))
                    continue
                if act == 4 and (cls == 514 or 537 <= cls <= 539):
                    res.append((2, 461 if cls == 514 else 1013 - cls, x, y))
                    continue
            res.append((1, pl, x, y))
        elif t == 2:
            if ver >= 6:
                c = otab[act * 150 + i] if i < 150 else i - 150
            else:
                c = i
            res.append((2, c, x, y))
        else:
            res.append((t, i, x, y))
    return res


def imm_sites(value):
    """Every .text instruction with `value` as an immediate operand: objdump's operands, the raw imm32 bytes, r2."""
    od = sorted(va for va, (mn, ops) in A().ins.items()
                if any(int(h, 16) == value for h in re.findall(r"(?:^|,)0x([0-9a-f]+)$", (ops or "").replace(" ", "")))
                and "[" not in (ops or "").split(",")[-1])
    data = S.image()[0]
    import xrefscan
    base, secs = xrefscan.sections(EXE)
    raw = []
    pat = struct.pack("<I", value)
    for sct in secs:
        if not sct["flags"] & xrefscan.IMAGE_SCN_MEM_EXECUTE:
            continue
        blob = data[sct["raw"]:sct["raw"] + min(sct["rsize"], sct["vsize"])]
        k = blob.find(pat)
        while k >= 0:
            raw.append(base + sct["va"] + k)
            k = blob.find(pat, k + 1)
    # a raw imm32 hit belongs to the instruction that holds it when they are its last 4 bytes; an objdump site with a
    # 16-bit operand (`cmp WORD PTR [...], imm16`) is checked on its own last 2 bytes
    claimed, stray = set(), []
    for r in raw:
        hold = max((v for v, _ in A().range(r - 15, r + 1)), default=None)
        nv = A().next_va(hold) if hold is not None else None
        if hold is not None and nv == r + 4 and hold in od:
            claimed.add(hold)
        else:
            stray.append((r, hold))
    for va in od:
        nv = A().next_va(va)
        if "WORD PTR" in (A().ins[va][1] or "") and "DWORD" not in A().ins[va][1] and \
                data[S.va_off(nv) - 2:S.va_off(nv)] == struct.pack("<H", value):
            claimed.add(va)
    dec = r2_many(od)
    r2s = sorted(v for v, d in dec.items() if d and re.search(r"(?:^|[, ])0x%x$" % value, d[1].lower().strip()))
    return od, sorted(claimed), stray, r2s


@section
def sec_data():
    # ---- tables, read twice: the plain .txt reader above and the compiled .bin through tools/excel_bin.py
    _, mon_t = tab("monstats")
    mon_b = binrecs("monstats")
    names = [r["Id"] for r in mon_t]
    out("data", "monstats rows", txt=len(mon_t), bin=len(mon_b), row377=names[377] if len(names) > 377 else "-",
        bad=int(len(mon_t) != len(mon_b) or names[377] != "act2guard4"))
    _, su_t = tab("superuniques")
    su_names = [r["Superunique"] for r in su_t]
    _, mpl_t = tab("monplace")
    mpl = [r["code"] for r in mpl_t]
    _, mp_t = tab("monpreset")
    mp_b = binrecs("monpreset")
    mp = collections.defaultdict(list)
    dis = 0
    for k, r in enumerate(mp_t):
        b = mp_b[k]
        pl = r["Place"]
        kind = 1 if pl in names else 2 if pl in su_names else 0 if pl in mpl else None
        idx = names.index(pl) if kind == 1 else su_names.index(pl) if kind == 2 else mpl.index(pl) if kind == 0 else None
        if int(r["Act"]) != b["Act"] or kind != b.get("PlaceKind") or idx != b["Place"]:
            dis += 1
        mp[int(r["Act"])].append((kind, idx, pl))
    out("data", "monpreset txt=bin", rows=len(mp_t), bin=len(mp_b), disagree=dis, bad=dis + int(len(mp_t) != len(mp_b)))
    a2 = [(i, e[2]) for i, e in enumerate(mp[2]) if e[2] in ("act2guard4", "place_talkingguard", "place_dumbguard")]
    note("MonPreset act 2 entries for NPC 377 and its placeholders: %s" % a2)
    _, lp_t = tab("lvlprest")
    lp_b = binrecs("lvlprest")
    named_t = set()
    for r in lp_t:
        for k in range(1, 7):
            f = (r.get("File%d" % k) or "").strip().lower().replace("\\", "/")
            if f and f != "0":
                named_t.add(f)
    named_b = set()
    for r in lp_b:
        for k in range(1, 7):
            f = (r.get("File%d" % k) or "").strip().lower().replace("\\", "/")
            if f and f != "0":
                named_b.add(f)
    out("data", "lvlprest files named", txt=len(named_t), bin=len(named_b), same=int(named_t == named_b),
        bad=int(named_t != named_b))
    otab = S.dwords(DS1_OBJ_IDS, 750)
    out("data", "g_Ds1ObjectIds", entries=750, r2_same=int(otab == r2_words(DS1_OBJ_IDS, 750)),
        bad=int(otab != r2_words(DS1_OBJ_IDS, 750)))
    # ---- every DS1, by this file's reader and by tools/ds1.py
    import ds1 as D1
    files = []
    for d, dirs, fnames in os.walk(TILES):
        dirs.sort()
        for fn in sorted(fnames):
            if fn.lower().endswith(".ds1"):
                files.append(os.path.join(d, fn))
    ok = err = diff = other_err = 0
    hits = collections.defaultdict(list)
    for path in files:
        data = open(path, "rb").read()
        ver, act, objs, e = ds1_objects(data)
        try:
            f1 = D1.parse(data)
            o1 = [(u["type"], u["id"], u["x"], u["y"]) for u in f1.get("objects", [])]
        except Exception as ex:  # noqa: BLE001
            f1, o1 = None, ("err", str(ex))
        rel = os.path.relpath(path, TILES).replace(os.sep, "/").lower()
        if e:
            err += 1
            note("DS1 %s: this reader: %s; tools/ds1.py: %s" % (rel, e, "error" if f1 is None else "%d objects" % len(o1)))
            continue
        ok += 1
        if f1 is None:
            other_err += 1
            note("DS1 %s: tools/ds1.py refuses it (%s); this reader stops after the object list (%d objects)" % (
                rel, o1[1], len(objs)))
        elif [(t, i, x, y) for t, i, x, y, _ in objs] != o1:
            diff += 1
            note("DS1 %s: object lists differ (%d here, %d there)" % (rel, len(objs), len(o1)))
        named = rel in named_t
        for t, c, x, y in ds1_map(ver, act, objs, mp, otab):
            if t == 1 and c and c[2] in ("act2guard4", "place_talkingguard", "place_dumbguard"):
                hits["377"].append((rel, c[2], x, y, named))
            if t == 2 and c in (567, 410):
                hits[c].append((rel, c, x, y, named))
    out("data", "DS1 files", files=len(files), parsed=ok, errors=err, lists_differ=diff, ds1py_errors=other_err,
        both=ok - other_err, bad=diff + err)
    n377 = [h for h in hits["377"] if h[4]]
    out("data", "P179 R3 DS1 units NPC 377 or placeholders", units=len(hits["377"]), in_lvlprest_files=len(n377),
        bad=len(n377))
    for h in hits["377"]:
        note("unit %s %s at (%d, %d), LvlPrest names the file: %s" % h)
    for c in (567, 410):
        out("data", "P302 T56 R3 DS1 objects class %d" % c, units=len(hits[c]), bad=len(hits[c]))
        for h in hits[c]:
            note("object %s %d at (%d, %d), LvlPrest names the file: %s" % h)
    # ---- Levels and SuperUniques columns naming MonStats 377
    _, lv_t = tab("levels")
    lv_b = binrecs("levels")
    lt = [(r.get("Name"), k) for r in lv_t for k, v in r.items() if v == "act2guard4"]
    cols = ["mon%d" % k for k in range(1, 11)] + ["nmon%d" % k for k in range(1, 11)] + \
           ["umon%d" % k for k in range(1, 11)] + ["cmon%d" % k for k in range(1, 5)]
    lb = [(i, c) for i, r in enumerate(lv_b) for c in cols if r.get(c) == 377]
    out("data", "P179 Levels cells naming act2guard4", txt=len(lt), bin_mon_cells_377=len(lb), rows=len(lv_t),
        bin_rows=len(lv_b), bad=len(lt) + len(lb))
    # every cell of every excel .txt that names act2guard4 (its own rows: MonStats Id/BaseId/MonStatsEx, MonStats2 Id,
    # MonPreset Place)
    own = {("monstats", "Id"), ("monstats", "BaseId"), ("monstats", "MonStatsEx"), ("monstats2", "Id"),
           ("monpreset", "Place")}
    cells = []
    for fn in sorted(os.listdir(EXCEL)):
        if not fn.lower().endswith(".txt"):
            continue
        h, rows = tab(fn[:-4])
        for r in rows:
            for k, v in r.items():
                if v == "act2guard4":
                    cells.append((fn[:-4].lower(), k))
    other = [c for c in cells if c not in own]
    out("data", "P179 excel cells naming act2guard4", cells=len(cells), outside_own_rows=len(other), bad=len(other))
    note("cells: %s" % " ".join("%s.%s" % c for c in cells))
    _, hi_t = tab("hireling")
    hc = [r.get("Hireling") for r in hi_t if r.get("Class") == "377"]
    out("data", "P179 Hireling Class 377 (txt; the one numeric monster-class column)", rows=len(hi_t), n=len(hc),
        bad=len(hc))
    su_b = binrecs("superuniques")
    st = [r["Superunique"] for r in su_t if r.get("Class") == "act2guard4"]
    sb = [i for i, r in enumerate(su_b) if r.get("Class") == 377]
    out("data", "P179 SuperUniques Class 377", txt=len(st), bin=len(sb), rows=len(su_t), bad=len(st) + len(sb))
    # ---- objgroup cells naming objects 410 and 567
    _, og_t = tab("objgroup")
    og_b = binrecs("objgroup")
    for c in (410, 567):
        ct = [(r.get("GroupName"), k) for r in og_t for k in ["ID%d" % j for j in range(8)] if r.get(k) == str(c)]
        cb = [(i, "ID%d" % j) for i, r in enumerate(og_b) for j in range(8) if r.get("ID%d" % j) == c]
        out("data", "T56 P302 objgroup ID cells = %d" % c, txt=len(ct), bin=len(cb), rows=len(og_t), bad=len(ct) + len(cb))
    # ---- code immediates for the three classes
    for v, lab in ((377, "P179 R3 class 377"), (567, "P302 R3 class 567"), (410, "T56 class 410")):
        od, claimed, stray, r2s = imm_sites(v)
        out("data", "%s immediates" % lab, objdump=len(od), raw_imm32=len(claimed), r2=len(r2s),
            agree=int(od == claimed == r2s), raw_other=len(stray), bad=int(not (od == claimed == r2s)))
        for va in od:
            nc = next_call(va, va + 0x80)
            note("0x%08X %s: %s %s; next call 0x%08X %s [r2 %s]" % (
                va, nm(va), A().ins[va][0], A().ins[va][1], nc[0] or 0, nm(nc[1]) if nc[1] else A().ins.get(
                    nc[0], ("", "?"))[1] if nc[0] else "-", r2_text(va)))
        for r, h in stray:
            note("raw %#x at 0x%08X inside 0x%08X %s %s (not an imm32 operand)" % (
                v, r, h or 0, A().ins.get(h, ("?", ""))[0], A().ins.get(h, ("", ""))[1]))
    # ---- T32: the waypoint rows' Sync and FrameDelta; T30: Levels.Waypoint
    _, ob_t = tab("objects")
    ob_b = binrecs("objects")
    op46t = [k for k, r in enumerate(ob_t) if r.get("OperateFn") == "46"]
    op46b = [k for k, r in enumerate(ob_b) if r.get("OperateFn") == 46]
    out("data", "T56 Objects rows with OperateFn 46", txt=" ".join(map(str, op46t)), bin=" ".join(map(str, op46b)),
        names="|".join(ob_t[k]["Name"] for k in op46t), row410=ob_t[410]["Name"].replace(" ", "_"),
        bad=int(op46t != op46b or 410 not in op46t))
    wp_t = [k for k, r in enumerate(ob_t) if r.get("InitFn") == "17" and r.get("OperateFn") == "23"]
    wp_b = [k for k, r in enumerate(ob_b) if r.get("InitFn") == 17 and r.get("OperateFn") == 23]
    sync0_t = [k for k in wp_t if ob_t[k]["Sync"] in ("0", "")]
    sync0_b = [k for k in wp_b if ob_b[k]["Sync"] == 0]
    fd = sorted(set((int(ob_t[k]["FrameDelta1"] or 0), int(ob_t[k]["FrameDelta2"] or 0)) for k in sync0_t))
    fdb = sorted(set((ob_b[k]["FrameDelta1"], ob_b[k]["FrameDelta2"]) for k in sync0_b))
    want = [429, 494, 496, 511, 539]
    out("data", "T32 waypoint rows (InitFn 17, OperateFn 23)", txt=len(wp_t), bin=len(wp_b),
        sync0_txt=" ".join(map(str, sync0_t)), sync0_bin=" ".join(map(str, sync0_b)),
        fd12_txt=fd, fd12_bin=fdb, sync1=len([k for k in wp_t if ob_t[k]["Sync"] == "1"]),
        bad=int(sync0_t != want or sync0_b != want or wp_t != wp_b or fd != [(200, 100)] or fdb != [(200, 100)]
                or len(wp_t) != 16))
    note("waypoint rows: %s" % " ".join("%d:%s:Sync%s" % (k, ob_t[k]["Name"], ob_t[k]["Sync"]) for k in wp_t))
    wpl_t = [(int(r["Id"]), int(r["Waypoint"] or 255)) for r in lv_t if r.get("Id", "") != ""]
    wpl_b = [(r["Id"], r["Waypoint"]) for r in lv_b]
    out("data", "T30 Levels.Waypoint", rows_txt=len(wpl_t), rows_bin=len(wpl_b), same=int(wpl_t == wpl_b),
        with_waypoint=sum(1 for _, w in wpl_b if w != 255), bad=int(wpl_t != wpl_b))
    note("Levels with a waypoint index: %s" % " ".join("%d:%d" % x for x in wpl_b if x[1] != 255))


# ================================================================================================== part2 (remainders)
def r2_lines(lo, hi):
    return [(va, mn, norm(ops)) for va, mn, ops in T.r2_range(lo, hi)]


def od_lines(lo, hi):
    return [(va, mn, norm(ops)) for va, mn, ops in fresh(lo, hi)]


def into(lo, hi):
    """Branch sites (raw rel32 index and objdump's jcc/jmp operands) whose target lies in (lo, hi]."""
    res = set()
    for t, lst in raw_index().items():
        if lo < t <= hi:
            res |= set(s for _, s in lst)
    for t, lst in od_index().items():
        if lo < t <= hi:
            res |= set(s for _, s in lst)
    # short jumps are not in the rel32 index: objdump's operands cover them
    return sorted(res)


@section
def sec_part2():
    # ---- P37: QUESTS_MonsterDeathEvent's forced list
    lo, hi = 0x00543B12, 0x00543B4B
    a, b = od_lines(lo, hi), r2_lines(lo, hi)
    imms = sorted(int(o.split(",")[1], 0) for va, mn, o in a if mn == "cmp" and o.startswith("eax,"))
    same = [(x[0], x[1]) for x in a] == [(x[0], x[1]) for x in b]
    out("part2", "P37 class compares 0x00543B12-0x00543B4B", objdump=len(a), r2=len(b), same_listing=int(same),
        classes=" ".join(map(str, imms)), bad=int(imms != [0xF2, 0xF3, 0x187, 0x220] or not same))
    for x, y in zip(a, b):
        note("0x%08X objdump %s %s | r2 %s %s" % (x[0], x[1], x[2], y[1], y[2]))
    bt = S.image()[0][S.va_off(0x00543B68):S.va_off(0x00543B68) + 0x23]
    bt_r2 = T.r2_bytes(0x00543B68, 0x23)
    jt = S.dwords(0x00543B60, max(bt) + 1)
    jt_r2 = r2_words(0x00543B60, max(bt) + 1)
    forced = [k + 0x1A for k in range(0x23) if jt[bt[k]] == 0x00543B0E]
    _, su_t = tab("superuniques")
    su_b = binrecs("superuniques")
    want = [26, 27, 29, 36, 37, 38, 39, 42, 43, 44, 45, 60]
    out("part2", "P37 superunique switch", bytes_r2_same=int(bytes(bt) == bt_r2), targets=len(jt),
        targets_r2_same=int(jt == jt_r2), forced=" ".join(map(str, forced)),
        selfidx_txt_bin=int(all(su_b[k]["Superunique"] == k for k in forced)),
        bad=int(forced != want or bytes(bt) != bt_r2 or jt != jt_r2))
    note("jump targets: %s" % " ".join("0x%08X" % t for t in jt))
    note("forced superuniques: %s" % ", ".join("%d %s" % (k, su_t[k]["Superunique"]) for k in forced))
    # the SuperUniques row's +0x08 is the row's own index (Superunique column) in every row of the .bin
    out("part2", "P37 SuperUniques +0x08 = row index", rows=len(su_b),
        equal=sum(1 for k, r in enumerate(su_b) if r["Superunique"] == k),
        bad=sum(1 for k, r in enumerate(su_b) if r["Superunique"] != k))
    # "after the drop": UnitKilled's MonSetMode call (the drop, items/0010) then the quest event, nothing entering between
    a, b = od_lines(0x0057CDC4, 0x0057CDDE), r2_lines(0x0057CDC4, 0x0057CDDE)
    ins_ = into(0x0057CDC4, 0x0057CDD9)
    inside = [s_ for s_ in ins_ if not (0x0057CDC4 <= s_ <= 0x0057CDD9)]
    out("part2", "P37 drop then quest event in UnitKilled", objdump=len(a), r2=len(b),
        same=int([(x[0], x[1]) for x in a] == [(x[0], x[1]) for x in b]), branches_into_from_outside=len(inside),
        bad=int(len(inside) != 0 or a[0][1:] != ("call", str(0x005A7C20)) or a[-1][1:] != ("call", str(0x00543A30))))
    for x in a:
        note("0x%08X %s %s" % x)
    for s_ in ins_:
        note("branch into the span from 0x%08X %s" % (s_, nm(s_)))
    # ---- P316: InitFn 6 (the cairn stones)
    d = S.dwords(0x00731BC0, 90)
    f6 = d[6]
    out("part2", "P316 g_ObjInitFns[6]", image="0x%08X" % f6, r2="0x%08X" % r2_words(0x00731BC0, 7)[6],
        fn=nm(f6), bad=int(f6 != r2_words(0x00731BC0, 7)[6]))
    lo6, hi6 = fn_range(f6)
    body = fresh(f6, hi6)
    cs = [(va, S.branch_target(o)) for va, mn, o in body if mn == "call"]
    qr = [(va, t) for va, t in cs if t in QUEST_READERS or t == GQG]
    out("part2", "P316 InitFn 6 calls", calls=len(cs), quest_readers=" ".join("%s@0x%08X" % (QUEST_READERS.get(t, "GQG"), va)
                                                                              for va, t in qr),
        record_readers=sum(1 for va, t in qr if t in (0x0065C310, GQG, 0x00543520)),
        bad=sum(1 for va, t in qr if t in (0x0065C310, GQG, 0x00543520)))
    for va, t in cs:
        note("call 0x%08X -> 0x%08X %s; edx=%s" % (va, t or 0, nm(t) if t else "?", expr(va, "edx")))
    _, ob_t = tab("objects")
    ob_b = binrecs("objects")
    r6t = [k for k, r in enumerate(ob_t) if r.get("InitFn") == "6"]
    r6b = [k for k, r in enumerate(ob_b) if r.get("InitFn") == 6]
    out("part2", "P316 Objects rows with InitFn 6", txt=" ".join(map(str, r6t)), bin=" ".join(map(str, r6b)),
        names="|".join(ob_t[k]["Name"] for k in r6t), bad=int(r6t != r6b))
    # ---- P319: the level-27 bit; calls of the level getters with level 27, and quest functions calling them
    for t, n in ((0x00642BB0, "LevelEnsure"), (0x00642AE0, "DRLG_LevelCreate"), (0x0061DB70, "LEVELS_GetRecord")):
        sites = ref_line("part2", "P319 %s" % n, t)
        l27, quest = [], []
        for s_ in sites:
            args = od_push_args(s_, 2) or []
            ed = expr(s_, "edx")
            if "27" in args or ed == 27:
                l27.append(s_)
            if QUEST_NAME.search(nm(s_)):
                quest.append(s_)
        out("part2", "P319 %s with level 27" % n, calls=len(sites), level27=" ".join("0x%08X:%s" % (x, nm(x)) for x in l27)
            or "-", quest_callers=" ".join("0x%08X:%s" % (x, nm(x)) for x in quest) or "-")
    # the DRLG and room callees of every quest function (direct calls), for the scope of "no quest code reads it"
    fns = [(int(l.split(",")[0], 16), l.split(",")[2]) for l in open(os.path.join(S.ROOT, "re", "symbols.csv"))
           if l.count(",") >= 3 and l.split(",")[1] == "func" and QUEST_NAME.search(l.split(",")[2])]
    cnt = collections.Counter()
    for e, n in fns:
        flo, fhi = func_bounds(e)
        for va, t in calls_in(flo, fhi):
            if t and any(k in nm(t) for k in ("Level", "Room", "DRLG", "Drlg", "DUNGEON")):
                cnt[t] += 1
    getters = sum(cnt[t] for t in (0x00642BB0, 0x00642AE0))
    out("part2", "P319 quest functions' DRLG/room callees", functions=len(fns), callees=len(cnt),
        level_struct_getters=getters, bad=getters)
    for t, v in sorted(cnt.items()):
        note("0x%08X %s x%d" % (t, nm(t), v))
    # ---- T21: the field's centre words 0x0096D664 / 0x0096D668
    data = S.image()[0]
    for g in (0x0096D664, 0x0096D668):
        ab = [a_ for sec_, a_ in raw_abs(g) if sec_ == ".text"]
        sites = sorted(set(max(v for v, _ in A().range(a_ - 15, a_ + 1)) for a_ in ab))
        od = sorted(va for va, (mn, ops) in A().ins.items() if "0x%x" % g in (ops or "").lower())
        dec = r2_many(od)
        rs = sorted(v for v, dd in dec.items() if dd and "0x%x" % g in dd[1].lower())
        rows = []
        for va in od:
            mn, ops = A().ins[va]
            w = "write" if "0x%x" % g in split_ops(ops)[0].lower() and mn not in ("cmp", "test", "push") else "read"
            rows.append((va, nm(va), w, mn, ops))
        writers = sorted(set(r[1].split("+")[0] for r in rows if r[2] == "write"))
        readers = sorted(set(r[1].split("+")[0] for r in rows if r[2] == "read"))
        out("part2", "T21 0x%08X" % g, raw_abs32=len(ab), objdump=len(od), r2=len(rs),
            agree=int(sites == od == rs), writers="|".join(writers), readers="|".join(readers),
            bad=int(not (sites == od == rs)))
        for r in rows:
            note("0x%08X %s %s: %s %s" % r)
    ef = os.path.join(MERGED, "data", "global", "expfield.d2")
    raw_ = open(ef, "rb").read()
    w_, h_ = struct.unpack_from("<II", raw_, 2)
    out("part2", "T21 expfield.d2 header", width=w_, height=h_, size=len(raw_), centre_col=w_ >> 1, centre_row=h_ >> 1,
        bad=int((w_, h_) != (256, 256) or len(raw_) != 10 + w_ * h_))
    # ---- T30: WAYPOINT_IndexFromLevel's read and WaypointOperate's references
    a, b = od_lines(0x00660E00, 0x00660E49), r2_lines(0x00660E00, 0x00660E49)
    rd = [x for x in a if "+0xe4]" in x[2]]
    out("part2", "T30 WAYPOINT_IndexFromLevel", objdump=len(a), r2=len(b),
        same=int([(x[0], x[1]) for x in a] == [(x[0], x[1]) for x in b]),
        reads_e4=" ".join("0x%08X:%s %s" % x for x in rd), getter=" ".join("0x%08X" % x[0] for x in a
                                                                          if x[1] == "call"),
        bad=int(len(rd) != 1))
    for x in a:
        note("0x%08X %s %s" % x)
    sites = ref_line("part2", "T30 WaypointOperate direct calls", 0x00584E30, want=[])
    ab = raw_abs(0x00584E30)
    slots = [(a_, (a_ - 0x00732D18) // 4) for sec_, a_ in ab if sec_ != ".text"]
    texts = []
    for sec_, a_ in ab:
        if sec_ == ".text":
            hold = max(v for v, _ in A().range(a_ - 15, a_ + 1))
            texts.append((hold, nm(hold), A().ins[hold][0], A().ins[hold][1], r2_text(hold)))
    out("part2", "T30 WaypointOperate abs32", n=len(ab), table=" ".join("0x%08X:slot%d" % x for x in slots),
        text=" ".join("0x%08X:%s" % (t[0], t[2]) for t in texts),
        bad=int([x[1] for x in slots] != [23] or any(t[2] != "cmp" for t in texts)))
    for t in texts:
        note("0x%08X %s: %s %s [r2 %s]" % t)


# ================================================================================================== totals
@section
def sec_totals():
    """Plan 0066's class totals: every per-spec inventory file's rows (Class, Count) summed, against each file's own
    *Totals by class* line."""
    d = os.path.join(S.ROOT, "docs", "plans", "0066-inventory")
    tot, bad = collections.Counter(), 0
    files = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "README.md")
    for f in files:
        rows, line = collections.Counter(), None
        for ln in open(os.path.join(d, f), encoding="utf-8"):
            c = [x.strip() for x in ln.split(" | ")]
            if ln.startswith("| ") and len(c) >= 9 and c[0].lstrip("| ").isdigit():
                rows[c[5]] += int(c[-1].rstrip(" |\n"))
            if ln.startswith("**Totals by class:**"):
                line = collections.Counter({k: int(v) for k, v in re.findall(r"([a-z][a-z0-9-]*) (\d+)", ln.split("(sum")[0])})
        tot += rows
        if line is not None and +line != +rows:
            bad += 1
            note("%s: rows %s, totals line %s" % (f, dict(rows), dict(line)))
    out("totals", "plan 0066 classes", files=len(files), sum=sum(tot.values()),
        **{k.replace("-", "_"): v for k, v in sorted(tot.items())}, bad=bad)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Plan 0066 Phase 1, batches S1f and S1o: exhaustive static scans with a second tool for the class-c rows of
monsters/ai/catalogue (S1f, with the five S1e remainders routed to it), monsters/ai/machinery and monsters/ai/README
(S1o). No game, no Ghidra.

Usage:
  python3 -I tools/ai_s1fo.py <section> [<section> ...]
  python3 -I tools/ai_s1fo.py all

Tools, as tools/skills_s2c.py and tools/quests_s3c.py (whose helpers this file imports): every reference scan three
ways (raw-byte rel32 and abs32, objdump's linear listing, r2 re-decoding each site); an instruction claimed at a site is
decoded by objdump and by r2 and both must agree (`site_line`); call arguments by two walkers (objdump and r2); image
words read twice, by Python from the file (tools/sweep_s4b.py) and by r2 `pxwj`. Table cells read twice: the plain .txt
reader of quests_s3c (`tab`) and the compiled .bin through tools/excel_bin.py (`binrecs`). A count line carries `bad=`
(an observation against the statement the row tests, or a tool disagreement).

Sections (inventory rows: C = monsters-ai-catalogue.md, M = monsters-ai-machinery.md, R = monsters-ai-README.md):
  entry    C1 C2 C52 R1 R2 R16: the think call, MonAiEvent's references, the nine direct calls, MonAiInit's row reads
  tables   C16 C274 C275 C372 C473 C440 C443 R4 R26 M57 M1: g_MonAiTable and g_MonAiStateRows read twice, the alias
           words, the `ret 4` stubs, the kind and alt columns, MonStats `AI` over every record
  init     C514 R3 R34 R35: MonAiInit's 33 calls and their state arguments, SpawnOwnedMonster's 15 callers
  more     the other rows (see each check's name)
  totals   plan 0066's class totals over the per-spec inventory files
Stdlib, objdump and r2. Read-only.
"""
import collections
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import quests_s3c as Q  # noqa: E402
import skills_s2c as C2  # noqa: E402
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
    print("S1fo %s %s %s bad=%d" % (sec, name, " ".join("%s=%s" % (k, kv[k]) for k in sorted(kv)), bad))


note = Q.note
nm = Q.nm


def A():
    return S.asm()


def site_line(sec, label, vas, want=None):
    """Each va decoded by objdump and r2; bad when they disagree or objdump's text misses the regex `want[k]`."""
    bad = 0
    txt = []
    for k, va in enumerate(vas):
        ot, rt, ag = C2.site(va)
        ot, rt = ot.replace("*1-", "-"), rt.replace("*1-", "-")
        ag = ot == rt
        ok = ag and (want is None or re.search(want[k], ot) is not None)
        bad += 0 if ok else 1
        txt.append("0x%08X %s%s" % (va, ot, "" if ag else "  [r2: %s]" % rt))
    out(sec, label, sites=len(vas), bad=bad)
    for t in txt:
        note(t)
    return bad


def words(va, n):
    """n image dwords at va, read by Python (tool 1) and by r2 pxwj (tool 2): (list, agree)."""
    a = [S.dword(va + 4 * k) for k in range(n)]
    txt = T.r2("pxwj %d @ 0x%x" % (4 * n, va))
    b = [v & 0xFFFFFFFF for v in json.loads(txt[txt.index("["):txt.rindex("]") + 1])]
    return a, a == b


def raw_abs_text(target):
    return [va for secn, va in Q.raw_abs(target) if secn == ".text"]


def abs_in_range(lo, hi):
    """Every .text dword whose value lies in [lo, hi), any alignment: [(site, value)] (raw bytes)."""
    data = S.image()
    import xrefscan
    blob = open(S.EXE, "rb").read()
    base, secs = xrefscan.sections(S.EXE)
    hits = []
    for s in secs:
        if s["name"] != ".text":
            continue
        raw, rsize, va = s["raw"], min(s["rsize"], s["vsize"]), s["va"]
        b = blob[raw:raw + rsize]
        for k in range(len(b) - 3):
            v = struct.unpack_from("<I", b, k)[0]
            if lo <= v < hi:
                hits.append((base + va + k, v))
    del data
    # keep a hit only when objdump's instruction covering it names the value as an operand (and r2's agrees)
    import bisect
    if A()._sorted is None:
        A()._sorted = sorted(A().ins)
    keep = []
    for h, v in hits:
        i = bisect.bisect_right(A()._sorted, h) - 1
        st = A()._sorted[i]
        mn, ops = A().ins[st]
        r = Q.r2_many([st])[st]
        if ("0x%x" % v) in (ops or "").lower() and r and ("0x%x" % v) in r[1].lower():
            keep.append((h, v, st))
    return keep


def body(entry):
    import sweep2_s7a as W
    vas, calls, icalls = W.body2(A(), entry)
    return sorted(vas), calls, icalls


def callers(target):
    """(raw, objdump, r2) call sites of target."""
    return Q.refs(target, ("call",))


def ref_count(sec, label, target, want_n=None, want_owners=None, kinds=("call",)):
    raw, od, r2s = Q.refs(target, kinds)
    agree = int(raw == od == r2s)
    owners = collections.Counter(T.owner(s)[1] for s in r2s)
    bad = 1 - agree
    if want_n is not None and len(r2s) != want_n:
        bad += 1
    if want_owners is not None and len(owners) != want_owners:
        bad += 1
    out(sec, label, target="0x%08X" % target, raw=len(raw), objdump=len(od), r2=len(r2s), agree=agree,
        functions=len(owners), bad=bad)
    note(", ".join("0x%08X %s" % (s, nm(s)) for s in r2s))
    return r2s


AI_TABLE, AI_ROWS = 0x0073CA18, 148
ST_TABLE, ST_ROWS = 0x0073D358, 18
EVFUNCS = 0x006E2490
MON_AI_EVENT = 0x005B1740
MON_AI_INIT = 0x005B0E00
ENTRY_GET = 0x005B15D0
TARGET_BY_KIND = 0x005B1650


def ai_rows():
    w, ag = words(AI_TABLE, 4 * AI_ROWS)
    return [tuple(w[4 * k:4 * k + 4]) for k in range(AI_ROWS)], ag


def st_rows():
    w, ag = words(ST_TABLE, 4 * ST_ROWS)
    return [tuple(w[4 * k:4 * k + 4]) for k in range(ST_ROWS)], ag


# ================================================================================================== entry
@section("entry")
def sec_entry():
    # R1: g_MonEventFuncs[2] is MonAiEvent; MonAiEvent's only reference is that slot.
    w, ag = words(EVFUNCS, 16)
    out("entry", "R1 g_MonEventFuncs[2]", word="0x%08X" % w[2], agree=int(ag), bad=int(w[2] != MON_AI_EVENT) + (1 - int(ag)))
    raw, od, r2s = Q.refs(MON_AI_EVENT, ("call", "jmp", "jcc"))
    ab = Q.raw_abs(MON_AI_EVENT)
    out("entry", "C1/R2 MonAiEvent references", rel32=len(raw), objdump=len(od), r2=len(r2s), abs32=len(ab),
        bad=int(len(raw) + len(od) + len(r2s) != 0) + int(ab != [(".rdata", EVFUNCS + 8)]))
    for secn, a in ab:
        note("abs32 in %s at 0x%08X" % (secn, a))
    # R2/R16: the nine direct calls: abs32 loads of the slot in .text, each followed by its indirect call.
    loads = raw_abs_text(EVFUNCS + 8)
    want = [0x005A80F5, 0x005A813F, 0x005A818E, 0x005A81ED, 0x005A822E, 0x005A8267, 0x005A82AD, 0x005A83D1, 0x005A8481]
    calls = []
    for s in loads:
        ins_va = s
        while ins_va not in A().ins and ins_va > s - 4:
            ins_va -= 1
        va = ins_va
        for _ in range(24):
            mn, ops = A().at(va)
            if mn == "call" and S.branch_target(ops or "") is None:
                calls.append(va)
                break
            va = A().next_va(va)
    owners = collections.Counter(T.owner(c)[1] for c in calls)
    out("entry", "R2/R16 slot-2 loads in .text and their indirect calls", loads=len(loads), calls=len(calls),
        functions=len(owners), bad=int(calls != want))
    note("owners: %s" % ", ".join("%s %d" % kv for kv in sorted(owners.items())))
    site_line("entry", "R2/R16 the nine calls decoded", calls, ["^call (e[a-z]{2}|\\[)"] * len(calls))
    # dispatch by index (MonEventDispatch): the only other reader of the table base
    out("entry", "R1 g_MonEventFuncs base abs32 in .text", sites=len(raw_abs_text(EVFUNCS)), bad=0)
    note(", ".join("0x%08X %s" % (s, nm(s)) for s in raw_abs_text(EVFUNCS)))
    # C1: the think call at 0x005B186F: eax = ctx.ctl->think (ctl at [ebp-0x24]) called with ecx game, edx unit, &ctx.
    site_line("entry", "C1 the think call", [0x005B1861, 0x005B1864, 0x005B1867, 0x005B186A, 0x005B186F],
              ["mov eax,\\[ebp-0x24\\]", "mov eax,\\[eax\\+0x4\\]", "lea edx,\\[ebp-0x24\\]", "push edx", "call eax"])
    # the three stops before it, each a non-zero return ending the event
    site_line("entry", "C1 the pre-steps before the think call", [0x005B1806, 0x005B1817, 0x005B1828],
              ["^call", "^call", "^call"])
    # C2/C52: the table range is read in .text by MonAiEntryGet only; its callers; the row words each caller reads.
    hits = abs_in_range(AI_TABLE, ST_TABLE + 16 * ST_ROWS)
    own = collections.Counter(T.owner(s)[1] for s, v, st in hits)
    out("entry", "C2 abs32 operands into the two AI tables from .text", hits=len(hits), functions=len(own),
        bad=int(set(own) != {"sub_005B15D0_MonAiEntryGet"}))
    for s, v, st in hits:
        note("0x%08X -> 0x%08X (instruction 0x%08X %s)" % (s, v, st, C2.site(st)[0]))
    ref_count("entry", "C2 MonAiEntryGet callers", ENTRY_GET, want_n=3, want_owners=2)
    site_line("entry", "C2/R26 MonAiTargetByKind: the stored state's row, its +0 only (kind switch)",
              [0x005B1655, 0x005B1658, 0x005B165D, 0x005B1663, 0x005B1668, 0x005B166A, 0x005B1673],
              ["mov esi,\\[ebp\\+0x8\\]", "mov eax,\\[esi\\]", "mov edx,\\[eax\\]", "call 0x5b15d0", "mov eax,\\[eax\\]",
               "cmp eax,0x5", "jmp \\[eax\\*4\\+0x5b1720\\]"])
    site_line("entry", "C2/C52 MonAiInit, alt step on the current state's row",
              [0x005B0E77, 0x005B0E7D, 0x005B0E81, 0x005B0E86, 0x005B0E89, 0x005B0E8E, 0x005B0E94, 0x005B0E96, 0x005B0E99],
              ["cmp \\[esi\\+0x4\\],0x0", "mov edx,\\[esi\\]", "call 0x5b15d0", "mov edx,\\[esi\\+0x4\\]",
               "cmp edx,\\[eax\\+0x8\\]", "cmp \\[eax\\+0xc\\],0x0", "mov \\[esi\\],ebx", "mov eax,\\[eax\\+0xc\\]",
               "mov \\[esi\\+0x4\\],eax"])
    site_line("entry", "C2 MonAiInit, init call and think store on the new state's row",
              [0x005B0EBE, 0x005B0EC9, 0x005B0F18, 0x005B0F1B, 0x005B0F22, 0x005B0F2B, 0x005B0F2D],
              ["call 0x5b15d0", "cmp \\[ebx\\+0x4\\],0x0", "call \\[ebx\\+0x4\\]", "mov ebx,\\[ebx\\+0x8\\]",
               "mov ebx,0x5b0cd0", "mov \\[esi\\],edx", "mov \\[esi\\+0x4\\],ebx"])
    site_line("entry", "C73 MonAiEvent stops on MonAiTargetByKind's non-zero return", [0x005B1817, 0x005B181C, 0x005B181E],
              ["call 0x5b1650", "test eax,eax", "^jne "])
    site_line("entry", "C73/M1 kind 1: target <- MonAiTargetOrIdle, return 1 (stop) when it is 0",
              [0x005B1692, 0x005B1699, 0x005B169B, 0x005B169F, 0x005B16A4],
              ["call 0x5de890", "test eax,eax", "sete cl", "mov \\[esi\\+0x8\\],eax", "mov eax,ecx"])
    site_line("entry", "M1 kind 2: MonAiFindTarget, return 0", [0x005B16B9, 0x005B16BF, 0x005B16C3],
              ["call 0x5dd7f0", "mov \\[esi\\+0x8\\],eax", "xor eax,eax"])
    site_line("entry", "M1 kind 4: MonAiTargetOrWait, stop when 0", [0x005B16D9, 0x005B16E2, 0x005B16E6, 0x005B16EB],
              ["call 0x5de9d0", "sete dl", "mov \\[esi\\+0x8\\],eax", "mov eax,edx"])
    site_line("entry", "M1 kind 5: MonAiTargetOrWait, return 0", [0x005B1700, 0x005B1706, 0x005B170A],
              ["call 0x5de9d0", "mov \\[esi\\+0x8\\],eax", "xor eax,eax"])
    site_line("entry", "M1 kinds 3 and >5: return 1", [0x005B166D, 0x005B1713], ["^ja 0x5b1711", "mov eax,0x1"])
    ref_count("entry", "M1 MonAiFindTarget callers", 0x005DD7F0)
    # kind switch table: entries for kinds 0..5
    jt, ag = words(0x005B1720, 6)
    out("entry", "M1/C73 MonAiTargetByKind jump table", agree=int(ag), entries=" ".join("%X" % v for v in jt),
        bad=1 - int(ag))


# ================================================================================================== tables
TIER = (2, 6, 9, 13, 20, 21, 22, 28, 29, 30, 34, 35, 37, 61, 64, 67, 89, 125)


def monai_names():
    head, rows = Q.tab("monai")
    return [r["AI"] for r in rows], rows


def monstats_ai():
    """[(record index, Id, AI row)] by the .txt (names through monai.txt's order) and by the .bin `AI` field."""
    names, _ = monai_names()
    idx = {n: k for k, n in enumerate(names)}
    head, rows = Q.tab("monstats")
    txt = [(k, r["Id"], idx.get(r["AI"], -1)) for k, r in enumerate(rows)]
    b = Q.binrecs("monstats")
    binv = [(k, r.get("AI")) for k, r in enumerate(b)]
    return txt, binv, rows


def stub_bytes(va, n):
    a = S.image()[0][S.va_off(va):S.va_off(va) + n]
    b = T.r2_bytes(va, n)
    return a, a == b


@section("tables")
def sec_tables():
    R, ag1 = ai_rows()
    ST, ag2 = st_rows()
    out("tables", "g_MonAiTable and g_MonAiStateRows read twice", rows=len(R), states=len(ST), agree=int(ag1 and ag2),
        bad=int(not (ag1 and ag2)))
    names, mrows = monai_names()
    out("tables", "monai.txt rows", rows=len(names), bad=int(len(names) != AI_ROWS))
    # aliases (C16 C274 C275 C372 C473)
    for lab, st, row, cols in (("C16 state 1 = row 1", 1, 1, (2,)), ("C275 state 4 = row 61 (think, alt)", 4, 61, (2, 3)),
                               ("C473 state 5 = row 60", 5, 60, (2,)), ("C274 state 7 = row 67", 7, 67, (2,)),
                               ("C372 state 15 = row 117", 15, 117, (2,))):
        eq = all(ST[st][c] == R[row][c] for c in cols)
        out("tables", lab, state=" ".join("%X" % ST[st][c] for c in cols), row=" ".join("%X" % R[row][c] for c in cols),
            row_name=names[row], bad=int(not eq))
    first = {r[2] for r in R}
    inf = [k for k in range(ST_ROWS) if ST[k][2] in first]
    out("tables", "R4/E-states whose think word is a first-table think", states=",".join(map(str, inf)),
        bad=int(inf != [1, 4, 5, 7, 15]))
    shared = [k for k in range(ST_ROWS) if ST[k][2] == 0x005E8020]
    out("tables", "states sharing 0x005E8020", states=",".join(map(str, shared)), in_first=int(0x005E8020 in first),
        bad=int(shared != [10, 17] or 0x005E8020 in first))
    # R4: 18 rows, the word after is not a row (a pointer to text), and the signed bound
    nxt, ag = words(ST_TABLE + 16 * ST_ROWS, 4)
    def ascii_at(va):
        try:
            o = S.va_off(va)
        except Exception:  # noqa: BLE001
            return None
        d = S.image()[0][o:o + 24]
        t = d.split(b"\0")[0]
        return t.decode("latin-1") if t and all(32 <= c < 127 for c in t) else None
    txts = [ascii_at(v) for v in nxt]
    out("tables", "R4 the dwords after state row 17 (0x0073D478)", words=" ".join("%08X" % v for v in nxt),
        text=json.dumps(txts), agree=int(ag), bad=int(not ag or txts[0] is None))
    st_kind_ok = all(ST[k][0] in (0, 1, 2) and all(w == 0 or 0x401000 <= w < 0x6CC000 for w in ST[k][1:]) for k in range(ST_ROWS))
    out("tables", "R4 every state row 0..17 is a row (kind 0..2, code words or 0)", bad=int(not st_kind_ok))
    site_line("tables", "R4 MonAiInit's state bound", [0x005B0E4A, 0x005B0E4D, 0x005B0E50],
              ["mov ebx,\\[ebp\\+0xc\\]", "cmp ebx,0x12", "jge "])
    # R26 / D2: 147 distinct thinks; the shared pair; rows named by MonStats
    thinks = collections.Counter(r[2] for r in R)
    dup = sorted(k for k in range(AI_ROWS) if thinks[R[k][2]] > 1)
    out("tables", "R26 distinct think words", distinct=len(thinks), shared_rows=",".join(map(str, dup)),
        names=",".join(names[k] for k in dup), bad=int(len(thinks) != 147 or dup != [106, 143]))
    txt, binv, msrows = monstats_ai()
    used_t = {a for _, _, a in txt}
    used_b = {a for _, a in binv}
    unused = sorted(set(range(AI_ROWS)) - used_t)
    out("tables", "R26 rows named by a MonStats record (.txt and .bin)", records=len(txt), bin_records=len(binv),
        used_txt=len(used_t), used_bin=len(used_b), unused=",".join("%d %s" % (k, names[k]) for k in unused),
        bad=int(len(used_t) != 146 or used_t != used_b or unused != [0, 143] or -1 in used_t))
    kinds = collections.Counter(r[0] for r in R)
    out("tables", "M1/D2 row kinds over the 148 rows", **{"k%d" % k: v for k, v in sorted(kinds.items())},
        inits=sum(1 for r in R if r[1]), alts=sum(1 for r in R if r[3]),
        bad=int(kinds != collections.Counter({0: 26, 1: 104, 2: 16, 4: 1, 5: 1})))
    note("kind 2 rows: %s" % ", ".join("%d %s" % (k, names[k]) for k in range(AI_ROWS) if R[k][0] == 2))
    note("kind 4/5 rows: %s" % ", ".join("%d %s k%d" % (k, names[k], R[k][0]) for k in range(AI_ROWS) if R[k][0] in (4, 5)))
    note("rows with alt: %s" % ", ".join("%d %s %X" % (k, names[k], R[k][3]) for k in range(AI_ROWS) if R[k][3]))
    # rows 0 and 1
    b0, ag = stub_bytes(R[0][2], 3)
    out("tables", "R26 row 0 think bytes", think="0x%08X" % R[0][2], bytes=b0.hex(), agree=int(ag),
        bad=int(b0 != b"\xc2\x04\x00" or not ag))
    site_line("tables", "R26/C16 row 1 Idle: with a room, MonAiIdle(200)", [0x005B0CD7, 0x005B0CDE, 0x005B0CE0, 0x005B0CE9],
              ["call 0x620bb0", "je 0x5b0cee", "push 0xc8", "call 0x5de080"])
    # M57: the tier rows
    tal = [k for k in TIER if R[k][3]]
    tin = [k for k in TIER if R[k][1]]
    tk = {k: R[k][0] for k in TIER}
    out("tables", "M57 tier rows with an alt", rows=",".join(map(str, tal)), inits=len(tin),
        kind0=",".join(str(k) for k in TIER if tk[k] == 0), other_kinds=",".join(str(k) for k in TIER if tk[k] not in (0, 1)),
        bad=int(tal != [29, 61] or tin or [k for k in TIER if tk[k] == 0] != [61, 67]))
    # C440 C443 and row 146: the `ret 4` thinks and their alts
    for row, alt, altname in ((145, 0x005FCF30, "AiBaalAlt"), (146, None, None), (147, 0x005E8480, "AiDiabloAlt")):
        b, ag = stub_bytes(R[row][2], 3)
        same = [k for k in range(AI_ROWS) if k != row and alt and R[k][3] == alt]
        out("tables", "C440/C443 row %d %s" % (row, names[row]), think="0x%08X" % R[row][2], bytes=b.hex(),
            alt="0x%08X" % R[row][3], alt_also_rows=",".join("%d %s" % (k, names[k]) for k in same), agree=int(ag),
            bad=int(b != b"\xc2\x04\x00" or not ag or (alt is not None and R[row][3] != alt)))
    # C473: row 60's records and its aip descriptions
    recs = [(k, i) for k, i, a in txt if a == 60]
    brecs = [k for k, a in binv if a == 60]
    aipd = [mrows[60]["*aip%d" % n] for n in range(1, 9)]
    out("tables", "C473 row 60 records", records=" ".join("%d %s" % r for r in recs), bin_records=",".join(map(str, brecs)),
        aip_descriptions=json.dumps(aipd), bad=int(len(recs) != 1 or recs[0][1] != "rogue2" or [r[0] for r in recs] != brecs
                                                 or any(aipd)))
    # data-section pointers into the two tables (a second route to the rows)
    import xrefscan
    blob = open(S.EXE, "rb").read()
    base, secs = xrefscan.sections(S.EXE)
    dh = []
    for s_ in secs:
        if s_["name"] in (".text", ".rsrc", ".reloc"):
            continue
        raw, rsize, va = s_["raw"], min(s_["rsize"], s_["vsize"]), s_["va"]
        for k in range(0, rsize - 3, 4):
            v = struct.unpack_from("<I", blob, raw + k)[0]
            if AI_TABLE <= v < ST_TABLE + 16 * ST_ROWS:
                dh.append((s_["name"], base + va + k, v))
    out("tables", "C2 aligned data dwords pointing into the two tables", hits=len(dh), bad=int(len(dh) != 0))
    for t in dh:
        note("%s 0x%08X -> 0x%08X" % t)


# ================================================================================================== init
def reg_source(site, reg):
    """The last write of reg before site in objdump's linear listing from the padded entry, decoded by both tools."""
    r = Q.reg_src(site, reg)
    if r is None:
        return None, "?"
    va = r[0]
    ot, rt, ag = C2.site(va)
    return va, "%s%s" % (ot, "" if ag else " [r2: %s]" % rt)


def push_vas(site, n):
    """The vas of the first n argument pushes of the call at site (objdump listing, od_push_args's rules)."""
    e = T.pad_entry(site)
    ins = Q.od_listing(e, site)
    res, skip = [], 0
    for va, mn, ops in reversed(ins[:-1]):
        if mn == "ret" or (mn == "sub" and ops.startswith("esp,")):
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
                res.append(va)
                if len(res) >= n:
                    break
    return res


@section("init")
def sec_init():
    sites = ref_count("init", "R3/R34 MonAiInit direct calls", MON_AI_INIT, want_n=33)
    raw, od, r2j = Q.refs(MON_AI_INIT, ("jmp", "jcc"))
    out("init", "R3 MonAiInit jumps and dword references", jumps=len(raw) + len(od) + len(r2j),
        abs32=len(Q.raw_abs(MON_AI_INIT)), bad=int(bool(raw or od or r2j or Q.raw_abs(MON_AI_INIT))))
    imm, regs, disagree = collections.Counter(), [], 0
    rows = []
    for st in sites:
        a, b, ag = Q.push_args(st, 2)
        disagree += 0 if ag else 1
        v = a[1] if a and len(a) > 1 else None
        if v is not None and v.isdigit():
            imm[int(v)] += 1
            rows.append("0x%08X %-40s state %s (r2 %s)" % (st, nm(st), v, b[1] if b and len(b) > 1 else "?"))
        else:
            regs.append(st)
            pv = push_vas(st, 2)
            src = reg_source(pv[1], v) if v in Q.REG32 and len(pv) > 1 else (None, v)
            rows.append("0x%08X %-40s state %s (r2 %s) <- %s" % (st, nm(st), v, b[1] if b and len(b) > 1 else "?",
                                                                   "0x%08X %s" % src if src[0] else src[1]))
    want = collections.Counter({0: 11, 5: 2, 6: 2, 10: 1, 11: 1, 13: 1, 15: 1, 16: 2})
    out("init", "R34 state argument: immediates and registers (objdump and r2 walkers)", immediates=sum(imm.values()),
        registers=len(regs), walkers_disagree=disagree,
        values=" ".join("%d:%d" % kv for kv in sorted(imm.items())),
        bad=int(imm != want) + int(len(regs) != 12) + disagree)
    none_of = [v for v in (1, 2, 3, 4, 7, 8, 9, 12, 14, 17) if imm[v]]
    out("init", "C514/R35 no immediate 1-4, 7-9, 12, 14, 17", found=",".join(map(str, none_of)) or "-", bad=len(none_of))
    for r in rows:
        note(r)
    ref_count("init", "R35 SpawnOwnedMonster direct calls", 0x0056D940, want_n=15)
    site_line("init", "R35 SpawnOwnedMonster's MonAiInit call passes block +0x0C", [0x0056DA61, 0x0056DA6A],
              ["\\[ebx\\+0xc\\]", "call 0x5b0e00"])
    site_line("init", "R35 InactiveMonsterSave stores ctl.state at record +0x28", [0x005422C9, 0x005422D7],
              [".", "\\+0x28\\]"])


# ================================================================================================== more
STORE = re.compile(r"^mov \[ebp-(0x[0-9a-f]+)\],(0x[0-9a-f]+|\d+)$")


REGS = ("eax", "ebx", "ecx", "edx", "esi", "edi")


def _track(listing):
    """{va: (ebp offset, signed value)} of every dword store to [ebp-X] in a straight-line listing, the stored value an
    immediate or a register holding a constant (`mov reg, imm`, `xor reg, reg`) from earlier in the listing; a store of
    a register with no known constant is kept with value None."""
    known, res = {}, {}
    for va, mn, ops in listing:
        o = C2.norm_ops(ops)
        parts = o.split(",", 1)
        dst = parts[0]
        src = parts[1] if len(parts) > 1 else None
        if mn == "mov" and dst in REGS and src is not None:
            known[dst] = _s32(int(src, 0)) if re.match(r"^(0x[0-9a-f]+|\d+)$", src) else None
        elif mn == "xor" and dst in REGS and src == dst:
            known[dst] = 0
        elif dst in REGS:
            known[dst] = None
        m = re.match(r"^\[ebp-(0x[0-9a-f]+)\]$", dst)
        if mn == "mov" and m and src is not None:
            if re.match(r"^(0x[0-9a-f]+|\d+)$", src):
                res[va] = (-int(m.group(1), 16), _s32(int(src, 0)))
            elif src in REGS:
                res[va] = (-int(m.group(1), 16), known.get(src))
    return res


def frame_stores(lo, hi):
    """objdump's and r2's tracked frame stores over [lo, hi] (inclusive of the instruction at hi)."""
    od = _track([(va, mn, ops or "") for va, (mn, ops) in A().range(lo, hi + 1)])
    r2 = _track([x for x in T.r2_range(lo, hi + 16) if x[0] <= hi])
    return od, r2


def _s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def branches(lo, hi):
    return [va for va, (mn, ops) in A().range(lo, hi + 1) if mn.startswith("j") or mn in ("call", "ret")]


@section("more")
def sec_more():
    R, _ = ai_rows()
    names, _r = monai_names()
    # ---- C73: row 23's four null tests of t; the row's kind
    site_line("more", "C73 row 23's null tests of t", [0x005F3184, 0x005F31D3, 0x005F325D, 0x005F33C1],
              ["test edi,edi"] * 4)
    out("more", "C73 row 23 kind", row=names[23], kind=R[23][0], think="0x%08X" % R[23][2], bad=int(R[23][0] != 1))
    # ---- C87 C89: the wisp's frame tables
    th = R[25][2]
    lo, hi = 0x005F39E1, 0x005F3E07
    od, r2 = frame_stores(th, hi)
    od = {va: v for va, v in od.items() if va >= lo}
    r2 = {va: v for va, v in r2.items() if va >= lo}
    br = [va for va in branches(th, hi)]
    tabs = {"A": (-0x2F4, 25, 52), "B": (-0x214, 25, 52), "A5": (-0x38, 1, 5), "B5": (-0x64, 1, 5)}
    vals = {}
    per = collections.Counter()
    stray = 0
    for va, (off, v) in od.items():
        hit = None
        for t, (base, a, b) in tabs.items():
            if base + 8 * a <= off < base + 8 * (b + 1):
                hit = t
                e, w = divmod(off - base, 8)
                vals[(t, e, w // 4)] = v
        if hit:
            per[hit] += 1
        else:
            stray += 1
    full = all((t, e, c) in vals for t, (base, a, b) in tabs.items() for e in range(a, b + 1) for c in (0, 1))
    out("more", "C87 wisp frame stores 0x005F39E1-0x005F3E07", think="0x%08X" % th, objdump=len(od), r2=len(r2),
        agree=int(od == r2), A=per["A"], B=per["B"], A5=per["A5"], B5=per["B5"], stray=stray, every_entry=int(full),
        branches_before=len(br), unknown=sum(1 for v in od.values() if v[1] is None),
        bad=int(len(od) != 132 or od != r2 or bool(stray) or not full or bool(br) or any(v[1] is None for v in od.values())))
    note("think entry 0x%08X; control transfers between entry and 0x%08X: %s" % (th, hi, br or "none"))
    zero_b = sorted((e, ) for (t, e, c) in vals if t == "B" and c == 0 and vals[(t, e, 0)] == 0 and vals[(t, e, 1)] == 0)
    zero_b5 = sorted(e for (t, e, c) in vals if t == "B5" and c == 0 and vals[(t, e, 0)] == 0 and vals[(t, e, 1)] == 0)
    out("more", "C89 (0, 0) entries of B and B5", B=",".join("%d (v14 %d, place %d)" % (e[0], (e[0] - 1) // 4, (e[0] - 1) % 4 + 1) for e in zero_b),
        B5=",".join(map(str, zero_b5)) or "-", bad=int(zero_b != [(52,)] or bool(zero_b5)))
    a5 = [(vals[("A5", e, 0)], vals[("A5", e, 1)]) for e in range(1, 6)]
    b5 = [(vals[("B5", e, 0)], vals[("B5", e, 1)]) for e in range(1, 6)]
    note("A5 %s; B5 %s" % (a5, b5))
    # ---- C155: the fetish shaman's revive filter
    site_line("more", "C155 AiFetishReviveCb's filter tests", [0x005F99E8, 0x005F99EF, 0x005F9A06, 0x005F9A0D, 0x005F9A14,
                                                               0x005F9A24, 0x005F9A28, 0x005F9A2F, 0x005F9A36],
              ["cmp \\[esi\\+0x18\\],eax", "call 0x58f0d0", "cmp eax,0x8d", "cmp eax,0x18c", "cmp \\[esi\\+0x18\\],0x1",
               "cmp \\[esi\\+0x18\\],0x3", "^jge ", "call 0x5a0180", "^jne "])
    site_line("more", "C155 the eax compared at 0x005F99E8 is 0", [0x005F99D7, 0x005F99DC, 0x005F99DE],
              ["call 0x63a770", "test eax,eax", "^jne "])
    txt, binv, msrows = monstats_ai()
    b = Q.binrecs("monstats")
    fs = [(k, i) for k, i, a in txt if a == 65]
    trip = {i: tuple(int(msrows[k][c] or 0) for c in ("aip2", "aip2(N)", "aip2(H)")) for k, i in fs}
    btrip = {i: tuple(b[k].get(c) for c in ("aip2", "aip2(N)", "aip2(H)")) for k, i in fs}
    norm0 = all(v[0] == 0 for v in trip.values())
    hell3 = sorted(i for i, v in trip.items() if v[2] == 3)
    out("more", "C155 MonStats aip2 of row 65's records (Normal, Nightmare, Hell)", records=len(fs),
        values=" ".join("%s=%s" % (i, "/".join(map(str, v))) for i, v in sorted(trip.items())),
        bin_equal=int(all(tuple(int(x or 0) for x in btrip[i]) == trip[i] for i in trip)),
        bad=int(not norm0 or hell3 != ["fetishshaman%d" % n for n in range(4, 9)]))
    # ---- C236: States pgsv
    _, st = Q.tab("states")
    pg = [(k, r["state"]) for k, r in enumerate(st) if r.get("pgsv") not in ("", "0")]
    sb = Q.binrecs("states")
    pgb = [k for k, r in enumerate(sb) if r.get("pgsv")]
    out("more", "C236 States rows with pgsv (.txt and .bin)", rows=" ".join("%d %s" % r for r in pg),
        bin_rows=",".join(map(str, pgb)) if pgb else "n/a",
        bad=int([k for k, _ in pg] != list(range(122, 128)) or not all(n.startswith("progressive_") for _, n in pg)
                or (pgb and pgb != list(range(122, 128)))))
    # ---- C244 C245 C247: ShadowMaster's record list
    _, sk = Q.tab("skills")
    skb = Q.binrecs("skills")
    ait = collections.Counter(int(r["aitype"] or 0) for r in sk)
    aitb = collections.Counter(int(r.get("aitype") or 0) for r in skb)
    out("more", "C244/C245/C247 Skills aitype (.txt and .bin)", rows=len(sk), bin_rows=len(skb),
        with_aitype=sum(v for k, v in ait.items() if k), values=" ".join("%d:%d" % kv for kv in sorted(ait.items()) if kv[0]),
        case8=ait[8], max=max(ait), bin_equal=int(ait == aitb),
        bad=int(sum(v for k, v in ait.items() if k) != 32 or ait[8] or max(ait) > 255 or ait != aitb or len(sk) != 357))
    site_line("more", "C244 the 4·acc + 3 lea, case 8's 2·v and 4·v, the signed compare with the previous record",
              [0x005EC19F, 0x005EC31F, 0x005EC328, 0x005EC4FF],
              ["lea ebx,\\[ebx\\+ecx\\*4\\+0x3\\]", "lea esi,\\[eax\\+eax(\\*1)?\\]", "add esi,esi",
               "cmp esi,\\[ebp\\+eax-0x450\\]"])
    site_line("more", "C244 the branch after the compare", [A().next_va(0x005EC4FF)], ["^j(l|g|le|ge) "])
    M = (1 << 31) - 1
    sq1, sq2 = (-32768) ** 2, (-32769) ** 2
    four = lambda v: _s32(4 * v)
    out("more", "C244 wrap bounds, computed", sq_32768=sq1, sq_32769=sq2, fits=int(sq2 <= M),
        four_2p29m1=four((1 << 29) - 1), four_2p29=four(1 << 29), four_m2p29=four(-(1 << 29)),
        four_m2p29m1=four(-(1 << 29) - 1), two_2p30=_s32(2 * (1 << 30)), two_2p30m1=_s32(2 * ((1 << 30) - 1)),
        res_div=(1 << 31) // 10, bad=int(not (sq1 == 1 << 30 and sq2 == 1073807361 and sq2 <= M
                                               and four((1 << 29) - 1) == M - 3 and four(1 << 29) == -(1 << 31)
                                               and four(-(1 << 29)) == -(1 << 31) and four(-(1 << 29) - 1) == M - 3
                                               and _s32(2 * (1 << 30)) == -(1 << 31) and (1 << 31) // 10 == 214748364 + 0)))
    site_line("more", "C245 the record index (20·k) and the five stores of record k at EBP-0x444",
              [0x005EC4F5, 0x005EC4F8, 0x005EC4FB, 0x005EC4FD, 0x005EC50B, 0x005EC515, 0x005EC521, 0x005EC528, 0x005EC52F,
               0x005EC51E, 0x005EC536],
              ["mov ecx,\\[ebp-0x2c\\]", "lea eax,\\[ecx\\+ecx\\*4\\]", "add eax,eax", "add eax,eax",
               "\\[ebp\\+eax-0x440\\]", "\\[ebp\\+eax-0x444\\]", "\\[ebp\\+eax-0x43c\\]", "\\[ebp\\+eax-0x438\\]",
               "\\[ebp\\+eax-0x434\\]", "add ecx,0x1", "mov \\[ebp-0x2c\\],ecx"])
    out("more", "C245 records of 20 bytes between EBP-0x444 and EBP-0x84", records=(0x444 - 0x84) // 20,
        bad=int((0x444 - 0x84) // 20 != 48))
    mt, ag = words(0x006CE268, 8)
    out("more", "C247 the mask table 0x006CE268", words=" ".join("%X" % w for w in mt), agree=int(ag),
        bad=int(mt[2] != 4 or not ag))
    # ---- C282 R55: Duriel's stock thresholds and the arithmetic
    du = [(k, i) for k, i, a in txt if a == 44]
    cols = [c + sfx for c in ("aip1", "aip2", "aip3", "aip4", "aip5") for sfx in ("", "(N)", "(H)")]
    dv = {i: {c: int(msrows[k][c] or 0) for c in cols} for k, i in du}
    dvb = {i: {c: int(b[k].get(c) or 0) for c in cols} for k, i in du}
    zero45 = all(v[c] == 0 for v in dv.values() for c in cols if c.startswith(("aip4", "aip5")))
    out("more", "C282/R55 row 44's records: aip4 and aip5 in every difficulty", records=" ".join(i for _, i in du),
        aip2=",".join(str(v["aip2"]) + "/" + str(v["aip2(N)"]) + "/" + str(v["aip2(H)"]) for v in dv.values()),
        aip3=",".join(str(v["aip3"]) + "/" + str(v["aip3(N)"]) + "/" + str(v["aip3(H)"]) for v in dv.values()),
        zero_aip4_aip5=int(zero45), bin_equal=int(dv == dvb), bad=int(not zero45 or dv != dvb or len(du) != 2))
    from fractions import Fraction as F
    for i, v in dv.items():
        for sfx in ("", "(N)", "(H)"):
            p2, p3, p4 = F(v["aip2" + sfx], 100), F(v["aip3" + sfx], 100), F(v["aip4" + sfx], 100)
            smite = p2
            jab = (1 - p2) * p3
            a2 = (1 - p2) * (1 - p3) * p4
            a1 = 1 - smite - jab - a2
            out("more", "R55 %s%s melee arms (D100 = Range(100), draw < aip)" % (i, sfx), smite=str(smite), jab=str(jab),
                a2=str(a2), a1=str(a1), bad=int((smite, jab, a2, a1) != (F(33, 100), F(67, 200), 0, F(67, 200))))
    # ---- C313: CORNER
    cw, ag = words(0x006E337C, 8)
    pts = [(_s32(cw[2 * k]), _s32(cw[2 * k + 1])) for k in range(4)]
    out("more", "C313 CORNER 0x006E337C", rows=json.dumps(pts), agree=int(ag),
        bad=int(pts != [(-5, -5), (5, -5), (5, 5), (-5, 5)] or not ag))
    cr = raw_abs_text(0x006E337C) + raw_abs_text(0x006E3380)
    note("abs32 users in .text: %s" % ", ".join("0x%08X %s" % (s_, nm(s_)) for s_ in cr))
    # ---- C422: Skill8 at stock
    s8 = [(k, msrows[k]["Id"], msrows[k]["Skill8"], txt[k][2]) for k in range(len(msrows)) if msrows[k]["Skill8"]]
    out("more", "C422 MonStats records with Skill8", records=" ".join("%d %s (%s, row %d %s)" % (k, i, sk8.replace(" ", "_"), a, names[a])
                                                              for k, i, sk8, a in s8),
        diablo_block=" ".join(i for k, i, _, a in s8 if a in (51, 147)), bad=0)
    # ---- S1e remainders 288 356 518
    ref_count("more", "S1e-288 Mephisto's pick 0x005F77C0 callers", 0x005F77C0, want_n=1)
    raw, od_, r2s = Q.refs(0x005F77C0, ("jmp", "jcc"))
    out("more", "S1e-288 pick jumps and dwords", jumps=len(raw) + len(od_) + len(r2s), abs32=len(Q.raw_abs(0x005F77C0)),
        bad=int(bool(raw or od_ or r2s or Q.raw_abs(0x005F77C0))))
    mep = [k for k in range(AI_ROWS) if names[k] == "Mephisto"]
    out("more", "S1e-288 Mephisto's row and think", rows=",".join("%d 0x%08X" % (k, R[k][2]) for k in mep), bad=0)
    cb = Q.raw_abs(0x005E26D0)
    out("more", "S1e-356 AiOverseerMinionCb 0x005E26D0 dword uses", sites=" ".join("%s 0x%08X %s" % (a, v, nm(v)) for a, v in cb),
        bad=int(not any(a == ".text" and v == 0x005EE907 for a, v in cb)))
    out("more", "S1e-356 row 128's think", think="0x%08X" % R[128][2], row=names[128], bad=int(R[128][2] != 0x005EE5D0))
    site_line("more", "S1e-356 row 128's push", [0x005EE906], ["push 0x5e26d0"])
    out("more", "S1e-356 States row 141", state=st[141]["state"], bad=int(st[141]["state"] != "bloodlust"))
    for tgt, lab in ((0x00621F20, "UnitLifePct"), (0x005DD280, "AiLifePct")):
        sites = ref_count("more", "S1e-518 %s direct calls" % lab, tgt)
        rows_ = sorted({k for s_ in sites for k in range(AI_ROWS)
                        if T.owner(s_)[0] in (R[k][2], R[k][3], R[k][1])})
        out("more", "S1e-518 %s callers that are a row's think, alt or init" % lab, calls=len(sites),
            rows=",".join("%d %s" % (k, names[k]) for k in rows_), bad=0)
    site_line("more", "S1e-518 AiLifePct is push ecx; call UnitLifePct; ret", [0x005DD280, 0x005DD281, 0x005DD286],
              ["push ecx", "call 0x621f20", "^ret"])
    # ---- M82 (T30a): a kind-14 block with a unit, written by row 65 for MonHelpBlock
    site_line("more", "M82 row 65's kind-14 block and its MonHelpBlock call",
              [0x005F9C17, 0x005F9C1A, 0x005F9C22, 0x005F9C29, 0x005F9C2C, 0x005F9C33],
              ["mov eax,\\[edx\\+0xc\\]", "lea ecx,\\[ebp-0x28\\]", "mov \\[ebp-0x20\\],0xe", "mov \\[ebp-0x1c\\],eax",
               "mov \\[ebp-0x18\\],0x1", "call 0x58f730"])
    out("more", "M82 row 65's think", think="0x%08X" % R[65][2], owner=nm(0x005F9C33), bad=int(T.owner(0x005F9C33)[0] != R[65][2]))
    # ---- C52: the maggot alt's record (AiCtlParamGet(14, 0)) and its +0x18 test
    site_line("more", "C52 the maggot alt's kind-14 record and its +0x18 test", [0x005F1757, 0x005F1759, 0x005F175F, 0x005F1764],
              ["push 0x0", "push 0xe", "call 0x58efa0", "cmp \\[eax\\+0x18\\],0x1"])
    out("more", "C52 row 15's think and alt", think="0x%08X" % R[15][2], alt="0x%08X" % R[15][3], kind=R[15][0],
        bad=int(R[15][3] != 0x005F1750))


@section("totals")
def sec_totals():
    Q.sec_totals()


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
    bad = sum(BAD.values()) + sum(Q.BAD.values())
    print("S1fo total bad=%d %s" % (bad, " ".join("%s=%d" % kv for kv in sorted((BAD + Q.BAD).items()))))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

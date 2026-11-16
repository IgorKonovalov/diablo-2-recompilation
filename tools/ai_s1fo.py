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


# ================================================================================================== part 2 (lane/n66x, 2026-11-16)
def both_listings(lo, hi):
    """objdump's and r2's linear listings of [lo, hi], operands normalised by skills_s2c.norm_ops: (od, r2)."""
    od = [(va, mn, C2.norm_ops(ops)) for va, (mn, ops) in A().range(lo, hi + 1)]
    r2 = [(va, mn.replace("retn", "ret"), C2.norm_ops(ops)) for va, mn, ops in T.r2_range(lo, hi + 16) if va <= hi]
    # one spelling for the padding `lea r,[r+0x0]` (r2 writes `lea r,[r]`)
    od = [(va, mn, re.sub(r"^(e[a-z]{2}),\[\1\+0x0\]$", r"\1,[\1]", ops) if mn == "lea" else ops) for va, mn, ops in od]
    return od, r2


def _reg_src(listing, reg):
    """The last instruction of a straight listing (ending at the call) that writes reg; a call clobbers eax/ecx/edx;
    a pop followed by a ret within six instructions (an earlier exit's epilogue) is skipped."""
    for k in range(len(listing) - 2, -1, -1):
        va, mn, ops = listing[k]
        dst = ops.split(",")[0]
        if mn == "call" and reg in ("eax", "ecx", "edx"):
            return va, mn, ops
        if mn == "pop" and any(m == "ret" for _, m, _o in listing[k + 1:k + 7]):
            continue
        if dst == reg and mn not in ("cmp", "test", "push"):
            return va, mn, ops
    return None


def reg_src2(site, reg):
    """(objdump source, r2 source, agree) of reg at the call at site, walking back linearly from the padded entry."""
    e = T.pad_entry(site)
    od, r2 = both_listings(e, site)
    a, b = _reg_src(od, reg), _reg_src(r2, reg)
    return a, b, a == b


def imm_value(src):
    """A register source's constant: `mov r, imm` → imm, `xor r, r` → 0, else None."""
    if src is None:
        return None
    va, mn, ops = src
    d, _, s = ops.partition(",")
    if mn == "xor" and d == s:
        return 0
    if mn == "mov" and re.match(r"^(0x[0-9a-f]+|\d+)$", s):
        return _s32(int(s, 0))
    return None


def disp_sites(lo, hi, pattern):
    """Instructions in [lo, hi] whose normalised operands match `pattern`, by objdump and by r2: (od vas, r2 vas)."""
    od, r2 = both_listings(lo, hi)
    rx = re.compile(pattern)
    return ([va for va, mn, ops in od if rx.search(mn + " " + ops)], [va for va, mn, ops in r2 if rx.search(mn + " " + ops)])


def ebx_zero(lo, hi, xor_va):
    """True when ebx's writes in [lo, hi] are the `xor ebx,ebx` at xor_va and epilogue pops only (both listings)."""
    res = []
    for lst in both_listings(lo, hi):
        w = []
        for k, (va, mn, ops) in enumerate(lst):
            if ops.split(",")[0] == "ebx" and mn not in ("cmp", "test", "push"):
                epi = mn == "pop" and any(m == "ret" for _, m, _o in lst[k + 1:k + 7])
                w.append((va, mn, epi))
        res.append(w)
    ok = res[0] == res[1] and res[0] and res[0][0][:2] == (xor_va, "xor") and all(e for _, _, e in res[0][1:])
    return bool(ok), res[0]


def table_stores(lo, hi, base, n, zero_regs=()):
    """The constant dword stores to the frame table [EBP-base, EBP-base+4n) in [lo, hi] (both listings, frame_stores),
    registers in zero_regs read as 0: ({va: (word, value)}, agree, unknown, rmw sites)."""
    od, r2 = frame_stores(lo, hi)
    res = {}
    unknown = 0
    for va, (off, v) in od.items():
        if -base <= off < -base + 4 * n:
            if v is None:
                src = A().ins[va][1].split(",")[1].strip()
                v = 0 if src in zero_regs else None
            unknown += v is None
            res[va] = ((off + base) // 4, v)
    rmw = [va for va, mn, ops in both_listings(lo, hi)[0]
           if mn not in ("mov", "cmp", "test", "push", "lea") and re.match(r"^\[ebp-0x([0-9a-f]+)\]", ops)
           and -base <= -int(re.match(r"^\[ebp-0x([0-9a-f]+)\]", ops).group(1), 16) < -base + 4 * n]
    return res, od == r2, unknown, rmw


def start_words(stores, lo, hi):
    """The table's words stored in [lo, hi] (the template block), as {word: value} for the non-zero ones."""
    return {w: v for va, (w, v) in sorted(stores.items()) if lo <= va <= hi and v}


@section("p2f")
def sec_p2f():
    R, _ = ai_rows()
    names, _r = monai_names()
    # ---- C171 (R71a): row 71's stores to AiCtl+0x14
    th = R[71][2]
    end = 0x005FAA8F
    od, r2 = disp_sites(th, end, r"^mov \[esi\+0x14\],")
    rd_od, rd_r2 = disp_sites(th, end, r"\+0x14\]")
    vals = []
    for va in od:
        s = A().ins[va][1].split(",")[1].strip().lower()
        if re.match(r"^(0x[0-9a-f]+|\d+)$", s):
            vals.append(int(s, 0))
        elif va == 0x005FA7DD:
            vals.append(0)      # a jump target: both jumps to it (0x005FA778, 0x005FA77E) follow `xor ecx,ecx` at 0x005FA771
        else:
            src = reg_src2(va, s)
            vals.append(imm_value(src[0]) if src[2] else None)
    out("p2f", "C171 row 71's think: stores to [esi+0x14] (objdump and r2, linear 0x%08X-0x%08X)" % (th, end),
        think="0x%08X" % th, stores_objdump=len(od), stores_r2=len(r2), agree=int(od == r2),
        values=",".join(map(str, vals)), other_refs=len(set(rd_od) - set(od)),
        bad=int(od != r2 or len(od) != 11 or 1 in vals or None in vals or sorted(set(vals)) != [0, 2, 3, 4, 5]
                or rd_od != rd_r2))
    note("stores: %s" % ", ".join("0x%08X=%s" % (va, v) for va, v in zip(od, vals)))
    note("other [..+0x14] operands in the range: %s" % ", ".join("0x%08X %s %s" % ((va,) + A().ins[va]) for va in rd_od if va not in od))
    site_line("p2f", "C171 the two GameFindUnit types: state 2 → eax − 1, state 3 → eax − 2, eax = [esi+0x14]",
              [0x005FA72E, 0x005FA75A, 0x005FA767, 0x005FA76C, 0x005FA7FA, 0x005FA803, 0x005FA808],
              ["mov eax,\\[esi\\+0x14\\]", "cmp eax,0x2", "lea edx,\\[eax-0x1\\]", "call 0x552f60", "cmp eax,0x3",
               "lea edx,\\[eax-0x2\\]", "call 0x552f60"])
    site_line("p2f", "C171 the store at 0x005FA7DD is reached by two jumps after xor ecx,ecx",
              [0x005FA771, 0x005FA778, 0x005FA77E, 0x005FA7DA, 0x005FA7DD],
              ["xor ecx,ecx", "je 0x5fa7dd", "jne 0x5fa7dd", "^ret ", "mov \\[esi\\+0x14\\],ecx"])
    site_line("p2f", "C171 the search path's test of v14 = 1", [0x005FA8D2, 0x005FA8D7], ["call 0x5dd0b0", "cmp \\[esi\\+0x14\\],0x1"])
    # ---- C196 (R78b): RNG_RandLoHi's callers, AiTrapArrowKind's callers, the region word's writers
    s = ref_count("p2f", "C196 RNG_RandLoHi 0x004BC500 direct calls", 0x004BC500, want_n=16)
    ai = [x for x in s if 0x005DC000 <= x < 0x005FE000]
    out("p2f", "C196 RNG_RandLoHi calls in the AI range 0x005DC000-0x005FE000", sites=",".join("0x%08X %s" % (x, nm(x)) for x in ai),
        bad=int(ai != [0x005FB69D]))
    ref_count("p2f", "C196 AiTrapArrowKind 0x005FB650 direct calls", 0x005FB650, want_n=2)
    raw, od_, r2s = Q.refs(0x005FB650, ("jmp", "jcc"))
    out("p2f", "C196 AiTrapArrowKind jumps and dwords", jumps=len(raw) + len(od_) + len(r2s), abs32=len(Q.raw_abs(0x005FB650)),
        bad=int(bool(raw or od_ or r2s or Q.raw_abs(0x005FB650))))
    out("p2f", "C196 rows 78 and 79 thinks", r78="0x%08X %s" % (R[78][2], names[78]), r79="0x%08X %s" % (R[79][2], names[79]),
        bad=int((R[78][2], R[79][2]) != (0x005FB6C0, 0x005FB7E0)))
    rx = re.compile(r"\[[a-z]{3}(\+[a-z]{3}(\*\d)?)?\+0x2d4\]")
    od_all = [va for va, (mn, ops) in sorted(A().ins.items()) if ops and rx.search(C2.norm_ops(ops))]
    raw_all = sorted(st for h, v, st in abs_in_range(0x2D4, 0x2D5) if rx.search(C2.norm_ops(A().ins[st][1])))
    r2dec = Q.r2_many(od_all)
    r2_all = [va for va in od_all if r2dec.get(va) and rx.search(C2.norm_ops(r2dec[va][1]))]
    writes = [va for va in od_all if rx.search(C2.norm_ops(A().ins[va][1]).split(",")[0]) and A().ins[va][0] not in ("cmp", "test", "push")]
    out("p2f", "C196 every .text operand [r+0x2d4] (objdump; r2 re-decode; raw disp32 dwords)", objdump=len(od_all), r2=len(r2_all),
        raw_disp32=len(raw_all), writes=len(writes), owners=",".join(sorted({nm(va).split("+")[0] for va in od_all})),
        bad=int(len(od_all) != 6 or r2_all != od_all or raw_all != od_all or writes != [0x00547AB4, 0x005FB682, 0x005FB6A2]))
    for va in od_all:
        note("0x%08X %-42s %s %s" % (va, nm(va), A().ins[va][0], A().ins[va][1]))
    site_line("p2f", "C196 MonRegionsBuild's −1 store and AiTrapArrowKind's guarded writes",
              [0x00547AAD, 0x00547AB4, 0x005FB674, 0x005FB67B, 0x005FB67D, 0x005FB682, 0x005FB696, 0x005FB698, 0x005FB69D, 0x005FB6A2],
              ["or ecx,0xffffffff", "mov \\[esi\\+0x2d4\\],ecx", "cmp \\[esi\\+0x2d4\\],0x0", "^jge ", "cmp ebx,0x28", "mov \\[esi\\+0x2d4\\],0x0",
               "push 0x3", "lea ecx,\\[edi\\+0x20\\]", "call 0x4bc500", "mov \\[esi\\+0x2d4\\],eax"])
    # ---- C420: the inline picks against 0x005FC130
    copies = (("Diablo", 0x005E8810, 0x005E8E16, 0x005E8EA1, 0x005E881E, 17, 11),
              ("BaalMelee", 0x005FC1C0, 0x005FC280, 0x005FC2FC, 0x005FC1C7, 16, 1),
              ("BaalBlocked", 0x005FC300, 0x005FC3C1, 0x005FC44B, 0x005FC30C, 16, 1),
              ("BaalRanged", 0x005FC450, 0x005FC5B0, 0x005FC62B, None, 16, 1))
    ref = [mn for va, mn, ops in both_listings(0x005FC130, 0x005FC1B8)[0]]
    for nm_, ent, lo, hi, xv, n, fb in copies:
        od, r2 = both_listings(lo, hi)
        mns = [mn for va, mn, ops in od]
        ops = " ; ".join("%s %s" % (mn, o) for va, mn, o in od)
        mult = len(re.findall(r"mov e[cd]x,0x6ac690c5", ops))
        has = dict(
            steps=mult, div=int("div ecx" in ops), mask=int("and edx,eax" in ops), pow2=int(re.search(r"lea edx,\[ecx-0x1\] ; (xor e[a-z]{2},e[a-z]{2} ; )?test ecx,edx", ops) is not None),
            le0=int(re.search(r"(cmp ecx,ebx|test ecx,ecx) ; jle ", ops) is not None),
            signed_scan=int(re.search(r"cmp edx,e[bs][xi] ; jl ", ops) is not None),
            n=int(("cmp eax,%s ; jl " % hex(n)) in ops),
            fallback=int(("mov eax,%s ; " % hex(fb)) in ops + " ; "))
        zb = ebx_zero(ent, lo, xv)[0] if xv else True
        out("p2f", "C420 %s's inline pick 0x%08X-0x%08X against 0x005FC130" % (nm_, lo, hi), agree=int(od == r2), words=n, fallback_value=fb,
            ebx_zero=int(zb), **has,
            bad=int(od != r2 or mult != 1 or not all(has.values()) or not zb))
    out("p2f", "C420 0x005FC130 reference shape", instructions=len(ref), bad=0)
    site_line("p2f", "C420 0x005FC130's sum ≤ 0: r = 0 with no step", [0x005FC14F, 0x005FC151, 0x005FC153, 0x005FC155],
              ["test ecx,ecx", "^jg ", "xor edx,edx", "jmp 0x5fc193"])
    site_line("p2f", "C420 the summing loops leave edx 0 (counter n, sub 1, jne)", [0x005E8E1B, 0x005E8E25, 0x005E8E28,
                                                                                  0x005FC291, 0x005FC294, 0x005FC3D5, 0x005FC3D8, 0x005FC5C4, 0x005FC5C7],
              ["mov edx,0x11", "sub edx,0x1", "jne 0x5e8e20", "sub edx,0x1", "^jne ", "sub edx,0x1", "^jne ", "sub edx,0x1", "^jne "])
    # ---- C422 (R51a): Diablo's three templates
    ok, ebx_w = ebx_zero(0x005E8810, 0x005E8E2A, 0x005E881E)
    out("p2f", "C422 ebx in AiDiabloDecide 0x005E8810-0x005E8E2A (before the pick's scan): xor at 0x005E881E, epilogue pops only", writes=" ".join("0x%08X %s" % (v, m) for v, m, e in ebx_w),
        bad=int(not ok))
    st, ag, unk, rmw = table_stores(0x005E8810, 0x005E8EA1, 0xA4, 34, ("ebx",))
    tmpl = {va: wv for va, wv in st.items() if wv[0] < 17}
    edit = {va: (w - 17, v) for va, (w, v) in st.items() if w >= 17}
    rmw_w = sorted({(int(re.match(r"^\[ebp-0x([0-9a-f]+)\]", C2.norm_ops(A().ins[va][1])).group(1), 16)) for va in rmw})
    rmw_w = [(0xA4 - o) // 4 - 17 if (0xA4 - o) // 4 >= 17 else (0xA4 - o) // 4 for o in rmw_w]
    melee = start_words(tmpl, 0x005E8AB5, 0x005E8B1D)
    blocked = start_words(tmpl, 0x005E8BAF, 0x005E8BFE)
    ranged = start_words(tmpl, 0x005E8C81, 0x005E8CE7)
    want = ({2: 40, 3: 70, 5: 40, 6: 24, 7: 40, 8: 15}, {4: 5, 6: 25, 8: 25, 9: 40, 12: 25}, {5: 25, 6: 25, 8: 15, 9: 20, 10: 10, 12: 20})
    zero_tmpl = all(v == 0 for va, (w, v) in tmpl.items() if w in (0, 11, 16))
    zero_edit = not [w for va, (w, v) in edit.items() if w in (0, 11, 16) and v != 0]
    out("p2f", "C422 AiDiabloDecide's table stores (template EBP-0xA4, copy EBP-0x60; objdump and r2)", agree=int(ag), stores=len(st),
        unknown=unk, melee=json.dumps(melee, sort_keys=True), blocked=json.dumps(blocked, sort_keys=True),
        ranged=json.dumps(ranged, sort_keys=True), w0_w11_w16_template_zero=int(zero_tmpl), w0_w11_w16_edits=int(not zero_edit),
        rmw_words=",".join(map(str, rmw_w)), indexed=len(disp_sites(0x005E8810, 0x005E8EA1, r"^mov \[ebp\+e[a-z]{2}(\*\d)?-0x")[0]),
        bad=int(not ag or unk or (melee, blocked, ranged) != want or not zero_tmpl or not zero_edit or any(w in (0, 11, 16) for w in rmw_w)))
    site_line("p2f", "C422 the score test (unsigned) and the difficulty word b+0x0C",
              [0x005E8D48, 0x005E8D5B, 0x005E8D6B], ["^jbe ", "lea edx,\\[ebp-0xc8\\]", "\\[ebp-0xbc\\]"])
    txt, binv, msrows = monstats_ai()
    s8 = [(k, msrows[k]["Id"], txt[k][2]) for k in range(len(msrows)) if msrows[k]["Skill8"]]
    b = Q.binrecs("monstats")
    s8b = [k for k, r in enumerate(b) if r.get("Skill8") not in (None, -1, 0xFFFF, "")]
    out("p2f", "C422 MonStats records with Skill8 (.txt; .bin)", records=" ".join("%d_%s_row%d" % r for r in s8),
        bin_records=",".join(map(str, s8b)), bad=int([r[1] for r in s8] != ["diabloclone", "uberdiablo", "uberbaal"]))
    # ---- C431 (R135a): Baal's three tables
    for nm_, lo, hi, base, tlo, thi, want_ in (
            ("melee", 0x005FC1C0, 0x005FC2FC, 0x40, 0x005FC1D1, 0x005FC219, {8: 20, 9: 30, 10: 150, 11: 10, 12: 10, 13: 70, 14: 40}),
            ("blocked", 0x005FC300, 0x005FC44B, 0x48, 0x005FC30E, 0x005FC34A, {2: 20, 3: 20, 4: 20, 6: 20, 8: 80, 9: 70}),
            ("ranged", 0x005FC450, 0x005FC62B, 0x54, 0x005FC466, 0x005FC4A2, {2: 5, 3: 5, 4: 5, 6: 5, 8: 40, 9: 40, 11: 70, 12: 80, 13: 60, 14: 20})):
        st, ag, unk, rmw = table_stores(lo, hi, base, 16)
        sw = start_words(st, tlo, thi)
        w0 = sorted({v for va, (w, v) in st.items() if w == 0})
        w7 = sorted({v for va, (w, v) in st.items() if w == 7})
        rmw_w = sorted({(base - int(re.match(r"^\[ebp-0x([0-9a-f]+)\]", C2.norm_ops(A().ins[va][1])).group(1), 16)) // 4 for va in rmw})
        out("p2f", "C431 Baal %s table EBP-0x%X (0x%08X-0x%08X)" % (nm_, base, lo, hi), agree=int(ag), stores=len(st),
            unknown_words=",".join(sorted({str(w) for va, (w, v) in st.items() if v is None})) or "-",
            start=json.dumps(sw, sort_keys=True), w0_values=",".join(map(str, w0)), w7_values=",".join(map(str, w7)) or "-",
            rmw_words=",".join(map(str, rmw_w)) or "-",
            bad=int(not ag or sw != want_ or w0 != [0] or (w7 and w7 != [0]) or 0 in rmw_w or 7 in rmw_w
                    or any(w not in (1, 15) and v is None for va, (w, v) in st.items())))
    site_line("p2f", "C431 P's store: w7 (EBP-0x38) = 0 in the ranged table", [0x005FC5A4], ["mov \\[ebp-0x38\\],0x0"])
    lv = disp_sites(0x005FC630, 0x005FC81F, r"^cmp .*,0x84$")
    out("p2f", "C431 level 132 compare in AiBaalDecide 0x005FC630-0x005FC81F", objdump=",".join("0x%08X" % v for v in lv[0]),
        r2=",".join("0x%08X" % v for v in lv[1]), bad=int(len(lv[0]) != 1 or lv[0] != lv[1]))


@section("p2o")
def sec_p2o():
    # ---- M10 (A1): the target lists
    ref_count("p2o", "M10 TargetListAddPlayer 0x005B1880 direct calls", 0x005B1880, want_n=1)
    site_line("p2o", "M10 TargetListAddPlayer: type 0, the first free of slots 0-7, game+0x8C ≤ 8",
              [0x005B188E, 0x005B189E, 0x005B18A6, 0x005B18B1, 0x005B18B6, 0x005B18BD, 0x005B18EE],
              ["cmp \\[ebx\\],0x0", "lea edi,\\[ecx\\+0x10f8\\]", "cmp \\[edi\\],0x0", "cmp esi,0x8", "cmp \\[ecx\\+0x8c\\],0x8",
               "^jg ", "mov \\[edi\\],eax"])
    s = ref_count("p2o", "M10 TargetListAttach 0x005B1900 direct calls", 0x005B1900, want_n=15)
    note("owners: %s" % ", ".join(sorted({T.owner(x)[1] for x in s})))
    site_line("p2o", "M10 TargetListAttach: i < 8, links after the head node (new+8 = head+8, new+0xC = head, head+8 = new)",
              [0x005B191B, 0x005B191E, 0x005B192C, 0x005B1966, 0x005B1969, 0x005B196C, 0x005B1979],
              ["cmp ebx,0x8", "^jge ", "mov esi,\\[ecx\\+ebx\\*4\\+0x10f8\\]", "mov edx,\\[esi\\+0x8\\]", "mov \\[eax\\+0x8\\],edx",
               "mov \\[eax\\+0xc\\],esi", "mov \\[esi\\+0x8\\],eax"])
    s = ref_count("p2o", "M10 TargetListAdd 0x005B1990 direct calls", 0x005B1990, want_n=9)
    lists = collections.Counter()
    dis = 0
    for x in s:
        a, b_, ag = Q.push_args(x, 2)
        dis += 0 if ag else 1
        lists[(a[1] if a and len(a) > 1 else "?", T.owner(x)[1])] += 1
    want = {("9", "sub_005424F0_InactiveMonstersRestore"), ("8", "sub_0054EF50_WandererSpawn"), ("9", "sub_005AEDA0_MissileSpawnOwnedMonster"),
            ("9", "sub_005C3B90_SkillDo59Attract"), ("9", "sub_005C3DE0_ConfuseApplyCb"), ("9", "sub_005C58B0_SkillBoneWallDo"),
            ("9", "sub_005C5BC0_BonePrisonPiece"), ("8", "sub_005EDC50_AiNpcBarb"), ("8", "sub_005EE3C0_AiWussie")}
    out("p2o", "M10 TargetListAdd's list argument per caller (objdump and r2 walkers)", walkers_disagree=dis,
        lists=" ".join("%s:%s" % k for k in sorted(lists)), bad=dis + int(set(lists) != want))
    site_line("p2o", "M10 TargetListAdd: list 8 or 9, pushes at the head (new+8 = old head, list = new)",
              [0x005B19AF, 0x005B19B2, 0x005B19B5, 0x005B19C6, 0x005B19FC, 0x005B1A05],
              ["lea eax,\\[ebx-0x8\\]", "cmp eax,0x1", "^ja ", "mov edi,\\[esi\\+ebx\\*4\\+0x10f8\\]", "mov \\[esi\\+ebx\\*4\\+0x10f8\\],eax",
               "mov \\[eax\\+0x8\\],edi"])
    # ---- M15 (A5): g_AiSearchKinds and the kinds passed
    w, ag = words(0x006E3300, 26)
    kinds = [(w[2 * k], w[2 * k + 1]) for k in range(13)]
    out("p2o", "M15 g_AiSearchKinds 0x006E3300, 13 {walker, callback} pairs (Python and r2)", agree=int(ag),
        walkers=",".join(str(a) for a, _ in kinds), callbacks=",".join("%d:0x%08X" % (k, c) for k, (a, c) in enumerate(kinds) if c),
        bad=int(not ag or [a for a, _ in kinds] != [0, 0, 1, 0, 0, 2, 0, 0, 0, 3, 3, 2, 0] or kinds[1][1] != 0))
    for k, (a, c) in enumerate(kinds):
        note("kind %d: walker %d, callback 0x%08X %s" % (k, a, c, nm(c) if c else "(param)"))
    site_line("p2o", "M15 AiUnitSearch: the table's callback, else param; walkers 1, 2, 3, else 0",
              [0x005DD0B7, 0x005DD0BE, 0x005DD0C5, 0x005DD0CC, 0x005DD0D9, 0x005DD0DE, 0x005DD0E3, 0x005DD0EF, 0x005DD103, 0x005DD115, 0x005DD127],
              ["mov ebx,\\[eax\\*8\\+0x6e3300\\]", "mov eax,\\[eax\\*8\\+0x6e3304\\]", "test eax,eax", "mov eax,\\[ebp\\+0xc\\]",
               "sub ebx,0x1", "sub ebx,0x1", "sub ebx,0x1", "call 0x5dce60", "call 0x5dd050", "call 0x5dcf70", "call 0x5dcee0"])
    s = ref_count("p2o", "M15 AiUnitSearch 0x005DD0B0 direct calls", 0x005DD0B0, want_n=29)
    kc, dis, fixed = collections.Counter(), 0, {0x005EE921: 0x005EE8F8, 0x005FA8D2: 0x005FA8C0, 0x005FAF4D: 0x005FAF20}
    for x in s:
        if x in fixed:
            continue
        a, b_, ag = Q.push_args(x, 3)
        dis += 0 if ag else 1
        kc[a[2] if a and len(a) > 2 else "?"] += 1
    site_line("p2o", "M15 the three kind pushes the walker misses (push 1 well before the call)", list(fixed.values()), ["push 0x1"] * 3)
    for x, p in fixed.items():
        kc["1"] += 1
    want = collections.Counter({"1": 19, "6": 2, "2": 1, "3": 1, "5": 1, "7": 1, "8": 1, "9": 1, "11": 1, "12": 1})
    out("p2o", "M15 kind argument (objdump and r2 walkers)", walkers_disagree=dis,
        kinds=" ".join("%s:%d" % kv for kv in sorted(kc.items(), key=lambda t: int(t[0]) if t[0].isdigit() else 99)),
        bad=dis + int(kc != want))
    # ---- M19 (A9): stat 89 by an immediate id; the search functions' callees
    import light_radius_scan as LR
    tot, imm_ids, nonimm, dis, get89, rdis = 0, collections.Counter(), 0, 0, [], 0
    for g in sorted(LR.GETTERS):
        raw, od_, r2s = Q.refs(g, ("call",))
        rdis += 0 if raw == od_ == r2s else 1
        tot += len(r2s)
        for x in r2s:
            a, b_, ag = Q.push_args(x, 2)
            v = a[1] if a and len(a) > 1 else None
            v2 = b_[1] if b_ and len(b_) > 1 else None
            if not ag:
                dis += 1
                note("walkers differ at 0x%08X %s: objdump %s, r2 %s" % (x, nm(x), a, b_))
                if v2 == "89":
                    get89.append(x)
            if v is not None and v.isdigit():
                imm_ids[int(v)] += 1
                if int(v) == 89:
                    get89.append(x)
            else:
                nonimm += 1
    out("p2o", "M19 calls to the ten stat getters of tools/light_radius_scan.py (three tools; stat id by two walkers)",
        calls=tot, immediate=sum(imm_ids.values()), distinct_ids=len(imm_ids), not_immediate=nonimm, id89=len(get89),
        reference_tools_disagree=rdis, walkers_disagree=dis, bad=int(bool(get89)) + rdis)
    p59_raw = []
    import xrefscan
    base, secs = xrefscan.sections(S.EXE)
    whole = open(S.EXE, "rb").read()
    for sct in secs:
        if sct["name"] == ".text":
            bb = whole[sct["raw"]:sct["raw"] + min(sct["rsize"], sct["vsize"])]
            p59_raw = [base + sct["va"] + m.start() for m in re.finditer(b"\x6a\x59", bb)]
    p59_od = [va for va, (mn, ops) in sorted(A().ins.items()) if mn == "push" and C2.norm_ops(ops) == "0x59"]
    p59_raw_ins = [va for va in p59_raw if va in A().ins]
    r2d = Q.r2_many(p59_od)
    p59_r2 = [va for va in p59_od if r2d.get(va) and r2d[va][0] == "push" and C2.norm_ops(r2d[va][1]) == "0x59"]
    m59_od = [va for va, (mn, ops) in sorted(A().ins.items()) if mn == "mov" and re.match(r"^e[a-z]{2},0x59$", C2.norm_ops(ops))]
    r2m = Q.r2_many(m59_od)
    m59_r2 = [va for va in m59_od if r2m.get(va) and r2m[va][0] == "mov" and re.match(r"^e[a-z]{2},0x59$", C2.norm_ops(r2m[va][1]))]
    nearcall = []
    for va in p59_od + m59_od:
        nxt, k = va, 0
        while k < 10:
            nxt = A().next_va(nxt)
            ins = A().at(nxt)
            if ins is None:
                break
            if ins[0] == "call":
                t = S.branch_target(ins[1])
                if t in LR.GETTERS:
                    nearcall.append(va)
                break
            k += 1
    out("p2o", "M19 `mov r32,0x59` in .text (objdump; r2 re-decode)", objdump=len(m59_od), r2=len(m59_r2), bad=int(m59_r2 != m59_od))
    out("p2o", "M19 `push 0x59` in .text (objdump; raw 6A 59 at an instruction start; r2 re-decode); with the movs, how many precede a getter call within 10 instructions", objdump=len(p59_od),
        raw=len(p59_raw_ins), r2=len(p59_r2), before_a_getter_call=len(nearcall),
        bad=int(p59_od != p59_raw_ins or p59_r2 != p59_od or bool(nearcall)))
    for va in p59_od:
        note("push 0x59 at 0x%08X %s" % (va, nm(va)))
    calls_all = []
    for f in LR.SEARCH_FNS:
        vas, calls, ic = body(f)
        calls_all += [(f, t) for s_, t in calls]
        out("p2o", "M19 %s's direct callees" % nm(f), calls=len(calls), indirect=len(ic),
            getters=sum(1 for s_, t in calls if t in LR.GETTERS), bad=int(any(t in LR.GETTERS for s_, t in calls)))
    # ---- M20 (A10): MonSkillTargetOk's callers and its TgtPlaceCheck read
    s = ref_count("p2o", "M20 MonSkillTargetOk 0x005FD470 direct calls", 0x005FD470, want_n=13, want_owners=10)
    out("p2o", "M20 the callers are AI functions (owner names Ai*)", owners=",".join(sorted({T.owner(x)[1] for x in s})),
        bad=int(not all(T.owner(x)[1].split("_", 2)[-1].startswith("Ai") for x in s)))
    mt, ag = words(0x006CE268, 1)
    out("p2o", "M20 the mask byte at 0x006CE268", byte=mt[0] & 0xFF, agree=int(ag), bad=int((mt[0] & 0xFF) != 1 or not ag))
    site_line("p2o", "M20 the Skills record's +0x08 test with that byte", [0x005FD4B3, 0x005FD4B9], ["mov dl,\\[0x6ce268\\]", "test \\[eax\\+0x8\\],dl"])
    # ---- M40 (D5): MonAiPathOverride's 103 types and AiPathOverrideSet's 9
    s = ref_count("p2o", "M40 MonAiPathOverride 0x005DE190 direct calls", 0x005DE190, want_n=103)
    tc, regs, dis = collections.Counter(), [], 0
    for x in s:
        a, b_, ag = reg_src2(x, "edx")
        dis += 0 if ag else 1
        v = imm_value(a)
        if v is None:
            regs.append(x)
        else:
            tc[v] += 1
    out("p2o", "M40 EDX at each call: immediates (objdump and r2 back-walks)", walkers_disagree=dis, registers=len(regs),
        values=" ".join("%d:%d" % kv for kv in sorted(tc.items())),
        bad=dis + int(tc != collections.Counter({0: 55, 7: 12, 1: 6, 2: 10, 13: 7, 15: 3, 5: 1}) or len(regs) != 9))
    note("register sites: %s" % ", ".join("0x%08X %s" % (x, nm(x)) for x in regs))
    site_line("p2o", "M40 the nine register sites: 13 (four), 2 (two), 0 (one), 5 or 6 (two)",
              [0x005E12E8, 0x005E12ED, 0x005F3805, 0x005F3810, 0x005F543C, 0x005F548B, 0x005F5490,
               0x005F3900, 0x005F3908, 0x005FADBC, 0x005FADCC, 0x005F0237, 0x005F023D, 0x005F025A,
               0x005DF7FA, 0x005DF804, 0x005DF80D, 0x005ECBCD, 0x005ECE63, 0x005ECE67, 0x005ECE89, 0x005ECE8D],
              ["xor eax,eax", "lea edx,\\[eax\\+0xd\\]", "xor ecx,ecx", "lea edx,\\[ecx\\+0xd\\]", "lea edx,\\[eax\\+0xd\\]",
               "xor eax,eax", "lea edx,\\[eax\\+0xd\\]", "cmp eax,0x2", "mov edx,eax", "xor ecx,ecx", "lea edx,\\[ecx\\+0x2\\]",
               "xor edx,edx", "jge 0x5f025a", "push 0x0", "mov ecx,0x6", "mov ecx,0x5", "mov edx,ecx", "mov edx,\\[ebp\\+0x10\\]",
               "push 0x5", "push 0x6", "push 0x5", "push 0x6"])
    site_line("p2o", "M40 the two lea [eax+0xd] of AiFetish 0x005F5437 and AiFetishBlowgun share the xor", [0x005F5437], ["xor eax,eax"])
    ref_count("p2o", "M40 AiRavenCircle 0x005ECBC0 direct calls", 0x005ECBC0, want_n=2)
    s = ref_count("p2o", "M40 AiPathOverrideSet 0x005A6260 direct calls", 0x005A6260, want_n=9)
    tc, regs, dis = collections.Counter(), [], 0
    for x in s:
        a, b_, ag = reg_src2(x, "edx")
        dis += 0 if ag else 1
        own = T.owner(x)[0] == 0x005DE190
        v = None if own else imm_value(a)
        (regs.append(x) if v is None else tc.update([v]))
    out("p2o", "M40 AiPathOverrideSet's EDX outside MonAiPathOverride", walkers_disagree=dis, inside=len(regs),
        values=" ".join("%d:%d" % kv for kv in sorted(tc.items())),
        bad=dis + int(tc != collections.Counter({1: 5, 13: 1, 0: 1}) or len(regs) != 2))
    site_line("p2o", "M40 AiPathOverrideSet stores the type at +0x18 when non-zero", [0x005A6263, 0x005A6267], ["test edx,edx", "mov \\[ecx\\+0x18\\],edx"])
    site_line("p2o", "M40 MonAiPathOverride maps 1 to 7", [0x005DE1A2, 0x005DE1A7], ["cmp edx,0x1", "mov edx,0x7"])
    site_line("p2o", "M40 the knockback start's PathSetType(8)", [0x005A781E, 0x005A7821], ["push 0x8", "call 0x648cf0"])
    # ---- M41 (D7): PathPlan's callers
    s = ref_count("p2o", "M41 PathPlan 0x00649970 direct calls", 0x00649970, want_n=68)
    mon = [x for x in s if 0x005A6000 <= x < 0x005A8000 or 0x005DC000 <= x < 0x005FE000]
    out("p2o", "M41 PathPlan calls in the monster mode (0x005A6000-0x005A8000) and AI (0x005DC000-0x005FE000) ranges",
        sites=",".join("0x%08X" % x for x in mon),
        bad=int(mon != [0x005A62EF, 0x005A634E, 0x005A760D, 0x005A7638, 0x005A7854, 0x005DD580, 0x005E912D, 0x005FBFB7]))
    note("others by owner: %s" % ", ".join(sorted({T.owner(x)[1] for x in s if x not in mon})))
    ref_count("p2o", "M41 MonPathPlanType 0x005A6290 direct calls (MonMovePlan)", 0x005A6290, want_n=1)
    ref_count("p2o", "M41 MonMovePlan 0x005A63F0 direct calls (MonSetMode)", 0x005A63F0, want_n=1)
    # ---- M44 (E2): AiCtlFollowSet's four callers and the pair it writes
    s = ref_count("p2o", "M44 AiCtlFollowSet 0x005DD330 direct calls", 0x005DD330, want_n=4)
    out("p2o", "M44 callers", owners=",".join(T.owner(x)[1] for x in s),
        bad=int([T.owner(x)[1] for x in s] != ["sub_005A0C00_UniqueMinions", "sub_005C07A0_SkillReviveDo", "sub_005C55C0_SummonFinish",
                                               "sub_005D8570_SkillDo71Taunt"]))
    site_line("p2o", "M44 the pair: +0x0C = edx+0x0C, +0x10 = [edx] (or −1, 1 with no edx)",
              [0x005DD34D, 0x005DD350, 0x005DD353, 0x005DD355, 0x005DD359, 0x005DD360],
              ["mov ecx,\\[edx\\+0xc\\]", "mov \\[eax\\+0xc\\],ecx", "mov ecx,\\[edx\\]", "mov \\[eax\\+0x10\\],ecx",
               "mov \\[eax\\+0xc\\],0xffffffff", "mov \\[eax\\+0x10\\],0x1"])
    site_line("p2o", "M44 UniqueMinions: ecx = the unit made at 0x005A0C83, edx = the input unit (edi)",
              [0x005A0C83, 0x005A0CB5, 0x005A0CB7, 0x005A0CB9, 0x005A0C04, 0x005A0C08], ["mov esi,eax", "mov edx,edi", "mov ecx,esi", "call 0x5dd330",
                                                                                   "test edi,edi", "cmp \\[edi\\],0x1"])
    # ---- M45 (E3): the owner link's writer/reader pair, the group walk
    site_line("p2o", "M45 MonSetOwner writes AiCtl+0x28 (game), +0x2C, +0x30", [0x0058F041, 0x0058F049, 0x0058F07E, 0x0058F081, 0x0058F084],
              ["mov edx,\\[edx\\+0x14\\]", "mov esi,\\[edx\\+0x28\\]", "mov \\[esi\\+0x2c\\],eax", "mov \\[esi\\+0x30\\],ecx", "mov \\[esi\\+0x28\\],edi"])
    site_line("p2o", "M45 MonsterOwner reads them into GameFindUnit", [0x0058F0DE, 0x0058F0E5, 0x0058F0EC, 0x0058F0F3, 0x0058F0F7, 0x0058F0FA],
              ["mov eax,\\[ecx\\+0x14\\]", "mov eax,\\[eax\\+0x28\\]", "mov ecx,\\[eax\\+0x28\\]", "mov edx,\\[eax\\+0x2c\\]",
               "mov edx,\\[eax\\+0x30\\]", "call 0x552f60"])
    site_line("p2o", "M45 MonGroupForEach reads +0x28/+0x2C/+0x30, then the owner's +0x34 list",
              [0x0058F3D0, 0x0058F3D7, 0x0058F3DB, 0x0058F3DE, 0x0058F400],
              ["mov ecx,\\[eax\\+0x28\\]", "mov edx,\\[eax\\+0x2c\\]", "mov edx,\\[eax\\+0x30\\]", "call 0x552f60", "mov eax,\\[eax\\+0x34\\]"])
    # ---- M54 (F table): UModTeleportTry's draws
    vas, calls, ic = body(0x005B11F0)
    rng = [(s_, t) for s_, t in calls if t in S.RNG_FNS or t == 0x0045C390]
    out("p2o", "M54 UModTeleportTry 0x005B11F0's calls", calls=len(calls), indirect=len(ic),
        spawnpospick=sum(1 for s_, t in calls if t == 0x0054DC40), rng=",".join("0x%08X->%s" % (s_, nm(t)) for s_, t in rng),
        bad=int(len(rng) != 2 or sum(1 for s_, t in calls if t == 0x0054DC40) != 1))
    site_line("p2o", "M54 the two Range(100) draws on the unit's seed (unit+0x20) and their thresholds",
              [0x005B12D3, 0x005B12D8, 0x005B12DB, 0x005B12E0, 0x005B12E3, 0x005B134F, 0x005B1352, 0x005B1355, 0x005B135A, 0x005B135D],
              ["mov edx,0x64", "lea ecx,\\[esi\\+0x20\\]", "call 0x45c390", "cmp eax,0xf", "^jge ", "lea edx,\\[eax\\+0x64\\]",
               "lea ecx,\\[esi\\+0x20\\]", "call 0x45c390", "cmp eax,0x19", "^jge "])
    site_line("p2o", "M54 eax is RoomIsTown's 0 at 0x005B134F", [0x005B133C, 0x005B1341, 0x005B1343], ["call 0x61ab00", "test eax,eax", "^jne "])
    # ---- M88 (T37a): row 37's think and two levels of callees, displacements 0x170-0x19F
    R, _ = ai_rows()
    th = R[37][2]
    seen, front = {}, [th]
    for d in range(3):
        nxt = []
        for f in front:
            if f in seen:
                continue
            vas, calls, ic = body(f)
            seen[f] = (vas, ic)
            nxt += [t for s_, t in calls]
        front = nxt
    hits_od, hits_r2, n_ins, n_ic = [], [], 0, 0
    rx = re.compile(r"\[[^\]]*\+0x(1[7-9][0-9a-f])\]")
    for f, (vas, ic) in seen.items():
        n_ins += len(vas)
        n_ic += len(ic)
        dec = Q.r2_many(sorted(vas))
        for va in vas:
            if rx.search(C2.norm_ops(A().ins[va][1])):
                hits_od.append(va)
            if dec.get(va) and rx.search(C2.norm_ops(dec[va][1])):
                hits_r2.append(va)
    out("p2o", "M88 row 37's think and its callees to depth 2: operands with displacement 0x170-0x19F",
        think="0x%08X" % th, row=_r_name(37), functions=len(seen), instructions=n_ins, indirect=n_ic,
        objdump=len(hits_od), r2=len(hits_r2), bad=int(bool(hits_od) or bool(hits_r2) or th != 0x005F6070))
    note("functions: %s" % ", ".join(nm(f) for f in seen))
    # ---- R21 (C5): kind-2 queueing and cancel sites
    for tgt, lab, want_n, want2 in ((0x005417D0, "UnitQueueEvent", 265, 30), (0x00540E60, "UNIT_CancelEvents", 141, 66)):
        s = ref_count("p2o", "R21 %s direct calls" % lab, tgt, want_n=want_n)
        kc, dis, two = collections.Counter(), 0, []
        for x in s:
            a, b_, ag = Q.push_args(x, 1)
            dis += 0 if ag else 1
            v = a[0] if a else "?"
            kc[v] += 1
            if v == "2":
                two.append(x)
        out("p2o", "R21 %s kind argument (objdump and r2 walkers)" % lab, walkers_disagree=dis, kind2=len(two),
            not_immediate=sum(v for k, v in kc.items() if not k.isdigit()),
            bad=dis + int(len(two) != want2) + sum(v for k, v in kc.items() if not k.isdigit()))
        if lab == "UnitQueueEvent":
            for x in two:
                a, b_, ag = Q.push_args(x, 2)
                try:
                    e = Q.expr(x, a[1])
                except Exception as ex:  # noqa: BLE001
                    e = "?"
                note("kind 2 at 0x%08X %-44s frame %s" % (x, nm(x), e))
    ref_count("p2o", "R21 EventQueueAt 0x005416B0 direct calls", 0x005416B0, want_n=2)
    site_line("p2o", "R21 UnitQueueEventCb's one call passes kind 14", [0x00555040, 0x00555046], ["push 0xe", "call 0x541800"])
    ref_count("p2o", "R21 UnitQueueEventCb 0x00541800 direct calls", 0x00541800, want_n=1)
    # ---- R38 (E10): who has which row
    txt, binv, ms = monstats_ai()
    names, _ = monai_names()
    byid = {i.lower(): (k, a) for k, i, a in txt}
    _, hr = Q.tab("hireling")
    hc = collections.Counter((int(r["Class"]), txt[int(r["Class"])][2]) for r in hr if r.get("Class"))
    out("p2o", "R38 Hireling.txt classes and their MonStats AI rows", classes=" ".join("%d:row%d:%d" % (k, a, n) for (k, a), n in sorted(hc.items())),
        bad=int({a for (k, a) in hc} != {61}))
    _, sk = Q.tab("skills")
    sm = [(r["skill"], r["summon"], byid.get(r["summon"].lower(), (None, None))) for r in sk if r.get("summon")]
    rows_by = collections.OrderedDict((n, a) for n, s_, (k, a) in sm)
    out("p2o", "R38 Skills.txt summon classes' rows", rows=len(sm), unresolved=sum(1 for n, s_, (k, a) in sm if a is None),
        bad=int(any(a is None for n, s_, (k, a) in sm)))
    for n, s_, (k, a) in sm:
        note("%-22s %-18s class %s row %s %s" % (n, s_, k, a, names[a] if a is not None else ""))
    want = {"Raise Skeleton": 67, "Raise Skeletal Mage": 67, "Clay Golem": 67, "BloodGolem": 67, "IronGolem": 67, "FireGolem": 67,
            "Valkyrie": 67, "Dopplezon": 1, "Bone Wall": 84, "Hydra": 86, "Overseer Whip": 117, "Impregnate": 69}
    druid = {a for n, a in rows_by.items() if n in ("Raven", "Plague Poppy", "Oak Sage", "Summon Spirit Wolf", "Cycle of Life",
                                                        "Heart of Wolverine", "Summon Fenris", "Vines", "Spirit of Barbs", "Summon Grizzly")}
    assa = {a for n, a in rows_by.items() if n in ("Blade Sentinel", "Charged Bolt Sentry", "Wake of Fire Sentry", "Shadow Warrior",
                                                       "Lightning Sentry", "Inferno Sentry", "Death Sentry", "Shadow Master")}
    out("p2o", "R38 the named rows", named=" ".join("%s=%s" % (n.replace(" ", "_"), rows_by.get(n)) for n in want),
        druid=",".join(map(str, sorted(druid))), assassin=",".join(map(str, sorted(assa))),
        bone_prison=rows_by.get("Bone Prison"), boneprison_classes=",".join("%d:row%d" % (k, txt[k][2]) for k in range(340, 344)),
        bad=int(any(rows_by.get(n) != v for n, v in want.items()) or druid != set(range(107, 113)) or assa != {101, 102, 104, 105, 106}))
    _, pt = Q.tab("pettype")
    pc = [(r.get("pet type"), c, txt[int(r[c])][2]) for r in pt for c in ("mclass1", "mclass2", "mclass3", "mclass4") if r.get(c)]
    out("p2o", "R38 PetType mclass columns' rows", cells=" ".join("%s:%s" % (p, a) for p, c, a in pc), bad=0)


def _r_name(k):
    return monai_names()[0][k]


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

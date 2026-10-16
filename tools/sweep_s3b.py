"""Plan 0038 batch S3b: static second sources for hirelings, player/creation and monsters claims (no game run, no slot).

Usage:
  python3 -I tools/sweep_s3b.py <check> [-v]
  python3 -I tools/sweep_s3b.py all

Checks:
  logs     the kept logs this batch re-reads, sha256 against their records (tools/mon_sweep.py RUNS for the monster
           runs, the S4b manifest for run:2026-10-15-objects); --write FILE writes the batch manifest
  hire     hirelings 7, 8: Hireling Level order, the GetRecord walk against "greatest Level <= L", the loader's
           first-row index and name ranges (objdump pins, every reference to g_HirelingFirstById), the fatal tests on
           stock data; tools/hirelings.py check on run:2026-10-16-hirelings still 0 mismatches
  player   player/creation 16, 21, 36: SKILLS_AddSkill's raise branch and its callers, CharStats Skill1..10 duplicates,
           ExpMaxLevel against EXP_LevelFromExp's inlined bound and EXP_GetRatio, the ExpRatio shift count per row
  pool     monsters/pool 9, 23: MonStats2 +0x025 recomputed from the .txt lists and from the .bin counts, the game's own
           -txt compile (run:2026-10-15-cube-saves), the cap; RegionActClass read and modelled on the barrel and casket
           monster spawns of run:2026-10-15-objects
  spawn    monsters/spawn 1, 2, 7, 41, 50, 52: RoomUpdateOne against NewRoomsUpdate's per-room body, every caller of
           RoomPopulate, RoomUpdateOne and NewRoomsUpdate, the game pointer of every logged pass, MonStats2 SizeX of
           every class against the pools and the DS1 presets, every reader of Levels +0x2E and region +0x2BE
  special  monsters/special 43: the minion's copied list (ModsXferCopy, MonsterData +0x1C) against the packet builder's
           reader, and the handler-call lines (HD0) of the kept logs against every live minion
  stats    monsters/stats 19, 30, 45: MonStats rows with a reversed HP range, scaled by every MonLvl row, and where
           their classes can be created; the HP draw's instructions; MonProp rows by difficulty and the classes that
           name them; every reference to g_pMonProp

Each check prints one `S3B <check> key=value ...` line of counts plus detail lines, and exits 1 when an observation
contradicts the claim it tests (`bad` > 0). A `contra` count is an observation that contradicts a statement the batch
records as a correction (not a failure of the check). A counterfactual (`cf_*`) must fail where the rule decides.
The second tool next to Ghidra is GNU objdump through tools/sweep_s4b.py's walker (accepted at the S4b review).
The batch record is the "Plan 0038 batch S3b" section of each finding. Unit tests: python3 -I tools/test_sweep_s3b.py.
Stdlib only, plus objdump. Read-only (logs --write writes the manifest file it is given).
"""
import collections
import csv
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
WS = os.path.join(ROOT, "workspace")
LOGS = os.path.join(WS, "logs")
EXCEL = os.path.join(WS, "merged", "data", "global", "excel")
PROBE = os.path.join(WS, "runtime", "game-cubeprobe", "data", "global", "excel")   # run:2026-10-15-cube-saves
OBJ_MANIFEST = ("workspace/logs/sweep-s4b-objects-manifest.txt", "3793a1fae37129f8")

import sweep_s4b as S4  # noqa: E402

VERBOSE = False


class Report(S4.Report):
    def done(self):
        print("S3B %s %s" % (self.name, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        return 1 if self.c["bad"] else 0

    def expect(self, ok, what):
        if not ok:
            self.add("bad")
            self.note("BAD " + what)


# ------------------------------------------------------------------------------------------------------- helpers
def ins(va):
    return S4.asm().at(va)


def pin(R, va, mn, ops_re, what):
    """One instruction of the pinned image, decoded by objdump, must match."""
    got = ins(va)
    ok = got is not None and got[0] == mn and re.search(ops_re, got[1]) is not None
    R.add("pins")
    R.expect(ok, "pin 0x%08X %s: objdump has %s" % (va, what, got))


def direct_refs(target):
    """(mnemonic, site) of every direct call or jmp to target in the objdump decoding of .text."""
    A = S4.asm()
    out = []
    for va, (mn, ops) in A.ins.items():
        if mn in ("call", "jmp") and S4.branch_target(ops) == target:
            out.append((mn, va))
    return sorted(out, key=lambda x: x[1])


def text_matching(pattern):
    rx = re.compile(pattern)
    A = S4.asm()
    return sorted(va for va, (mn, ops) in A.ins.items() if rx.search(ops))


def enclosing(va, after_ret=True):
    """Start of the function holding va: the instruction after the nearest int3 padding or ret before it (a heuristic:
    a function with a ret before its end would be cut; used only to name the caller of a call site)."""
    A = S4.asm()
    if A._sorted is None:
        A.next_va(0)
    import bisect
    i = bisect.bisect_left(A._sorted, va)
    stops = ("int3", "ret") if after_ret else ("int3",)
    while i > 0 and A.ins[A._sorted[i - 1]][0] not in stops:
        i -= 1
    return A._sorted[i]


def call_paths(A, start, stop=(), limit=64):
    """Every acyclic path from start to a ret or to an address in stop, as the tuple of its direct call targets (a
    conditional jump forks the path; no loop is followed twice). A is a decoding with .at(va) and .next_va(va)."""
    out = set()
    work = [(start, (), frozenset())]
    while work and len(out) < limit:
        va, seq, seen = work.pop()
        while True:
            if va in stop or va in seen or va is None:
                out.add(seq)
                break
            seen = seen | {va}
            got = A.at(va)
            if got is None:
                out.add(seq + ("?",))
                break
            mn, ops = got
            if mn == "call":
                t = S4.branch_target(ops)
                seq = seq + (t,)
            elif mn in ("ret", "retn"):
                out.add(seq)
                break
            elif mn == "jmp":
                t = S4.branch_target(ops)
                if t is None:
                    out.add(seq + ("jmp*",))
                    break
                va = t
                continue
            elif mn.startswith("j"):
                t = S4.branch_target(ops)
                if t is not None:
                    work.append((t, seq, seen))
            va = A.next_va(va)
    return out


def comp_count(cell):
    """MonStats2CompList (0x00657010): the number of tokens it stores from one list cell: a leading quote skipped,
    quotes cut, tokens split at ',', stop at an empty token or one longer than 4 characters, at most 12."""
    if cell is None:
        return 0
    s = cell[1:] if cell.startswith('"') else cell
    s = s.split('"')[0]
    n = 0
    for tok in s.split(","):
        if not tok or len(tok) > 4:
            break
        n += 1
        if n >= 12:
            break
    return n


def comp_sum(counts):
    """The +0x025 byte: sum over the 16 counts of (count - 1) for each count >= 2, capped at 254 (0x00657138..90)."""
    return min(sum(c - 1 for c in counts if c > 1), 0xFE)


def shift_count(r, s=10):
    """XP_ApplyExpRatio (0x0057E3B5..C5): (r >> s) + s, the count of the overflow bound's shift."""
    return (r >> s) + s


def greatest_band(rows, vflag, hid, lvl):
    """Reference for HIRELING_GetRecord: the row of (version, Id) with the greatest Level <= lvl, else its first row."""
    v = 100 if vflag else 0
    idx = [i for i, r in enumerate(rows) if r["Id"] == hid and r["Version"] == v]
    if not idx or hid > 255:
        return None
    best = [i for i in idx if rows[i]["Level"] <= lvl]
    return max(best, key=lambda i: rows[i]["Level"]) if best else idx[0]


RANGES_A = {True: [0x60], False: [5]}          # act index 1 (Act II) or other: one 5-class range
RANGES_B = [0, 0xAA, 0x112, 0x17B, 0x17F, 0x183]   # six 4-class ranges
REGION_DEFAULT = 0xEA


def region_act_class(pool, act_index):
    """sub_005474C0_RegionActClass on an empty cache: the base of the range holding the first pool entry that falls in
    one, the act's 5-class range tested first for each entry; 0xEA when none does."""
    for c in pool:
        for b in RANGES_A[act_index == 1]:
            if b <= c < b + 5:
                return b
        for b in RANGES_B:
            if b <= c < b + 4:
                return b
    return REGION_DEFAULT


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def jl(line, tag):
    return json.loads(line[len(tag) + 1:])


# ---------------------------------------------------------------------------------------------------------- logs
def monster_logs():
    import mon_sweep
    out = []
    for run in ("run:2026-10-13-mon-spawn", "run:2026-10-14-mon-special", "run:2026-10-15-mon-stats"):
        out += [(run, p, h) for p, h in mon_sweep.run_logs(run)]
    return out


def objects_logs():
    rel, want = OBJ_MANIFEST
    path = os.path.join(ROOT, rel)
    got = sha256(path)
    if not got.startswith(want):
        raise SystemExit("%s: sha256 %s, the S4b record says %s…" % (rel, got, want))
    out = []
    for ln in open(path):
        if ln.strip():
            h, name = ln.split()
            p = os.path.join(ROOT, name) if "/" in name else os.path.join(LOGS, name)
            g = sha256(p)
            if g != h:
                raise SystemExit("%s: sha256 %s, the manifest says %s" % (p, g, h))
            out.append(("run:2026-10-15-objects", p, g))
    return out


def chk_logs(a):
    R = Report("logs")
    lg = monster_logs() + objects_logs()
    for run, p, h in lg:
        R.add(run.split(":")[1].replace("-", "_"))
    R.add("total", len(lg))
    R.note("every sha256 equal to its record")
    if a.get("write"):
        with open(a["write"], "w") as f:
            f.write("".join("%s  %s\n" % (h, os.path.relpath(p, ROOT)) for run, p, h in lg))
        R.note("manifest written: %s (sha256 %s)" % (a["write"], sha256(a["write"])))
    return R.done()


# ---------------------------------------------------------------------------------------------------------- hire
def chk_hire(a):
    import hirelings
    R = Report("hire")
    t = hirelings.Tables(EXCEL)
    rows = t.rows
    R.add("rows", len(rows))
    vers = collections.Counter(r["Version"] for r in rows)
    R.expect(set(vers) <= {0, 100}, "Version values %s" % dict(vers))
    R.note("Version values %s; Ids %d..%d" % (dict(vers), min(r["Id"] for r in rows), max(r["Id"] for r in rows)))
    # Level order inside each (version, Id), the condition of A3
    for v in (0, 100):
        for hid in sorted({r["Id"] for r in rows if r["Version"] == v}):
            lv = [r["Level"] for r in rows if r["Id"] == hid and r["Version"] == v]
            R.add("ids")
            R.add("bands", len(lv))
            R.expect(lv == sorted(lv) and len(set(lv)) == len(lv), "Id %d version %d Levels %s" % (hid, v, lv))
    # the walk (tools/hirelings.py, the [C] model of run:2026-10-16-hirelings) against the reference reading
    for vf in (0, 1):
        for hid in list(range(0, 31)) + [255, 256]:
            for lvl in range(-5, 106):
                got, ref = t.get_record(vf, hid, lvl), greatest_band(rows, vf, hid, lvl)
                R.add("walks")
                R.expect(got == ref, "GetRecord(%d, %d, %d) = %s, greatest band %s" % (vf, hid, lvl, got, ref))
    # the loader (0x00655720): the first-row index and its reader
    pin(R, 0x0065623E, "cmp", r"WORD PTR \[edi\+ecx\*1\],0x64", "Version compared with 100")
    pin(R, 0x00656243, "sbb", r"eax,eax", "Version < 100 -> -1")
    pin(R, 0x00656248, "shl", r"eax,0x8", "(Version > 99) * 256")
    pin(R, 0x0065624D, "cmp", r"\[eax\*4\+0x96bdd8\],esi", "slot < 0 tested (first row only)")
    pin(R, 0x0065625D, "mov", r"DWORD PTR \[eax\],ebx", "row index stored")
    pin(R, 0x00656236, "cmp", r"edx,0x100", "Id >= 256 skipped")
    pin(R, 0x0065631A, "setne", r"dl", "GetRecord: vflag != 0")
    pin(R, 0x0065631D, "shl", r"edx,0x8", "GetRecord: * 256")
    pin(R, 0x00656322, "mov", r"ecx,DWORD PTR \[edx\*4\+0x96bdd8\]", "GetRecord reads the slot")
    pin(R, 0x00656180, "mov", r"DWORD PTR \[eax-0x400\],0xffffffff", "loader: both halves set to -1")
    # 0x96C5D8 is the end bound of the two loops; `ds:0x96c5d8` elsewhere is the next global, not this table
    refs = text_matching(r"0x96bdd8|0x96c1d8|^eax,0x96c5d8$")
    other = text_matching(r"ds:0x96c5d8")
    R.add("firstbyid_refs", len(refs))
    R.note("ds:0x96c5d8 (the next global) at %s" % ", ".join("0x%08X" % v for v in other))
    R.note("instructions naming g_HirelingFirstById or its bounds: %s" % ", ".join("0x%08X" % v for v in refs))
    own = [v for v in refs if not (0x00655720 <= v < 0x006562E3 or 0x006562F0 <= v < 0x00656390)]
    R.expect(not own, "a reference outside the loader, its unloader and GetRecord: %s" % own)
    # name ranges: the loader's two STRTABLE_GetByKey writes and their readers
    pin(R, 0x006561CF, "call", r"0x524d30", "STRTABLE_GetByKey(NameFirst)")
    pin(R, 0x006561DA, "mov", r"WORD PTR \[edi\+ecx\*1\+0x114\],ax", "+0x114 written")
    pin(R, 0x006561F3, "call", r"0x524d30", "STRTABLE_GetByKey(NameLast)")
    pin(R, 0x00656201, "mov", r"WORD PTR \[edi\+edx\*1\+0x116\],ax", "+0x116 written")
    pin(R, 0x0057601F, "movzx", r"edx,WORD PTR \[eax\+0x114\]", "HIRE_GetNameRange reads +0x114")
    pin(R, 0x0057602C, "movzx", r"esi,WORD PTR \[eax\+0x116\]", "HIRE_GetNameRange reads +0x116")
    pin(R, 0x0065621C, "jbe", r"0x656281", "fatal 0x816: first index 0")
    pin(R, 0x00656226, "jbe", r"0x6562a0", "fatal 0x817: last <= first")
    pin(R, 0x00656230, "jge", r"0x6562a7", "fatal 0x818: Id >= 256")
    R.add("stock_first_zero", sum(1 for r in rows if r["first"] == 0))
    R.add("stock_last_le_first", sum(1 for r in rows if r["last"] <= r["first"]))
    R.add("stock_id_ge_256", sum(1 for r in rows if r["Id"] >= 256))
    R.note("stock name ranges (first..last): %s" % sorted({(r["first"], r["last"]) for r in rows}))
    # the run still reproduces with this model
    man = os.path.join(LOGS, "hire-run-manifest.txt")
    logs = [os.path.join(LOGS, ln.split()[1]) for ln in open(man) if ln.strip()]
    p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "hirelings.py"), "check", EXCEL] + logs,
                       capture_output=True, text=True)
    tail = [ln for ln in p.stdout.splitlines() if "mismatch" in ln.lower()][-1:] or p.stdout.splitlines()[-1:]
    R.add("hirelings_check_rc", p.returncode)
    R.expect(p.returncode == 0, "tools/hirelings.py check returned %d" % p.returncode)
    R.note("tools/hirelings.py check on %d logs of run:2026-10-16-hirelings: %s" % (len(logs), " ".join(tail)))
    return R.done()


# -------------------------------------------------------------------------------------------------------- player
def chk_player(a):
    import excel_bin
    R = Report("player")
    # SKILLS_AddSkill (0x00647110): the existing-entry branch
    pin(R, 0x00647167, "cmp", r"DWORD PTR \[esi\],edi", "entry skill = the record")
    pin(R, 0x0064716B, "cmp", r"DWORD PTR \[esi\+0x34\],0xffffffff", "entry item ref = -1")
    pin(R, 0x0064716F, "je", r"0x647245", "found -> raise branch")
    pin(R, 0x0064724A, "call", r"0x4aa8b0", "SKILLS_GetMaxLevel")
    pin(R, 0x0064724F, "cmp", r"edi,eax", "level < max")
    pin(R, 0x00647251, "jl", r"0x64725b", "below max -> +1")
    pin(R, 0x00647256, "cmp", r"DWORD PTR \[eax\],0x1", "unit type 1 (monster) raises past the max")
    pin(R, 0x0064725B, "add", r"edi,0x1", "level + 1")
    pin(R, 0x0064725E, "mov", r"DWORD PTR \[esi\+0x28\],edi", "level stored at entry +0x28")
    pin(R, 0x006471EE, "mov", r"DWORD PTR \[esi\+0x28\],0x1", "a new entry gets level 1")
    pin(R, 0x004AA8CD, "movsx", r"eax,WORD PTR \[eax\+ecx\*1\+0x12c\]", "max level = Skills +0x12C")
    pin(R, 0x004AA8D9, "mov", r"eax,0x14", "max level 20 when the cell is <= 0")
    callers = direct_refs(0x00647110)
    R.add("addskill_sites", len(callers))
    R.note("SKILLS_AddSkill call sites: %s" % ", ".join("0x%08X" % v for _, v in callers))
    pin(R, 0x005700FF, "call", r"0x6253b0", "spend path: GetStat(unit, 5 newskills)")
    pin(R, 0x00570113, "call", r"0x6272b0", "spend path: AddStat(unit, 5, -cost)")
    pin(R, 0x0057011A, "call", r"0x647110", "spend path: SKILLS_AddSkill on the same skill")
    # CharStats Skill1..10: can the creation itself meet the raise branch?
    recs, _ = excel_bin.read_bin(excel_bin.find_file(EXCEL, "charstats", ".bin"))
    dup = 0
    for i, r in enumerate(recs):
        ids = [s for s in struct.unpack_from("<10h", r, 0xAE) if s >= 0]
        if len(set(ids)) != len(ids) or 0 in ids:
            dup += 1
            R.note("CharStats record %d Skill1..10 %s repeats a skill or names Attack" % (i, ids))
        if VERBOSE:
            R.note("CharStats %d skills %s" % (i, ids))
    R.add("charstats_records", len(recs))
    R.add("charstats_repeat_or_attack", dup)
    # Experience: MaxLvl and ExpRatio
    rows = list(csv.reader(open(excel_bin.find_file(EXCEL, "experience", ".txt"), errors="replace"), delimiter="\t"))
    hdr, body = rows[0], [r for r in rows[1:] if r and r[0]]
    cls = hdr[1:8]
    maxrow = body[0]
    R.expect(maxrow[0] == "MaxLvl", "Experience row 0 is %r" % maxrow[0])
    R.note("Experience row 0 (%s) per class %s: %s; ExpRatio %s" % (maxrow[0], cls, maxrow[1:8], maxrow[hdr.index("ExpRatio")]))
    ri = hdr.index("ExpRatio")
    ratios = [int(r[ri]) for r in body[1:]]
    s = int(maxrow[ri])
    counts = collections.Counter(shift_count(r, s) for r in ratios)
    R.add("ratio_rows", len(ratios))
    R.add("ratio_max", max(ratios))
    R.expect(set(counts) <= {10, 11}, "shift counts %s" % dict(counts))
    R.note("ExpRatio rows %d, values %s; shift count (r >> %d) + %d per row: %s; with r = 0 above MaxLvl: %d" % (
        len(ratios), sorted(set(ratios)), s, s, dict(counts), shift_count(0, s)))
    # binary bin rows: the compiled table the game reads (row stride 0x20, ExpRatio at +0x1C)
    brecs, bsz = excel_bin.read_bin(excel_bin.find_file(EXCEL, "experience", ".bin"))
    R.expect(bsz == 0x20, "experience.bin record size 0x%X" % bsz)
    bmax = struct.unpack_from("<7I", brecs[0], 0)
    bratio = [struct.unpack_from("<I", r, 0x1C)[0] for r in brecs]
    R.expect(list(bmax) == [int(x) for x in maxrow[1:8]], "experience.bin row 0 %s" % (bmax,))
    R.expect(set(shift_count(r, bratio[0]) for r in bratio[1:]) <= {10, 11}, "bin shift counts")
    R.note("experience.bin: row 0 %s, ExpRatio of row 0 %d, %d rows" % (list(bmax), bratio[0], len(brecs)))
    # the three readers of Experience row 0
    pin(R, 0x00611854, "mov", r"eax,DWORD PTR \[edx\+eax\*4\]", "ExpMaxLevel reads row 0, column c")
    pin(R, 0x00611847, "mov", r"eax,DWORD PTR \[ecx\+eax\*4\]", "ExpMaxLevel, class out of 0..6 -> column 0")
    pin(R, 0x00611885, "mov", r"esi,DWORD PTR \[edx\+eax\*4\]", "EXP_LevelFromExp's loop bound, the same cell")
    pin(R, 0x00611895, "cmp", r"eax,esi", "EXP_LevelFromExp: n < MaxLvl")
    pin(R, 0x00613E81, "cmp", r"eax,DWORD PTR \[ecx\]", "EXP_GetRatio: L > row 0 column 0")
    pin(R, 0x00613E7A, "mov", r"eax,DWORD PTR \[ecx\+0x1c\]", "EXP_GetRatio(L <= 0): row 0 ExpRatio")
    # XP_ApplyExpRatio
    pin(R, 0x0057E3B0, "cmp", r"ecx,0x1e", "1 <= s <= 31")
    pin(R, 0x0057E3B9, "sar", r"edx,cl", "r >> s")
    pin(R, 0x0057E3C1, "add", r"edx,eax", "+ s")
    pin(R, 0x0057E3C5, "sar", r"ebx,cl", "0x7FFFFFFF >> ((r >> s) + s)")
    return R.done()


# ---------------------------------------------------------------------------------------------------------- pool
M2_LISTS = ["HDv", "TRv", "LGv", "Rav", "Lav", "RHv", "LHv", "SHv", "S1v", "S2v", "S3v", "S4v", "S5v", "S6v", "S7v",
            "S8v"]


def objects_events(path):
    """Barrel/casket monster spawns of one objects log: [(fn, object id, MT0 class, room, a10)], the room -> level map,
    and the region snapshots by level in log order."""
    out, room_lid, snaps = [], {}, []
    cur = None
    for i, ln in enumerate(open(path, errors="replace")):
        tag = ln.split(" ", 1)[0]
        if '"lid":' in ln and '"room":' in ln and tag in ("OPU0", "P0", "PX"):
            m = re.search(r'"room":(\d+)', ln)
            n = re.search(r'"lid":(\d+)', ln)
            if m and n and tag == "OPU0":
                room_lid[int(m.group(1))] = int(n.group(1))
        if tag in ("P0", "PX") and '"reg":' in ln:
            d = jl(ln, tag)
            g = d.get("reg") or {}
            if "lid" in g:
                snaps.append((i, g["lid"], g["npool"], [e[0] for e in g["ents"]]))
        if tag == "OO0":
            d = jl(ln, tag)
            cur = d if d.get("fn") in (1, 5) else None
        elif tag == "OOX":
            cur = None
        elif tag == "MT0" and cur is not None:
            d = jl(ln, tag)
            out.append((i, cur["fn"], cur["id"], d["cls"], d["room"], d["a10"]))
    return out, room_lid, snaps


def chk_pool(a):
    import excel_bin
    import monpool
    R = Report("pool")
    hdr, rows = excel_bin.read_txt(excel_bin.find_file(EXCEL, "monstats2", ".txt"))
    rows = [r for r in rows if r and r[0] and r[0] != "Expansion"]
    recs, sz = excel_bin.read_bin(excel_bin.find_file(EXCEL, "monstats2", ".bin"))
    R.add("records", len(recs))
    R.expect(len(rows) == len(recs), "%d .txt rows, %d records" % (len(rows), len(recs)))
    sums = collections.Counter()
    for r, b in zip(rows, recs):
        txt_counts = [comp_count(r[hdr.index(c)]) for c in M2_LISTS]
        bin_counts = list(b[0x15:0x25])
        R.expect(txt_counts == bin_counts, "%s: counts %s, .bin %s" % (r[0], txt_counts, bin_counts))
        s = comp_sum(bin_counts)
        raw = sum(c - 1 for c in bin_counts if c > 1)
        sums[raw] += 1
        R.expect(b[0x25] == s, "%s: +0x025 = %d, sum %d" % (r[0], b[0x25], s))
        R.add("sum_matches", int(b[0x25] == s))
        R.add("raw_over_254", int(raw > 254))
        R.add("cf_all_counts", int(b[0x25] == min(sum(bin_counts), 254)))    # without the "count >= 2" rule
    R.note("+0x025 values: 0 in %d records, largest %d" % (sums[0], max(sums)))
    probe = os.path.join(PROBE, "monstats2.bin")
    same = os.path.exists(probe) and open(probe, "rb").read() == open(
        excel_bin.find_file(EXCEL, "monstats2", ".bin"), "rb").read()
    R.add("game_compile_identical", int(same))
    R.expect(same, "the game's -txt compile of monstats2 differs from the shipped .bin (or is missing)")
    pin(R, 0x0065712C, "cmp", r"eax,0xf", "the sum is taken at the last list (S8v)")
    pin(R, 0x00657143, "cmp", r"dl,0x1", "counts <= 1 skipped")
    pin(R, 0x0065714B, "lea", r"ecx,\[ecx\+edx\*1-0x1\]", "sum += count - 1")
    pin(R, 0x00657183, "cmp", r"ecx,0xfe", "cap 254")
    pin(R, 0x0065718B, "mov", r"ecx,0xfe", "cap 254")
    pin(R, 0x00657190, "mov", r"BYTE PTR \[ebx\+0x25\],cl", "stored at +0x025")
    # RegionActClass (0x005474C0): its pool reads and the logged spawns that go through it
    pin(R, 0x0054754C, "lea", r"ecx,\[edi\+0xf0\]", "game +0xF0 (pMonRegions)")
    pin(R, 0x00547554, "call", r"0x547bb0", "the level's MonRegion")
    pin(R, 0x00547563, "movzx", r"ecx,BYTE PTR \[eax\+0x10\]", "MonRegion nPool (+0x010)")
    pin(R, 0x00547570, "lea", r"edi,\[eax\+0x14\]", "entries at +0x014")
    pin(R, 0x00547573, "movsx", r"edx,WORD PTR \[edi\]", "entry classId (+0x00)")
    pin(R, 0x005475AA, "add", r"edi,0x34", "entry stride 0x34")
    pin(R, 0x0054755C, "mov", r"DWORD PTR \[ecx\+0x1c\],0xea", "cache default 0xEA")
    pin(R, 0x005474F1, "mov", r"ecx,DWORD PTR \[ecx\+0x1c\]", "cached class read first")
    for site in (0x00582338, 0x00582568, 0x005864C9, 0x0058696D):
        pin(R, site, "call", r"0x5474c0", "RegionActClass caller")
    callers = direct_refs(0x005474C0)
    R.add("regionactclass_sites", len(callers))
    T = monpool.Tables(EXCEL)
    lists = [p for _, p, _ in objects_logs()]
    cache = {}
    for path in lists:
        ev, room_lid, snaps = objects_events(path)
        cache = {}
        for (i, fn, oid, cls, room, a10) in ev:
            if a10 != 8:
                continue
            lid = room_lid.get(room)
            snap = [s for s in snaps if s[0] < i and s[1] == lid]
            if lid is None or not snap:
                R.add("spawn_no_context")
                continue
            _, _, npool, ents = snap[-1]
            act = T.lvl_u8(lid, 3)
            base = cache.get(lid)
            if base is None:
                base = region_act_class(ents[:npool], act)
                cache[lid] = base
            # LevelClassVariant (0x0063EC70): the level's mon-list class with the same BaseId (the branch both
            # logged spawns take; its NextInClass walk is not modelled)
            bid = T.m16(base, 0x02) if hasattr(T, "m16") else struct.unpack_from("<h", T.ms[base], 0x02)[0]
            lst = [c for c in T.slots(lid, 0x36) if struct.unpack_from("<h", T.ms[c], 0x02)[0] == bid]
            pred = lst[0] if lst else None
            R.add("spawns")
            R.expect(pred == cls, "%s line %d: fn %d object %d level %d pool %s -> base %d, variant %s, logged %d" % (
                os.path.basename(path), i, fn, oid, lid, ents[:npool], base, pred, cls))
            cfb = REGION_DEFAULT
            cfl = [c for c in T.slots(lid, 0x36) if struct.unpack_from("<h", T.ms[c], 0x02)[0]
                   == struct.unpack_from("<h", T.ms[cfb], 0x02)[0]]
            R.add("cf_no_pool_read_ok", int((cfl[0] if cfl else cfb) == cls))
            R.note("%s line %d: fn %d object %d, level %d, nPool %d %s -> RegionActClass %d -> variant %s; logged %d" % (
                os.path.basename(path), i, fn, oid, lid, npool, ents[:npool], base, pred, cls))
    return R.done()


# --------------------------------------------------------------------------------------------------------- spawn
def chk_spawn(a):
    import excel_bin
    import monpool
    R = Report("spawn")
    A = S4.asm()
    seq_one = call_paths(A, 0x0052D0F0)
    seq_room = call_paths(A, 0x0052D1C0, stop={0x0052D211})     # one turn of NewRoomsUpdate's room loop

    def fmt(ps):
        return sorted(" -> ".join("0x%08X" % t for t in p) for p in ps)
    R.note("RoomUpdateOne call paths: %s" % fmt(seq_one))
    R.note("NewRoomsUpdate, one room: call paths: %s" % fmt(seq_room))
    R.expect(seq_one == seq_room, "the call paths differ")
    R.add("call_paths", len(seq_one))
    R.add("same_call_paths", int(seq_one == seq_room))
    pin(R, 0x0052D0FB, "test", r"BYTE PTR \[esi\+0x34\],0x1", "RoomUpdateOne: bit 0 tested")
    pin(R, 0x0052D1C9, "test", r"BYTE PTR \[esi\+0x34\],bl", "NewRoomsUpdate: bit 0 tested (bl = 1)")
    pin(R, 0x0052D125, "or", r"DWORD PTR \[esi\+0x34\],0x1", "RoomUpdateOne: bit 0 set")
    pin(R, 0x0052D1F2, "or", r"DWORD PTR \[esi\+0x34\],ebx", "NewRoomsUpdate: bit 0 set")
    for name, t in (("RoomPopulate", 0x0054EC90), ("RoomUpdateOne", 0x0052D0F0), ("NewRoomsUpdate", 0x0052D160),
                    ("dead fragment 0x0052D0C0", 0x0052D0C0)):
        refs = direct_refs(t)
        absr = S4.raw_abs(t)
        R.add("refs_" + name.split()[0], len(refs))
        R.note("%s: direct references %s; absolute pointers %d" % (
            name, ", ".join("%s 0x%08X (fn 0x%08X)" % (mn, v, enclosing(v)) for mn, v in refs), len(absr)))
    # the game pointer of every logged pass
    games = collections.Counter()
    for run, p, _ in monster_logs() + objects_logs():
        g = set()
        n = 0
        for ln in open(p, errors="replace"):
            if ln.startswith("P0 {"):
                m = re.match(r'P0 \{"game":(\d+)', ln)
                g.add(int(m.group(1)))
                n += 1
        if n:
            R.add("pass_logs")
            R.add("passes", n)
            games[len(g)] += 1
            R.expect(len(g) == 1, "%s: %d game pointers in its passes" % (os.path.basename(p), len(g)))
    R.note("logs with passes by number of distinct game pointers: %s" % dict(games))
    # SizeX: which classes have 0, 1 or another size, and where they come from
    T = monpool.Tables(EXCEL)
    m2 = T.ms2
    names = []
    hdr, mrows = excel_bin.read_txt(excel_bin.find_file(EXCEL, "monstats", ".txt"))
    names = [r[0] for r in mrows if r and r[0] and r[0] != "Expansion"]
    size = {}
    for c in range(len(T.ms)):
        i2 = struct.unpack_from("<h", T.ms[c], 0x18)[0]
        size[c] = struct.unpack_from("<b", m2[i2], 0x08)[0] if 0 <= i2 < len(m2) else None
    hist = collections.Counter(struct.unpack_from("<b", r, 0x08)[0] for r in m2)
    R.note("MonStats2 SizeX over %d records: %s" % (len(m2), dict(sorted(hist.items()))))
    R.add("sizex_other", sum(n for k, n in hist.items() if k not in (0, 1, 2, 3)))
    pools = collections.defaultdict(set)
    for lid in range(1, len(T.lv)):
        for off in (0x36, 0x68, 0x9A):
            for c in T.slots(lid, off):
                pools[c].add((lid, {0x36: "mon", 0x68: "nmon", 0x9A: "umon"}[off]))
    small = sorted(c for c in size if size[c] in (0, 1))
    R.add("classes_size01", len(small))
    for c in small:
        if pools.get(c):
            R.add("pool_size01")
            R.note("pool class %d %s SizeX %d in %s" % (c, names[c], size[c], sorted(pools[c])))
    R.note("classes with SizeX 0 or 1: %s" % ", ".join("%d %s(%d)" % (c, names[c], size[c]) for c in small))
    pin(R, 0x0064D9B0, "push", r"ebp", "CollisionTest entry")
    # MonWndr: every reader of Levels +0x2E and of region +0x2BE
    g = text_matching(r"\+0x2be\]")
    R.note("instructions with displacement +0x2BE: %s" % ["0x%08X %s %s" % (v, *A.ins[v]) for v in g])
    R.add("disp_2be", len(g))
    R.expect(g == [0x00547A9D], "+0x2BE operands %s" % g)
    sites = direct_refs(0x0061DB70)
    fns = sorted({enclosing(v, after_ret=False) for _, v in sites})
    R.add("getrecord_sites", len(sites))
    R.add("getrecord_fns", len(fns))
    readers = []
    for f in fns:
        vas, _, _ = S4.body(A, f)
        hit = [v for v in sorted(vas) if re.search(r"\+0x2e\]", A.ins[v][1])]
        if hit:
            readers.append((f, hit))
    R.note("LEVELS_GetRecord callers with a +0x2E operand: %s" % [("0x%08X" % f, ["0x%08X %s %s" % (v, *A.ins[v])
                                                                                    for v in h]) for f, h in readers])
    R.expect([f for f, _ in readers] == [0x005479C0, 0x0054F060], "readers %s" % readers)
    c58 = text_matching(r"\+0xc58\]")
    c58 = [v for v in c58 if "ebp" not in A.ins[v][1]]
    R.note("DataTables +0xC58 operands: %s" % ["0x%08X" % v for v in c58])
    R.expect(all(0x0061DB70 <= v < 0x0061DD00 for v in c58), "a +0xC58 operand outside the Levels accessors")
    i220 = text_matching(r",0x220$")
    i220 = [v for v in i220 if A.ins[v][0] == "imul"]
    R.note("imul by 0x220: %s" % ["0x%08X" % v for v in i220])
    R.expect(all(0x0061DB70 <= v < 0x0061DD00 for v in i220), "an imul 0x220 outside the Levels accessors")
    pin(R, 0x00547A99, "movzx", r"edx,BYTE PTR \[eax\+0x2e\]", "region build reads MonWndr")
    pin(R, 0x00547A9D, "mov", r"BYTE PTR \[esi\+0x2be\],dl", "copied to region +0x2BE")
    pin(R, 0x0054F0AA, "cmp", r"BYTE PTR \[eax\+0x2e\],0x0", "the tick reads MonWndr from the Levels record")
    return R.done()


# ------------------------------------------------------------------------------------------------------- special
def chk_special(a):
    R = Report("special")
    pin(R, 0x005A0949, "lea", r"ebx,\[eax\+0x1c\]", "ModsXferCopy: source list = boss MonsterData +0x1C")
    pin(R, 0x005A0960, "lea", r"esi,\[eax\+0x1c\]", "ModsXferCopy: destination = minion MonsterData +0x1C")
    pin(R, 0x005A09B6, "mov", r"BYTE PTR \[esi\],cl", "the copy")
    pin(R, 0x005A0133, "lea", r"eax,\[ecx\+0x1c\]", "MonGetModList returns MonsterData +0x1C")
    pin(R, 0x005A0395, "cmp", r"BYTE PTR \[ecx\+0x1c\],al", "MonHasMods tests MonsterData +0x1C")
    pin(R, 0x0053E494, "call", r"0x5a0380", "MonUnitPacketBuild: has mods?")
    pin(R, 0x0053E594, "call", r"0x5a0120", "MonUnitPacketBuild: the mod list")
    vas, calls, _ = S4.body(S4.asm(), 0x0053E2E0)
    R.add("packet_list_calls", sum(1 for _, t in calls if t == 0x005A0120))
    R.note("MonGetModList (0x005A0120) direct callers: %d sites" % len(direct_refs(0x005A0120)))
    live_total, hd_total, hd_on_minion, hd_on_reused = 0, 0, 0, 0
    for run, p, _ in monster_logs():
        if "special" not in run and "stats" not in run:
            continue
        live, dead = {}, set()
        for ln in open(p, errors="replace"):
            if ln.startswith("MU {"):
                u = jl(ln, "MU")["unit"]["u"]
                if u in live:
                    dead.add(u)
                live.pop(u, None)
            elif ln.startswith("XF {"):
                d = jl(ln, "XF")
                live[d["m"]] = d
                live_total += 1
            elif ln.startswith("HD0 {"):
                d = jl(ln, "HD0")
                hd_total += 1
                if d["u"] in live:
                    hd_on_minion += 1
                    R.note("HD0 on a live minion: %s %s" % (os.path.basename(p), d))
    R.add("minion_lists", live_total)
    R.add("handler_calls", hd_total)
    R.add("handler_on_live_minion", hd_on_minion)
    R.expect(hd_on_minion == 0, "a handler call on a live minion")
    return R.done()


# --------------------------------------------------------------------------------------------------------- stats
def chk_stats(a):
    import excel_bin
    import monpool
    import monstats
    import ds1
    R = Report("stats")
    MT = monstats.Tables(EXCEL)
    M = monstats.Model(MT)
    hdr, mrows = excel_bin.read_txt(excel_bin.find_file(EXCEL, "monstats", ".txt"))
    names = [r[0] for r in mrows if r and r[0] and r[0] != "Expansion"]
    rev = []
    for c in range(len(MT.ms)):
        for d in range(3):
            lo, hi = MT.m16(c, 0xB0 + 2 * d), MT.m16(c, 0xB6 + 2 * d)
            if hi < lo:
                nle0 = sum(1 for L in range(0, 111) if (lambda o: o[1] - o[0] + 1 <= 0)(M.monlvl_stats(c, 1, d, L)))
                rev.append((c, d, lo, hi, nle0))
                R.note("reversed HP: class %d %s difficulty %d minHP %d maxHP %d; scaled n = hi - lo + 1 <= 0 at %d of "
                       "111 MonLvl rows" % (c, names[c], d, lo, hi, nle0))
    R.add("reversed_rows", len(rev))
    pin(R, 0x00573F83, "mov", r"edx,DWORD PTR \[ebp-0x58\]", "maxHp (scaled)")
    pin(R, 0x00573F86, "sub", r"edx,DWORD PTR \[ebp-0x5c\]", "- minHp")
    pin(R, 0x00573F8C, "add", r"edx,0x1", "+ 1")
    pin(R, 0x00573F8F, "call", r"0x45c3e0", "RNG_RangeB(unit seed, n)")
    pin(R, 0x00573F99, "add", r"edi,DWORD PTR \[ebp-0x5c\]", "+ minHp")
    pin(R, 0x0045C3E3, "test", r"esi,esi", "RNG_RangeB tests n")
    pin(R, 0x0045C3E5, "jg", r"0x45c3eb", "n > 0 (signed) -> the step")
    pin(R, 0x0045C3E7, "xor", r"eax,eax", "n <= 0 -> 0, no step")
    # where the reversed classes come from: pools and the DS1 presets lvlprest names
    T = monpool.Tables(EXCEL)
    revc = sorted({c for c, *_ in rev})
    for c in revc:
        pl = sorted({lid for lid in range(1, len(T.lv)) for off in (0x36, 0x68, 0x9A) if c in T.slots(lid, off)})
        R.note("class %d %s in the pools of levels %s" % (c, names[c], pl))
    root = os.path.join(WS, "merged")
    tables = ds1._tables(root)
    tiles = os.path.join(root, "data", "global", "tiles")
    files = {}
    for dp, _, fn in os.walk(tiles):
        for f in fn:
            files[os.path.relpath(os.path.join(dp, f), tiles).replace("\\", "/").lower()] = os.path.join(dp, f)
    placed = collections.defaultdict(set)
    for n in sorted(ds1.lvlprest_names(root)):
        p = files.get(n)
        if not p:
            continue
        for u in ds1._units(ds1.parse(open(p, "rb").read()), tables, None):
            if u["type"] == 1 and u["id"] in revc:
                placed[u["id"]].add(n)
    for c in revc:
        R.note("class %d %s placed by DS1s: %s" % (c, names[c], sorted(placed.get(c, ()))))
        R.add("ds1_placed_%d" % c, len(placed.get(c, ())))
    # MonProp: the rows with a normal slot, and the classes naming them
    mp_hdr, mp_rows = excel_bin.read_txt(excel_bin.find_file(EXCEL, "monprop", ".txt"))
    mp_rows = [r for r in mp_rows if r and r[0]]
    mp_col = hdr.index("MonProp")
    namers = collections.defaultdict(list)
    for r in mrows:
        if r and r[0] and r[0] != "Expansion" and len(r) > mp_col and r[mp_col]:
            namers[r[mp_col]].append(r[0])
    normal = [r[0] for r in mp_rows if any(r[mp_hdr.index("prop%d" % k)] for k in range(1, 7))]
    R.add("monprop_rows", len(mp_rows))
    R.add("monprop_normal_rows", len(normal))
    for row in normal:
        R.note("MonProp row %s has a normal slot; named by MonStats %s" % (row, namers.get(row, [])))
    sk_hdr, sk_rows = excel_bin.read_txt(excel_bin.find_file(EXCEL, "skills", ".txt"))
    si, ci = sk_hdr.index("summon"), sk_hdr.index("charclass")
    summons = {r[si]: (r[0], r[ci]) for r in sk_rows if r and len(r) > si and r[si]}
    for row in normal:
        for cls in namers.get(row, []):
            if cls in summons and summons[cls][1] in ("ama", "sor", "nec", "pal", "bar", "dru", "ass"):
                R.add("contra")
                R.note("CONTRA %s is the player skill %s's summon (charclass %s): created in a normal game with "
                       "MonStatsInit's d = 0" % (cls, summons[cls][0], summons[cls][1]))
    pin(R, 0x005734A6, "imul", r"eax,eax,0x138", "MonPropRec: record stride 0x138")
    pin(R, 0x005734AC, "add", r"eax,DWORD PTR \[edx\+0xc30\]", "MonPropRec reads DataTables +0xC30")
    A = S4.asm()
    c30 = [v for v in text_matching(r"\+0xc30\]") if "ebp" not in A.ins[v][1]]
    absr = [v for v in text_matching(r"0x96c860\b")]
    R.note("DataTables +0xC30 operands: %s; g_pMonProp by address: %s" % (
        ["0x%08X" % v for v in c30], ["0x%08X %s %s" % (v, *A.ins[v]) for v in absr]))
    R.expect(c30 == [0x005734AC], "+0xC30 operands %s" % c30)
    R.expect(all(0x00659400 <= v < 0x00659600 or 0x0065A200 <= v < 0x0065A300 for v in absr),
             "g_pMonProp named outside its loader and unloader")
    R.add("monprop_readers", len(c30))
    c34 = [v for v in text_matching(r"\+0xc34\]") if "ebp" not in A.ins[v][1]]
    R.note("DataTables +0xC34 (MonProp count) operands: %s" % ["0x%08X" % v for v in c34])
    return R.done()


CHECKS = collections.OrderedDict([("logs", chk_logs), ("hire", chk_hire), ("player", chk_player), ("pool", chk_pool),
                                  ("spawn", chk_spawn), ("special", chk_special), ("stats", chk_stats)])


def main(argv):
    global VERBOSE
    a = {}
    args = [x for x in argv if not x.startswith("-")]
    VERBOSE = "-v" in argv
    if "--write" in argv:
        a["write"] = argv[argv.index("--write") + 1]
        args = [x for x in args if x != a["write"]]
    if not args or args[0] not in list(CHECKS) + ["all"]:
        print(__doc__)
        return 2
    names = list(CHECKS) if args[0] == "all" else [args[0]]
    rc = 0
    for n in names:
        rc |= CHECKS[n](a)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

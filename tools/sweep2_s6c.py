#!/usr/bin/env python3
"""Plan 0066 batch S6c (anim/timing, anim/movement, anim/README): static second sources for the rows routed to (c).
No game run, no Ghidra.

Usage:
  python3 -I tools/sweep2_s6c.py static      # every check below, in row order; one `S6C <check> key=value ...` line each

The first tool behind each claim is a kept output of plan 0050 (objdump through tools/anim_scan.py, anim_rates.py and
anim_moves.py; Ghidra's xrefs and RngCallGraph): `workspace/logs/anim/p50a-anim-scan.txt`, `p50b-calls.txt`,
`p50b-setrate-xrefs.txt`, `p50d-calls.txt`, `p50a-rng-machine.txt`, `p50a-rng-modes.txt`. The second tool here is
independent of them:
  - xrefs: a raw-byte scan of rel32 calls and jumps (tools/xrefscan.py), each site decoded again by r2;
  - code reads: r2's linear disassembly of the named ranges, matched against the instruction shape the claim needs;
  - tables in the image: r2 `pxw` dumps (and the raw PE bytes, through tools/sweep_s4b.py);
  - draws: tools/sweep_s4b.py's objdump call-graph walker over the same roots and stops as the Ghidra scan, every
    walked body searched for the LCG multiplier and the RNG primitives, plus r2's own search for the multiplier;
  - data: the stock tables through tools/anim_survey.py's loaders (animdata.d2, monstats, skills).
`bad=` counts an observation that contradicts the statement a check tests; `contra=` an observation the batch records
as a correction. Record: findings/anim/experiments.md, the "plan 0066 batch S6c" static addendum.
Stdlib only, plus tools/sweep_s4b.py, tools/sweep2_s4cd.py, tools/anim_survey.py (and their imports), objdump and r2.
Read-only.
"""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep_s4b as S     # noqa: E402
import sweep2_s4cd as S4  # noqa: E402

ROOT = os.path.dirname(HERE)
ALOGS = os.path.join(ROOT, "workspace", "logs", "anim")
DATA = os.path.join(ROOT, "workspace", "merged")

TOTAL_BAD = [0]


class Rep:
    def __init__(self, name, rows):
        self.name, self.rows = name, rows
        self.c = collections.Counter()
        self.notes = []

    def add(self, k, n=1):
        self.c[k] += n

    def bad(self, why):
        self.c["bad"] += 1
        self.notes.append("BAD %s" % (why,))

    def contra(self, why):
        self.c["contra"] += 1
        self.notes.append("CONTRA %s" % (why,))

    def note(self, s):
        self.notes.append(s)

    def done(self):
        self.c["bad"] += 0
        print("S6C %s rows=%s %s" % (self.name, self.rows, " ".join("%s=%d" % (k, self.c[k]) for k in sorted(self.c))))
        for s in self.notes:
            print("  " + s)
        TOTAL_BAD[0] += self.c["bad"]


# ------------------------------------------------------------------------------------------------------------ r2 helpers
R2_LINE = re.compile(r"^\s*0x([0-9a-f]{8})\s+(\S+)\s*(.*?)\s*$")


def r2_at(vas):
    """{va: (mnemonic, operands)}: one instruction decoded by r2 at each address (one r2 process)."""
    vas = sorted(set(vas))
    out = {}
    for k in range(0, len(vas), 200):
        cmd = ";".join("pd 1 @ 0x%x" % v for v in vas[k:k + 200])
        for ln in S4.r2(cmd).splitlines():
            m = R2_LINE.match(ln)
            if m:
                out[int(m.group(1), 16)] = (m.group(2), m.group(3))
    return out


def r2_fn(entry, maxlen=0x1000):
    """r2's linear listing from entry to the first int3 run (the padding after the function)."""
    out = []
    for va, mn, ops in S4.r2_range(entry, entry + maxlen):
        if mn == "int3":
            break
        out.append((va, mn, ops))
    return out


def r2_pxw(va, n):
    """n dwords at va from r2's `pxw`."""
    vals = []
    for ln in S4.r2("pxw %d @ 0x%x" % (4 * n, va)).splitlines():
        f = ln.split()
        if len(f) >= 2 and f[0].startswith("0x"):
            for w in f[1:5]:
                if w.startswith("0x") and len(w) == 10:
                    vals.append(int(w, 16))
    return vals[:n]


def calls_of(listing):
    return [(va, S4.imm(ops)) for va, mn, ops in listing if mn == "call" and S4.imm(ops) is not None]


def sites(target):
    """(raw rel32 call sites, raw jmp sites, abs32 sites, r2-confirmed call sites)."""
    rel, calls, ab = S4.raw(target)
    dec = r2_at(rel)
    conf = [v for v in calls if dec.get(v, ("", ""))[0] == "call" and S4.imm(dec[v][1]) == target]
    jmps = [v for v in rel if v not in calls]
    return calls, jmps, ab, conf


def kept_calls(fname, name):
    """{site: enclosing} from a kept `CALL <name> <target> <site> call in <enclosing>` listing."""
    out = {}
    for ln in open(os.path.join(ALOGS, fname)):
        f = ln.split()
        if f and f[0] == "CALL" and f[1] == name and len(f) in (6, 7):
            out[int(f[-4], 16)] = int(f[-1], 16)
    return out


def ghidra_xref_sites(fname):
    out = set()
    for ln in open(os.path.join(ALOGS, fname)):
        f = ln.split()
        if len(f) >= 3 and f[0] == "to" and "CALL" in f[2]:
            out.add(int(f[1], 16))
    return out


def xref_check(rp, target, name, kept_file, want_n):
    calls, jmps, ab, conf = sites(target)
    kept = kept_calls(kept_file, name)
    rp.add("%s_raw_calls" % name, len(calls))
    rp.add("%s_r2_confirmed" % name, len(conf))
    rp.add("%s_raw_jmps" % name, len(jmps))
    rp.add("%s_abs32" % name, len(ab))
    if sorted(conf) != sorted(kept):
        rp.bad(("%s sites differ from %s" % (name, kept_file), sorted(set(conf) ^ set(kept))))
    if len(conf) != want_n or len(calls) != want_n:
        rp.bad(("%s count" % name, len(calls), len(conf), want_n))
    if jmps or ab:
        rp.note("%s other refs: jmp %s abs %s" % (name, [hex(v) for v in jmps], [hex(v) for v in ab]))
    rows = []
    for v in sorted(conf):
        o = S4.owner(v)
        pe = S4.pad_entry(v)
        rows.append("0x%08X in %s (pad entry 0x%08X)" % (v, o[1], pe or 0))
    rp.note("%s %d sites: %s" % (name, len(conf), "; ".join(rows)))
    return sorted(conf)


# ================================================================================================================ checks
def chk_advance():
    """timing 14 (A2): UNIT_AnimAdvance's 11 call sites (7 monster mode functions, 4 client in 0x00463390 and
    0x004B1280), UNIT_AnimAdvanceLoop's 5 (client); the player move frame reaches no advance; the player move modes'
    frame function is PlrModeMoveFrame; monster NU, S3, S4, DD records queue nothing (schedule 0)."""
    rp = Rep("advance-callers", "timing 14")
    adv = xref_check(rp, 0x00623E00, "UNIT_AnimAdvance", "p50a-anim-scan.txt", 11)
    loop = xref_check(rp, 0x00621310, "UNIT_AnimAdvanceLoop", "p50a-anim-scan.txt", 5)
    mon = [v for v in adv if 0x005A6000 <= S4.owner(v)[0] < 0x005A9000]
    cli = [v for v in adv if v < 0x00520000]
    rp.add("adv_monster_mode_fns", len(mon))
    rp.add("adv_client_low", len(cli))
    rp.add("loop_client_low", len([v for v in loop if v < 0x00520000]))
    rp.note("client sites' entries: re/symbols.csv %s, int3 padding %s" % (sorted({hex(S4.owner(v)[0]) for v in cli}),
                                                                         sorted({hex(S4.pad_entry(v)) for v in cli})))
    if len(mon) != 7 or len(cli) != 4:
        rp.bad(("adv split", [hex(v) for v in mon], [hex(v) for v in cli]))
    # the player mode frame table (0x00732C10): modes 2, 3, 6, 19 -> PlrModeMoveFrame
    pm = r2_pxw(0x00732C10, 20)
    mv = [pm[k] for k in (2, 3, 6, 19)]
    rp.note("player frame table 0x00732C10 (r2 pxw): %s" % " ".join("%d:%08X" % (k, v) for k, v in enumerate(pm)))
    if set(mv) != {0x00580C20}:
        rp.bad(("move frame", [hex(v) for v in mv]))
    # PlrModeMoveFrame's direct-call closure (objdump walker; stops: the fatal and allocator entries) reaches no advance
    G = S.graph([0x00580C20], stop=STOP_MACHINE)
    hit = [hex(e) for e in G if e in (0x00623E00, 0x00621310)]
    rp.add("movefr_closure_fns", len(G))
    if hit:
        rp.bad(("move frame reaches the advance", hit))
    # g_MonModeRecords schedule words for NU 1, S3 10, S4 11, DD 12
    rec = r2_pxw(0x006E2260, 21 * 4)
    sch = {k: rec[4 * k + 3] for k in (1, 10, 11, 12)}
    rp.note("schedule words NU/S3/S4/DD: %s" % sch)
    if any(sch.values()):
        rp.bad(("schedule", sch))
    rp.done()


STOP_MACHINE = {0x00408090, 0x00408A60, 0x0040B430, 0x0040B480, 0x0040B4B0, 0x005544B0, 0x00681E09}


def ghidra_fns(path):
    fns = {}
    for ln in open(path, errors="replace"):
        if ln.startswith("fn "):
            f = ln.split()
            fns[int(f[1], 16)] = (" rng" in ln, f[2])
    return fns


def ghidra_roots(path):
    return [int(ln.split()[1], 16) for ln in open(path, errors="replace") if ln.startswith("fn ") and " depth=0 " in ln]


def ghidra_stops(path):
    names = set()
    for ln in open(path, errors="replace"):
        f = ln.split()
        if len(f) >= 4 and f[0] == "stop" and f[2] == "->":
            names.add(f[3])
    out = set()
    syms = {n: a for a, n in S4.funcs()}
    for n in names:
        if n.startswith("FUN_"):
            out.add(int(n[4:], 16))
        elif n in syms:
            out.add(syms[n])
        else:
            m = re.search(r"_([0-9A-Fa-f]{8})_", n)
            out.add(int(m.group(1), 16) if m else -1)
    return out


LCG = None


def lcg_sites():
    global LCG
    if LCG is None:
        LCG = S4.r2_lcg_sites()[1]
    return LCG


def closure(rp, label, roots, stops, ghidra=None):
    """The objdump walker's closure under roots, its draw functions, r2's LCG sites in the walked bodies; with a Ghidra
    RngCallGraph file, its function list walked again by objdump (every body searched for draws)."""
    A = S.asm()
    G = S.graph(roots, stop=stops)
    R = S.rng_functions(G)
    vas = set()
    for e, v in G.items():
        vas |= v[2]
    r2in = sorted(s for s in lcg_sites() if s in vas)
    icalls = sum(len(v[4]) for v in G.values())
    draws = {e: ([hex(x) for x in v[0]], [(hex(s), n) for s, n in v[1]]) for e, v in R.items()}
    rp.note("%s objdump: roots=%d functions=%d indirect_sites=%d draw_functions=%d %s r2_lcg_in_bodies=%s" % (
        label, len(roots), len(G), icalls, len(R), sorted((hex(e), d) for e, d in draws.items()), [hex(x) for x in r2in]))
    gdraw = None
    if ghidra:
        gf = ghidra_fns(ghidra)
        gdraw, unw = [], 0
        for e in sorted(gf):
            if e < 0x00401000:
                continue
            if A.at(e) is None:
                unw += 1
                continue
            v2, _, _ = S.body(A, e)
            lc, rc_ = S.rng_sites(A, v2)
            if lc or rc_ or any(x in v2 for x in lcg_sites()):
                gdraw.append(e)
        gr = sorted(e for e, (r, _) in gf.items() if r)
        rp.note("%s ghidra list: functions=%d rng-tagged=%s; objdump bodies with a draw=%s unwalked=%d; ghidra-only=%d "
                "objdump-only=%d" % (label, len(gf), [hex(x) for x in gr], [hex(x) for x in gdraw], unw,
                                     len(set(gf) - set(G)), len(set(G) - set(gf))))
        rp.add("%s_ghidra_fns" % label, len(gf))
        if sorted(gdraw) != gr:
            rp.bad(("%s ghidra rng tags differ from the objdump bodies" % label, [hex(x) for x in gdraw], [hex(x) for x in gr]))
    rp.add("%s_fns" % label, len(G))
    rp.add("%s_draw_fns" % label, len(R))
    return G, R, r2in, gdraw


def chk_machine_draws():
    """timing 15 (A3: the advance and the rate draw nothing), timing 121 (N1: one RNG call in the machine, the object
    start draw), README 7 (B1: no seed of the animation's own)."""
    rp = Rep("machine-draws", "timing 15, 121; README 7")
    path = os.path.join(ALOGS, "p50a-rng-machine.txt")
    roots, stops = ghidra_roots(path), ghidra_stops(path)
    rp.note("roots (%d, from the Ghidra file) %s; stops %s" % (len(roots), [hex(r) for r in roots],
                                                               sorted(hex(s) for s in stops)))
    if len(roots) != 29 or stops != STOP_MACHINE:
        rp.bad(("roots/stops", len(roots), sorted(hex(s) for s in stops)))
    G, R, r2in, gdraw = closure(rp, "machine", roots, stops, ghidra=path)
    if set(R) != {0x00624390} or R[0x00624390][1] != [(0x00624563, "RNG_RangeB")] or R[0x00624390][0]:
        rp.bad(("machine draws", {hex(e): v for e, v in R.items()}))
    if r2in:
        rp.bad(("r2 lcg in machine", [hex(x) for x in r2in]))
    # the advance, the rate and the schedule alone (A3)
    for r, nm in ((0x00623E00, "advance"), (0x00623F50, "rate"), (0x005539B0, "schedule")):
        G1, R1, r2in1, _ = closure(rp, nm, [r], stops)
        if R1 or r2in1:
            rp.bad(("%s draws" % nm, {hex(e): v for e, v in R1.items()}, r2in1))
    rp.done()


def chk_mode_draws():
    """README 5 (frame event: PlrModeSkillFrame draws nothing of the animation's own), README 6 (mode end: the draws
    are the next start's, PlayerModeAllowed's, the AI's): the closures under the stops of p50a-rng-modes.txt (the
    skill, combat, path, AI and mode-command entries)."""
    rp = Rep("mode-draws", "README 5, 6")
    path = os.path.join(ALOGS, "p50a-rng-modes.txt")
    stops = ghidra_stops(path)
    gf = ghidra_fns(path)
    rp.note("stops (%d) %s" % (len(stops), sorted(hex(s) for s in stops)))
    if -1 in stops or len(stops) != 19:
        rp.bad(("stops", len(stops)))
    G, R, r2in, _ = closure(rp, "skillframe", [0x00580460], stops)
    if R or r2in:
        rp.bad(("PlrModeSkillFrame draws", {hex(e): v for e, v in R.items()}, r2in))
    G, R, r2in, _ = closure(rp, "modeend", [0x00581020], stops)
    A = S.asm()
    vas, calls, icalls = S.body(A, 0x00581020)
    lc, rc_ = S.rng_sites(A, vas)
    rp.note("PlayerModeEnd body: draws %s %s; indirect %s; direct callees with a draw below them: %s" % (
        lc, rc_, [hex(v) for v in icalls], sorted({(hex(t), S4.owner(t)[1], len(S.rng_functions(S.graph([t], stop=stops))))
                                                    for _, t in calls if t not in stops})))
    if lc or rc_:
        rp.bad(("PlayerModeEnd draws in its body",))
    for e, nm in ((0x005A8030, "MonModeEndGeneric"), (0x005A7BE0, "MonModeEndEvent")):
        G, R, r2in, _ = closure(rp, nm, [e], stops)
        rp.note("%s draw functions: %s" % (nm, [(hex(x), S4.owner(x)[1]) for x in sorted(R)]))
        rp.add("%s_draws" % nm, len(R))
    rp.done()


def chk_objinit():
    """timing 27 (C2): UNIT_AnimInit's type-2 case (jump table 0x0062467C) calls neither UNIT_AnimSetRate nor
    UNIT_AnimSetRecord; the Objects loader shifts the eight FrameCnt dwords left by 8 (0x00640E33-0x00640E64)."""
    rp = Rep("object-init", "timing 27")
    tab = r2_pxw(0x0062467C, 5)
    rp.note("UNIT_AnimInit type cases (r2 pxw 0x0062467C): %s" % [hex(t) for t in tab])
    e = tab[2]
    nxt = min(t for t in tab if t > e)
    lst = S4.r2_range(e, nxt)
    r2c = sorted({t for _, t in calls_of(lst)})
    jm = [(va, ops) for va, mn, ops in lst if mn.startswith("j")]
    objd = [(va, mn, ops) for va, (mn, ops) in S.asm().range(e, nxt)]
    oc = sorted({S.branch_target(ops) for va, mn, ops in objd if mn == "call"})
    fat = calls_of(S4.r2_range(0x006243A5, 0x006243BF))
    rp.note("type 2 case [0x%08X, 0x%08X): r2 callees %s, objdump callees %s; jumps %s; the jump target 0x006243A5's "
            "calls %s" % (e, nxt, [hex(t) for t in r2c], [hex(t) for t in oc], ["0x%08X %s" % j for j in jm],
                          [hex(t) for _, t in fat]))
    if e != 0x00624504 or r2c != oc or {0x00623F50, 0x00620E80} & set(r2c) or any(mn == "call" and S4.imm(ops) is None
                                                                                for _, mn, ops in lst):
        rp.bad(("object case", hex(e), r2c, oc))
    if r2c != [0x0045C3E0, 0x00640E90] or [t for _, t in fat] != [0x00408090, 0x00408A60, 0x00681E09]:
        rp.bad(("object case callees", r2c))
    sh = S4.r2_range(0x00640E33, 0x00640E6B)
    offs = [S4.imm(ops.split("+")[1].split("]")[0]) for va, mn, ops in sh if mn == "shl" and ops.endswith(", 8")]
    rp.note("loader 0x00640E33..0x00640E6B: %s" % ["%s %s" % (mn, ops) for va, mn, ops in sh])
    if offs != list(range(0xD8, 0xF8, 4)):
        rp.bad(("shift", offs))
    rp.add("shl8", len(offs))
    rp.done()


def chk_rate_readers():
    """timing 28 (C2): no server advance for an object, a missile or an item (the advance's server callers are the
    monster mode functions, timing 14); the missile and item cases of UNIT_AnimInit set +0x4C to constants."""
    rp = Rep("rate-readback", "timing 28")
    tab = r2_pxw(0x0062467C, 5)
    for k, nm in ((3, "missile"), (4, "item")):
        lst = r2_fn(tab[k], 0x60)
        st = ["%s %s" % (mn, ops) for va, mn, ops in lst if "0x4c]" in ops]
        rp.note("%s case 0x%08X: +0x4C stores %s; calls %s" % (nm, tab[k], st, [hex(t) for _, t in calls_of(lst)]))
    rp.done()


def chk_startframes():
    """timing 31 (D1): g_AttackStartFrames 0x006E8E60, 14 weapon classes x 7 character classes: the non-zero cells
    are the Amazon's and the Sorceress's only, 1 for hand to hand, 2 for 1hs, 1ht, stf, 2hs, 2ht; bow, xbw, ht1 0."""
    rp = Rep("start-frames", "timing 31")
    t = r2_pxw(0x006E8E60, 14 * 7)
    raw = S.dwords(0x006E8E60, 14 * 7)
    if t != raw:
        rp.bad(("r2 and raw differ",))
    nz = [(w, c, t[w * 7 + c]) for w in range(14) for c in range(7) if t[w * 7 + c]]
    rp.note("non-zero cells (wclass, class, value): %s" % nz)
    want = [(w, c, 1 if w == 0 else 2) for w in (0, 2, 3, 4, 5, 6) for c in (0, 1)]
    want.sort()
    if sorted(nz) != want:
        rp.bad(("cells", nz))
    rp.add("cells", len(t))
    rp.add("nonzero", len(nz))
    rp.done()


def chk_noevent():
    """timing 37 (E2): no player record with a frame event reaches the no-event case r >= 256 (F - S) at a factor
    <= 175 (r = speed x 175 / 100), S the record's start frame (D1's cells: 1 or 2 for A1 and A2 of the Amazon and the
    Sorceress, else 0)."""
    import anim_survey as AS
    rp = Rep("no-event", "timing 37")
    d = AS.Data(DATA)
    ptok = [p.upper() for _, p in d.ptokens]
    st = S.dwords(0x006E8E60, 14 * 7)
    worst = None
    for r in d.recs:
        if r.name[:2] not in ptok or not any(r.events[:r.frames]):
            continue
        cls = ptok.index(r.name[:2])
        smax = 0
        if r.name[2:4] in ("A1", "A2"):
            smax = max(st[w * 7 + cls] for w in range(14)) if cls < 7 else 0
        rmax = r.speed * 175 // 100
        rp.add("records")
        margin = 256 * (r.frames - smax) - rmax
        if worst is None or margin < worst[0]:
            worst = (margin, r.name, r.frames, r.speed, smax, rmax)
        if rmax >= 256 * (r.frames - smax):
            rp.bad(("reaches", r.name, r.frames, r.speed, smax))
    rp.note("player tokens %s; the smallest margin 256(F-S) - r_max: %s" % (ptok, worst))
    rp.done()


def chk_seq():
    """timing 47 (G1): the player sequence tables 0x007483B8 (24 pointers, 14 columns of 12-byte entries): 207 non-empty
    entries, each with length = frames (r2 against the kept pseq scan); Skills rows with a charclass and a seqnum stay
    below 24; MONSEQ_Load's stores of the row count."""
    import anim_survey as AS
    rp = Rep("sequences", "timing 47")
    ptr = r2_pxw(0x007483B8, 24)
    ne = 0
    eq = 0
    for s, p in enumerate(ptr):
        if not p:
            continue
        ent = r2_pxw(p, 14 * 3)
        for c in range(14):
            f, ln, fr = ent[3 * c:3 * c + 3]
            if f:
                ne += 1
                eq += int(ln == fr)
    kept = sum(1 for ln in open(os.path.join(ALOGS, "p50a-anim-scan.txt")) if ln.startswith("PSEQ "))
    rp.add("nonempty", ne)
    rp.add("len_eq_frames", eq)
    rp.add("kept_pseq_lines", kept)
    if ne != 207 or eq != ne or kept != ne:
        rp.bad(("entries", ne, eq, kept))
    d = AS.Data(DATA)
    sk = d.t["skills"]
    rows = [(i, r) for i, r in enumerate(sk.txt) if (r.get("charclass") or "").strip() and (r.get("seqnum") or "").strip()]
    mx = max(int(r["seqnum"]) for _, r in rows)
    rp.add("skills_charclass_seqnum", len(rows))
    rp.add("seqnum_max", mx)
    if len(rows) != 25 or mx >= 24:
        rp.bad(("skills", len(rows), mx))
    inc = S4.r2_range(0x00659DB6, 0x00659DC9)
    rp.note("MONSEQ_Load per row (r2): %s" % ["0x%08X %s %s" % x for x in inc])
    sh = [(mn, ops) for _, mn, ops in inc]
    if sh != [("mov", "edx, 1"), ("add", "dword [eax + ecx + 4], edx"), ("mov", "ecx, dword [0x96c7b4]"),
              ("add", "dword [eax + ecx + 8], edx")]:
        rp.bad(("MONSEQ_Load increments", sh))
    rp.done()


def chk_x4e():
    """timing 48 (G3): the byte stores to [reg + 0x4E] in dos 87 (0x005CB48E), 89 and 103."""
    rp = Rep("event-byte-stores", "timing 48")
    for e, nm in ((0x005CB3C0, "do87"), (0x005CB940, "do89"), (0x005CD380, "do103"), (0x00623E00, "advance")):
        lst = r2_fn(e, 0x800)
        st = ["0x%08X %s" % (va, ops) for va, mn, ops in lst if mn == "mov" and ops.startswith("byte [") and "+ 0x4e]" in ops]
        rp.note("%s 0x%08X: %s" % (nm, e, st))
        rp.add("%s_stores" % nm, len(st))
        if nm != "advance" and not st:
            rp.bad(("no store", nm))
    if not any(x.startswith("0x005CB48E") for x in [n for n in rp.notes if "do87" in n][0].split(": ")[1:]):
        pass
    if "0x005CB48E" not in [n for n in rp.notes if n.startswith("do87")][0]:
        rp.bad(("do 87 store address",))
    rp.done()


def chk_seqpos():
    """timing 50 (G5): writer PlrModeSkillFrame -> UnitSetSeqPos(unit, b) (0x00580482-0x00580488; UnitSetSeqPos keeps
    the low byte and adds b << 8); readers: SKILLS_SrvDo's `test [unit + 0x38], 0xFFFFFF00` (0x0056FAB4) and do 35's
    `(+0x38 >> 8)` parity (0x005D3659)."""
    rp = Rep("seq-pos-pair", "timing 50")
    w = S4.r2_range(0x00580475, 0x0058048D)
    rp.note("PlrModeSkillFrame: %s" % ["0x%08X %s %s" % x for x in w])
    shape = [(mn, ops) for _, mn, ops in w]
    if ("mov", "eax, dword [ebp + 0xc]") not in shape or ("call", "0x6212c0") not in shape or ("lea", "eax, [edi + 2]") not in shape:
        rp.bad(("writer shape",))
    u = r2_fn(0x006212C0, 0x60)
    us = [(mn, ops) for _, mn, ops in u]
    rp.note("UnitSetSeqPos: %s" % ["%s %s" % x for x in us[-8:]])
    for need in (("and", "ecx, 0xff"), ("shl", "edx, 8"), ("mov", "dword [eax + 0x38], ecx")):
        if need not in us:
            rp.bad(("UnitSetSeqPos", need))
    g = S4.r2_range(0x0056FAB4, 0x0056FABD)
    p = S4.r2_range(0x005D3659, 0x005D366C)
    rp.note("SrvDo gate: %s; do 35: %s" % (["%s %s" % x[1:] for x in g], ["%s %s" % x[1:] for x in p]))
    if not g or g[0][1:] != ("test", "dword [edi + 0x38], 0xffffff00"):
        rp.bad(("gate",))
    pb = S4.r2_bytes(0x0058365F + 0x50000, 6) if False else S4.r2_bytes(0x005D365F, 6)
    rp.note("bytes at 0x005D365F (the and): %s" % pb.hex())
    if [x[1:] for x in p[:2]] != [("mov", "edx, dword [esi + 0x38]"), ("sar", "edx, 8")] or pb != bytes.fromhex("81e201000080"):
        rp.bad(("parity",))
    rp.add("owner_gate_" + S4.owner(0x0056FAB4)[1])
    rp.add("owner_parity_" + S4.owner(0x005D3659)[1])
    rp.done()


def chk_nullrec():
    """timing 55 (H3): MonModeFrameEvent and MonModeEndEvent call 0x005A7B30 when MonModeRecord returns 0 or the slot
    is 0; 0x005A7B30 (ESI unit, EDI mode, one stack argument) clears the used skill and, unless the unit is dead in a
    mode other than 0 and 12, calls MonModeStartNeutral. Also MonSetMode's call at 0x005A7DFD."""
    rp = Rep("null-record", "timing 55")
    for e, slot in ((0x005A7BA0, 4), (0x005A7BE0, 8)):
        lst = r2_fn(e, 0x40)
        sh = [(mn, ops) for _, mn, ops in lst]
        ok = ("call", "0x5a78a0") in sh and ("call", "0x5a7b30") in sh and ("mov", "eax, dword [eax + %d]" % slot) in sh
        rp.note("0x%08X: %s" % (e, ["%s %s" % x for x in sh]))
        rp.add("handlers_ok", int(ok))
        if not ok:
            rp.bad(("handler", hex(e)))
    b = [(mn, ops) for _, mn, ops in r2_fn(0x005A7B30, 0x80)]
    rp.note("0x005A7B30: %s" % ["%s %s" % x for x in b])
    need = [("push", "0"), ("push", "esi"), ("call", "0x620210"), ("test", "edi, edi"), ("cmp", "edi, 0xc"),
            ("call", "0x5541b0"), ("call", "0x5a73e0")]
    if [x for x in b if x in need] != need:
        rp.bad(("0x005A7B30 shape",))
    m = S4.r2_range(0x005A7DF0, 0x005A7E05)
    rp.note("MonSetMode near 0x005A7DFD: %s" % ["0x%08X %s %s" % x for x in m])
    if not any(mn == "call" and "0x5a7b30" in ops for _, mn, ops in m):
        rp.bad(("MonSetMode call",))
    rp.done()


MMODE_WANT = {
    # row: (start, frame, end, schedule) as in p50a-anim-scan.txt MMODE
    0: (0x005A6FF0, 0x005A7350, 0x005A72B0, 1), 1: (0x005A73E0, 0x005A6DE0, 0, 0), 2: (0x005A7520, 0x005A8490, 0, 1),
    3: (0x005A7580, 0x005A6DE0, 0x005A8030, 1), 4: (0x005A75C0, 0x005A7670, 0x005A8030, 1),
    6: (0x005A77C0, 0x005A6DE0, 0x005A8030, 1), 10: (0x005A7490, 0x005A74A0, 0x005A74D0, 0),
    11: (0x005A74E0, 0x005A6DE0, 0, 0), 12: (0x005A7390, 0x005A6DE0, 0, 0), 13: (0x005A77D0, 0x005A8630, 0x005A8520, 1),
    14: (0x005A7870, 0x005A8670, 0x005A8030, 1), 15: (0x005A7550, 0x005A84F0, 0, 1),
}
for _k in (5, 7, 8, 9):
    MMODE_WANT[_k] = MMODE_WANT[4]


def seq_calls(e, maxlen=0x200):
    """[(callee, pushed immediates since the previous call)] in r2's linear listing of the function at e."""
    out, push = [], []
    for va, mn, ops in r2_fn(e, maxlen):
        if mn == "push" and S4.imm(ops) is not None:
            push.append(S4.imm(ops))
        elif mn == "mov" and ops.startswith("edx, ") and S4.imm(ops[5:]) is not None:
            push.append(("edx", S4.imm(ops[5:])))
        elif mn == "call":
            out.append((S4.imm(ops), tuple(push)))
            push = []
    return out


def chk_monrecords():
    """timing 64-72 (I2's table): g_MonModeRecords 0x006E2260, 21 x 16 bytes, r2 against the raw bytes and the kept
    MMODE lines; each named frame and end function's call sequence (r2)."""
    rp = Rep("mon-mode-records", "timing 64-72")
    rec = r2_pxw(0x006E2260, 21 * 4)
    if rec != S.dwords(0x006E2260, 21 * 4):
        rp.bad(("r2 and raw differ",))
    kept = {}
    for ln in open(os.path.join(ALOGS, "p50a-anim-scan.txt")):
        f = ln.split()
        if f and f[0] == "MMODE":
            kept[int(f[1])] = (int(f[2], 16), int(f[3], 16), int(f[4], 16), int(f[5]))
    for k in range(21):
        got = tuple(rec[4 * k:4 * k + 4])
        if got != kept.get(k):
            rp.bad(("row vs kept", k, [hex(x) for x in got]))
        if k in MMODE_WANT and got != MMODE_WANT[k]:
            rp.bad(("row vs table", k, [hex(x) for x in got]))
        rp.add("rows")
    rp.note("rows 0-15 (start frame end schedule): %s" % "; ".join(
        "%d %s" % (k, " ".join("%08X" % x for x in rec[4 * k:4 * k + 4])) for k in range(16)))
    fns = {
        "DT frame 0x005A7350": (0x005A7350, [0x0063E8D0, 0x00554CA0, 0x00623E00, 0x006217C0, 0x00553570]),
        "DT end 0x005A72B0": (0x005A72B0, [0x00553570, 0x005C0C30]),
        "NU/GH/BL/S4/DD frame 0x005A6DE0": (0x005A6DE0, [0x00540E60]),
        "WL frame 0x005A8490": (0x005A8490, [0x00639DF0, 0x005C9D90, 0x00639DF0, 0x005CE4F0, 0x00554CA0, 0x005A8030]),
        "RN frame 0x005A84F0": (0x005A84F0, [0x00554CA0, 0x005A8030]),
        "S3 frame 0x005A74A0": (0x005A74A0, [0x00554CA0, 0x00623E00, 0x006217C0, 0x00553570]),
        "S3 end 0x005A74D0": (0x005A74D0, []),
        "KB frame 0x005A8630": (0x005A8630, [0x00554CA0, 0x00623E00, 0x006217C0, 0x005A8520]),
    }
    for nm, (e, want) in fns.items():
        sc = seq_calls(e, 0x100)
        got = [t for t, _ in sc]
        rp.note("%s: %s" % (nm, ["%s%s" % (hex(t), " push %s" % (p,) if p else "") for t, p in sc]))
        if got[:len(want)] != want:
            rp.bad(("calls", nm, [hex(t) for t in got]))
        rp.add("fns_checked")
    # the mode argument of the SUNIT_SetMode calls: DT frame and end 12, S3 frame 11
    for e, mode in ((0x005A7350, 12), (0x005A72B0, 12), (0x005A74A0, 11)):
        ps = [p for t, p in seq_calls(e, 0x100) if t == 0x00553570]
        if not ps or ps[0][-1:] != (mode,):
            rp.bad(("SetMode arg", hex(e), ps))
    rp.contra("the frame slot of GH (3), BL (6), S4 (11) and DD (12) is 0x005A6DE0 = UNIT_CancelEvents(0, 0), the "
              "same as NU's, where the table prints '—' (GH, BL, DD) or merges it into S3's row (S4)")
    rp.done()


def chk_overrides():
    """timing 74 (I2 class overrides): MonModeRecord's switch over the class (0x005A7923-0x005A7990, r2) against the
    MonStats rows with SplGetModeChart set."""
    import anim_survey as AS
    rp = Rep("mode-chart-overrides", "timing 74")
    lst = r2_fn(0x005A78A0, 0x200)
    cmps = [S4.imm(ops.split(",")[1]) for va, mn, ops in lst if mn == "cmp" and "," in ops and
            0x005A7900 <= va < 0x005A79A0 and S4.imm(ops.split(",")[1]) is not None]
    subs = [(va, mn, ops) for va, mn, ops in lst if 0x005A7900 <= va < 0x005A79A0]
    rp.note("MonModeRecord 0x005A7900..0x005A79A0 (r2): %s" % ["0x%08X %s %s" % x for x in subs])
    head = S4.r2_range(0x005A78A0, 0x005A7904)
    rp.note("MonModeRecord head (r2): %s" % ["0x%08X %s %s" % x for x in head])
    # the class switch: [esi - 0xF3] over 0..0xAF by bytes at 0x005A79C4 into dwords at 0x005A79B4, [esi - 0x220] over
    # 0..0xA5 by bytes at 0x005A7A80 into 0x005A7A74, and the direct `je` at 0x005A7904 (taken for the compared class)
    cases = collections.defaultdict(list)
    for base, n, btab, dtab in ((0xF3, 0xAF, 0x005A79C4, 0x005A79B4), (0x220, 0xA5, 0x005A7A80, 0x005A7A74)):
        bt = S4.r2_bytes(btab, n + 1)
        for k in range(n + 1):
            t = r2_pxw(dtab + 4 * bt[k], 1)[0]
            if t != 0x005A799E:
                cases[t].append(base + k)
    cmpcls = [S4.imm(ops.split(",")[1]) for va, mn, ops in head if mn == "cmp" and ops.startswith("esi,")]
    if cmpcls:
        cases[0x005A7991].append(cmpcls[-1])
    rows = {}
    for t, cl in sorted(cases.items()):
        modes = []
        for va, mn, ops in S4.r2_range(t, t + 0x30):
            if mn == "mov" and ops.startswith("eax, 0x6e2"):
                modes.append((S4.imm(ops.split(",")[1]) - 0x006E2260) // 16)
            if mn == "ret":
                if len(modes) >= 2 or t in (0x005A794E, 0x005A7991):
                    break
        rows[t] = (sorted(cl), modes)
    rp.note("switch cases (target: classes, record rows): %s" % {hex(t): v for t, v in rows.items()})
    d = AS.Data(DATA)
    ms = d.t["monstats"]
    chart = [i for i, r in enumerate(ms.rec) if r.get("SplGetModeChart")]
    sw = sorted(c for cl, _ in rows.values() for c in cl)
    rp.note("MonStats rows with SplGetModeChart: %s; switch classes %s; set without a case %s" % (
        chart, sw, sorted(set(chart) - set(sw))))
    rp.add("chart_rows", len(chart))
    rp.add("switch_classes", len(sw))
    want = {(243, 333, 705): [16, 17], (403,): [18, 19], (417, 418): [20], (543, 544, 570, 709): [7]}
    got = {tuple(cl): sorted(set(m)) for cl, m in rows.values()}
    if got != {k: v for k, v in want.items()} or not set(sw) <= set(chart):
        rp.bad(("overrides", got))
    rp.done()
    return subs


def chk_ratemin():
    """timing 86 (J1): every property block naming a code that writes 93, 96, 99, 102 or 105 has min and max >= 3
    (tools/anim_survey.py ratemin, the table doc's full-table check, re-run here)."""
    import anim_survey as AS
    rp = Rep("rate-stat-minima", "timing 86")
    d = AS.Data(DATA)
    out, kv = AS.sec_ratemin(d)
    for k in ("rate_src_blocks", "rate_src_other_cells", "rate_src_negative", "rate_src_nonint", "rate_src_lowest",
              "rate_src_reach_wrap"):
        rp.add(k, kv[k])
    if kv["rate_src_blocks"] != 353 or kv["rate_src_negative"] or kv["rate_src_lowest"] < 3 or kv["rate_src_other_cells"]:
        rp.bad(("minima", dict(kv)))
    rp.done()


def chk_setrate_sites():
    """timing 93 (J6): UNIT_AnimSetRate's 31 call sites (raw bytes + r2) against objdump's (p50b-calls.txt) and Ghidra's
    (p50b-setrate-xrefs.txt); ITEMS_DetachFromOwner not a caller; the UpdateAnimRate mask byte 0x006CE26C's
    references."""
    rp = Rep("setrate-sites", "timing 93")
    conf = xref_check(rp, 0x00623F50, "UNIT_AnimSetRate", "p50a-anim-scan.txt", 31)
    gx = ghidra_xref_sites("p50b-setrate-xrefs.txt")
    rp.add("ghidra_call_sites", len(gx))
    if gx != set(conf):
        rp.bad(("ghidra differs", sorted(hex(v) for v in gx ^ set(conf))))
    low = [v for v in conf if v < 0x00520000]
    rp.add("sites_below_0x520000", len(low))
    if len(low) != 7:
        rp.bad(("client split", [hex(v) for v in low]))
    if any(0x0055C730 <= S4.owner(v)[0] <= 0x0055C730 for v in conf):
        rp.bad(("Detach calls the rate",))
    rp.done()


def chk_setrate_callees():
    """timing 94 (J7): UNIT_AnimSetRate's direct callees (r2 over 0x00623F50-0x00624390) against p50b-setrate-callees:
    neither UnitQueueEvent nor UNIT_CancelEvents nor the schedulers, directly or below."""
    rp = Rep("setrate-callees", "timing 94")
    lst = S4.r2_range(0x00623F50, 0x00624390)
    cs = collections.Counter(t for _, t in calls_of(lst))
    kept = {}
    for ln in open(os.path.join(ALOGS, "p50b-setrate-callees.txt")):
        f = ln.split()
        if len(f) == 3:
            kept[int(f[2], 16)] = int(f[0])
    rp.add("r2_distinct_callees", len(cs))
    rp.add("kept_distinct_callees", len(kept))
    if dict(cs) != kept:
        rp.bad(("callees differ", {hex(k): v for k, v in (collections.Counter(cs) - collections.Counter(kept)).items()},
                {hex(k): v for k, v in (collections.Counter(kept) - collections.Counter(cs)).items()}))
    bad_t = {0x005417D0, 0x00541800, 0x00540E60, 0x00540EA0, 0x00553990, 0x005539B0, 0x00553B10, 0x00553C70, 0x00553DC0,
             0x005416B0, 0x005415E0, 0x00541650}
    if set(cs) & bad_t:
        rp.bad(("queue/cancel callee", [hex(x) for x in set(cs) & bad_t]))
    G = S.graph([0x00623F50], stop=STOP_MACHINE)
    reach = sorted(hex(e) for e in G if e in bad_t)
    rp.add("closure_fns", len(G))
    rp.note("callees %s; closure reaches queue/cancel: %s" % (sorted(hex(x) for x in cs), reach))
    if reach:
        rp.bad(("closure reaches", reach))
    rp.done()


def chk_frame_return():
    """timing 131: MonModeFrameEvent's `call eax` result is not tested (it is returned); MonEventDispatch returns it
    untested; the runners' use of the dispatch return."""
    rp = Rep("frame-return", "timing 131")
    f = S4.r2_range(0x005A7BD6, 0x005A7BDE)
    rp.note("MonModeFrameEvent after the call: %s" % ["%s %s" % x[1:] for x in f])
    if [x[1] for x in f] != ["call", "pop", "pop", "pop", "ret"]:
        rp.bad(("frame event tail",))
    dsp = S4.r2_range(0x005A7FD6, 0x005A7FDF)
    rp.note("MonEventDispatch after the call: %s" % ["%s %s" % x[1:] for x in dsp])
    if [x[1] for x in dsp] != ["call", "pop", "pop", "pop", "pop", "ret"]:
        rp.bad(("dispatch tail",))
    calls, jmps, ab, conf = sites(0x005A7F80)
    dec = r2_at(ab)
    rp.note("MonEventDispatch refs: calls %s jmps %s abs %s" % ([hex(v) for v in conf], [hex(v) for v in jmps],
                                                               ["0x%08X %s %s" % (v, *dec.get(v, ("?", "?"))) for v in ab]))
    for v in conf:
        nx = r2_at([v])
        seq = S4.r2(";".join(["pd 4 @ 0x%x" % v]))
        rp.note("after the call at 0x%08X: %s" % (v, " | ".join(ln.strip() for ln in seq.splitlines()[:4])))
    sh = [(mn, ops) for _, mn, ops in S4.r2_range(0x00541136, 0x0054113A)] + \
        [(mn, ops) for _, mn, ops in S4.r2_range(0x00540CD0, 0x00540CD4)]
    rp.note("the first eax use after each call: 0x00541136 %s; 0x005410CF calls 0x00540CD0, whose first instruction is %s"
            % (sh[0], sh[1]))
    if sh != [("movzx", "eax, word [esi + 2]"), ("movzx", "eax, word [esi + 2]")] or \
            S4.r2_range(0x005410C9, 0x005410CF)[0][1] != "and" or S4.r2_range(0x005410CF, 0x005410D4)[0][2] != "0x540cd0":
        rp.bad(("runner use of the return", sh))
    rp.done()


# ---------------------------------------------------------------------------------------------------------- movement
def chk_baseid():
    """movement 12 (A4): every MonStats BaseId is in range (the guard's out-of-range branch is not reached)."""
    import anim_survey as AS
    rp = Rep("baseid-range", "movement 12")
    d = AS.Data(DATA)
    ms = d.t["monstats"]
    n = len(ms.rec)
    out = [i for i, r in enumerate(ms.rec) if not (0 <= r["BaseId"] < n)]
    rp.add("rows", n)
    rp.add("out_of_range", len(out))
    rp.note("rows out of range: %s" % out)
    lst = S4.r2_range(0x00650F00, 0x00650F40)
    rp.note("MonStatsSpeeds head (r2): %s" % ["0x%08X %s %s" % x for x in lst])
    rp.done()


def chk_pathspeed():
    """movement 16 (A6): PathSetSpeed's call sites (raw + r2 against p50d-calls.txt); PathMoveReset's +0x80 -> +0x7C copy
    under path flag 0x8000 (0x00648DEC-0x00648DFE)."""
    rp = Rep("path-speed-writers", "movement 16")
    conf = xref_check(rp, 0x00648690, "sub_00648690_PathSetSpeed", "p50d-calls.txt", 25)
    srv = [v for v in conf if v >= 0x00520000]
    rp.add("sites_at_or_above_0x520000", len(srv))
    rp.note("server-range owners: %s" % ["0x%08X %s" % (v, S4.owner(v)[1]) for v in srv])
    m = S4.r2_range(0x00648DEC, 0x00648E02)
    sh = [(mn, ops) for _, mn, ops in m]
    rp.note("PathMoveReset: %s" % ["%s %s" % x for x in sh])
    if sh[:2] != [("mov", "edx, dword [eax + 0x34]"), ("test", "edx, 0x8000")] or \
            ("mov", "esi, dword [eax + 0x80]") not in sh or ("mov", "dword [eax + 0x7c], esi") not in sh:
        rp.bad(("PathMoveReset shape",))
    rp.done()


def chk_pathstep():
    """movement 18, 19 (B, B1): PathStep's call sites: one at or above 0x00520000, UnitMoveStep's at 0x00554CD5 with
    `push 0x400` as its k; PathSetAccel's: 0x0059FDCC in MissileCreate and one client site."""
    rp = Rep("path-step-callers", "movement 18, 19")
    conf = xref_check(rp, 0x00650840, "sub_00650840_PathStep", "p50d-calls.txt", 3)
    srv = [v for v in conf if v >= 0x00520000]
    if srv != [0x00554CD5]:
        rp.bad(("server sites", [hex(v) for v in srv]))
    pb = S4.pushes_before(0x00554CD5, entry=0x00554CA0, want=2)
    rp.note("UnitMoveStep's PathStep pushes (arg 0 first): %s" % pb)
    if not pb or pb[-1] != "0x400":
        rp.bad(("k", pb))
    acc = xref_check(rp, 0x00648700, "sub_00648700_PathSetAccel", "p50d-calls.txt", 2)
    srv = [(hex(v), S4.owner(v)[1]) for v in acc if v >= 0x00520000]
    rp.note("PathSetAccel server-range sites: %s" % srv)
    if [v for v in acc if v >= 0x00520000] != [0x0059FDCC] or S4.owner(0x0059FDCC)[0] != 0x0059FA30:
        rp.bad(("accel", srv))
    rp.done()


def chk_dirtable():
    """movement 20 (B2): g_PathDirTable 0x006EB7E0, 128 rows of three dwords (path/0001): every row's vector norm^2
    within [16 767 217, 4096^2]; the table read by r2 (pxw) against the raw bytes; PathDirection's reads of it."""
    rp = Rep("path-dir-table", "movement 20")
    lst = r2_fn(0x0064FC60, 0x200)
    rp.note("PathDirection operands naming 0x006EB7E0..0x006EB7E8: %s" % ["0x%08X %s %s" % x for x in lst
                                                                         if re.search(r"0x6eb7e[0-8]", x[2])])
    t = r2_pxw(0x006EB7E0, 3 * 128)
    if t != S.dwords(0x006EB7E0, 3 * 128):
        rp.bad(("r2 and raw differ",))
    def s32(x):
        return x - (1 << 32) if x & 0x80000000 else x
    norms = [s32(t[3 * k]) ** 2 + s32(t[3 * k + 1]) ** 2 for k in range(128)]
    lo, hi = min(norms), max(norms)
    rp.add("rows", 128)
    rp.add("norm2_min", lo)
    rp.add("norm2_max", hi)
    rp.note("row 0 %s, row 127 %s" % ([s32(x) for x in t[0:3]], [s32(x) for x in t[381:384]]))
    if lo < 16767217 or hi > 4096 * 4096:
        rp.bad(("norm bounds", lo, hi))
    rp.done()


def chk_movestep():
    """movement 25 (C1): UnitMoveStep's 11 call sites and their owners."""
    rp = Rep("movestep-callers", "movement 25")
    conf = xref_check(rp, 0x00554CA0, "sub_00554CA0_UnitMoveStep", "p50d-calls.txt", 11)
    rp.done()


def chk_move_draws():
    """movement 37 (G1): no draw under PathStep, RunStaminaDrain, MonStatsSpeeds, PathSetSpeed, PathStepCollide,
    PathStepSnap and the knockback planner (objdump walker + r2's multiplier search)."""
    rp = Rep("move-draws", "movement 37")
    roots = [0x00650840, 0x0057F240, 0x00650F00, 0x00648690, 0x00650150, 0x00650090]
    syms = {n: a for a, n in S4.funcs()}
    kb = [a for n, a in syms.items() if "PathPlanKnockback" in n]
    roots += kb
    rp.note("roots: %s" % [(hex(r), S4.owner(r)[1]) for r in roots])
    G, R, r2in, _ = closure(rp, "move-stop-planner", roots, STOP_MACHINE | {0x00649970})
    if R or r2in:
        rp.bad(("draws", {hex(e): v for e, v in R.items()}, r2in))
    G, R, r2in, _ = closure(rp, "move-through-planner", roots, STOP_MACHINE)
    for e in R:
        chain = []
        x = e
        while x is not None:
            chain.append(S4.owner(x)[1])
            x = G[x][1]
        rp.note("draw function 0x%08X reached by %s" % (e, " <- ".join(chain)))
        if "sub_00650350_PathReplan" not in chain:
            rp.bad(("draw outside the replan", hex(e)))
    rp.done()


# ------------------------------------------------------------------------------------------------- routed remainders
def call_seq(e, maxlen=0x400, marks=()):
    """[(va, callee or a marked instruction)] in r2's listing of the function at e."""
    out = []
    for va, mn, ops in r2_fn(e, maxlen):
        if mn == "call":
            out.append((va, S4.imm(ops) if S4.imm(ops) is not None else ops))
        elif any(m in "%s %s" % (mn, ops) for m in marks):
            out.append((va, "%s %s" % (mn, ops)))
    return out


def in_order(seq, want):
    """True when the items of want occur in seq in that order."""
    k = 0
    for _, x in seq:
        if k < len(want) and x == want[k]:
            k += 1
    return k == len(want)


def chk_player_tables():
    """timing 4 remainder (the kind-1 dispatch is PlayerModeEnd, g_PlayerEventFuncs[1]) and timing 56 remainder (the
    neutral and town-neutral start is PlrModeStartNeutral): r2 dumps of 0x006E1810 and the start table 0x006E1740, and
    PlayerEventDispatch's indexed call."""
    rp = Rep("player-event-tables", "timing 4, 56 (remainders)")
    pev = r2_pxw(0x006E1810, 15)
    rp.note("g_PlayerEventFuncs (r2): %s" % " ".join("%d:%08X" % (k, v) for k, v in enumerate(pev)))
    if pev[0] != 0x005811D0 or pev[1] != 0x00581020:
        rp.bad(("PEV", hex(pev[0]), hex(pev[1])))
    d = [x for x in r2_fn(0x00581220, 0x100) if "0x6e1810" in x[2]]
    rp.note("PlayerEventDispatch's table reads: %s" % ["0x%08X %s %s" % x for x in d])
    if not d:
        rp.bad(("dispatch does not index 0x006E1810",))
    st = r2_pxw(0x006E1740, 40)
    rp.note("player start table 0x006E1740 (r2; per mode the xy and the unit start): %s" % " ".join(
        "%d:%08X/%08X" % (k, st[2 * k], st[2 * k + 1]) for k in range(20)))
    if st[2] != 0x0057F020 or st[10] != 0x0057F020 or st[3] or st[11] or S.dwords(0x006E1740, 40) != st:
        rp.bad(("start table", hex(st[2]), hex(st[10])))
    rp.done()


def chk_start_order():
    """timing 5, 39, 63, 73 remainders: the call order of MonSetMode (I2) and the player starts (I1, E4), r2."""
    rp = Rep("start-order", "timing 5, 39, 63, 73 (remainders)")
    N = {0x00553570: "SUNIT_SetMode", 0x005533D0: "SUNIT_AnimInit", 0x00620210: "UNIT_SetUsedSkill",
         0x00553990: "SUNIT_CancelModeEvents", 0x005539B0: "SUNIT_ScheduleModeEvents", 0x0056FAF0: "SKILLS_StartUsedSkill",
         0x00553F00: "SUNIT_ModeEveryFrame", 0x005A6B10: "MonModeEveryFrame", 0x005A78A0: "MonModeRecord",
         0x00639DF0: "UNIT_HasState", 0x005A63F0: "MonMovePlan", 0x005A4F50: "MonAttackStats", 0x005A7B30: "0x005A7B30",
         0x005A73E0: "MonModeStartNeutral", 0x00648AD0: "0x00648AD0", 0x00681E09: "fatal"}
    marks = ("0xc4], 0x80000", "0xc4], 0xffffffbf", "0xc], 0", "edi, 3", "eax, 3", "ecx, 3", "ebx, 3")
    for e, nm, want in (
            (0x005A7C20, "MonSetMode", ["UNIT_HasState", "fatal", "MonMovePlan", "MonAttackStats", "MonModeRecord",
                                        "eax", "or dword [esi + 0xc4], 0x80000", "SUNIT_AnimInit",
                                        "SUNIT_CancelModeEvents", "MonModeRecord", "MonModeEveryFrame",
                                        "SUNIT_ModeEveryFrame", "SUNIT_ScheduleModeEvents"]),
            (0x0057FE30, "PlrModeStartGetHit", ["SUNIT_SetMode", "SUNIT_AnimInit", "UNIT_SetUsedSkill",
                                                "SUNIT_CancelModeEvents", "SUNIT_ScheduleModeEvents"]),
            (0x0057FDC0, "PlrModeStartBlock", ["SUNIT_SetMode", "SUNIT_AnimInit", "UNIT_SetUsedSkill",
                                               "SUNIT_CancelModeEvents", "SUNIT_ScheduleModeEvents"]),
            (0x0057FE90, "PlrModeStartSkillXY", ["0x00648AD0", "SUNIT_SetMode", "SUNIT_AnimInit", "SUNIT_CancelModeEvents",
                                                 "SUNIT_ScheduleModeEvents", "and dword [esi + 0xc4], 0xffffffbf",
                                                 "SKILLS_StartUsedSkill"]),
            (0x0057FEF0, "PlrModeStartSkillUnit", ["SUNIT_SetMode", "SUNIT_AnimInit", "SUNIT_CancelModeEvents",
                                                   "SUNIT_ScheduleModeEvents", "and dword [esi + 0xc4], 0xffffffbf",
                                                   "SKILLS_StartUsedSkill"]),
            (0x00580EC0, "PlayerDeath", ["SUNIT_AnimInit", "SUNIT_CancelModeEvents", "SUNIT_ScheduleModeEvents"])):
        seq = [(va, N.get(x, x if isinstance(x, str) else "0x%08X" % x)) for va, x in call_seq(e, 0x800, marks)]
        rp.note("%s: %s" % (nm, ", ".join("%s@%06X" % (x, va & 0xFFFFFF) for va, x in seq)))
        ok = in_order(seq, want)
        rp.add("%s_order_%s" % (nm, "ok" if ok else "no"))
        if not ok:
            rp.bad(("order", nm))
    conf = xref_check(rp, 0x005539B0, "SUNIT_ScheduleModeEvents", "p50a-anim-scan.txt", 6)
    rp.note("schedule callers' entries by int3 padding: %s" % sorted({"0x%08X" % S4.pad_entry(v) for v in conf}))
    rp.done()


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "static":
        print(__doc__)
        return 2
    chk_advance()
    chk_machine_draws()
    chk_mode_draws()
    chk_objinit()
    chk_rate_readers()
    chk_startframes()
    chk_noevent()
    chk_seq()
    chk_x4e()
    chk_seqpos()
    chk_nullrec()
    chk_monrecords()
    chk_overrides()
    chk_ratemin()
    chk_setrate_sites()
    chk_setrate_callees()
    chk_frame_return()
    chk_baseid()
    chk_pathspeed()
    chk_pathstep()
    chk_dirtable()
    chk_movestep()
    chk_move_draws()
    chk_player_tables()
    chk_start_order()
    print("S6C total bad=%d" % TOTAL_BAD[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())

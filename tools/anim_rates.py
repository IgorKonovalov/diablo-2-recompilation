#!/usr/bin/env python3
"""Static scans, models and emulation cases behind docs/findings/anim/0002-rates.md (plan 0050 Phase 1, batch P1.2).

Usage:
  python3 -I tools/anim_rates.py tables <game.exe>        the rate tables in the image
  python3 -I tools/anim_rates.py calls <game.exe>         every call of UNIT_AnimSetRate, with its source-path push
  python3 -I tools/anim_rates.py uar <game.exe>           every test of ItemStatCost `UpdateAnimRate` (+0x005 bit 1)
  python3 -I tools/anim_rates.py data <merged root>       the data bounds the finding cites (counts and maxima only)
  python3 -I tools/anim_rates.py bp <merged root>         the derived breakpoint function: closed forms checked
                                                          against a brute-force model, and worked examples
  python3 -I tools/anim_rates.py cases <dir>              write the emulation families (bonus, advance) into <dir>
  python3 -I tools/anim_rates.py check <dir>              compare <dir>/<family>.out with the models

Sections (one `SCAN <section> ...` summary line each):
  tables  BONUS <i> type k stat: the rate-bonus table 0x006E8E24 (12 B per entry, read by 0x00621740);
          MCLS <table> <mode> skillmove move skillattack attack fixed: the mode-class tables 0x006E8A00 (player, 20
          modes), 0x006E8B90 (monster class < 410, 16) and 0x006E8CD0 (monster class >= 410, 16), 5 dwords each;
          PLRV: the immediates of the player walk/run base at 0x0062140E (`sub eax,3; neg; sbb; and 0x70; add 0x65`).
  calls   SR <site> in <function> file=<pushed source path> line=<pushed line>: every `call 0x623f50`.
  uar     UAR <site> in <function> stride=<record size seen before it>: every `mov r8, [0x6ce26c]` (the mask 2) whose
          next four instructions test a `[reg+0x5]` byte.
  data    animdata speed max (the u32 product bound), MonStats rows whose BaseId row comes later (MonStatsSpeeds),
          the ItemStatCost fMin of the rate stats.
  bp      for every rate X in 15..175 and every stock (frames, start) pair, the closed form of the schedule length
          and of the least X and least item stat of each breakpoint, against brute force; then examples.
Model rules are the code's (the finding's sections); every division is stated there. Stdlib plus objdump.
"""
import bisect
import collections
import csv
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_scan as AS  # noqa: E402
import animdata as AD   # noqa: E402

M32 = 0xFFFFFFFF
SETRATE = 0x00623F50
BONUS_T = 0x006E8E24
MCLS = (("P", 0x006E8A00, 20), ("M", 0x006E8B90, 16), ("X", 0x006E8CD0, 16))
MASK2 = 0x006CE26C
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)


def h(v):
    return "0x%08X" % v


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v


def cdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def symbols():
    rows = []
    with open(os.path.join(HERE, "..", "re", "symbols.csv")) as f:
        for r in csv.reader(f):
            if r and r[0].startswith("0x") and r[1] == "func":
                rows.append((int(r[0], 16), r[2]))
    rows.sort()
    return rows


def enclosing(syms, starts, a):
    """-> 'start=<padding-delimited start before a> sym=<nearest re/symbols.csv function at or before a>'."""
    i = bisect.bisect_right(starts, a) - 1
    st = starts[i] if i >= 0 else None
    j = bisect.bisect_right([x[0] for x in syms], a) - 1
    sym = "%s@%s" % (syms[j][1], h(syms[j][0])) if j >= 0 else "-"
    return "start=%s sym=%s" % (h(st) if st else "?", sym)


RECORD_HINTS = ((r"imul\s+\w+,\w+,0x144$", "ItemStatCost"), (r"call\s+0x45c4f0$", "ItemStatCost"),
                (r"imul\s+\w+,\w+,0x134$", "MonStats2"), (r"call\s+0x451fe0$", "MonStats2"),
                (r"imul\s+\w+,\w+,0x23c$", "Skills"), (r"call\s+0x46ace0$", "Missiles"),
                (r"imul\s+\w+,\w+,0x1a8$", "MonStats"))


# ----------------------------------------------------------------------------------------------- tables
def cmd_tables(exe):
    pe = AS.PE(exe)
    for i in range(6):
        t, k, st = struct.unpack("<3i", pe.rd(BONUS_T + 12 * i, 12))
        print("BONUS %d type=%d k=%d stat=%d" % (i, t, k, st))
    n = 0
    for name, base, cnt in MCLS:
        for m in range(cnt):
            v = struct.unpack("<5i", pe.rd(base + 20 * m, 20))
            print("MCLS %s %2d skillmove=%d move=%d skillattack=%d attack=%d fixed=%d" % ((name, m) + v))
            n += 1
    code = pe.rd(0x0062140E, 14)
    print("PLRV bytes=%s" % code.hex())
    ok = code[:13] == bytes.fromhex("83e803f7d81bc083e07083c065")
    print("SCAN tables bonus=6 mcls_rows=%d plrv_match=%d" % (n, int(ok)))


# ----------------------------------------------------------------------------------------------- calls, uar
def cstring(pe, va):
    try:
        b = pe.rd(va, 64)
    except ValueError:
        return "?"
    return b.split(b"\0")[0].decode("latin-1")


def cmd_calls(exe):
    pe = AS.PE(exe)
    ins = AS.disasm(exe)
    st = AS.starts(ins)
    syms = symbols()
    n = 0
    for k, (a, t) in enumerate(ins):
        if not re.match(r"call\s+0x%x$" % SETRATE, t):
            continue
        pushes = []
        for j in range(k - 1, max(k - 8, 0), -1):
            m = re.match(r"push\s+(0x[0-9a-f]+)$", ins[j][1])
            if m:
                pushes.append(int(m.group(1), 16))
            if len(pushes) == 2:
                break
        fname = cstring(pe, pushes[0]) if pushes else "?"
        line = pushes[1] if len(pushes) > 1 else -1
        print("SR %s %s file=%s line=%d" % (h(a), enclosing(syms, st, a), fname, line))
        n += 1
    print("SCAN calls sites=%d" % n)


def cmd_uar(exe):
    ins = AS.disasm(exe)
    st = AS.starts(ins)
    syms = symbols()
    n = 0
    cnt = collections.Counter()
    for k, (a, t) in enumerate(ins):
        if not re.match(r"mov\s+[a-d]l,(BYTE PTR )?ds:0x%x$" % MASK2, t):
            continue
        hit = None
        for j in range(k + 1, min(k + 5, len(ins))):
            if re.match(r"test\s+BYTE PTR \[e[a-z]{2}\+0x5\],[a-d]l$", ins[j][1]):
                hit = ins[j][0]
                break
        if hit is None:
            continue
        rec = "-"
        for j in range(k - 1, max(k - 26, 0), -1):
            for pat, nm in RECORD_HINTS:
                if re.match(pat, ins[j][1]):
                    rec = nm
                    break
            if rec != "-":
                break
        if rec == "-" and k >= 3 and re.match(r"mov\s+\w+,DWORD PTR \[ebp-0x10\]$", ins[k + 1][1]):
            rec = "local"
        print("UAR %s test=%s %s record=%s" % (h(a), h(hit), enclosing(syms, st, a), rec))
        n += 1
        cnt[rec] += 1
    print("SCAN uar sites=%d %s" % (n, " ".join("%s=%d" % kv for kv in sorted(cnt.items()))))


# ----------------------------------------------------------------------------------------------- data
def read_txt(path):
    with open(path, encoding="latin-1") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def cmd_data(root):
    recs = AD.load(os.path.join(root, "data", "global", "animdata.d2"))
    speeds = [r.speed for r in recs]
    frames = [r.frames for r in recs]
    print("ANIM records=%d speed_max=%d speed_min=%d frames_max=%d" % (len(recs), max(speeds), min(speeds), max(frames)))
    print("ANIM product_bound speed_max*175=%d fits_u32=%d" % (max(speeds) * 175, int(max(speeds) * 175 <= M32)))
    xd = os.path.join(root, "data", "global", "excel")
    hd, rows = read_txt(os.path.join(xd, "monstats.txt"))
    ids = [r[hd.index("Id")] for r in rows]
    idx = {}
    k = 0
    for r in rows:
        if r[hd.index("Id")] == "Expansion":
            continue
        idx[r[hd.index("Id")]] = k
        k += 1
    later = 0
    for r in rows:
        if r[hd.index("Id")] == "Expansion":
            continue
        b = r[hd.index("BaseId")]
        if b in idx and idx[b] > idx[r[hd.index("Id")]]:
            later += 1
    print("MONSTATS rows=%d base_later=%d" % (k, later))
    hi, irows = read_txt(os.path.join(xd, "itemstatcost.txt"))
    for r in irows:
        if r[hi.index("ID")] in ("67", "68", "69", "93", "96", "99", "102", "105"):
            print("ISC %s %s fMin=%r damagerelated=%r" % (r[hi.index("ID")], r[hi.index("Stat")], r[hi.index("fMin")],
                                                         r[hi.index("damagerelated")]))
    print("SCAN data anim_records=%d monstats_rows=%d" % (len(recs), k))
    del ids


# ----------------------------------------------------------------------------------------------- the models
BONUS = {0: (1, 120, 93), 1: (1, 120, 99), 2: (1, 120, 105), 3: (1, 120, 102), 4: (1, 150, 96), 5: (1, 1, 0)}


def bonus(i, v):
    """0x00621740: v = the stat (sub_00625500_UnitGetStat); type 1 and v != 0 -> imul, cdq, idiv."""
    t, k, _ = BONUS[i]
    v = s32(v)
    if t == 1 and v != 0:
        return cdiv(s32(k * v), s32(k + v))
    return v


def floor0_cap(q):
    """`test; setle; sub 1; and` then `cmp 0x7fff; jl`: q <= 0 (signed) -> 0; >= 0x7FFF -> 0x7FFF."""
    q = s32(q)
    if q <= 0:
        q = 0
    return min(q, 0x7FFF)


def rate_u(speed, x):
    """speed * X in 32 bits (imul), then the unsigned divide by 100 (mul 0x51EB851F, shr 5)."""
    return ((speed * x) & M32) // 100


def rate_attack(speed, x):
    return floor0_cap(rate_u(speed, max(15, min(175, x))))


def rate_cast(speed, fcr_bonus):
    return floor0_cap(rate_u(speed, min(100 + fcr_bonus, 175)))


def rate_gethit(speed, fhr_bonus):
    return floor0_cap(rate_u(speed, fhr_bonus + 50))


def rate_block(speed, fbr_bonus, holyshield):
    q = rate_u(speed, fbr_bonus + (100 if holyshield else 50))
    return floor0_cap(q if q >= 1 else 1)


def rate_default(speed, s69):
    return floor0_cap(rate_u(speed, max(15, min(175, s69))))


def sched_len(F, S, r):
    """The loop of SUNIT_ScheduleModeEvents (anim/0001 § 7): end at T + n; frame f fires at T + k_f."""
    L = F << 8
    if r == 0:
        return 1, {}
    acc = (S << 8) + r
    t = 0
    f = S
    fires = {}
    while acc < L:
        t += 1
        while f <= (acc >> 8) and f < 0x90:
            fires[f] = t
            f += 1
        acc += r
    if t == 0:
        t = 1
    return t + 1, fires


def ceil_div(a, b):
    return -((-a) // b)


def closed_len(F, S, r):
    if F <= S:
        return 2
    return max(2, ceil_div((F - S) << 8, r))


def least_x(speed, F, S, m, lo=15, hi=175):
    """Least X in [lo, hi] whose rate floor(speed*X/100) gives length <= m: r >= R = ceil(256(F-S)/m)."""
    R = ceil_div((F - S) << 8, m)
    x = max(lo, ceil_div(100 * R, speed))
    return x if x <= hi else None


def least_stat(k, y):
    """Least s >= 0 with floor(k*s/(k+s)) >= y (y < k): s >= ceil(k*y/(k-y))."""
    if y <= 0:
        return 0
    if y >= k:
        return None
    return ceil_div(k * y, k - y)


def cmd_bp(root):
    recs = AD.load(os.path.join(root, "data", "global", "animdata.d2"))
    pairs = sorted({(r.frames, r.speed) for r in recs if 0 < r.frames <= 0x90 and r.speed > 0})
    bad = checked = 0
    fchecked = [0]
    # (1) the closed form of the schedule length against the loop, every stock (frames, speed), S in {0,1,2}, X 15..175
    for F, sp in pairs:
        for S in (0, 1, 2):
            if S >= F:
                continue
            for x in range(15, 176):
                r = rate_attack(sp, x)
                if r == 0:
                    continue
                n, fires = sched_len(F, S, r)
                checked += 1
                if n != closed_len(F, S, r):
                    bad += 1
                    print("BAD len F=%d S=%d sp=%d x=%d loop=%d closed=%d" % (F, S, sp, x, n, closed_len(F, S, r)))
                want = {}
                N = ceil_div((F - S) << 8, r) - 1                 # the steps: 256S + k r < 256F
                for f in range(S, min(F, 0x90)):
                    kf = max(1, ceil_div((f - S) << 8, r))
                    if kf <= N:
                        want[f] = kf
                fchecked[0] += 1
                if want != fires:
                    bad += 1
                    print("BAD fires F=%d S=%d sp=%d x=%d" % (F, S, sp, x))
    print("CHECK closed_len_and_fires cases=%d bad=%d" % (checked, bad))
    # (2) least X per length against brute force
    b2 = c2 = 0
    for F, sp in pairs:
        for S in (0, 1, 2):
            if S >= F:
                continue
            lens = {}
            for x in range(15, 176):
                r = rate_attack(sp, x)
                if r == 0:
                    continue
                n = closed_len(F, S, r)
                lens.setdefault(n, x)
            for m in sorted(lens):
                c2 += 1
                bx = min(x for x in range(15, 176) if rate_attack(sp, x) and closed_len(F, S, rate_attack(sp, x)) <= m)
                if least_x(sp, F, S, m) != bx:
                    b2 += 1
                    print("BAD leastx F=%d S=%d sp=%d m=%d closed=%s brute=%d" % (F, S, sp, m, least_x(sp, F, S, m), bx))
    print("CHECK least_x cases=%d bad=%d" % (c2, b2))
    # (3) the least stat for a bonus y against brute force (k 120 and 150; s 0..2000)
    b3 = c3 = 0
    for k in (120, 150):
        tab = {}
        for s in range(0, 2001):
            y = cdiv(k * s, k + s) if s else 0
            tab.setdefault(y, s)
        for y in sorted(tab):
            c3 += 1
            if least_stat(k, y) != tab[y]:
                b3 += 1
                print("BAD leaststat k=%d y=%d closed=%s brute=%d" % (k, y, least_stat(k, y), tab[y]))
    print("CHECK least_stat cases=%d bad=%d" % (c3, b3))
    # (4) worked examples: the records named, the breakpoint function printed (length -> least X -> least stat)
    # S: g_AttackStartFrames (anim/0001 § 4): 1 for the Amazon and the Sorceress hand to hand, 2 with a 1hs weapon
    names = [("AMA1HTH", 1), ("AMA11HS", 2), ("SOA11HS", 2), ("BAA11HS", 0), ("PAA11HS", 0), ("SOSCHTH", 0),
             ("NESCHTH", 0), ("PAGHHTH", 0), ("BABL1HS", 0)]
    for nm, S in names:
        rs = AD.lookup(recs, nm)
        if not rs:
            print("EX %s missing" % nm)
            continue
        r = rs[0]
        F, sp = r.frames, r.speed
        ev = [i for i, b in enumerate(r.events[:F]) if b in (1, 2, 3, 4)]
        print("EX %s frames=%d speed=%d start=%d events=%s" % (nm, F, sp, S, ev))
        seen = None
        for x in range(15, 176):
            rr = rate_attack(sp, x)
            n = closed_len(F, S, rr)
            if n != seen:
                fire = {f: max(1, ceil_div((f - S) << 8, rr)) for f in ev
                        if f >= S and max(1, ceil_div((f - S) << 8, rr)) <= ceil_div((F - S) << 8, rr) - 1}
                print("EXBP %s X=%d rate=%d length=%d events_at=%s" % (nm, x, rr, n,
                      ",".join("%d:+%d" % kv for kv in sorted(fire.items()))))
                seen = n
    # (5) the item-stat side, for the cast (base 100, cap 175), get-hit (base 50) and block (base 50; 100 holy shield)
    for nm, base, cap, k, bi in (("SOSCHTH", 100, 175, 120, 2), ("NESCHTH", 100, 175, 120, 2),
                                 ("PAGHHTH", 50, None, 120, 1), ("BABL1HS", 50, None, 120, 3),
                                 ("BABL1HS", 100, None, 120, 3)):
        rs = AD.lookup(recs, nm)
        if not rs:
            continue
        F, sp = rs[0].frames, rs[0].speed
        seen = None
        for s_ in range(0, 2001):
            y = bonus(bi, s_)
            x = min(base + y, cap) if cap else base + y
            n = closed_len(F, 0, floor0_cap(rate_u(sp, x)))
            if n != seen:
                print("EXSTAT %s base=%d stat=%d bonus=%d X=%d length=%d closed_stat=%s" %
                      (nm, base, s_, y, x, n, least_stat(k, x - base) if (cap is None or x < cap) else "cap"))
                seen = n
    # (6) the edges the finding states: negative factors, the divide fault, the 32-bit products
    neg_c = [v for v in range(-119, 0) if 100 + bonus(2, v) < 0]
    neg_h = [v for v in range(-119, 0) if 50 + bonus(1, v) < 0]
    neg_b = [v for v in range(-119, 0) if 50 + bonus(3, v) < 0]
    print("EDGE cast_factor_negative stat=%d..%d rate_at_256=%d" % (neg_c[0], neg_c[-1], rate_cast(256, bonus(2, neg_c[-1]))))
    print("EDGE gethit_factor_negative stat=%d..%d rate_at_256=%d" % (neg_h[0], neg_h[-1], rate_gethit(256, bonus(1, neg_h[-1]))))
    print("EDGE block_factor_negative stat=%d..%d rate_at_256=%d" % (neg_b[0], neg_b[-1], rate_block(256, bonus(3, neg_b[-1]), False)))
    print("EDGE bonus k=120 s=-119 -> %d; s=-121 -> %d; s=-120 divides by zero" % (bonus(2, -119), bonus(2, -121)))
    print("EDGE bonus_max k=120: least s with bonus 119 = %d" % least_stat(120, 119))
    print("EDGE move_product 32767*65538=%d fits=%d 32767*65539=%d fits=%d" %
          (32767 * 65538, int(32767 * 65538 <= 2 ** 31 - 1), 32767 * 65539, int(32767 * 65539 <= 2 ** 31 - 1)))
    print("EDGE attack_product base_max_for_X175=%d" % (M32 // 175))
    print("SCAN bp pairs=%d" % len(pairs))


# ----------------------------------------------------------------------------------------------- emulation
UNIT, SL, ARR, REC = 0x20000000, 0x20001000, 0x20002000, 0x20003000
DT, ISC = 0x21000000, 0x21100000
STK_LO, STK_LEN = 0x7FEFFC00, 1024


def le32(v):
    return struct.pack("<I", v & M32)


def le16(v):
    return struct.pack("<H", v & 0xFFFF)


def guards():
    return ["guard %08x" % a for a in FATAL + ALLOC]


def fam_bonus(rnd):
    mem = ["dword 00744304 %08x" % DT, "dword %08x %08x" % (DT + 0xBD4, 512), "dword %08x %08x" % (DT + 0xBCC, ISC)]
    for i in range(6):
        mem.append("bytes %08x 00" % (ISC + 0x144 * BONUS[i][2] + 5))     # fMin clear (fMin blank in the .txt)
    mem += guards()
    cases, exp = [], []
    vals = list(range(-119, 400)) + [450, 500, 600, 800, 1000, 2000, 5000, 32767, 65535]
    for i in range(6):
        k = BONUS[i][1]
        pool = [v for v in vals if v != -k] + [rnd.randint(-2 ** 31, 2 ** 31 - 1) for _ in range(40)]
        pool = [v for v in pool if s32(k + v) != 0]
        for v in pool + [None]:
            c = []
            stats = {}
            if v is not None:
                stats[BONUS[i][2]] = v
            for _ in range(rnd.randrange(4)):                    # decoys: other stats, other layers
                d = rnd.randrange(0, 360)
                if d != BONUS[i][2]:
                    stats.setdefault(d, rnd.getrandbits(32))
            keys = sorted((s << 16, val) for s, val in stats.items())
            if rnd.random() < 0.2 and v is not None:
                keys = sorted(keys + [((BONUS[i][2] << 16) | 1, rnd.getrandbits(32))])
            c.append("w %08x %s" % (UNIT + 0x5C, le32(SL).hex()))
            c.append("w %08x %s" % (SL + 0x10, le32(0x80000000).hex()))
            c.append("w %08x %s" % (SL + 0x48, le32(ARR).hex()))
            c.append("w %08x %s" % (SL + 0x4C, le16(len(keys)).hex()))
            for j, (kk, val) in enumerate(keys):
                c.append("w %08x %s" % (ARR + 8 * j, (le32(kk) + le32(val)).hex()))
            c.append("r EAX %08x" % i)
            c.append("call 00621740 %08x 00000000" % UNIT)
            cases += c
            exp.append((i, v if v is not None else 0, bonus(i, v if v is not None else 0)))
    return cases, mem, exp


def adv_model(a, L, r, ev):
    """UNIT_AnimAdvance (0x00623E00), no sequence, a monster (start frame 0); ev: the record's 144 event bytes or None."""
    e = 0
    f = a >> 8
    if s16(r) >= 0x100:
        f += 1
    a = s32(a + s16(r))

    def take(x):
        nonlocal e
        if ev is not None and x < 0x90 and ev[x] in (1, 2, 3, 4):
            e = ev[x]
    if a >= L:
        while True:
            lf = L >> 8
            while f < lf:
                take(f)
                f += 1
            a -= L
            f = 0
            if not a >= L:
                break
    d = a >> 8
    while f <= d:
        take(f)
        f += 1
    return a, e


def fam_advance(rnd):
    mem = guards()
    cases, exp = [], []
    for k in range(1200):
        F = rnd.choice([1, 2, 4, 6, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20, 24, 0x8F, 0x90, 0x91, 0xA0])
        L = F << 8
        rec = rnd.random() > 0.05
        ev = [0] * 0x90
        if rec:
            for _ in range(rnd.choice([0, 1, 3, 10, 40])):
                ev[rnd.randrange(0x90)] = rnd.choice([1, 2, 3, 4, 5, 0xFF])
        pair = []
        a = rnd.randrange(0, L)
        for step in range(2):                                    # two advances; the second with another rate
            r = rnd.choice([0, 1, 0x40, 0x80, 0xFF, 0x100, 0x101, 0x180, 0x200, 0x300, rnd.randrange(0, 0x800),
                            rnd.randrange(0, 0x8000)])
            c = []
            c.append("w %08x %s" % (UNIT + 0x00, le32(1).hex()))
            c.append("w %08x %s" % (UNIT + 0x04, le32(rnd.randrange(0, 700)).hex()))
            c.append("w %08x %s" % (UNIT + 0x10, le32(rnd.choice([2, 4, 5, 13, 14, 15])).hex()))
            c.append("w %08x %s" % (UNIT + 0x30, le32(0).hex()))
            c.append("w %08x %s" % (UNIT + 0x44, le32(a).hex()))
            c.append("w %08x %s" % (UNIT + 0x48, le32(L).hex()))
            c.append("w %08x %s" % (UNIT + 0x4C, le16(r).hex()))
            c.append("w %08x %s" % (UNIT + 0x4E, "ee"))
            c.append("w %08x %s" % (UNIT + 0x50, le32(REC if rec else 0).hex()))
            c.append("w %08x %s" % (UNIT + 0xC8, le32(0).hex()))
            if rec:
                c.append("w %08x %s" % (REC + 0x10, bytes(ev).hex()))
            c.append("d %08x 4" % (UNIT + 0x44))
            c.append("d %08x 1" % (UNIT + 0x4E))
            c.append("d %08x 4" % (UNIT + 0x48))
            c.append("call 00623e00 00000000 00000000 %08x" % UNIT)
            na, ne = adv_model(a, L, r, ev if rec else None)
            cases += c
            exp.append((k, step, a, L, r, na, ne, pair[0] if pair else None, ev if rec else None))
            a = na
            pair.append(r)
    return cases, mem, exp


FAMILIES = {"bonus": fam_bonus, "advance": fam_advance}


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for name, fn in FAMILIES.items():
        rnd = random.Random("p50b-" + name)
        cases, mem, exp = fn(rnd)
        with open(os.path.join(d, name + ".cases"), "w") as f:
            f.write("\n".join(cases) + "\n")
        with open(os.path.join(d, name + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        print("CASES %s n=%d" % (name, len(exp)))


def read_out(path):
    calls, reads, writes = [], [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "fn": int(p[2], 16), "dumps": []}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            else:
                kv = dict(x.split("=") for x in p[3:])
                c.update(eax=int(kv["eax"], 16), pop=int(kv["pop"]))
            calls.append(c)
        elif p[0] == "D":
            calls[-1]["dumps"].append((int(p[1], 16), bytes.fromhex(p[2]) if len(p) > 2 else b""))
        elif p[0] in ("R", "W"):
            (reads if p[0] == "R" else writes).append((int(p[1], 16), int(p[2], 16), int(p[3]), int(p[4])))
    return calls, reads, writes


def cmd_check(d):
    tot_bad = 0
    for name, fn in FAMILIES.items():
        rnd = random.Random("p50b-" + name)
        _, _, exp = fn(rnd)
        calls, reads, writes = read_out(os.path.join(d, name + ".out"))
        bad = stops = 0
        if len(calls) != len(exp):
            print("BAD %s count out=%d exp=%d" % (name, len(calls), len(exp)))
            bad += 1
        br = collections.Counter()
        for c, e in zip(calls, exp):
            if "stop" in c:
                stops += 1
                print("STOP %s %d %s" % (name, c["n"], c["stop"]))
                continue
            if name == "bonus":
                i, v, want = e
                got = s32(c["eax"])
                br["neg" if v < 0 else ("zero" if v == 0 else "pos")] += 1
                if got != want or c["pop"] != 0:
                    bad += 1
                    print("BAD bonus case=%d i=%d v=%d got=%d want=%d pop=%d" % (c["n"], i, v, got, want, c["pop"]))
            else:
                k, step, a, L, r, na, ne, r0, ev = e
                if step == 1 and r0 != r:
                    br["sep_rate_differs"] += 1
                    if adv_model(a, L, r0, ev) != (na, ne):
                        br["sep_old_rate_would_mismatch"] += 1
                dm = dict(c["dumps"])
                got_a = s32(struct.unpack("<I", dm[UNIT + 0x44])[0])
                got_e = dm[UNIT + 0x4E][0]
                got_L = struct.unpack("<I", dm[UNIT + 0x48])[0]
                br["wrap" if a + s16(r) >= L else "nowrap"] += 1
                br["ev%d" % ne] += 1
                br["step%d" % step] += 1
                if got_a != na or got_e != ne or got_L != L or c["pop"] != 4:
                    bad += 1
                    print("BAD advance case=%d k=%d step=%d a=%d L=%d r=%d got=(%d,%d) want=(%d,%d)" %
                          (c["n"], k, step, a, L, r, got_a, got_e, na, ne))
        # read set: the image tables only
        allowed = []
        if name == "bonus":
            allowed = [(BONUS_T, BONUS_T + 72), (0x006CE270, 0x006CE271)]   # the table; the fMin mask byte (4)
        extra = [(pc, a) for pc, a, sz, cnt in reads if not any(lo <= a < hi for lo, hi in allowed)]
        for pc, a in extra:
            print("READ %s pc=%s addr=%s" % (name, h(pc), h(a)))
        extraw = [(pc, a) for pc, a, sz, cnt in writes]
        for pc, a in extraw:
            print("WRITE %s pc=%s addr=%s" % (name, h(pc), h(a)))
        print("FAMILY %s cases=%d bad=%d stops=%d reads_outside=%d writes_outside=%d branches=%s" %
              (name, len(calls), bad, stops, len(extra), len(extraw),
               ",".join("%s:%d" % kv for kv in sorted(br.items()))))
        tot_bad += bad + stops + len(extra) + len(extraw)
    print("SCAN check bad=%d" % tot_bad)
    return 0 if tot_bad == 0 else 1


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "tables":
        cmd_tables(arg)
    elif cmd == "calls":
        cmd_calls(arg)
    elif cmd == "uar":
        cmd_uar(arg)
    elif cmd == "data":
        cmd_data(arg)
    elif cmd == "bp":
        cmd_bp(arg)
    elif cmd == "cases":
        cmd_cases(arg)
    elif cmd == "check":
        return cmd_check(arg)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

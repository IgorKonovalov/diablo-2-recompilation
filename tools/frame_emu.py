#!/usr/bin/env python3
"""Plan 0055 phase 1.1 (the server frame: the tick and the messages, `lane/r55`): three pure list and clock functions
of the frame's passes run under Ghidra's p-code emulator (ADR-0015) with re/ghidra_scripts/EmuBoundary.java and
compared with the models below. No game run, no slot.

    python3 -I tools/frame_emu.py cases [--dir D]     write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/frame_emu.py check [--dir D]     compare every D/<family>.out with its model, account for every
                                                      traced access, run the negative controls
    python3 -I tools/frame_emu.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r55/emu. Every case draw comes from random.Random("r55-<family>"), so `cases` regenerates
identical files.

Families (function, what the claim covers):
  env    0x0061C040 (__stdcall(act, actNo), ret 8; the first pass of GameTick, once per act): the act's light clock at
         [act+4] (period p, value v, counter c, scale k at +0x28, table flag f at +0x30, last bucket b at +0x34),
         stepped by 0x0061BEE0, and the return (1: the clock moved to a new period or its bucket c/k moved by more
         than 16; 0 otherwise; 0 for a null clock). The three 6-row tables at 0x007443F0, 0x00744438 and 0x00744480
         are the image's own (declared case memory, never written: no write xref).
  mark   0x0064C040 (__stdcall(unit), ret 4; 78 direct call sites): the unit's room (unit types 2, 4, 5 through
         [unit+0x2C]+0x00, the others through the path's +0x1C, 0 for a null path), and, when the room is set, its
         flag +0x34 & 4 clear and the unit's +0xC4 bit 0x2000 clear: the bit set, the unit pushed on the front of the
         room's list at +0x1C (next +0xE0), and the act's dirty word ([room+0x2C]+0x00) set to 1. Otherwise nothing.
  clear  0x0064C160 (__stdcall(room), ret 4; called by ActUnitsFrameReset per room): every unit of the room's
         +0x1C list loses bit 0x2000 of +0xC4 and its +0xE0 link (0), and the head is set to 0. The act word is set
         to 1 by the shared getter only when its EDX is non-zero; here EDX = 0, so the act word is unchanged.

Not covered: the callers' loops (GameTick's act loop, ActUnitsFrameReset's room loop), UnitFrameReset, the packet sent
on a clock change, and every allocator or fatal path (guards: a case reaching one is a stop).
Stdlib only.
"""
import argparse
import hashlib
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r55", "emu")

ACT = 0x13000000
ENV = 0x13100000
ROOM = 0x13200000
PATH = 0x13300000
UNITS = 0x13400000          # unit i at UNITS + i * 0x1000
DROOM = 0x13500000          # the direct-room pointer cell of types 2, 4, 5
TABLES = 0x007443F0         # three tables of six rows (start, type, colour), 0x48 bytes each
TABLE_LEN = 3 * 0x48
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
FAMILIES = ("env", "mark", "clear")
SENT = 0xA5A5A5A5


def u32(v):
    return v & 0xFFFFFFFF


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


def hx32(v):
    return struct.pack("<I", u32(v)).hex()


def image_tables():
    exe = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
    d = open(exe, "rb").read()
    off = TABLES - 0x00705000 + 0x00305000
    rows = [struct.unpack_from("<3i", d, off + 12 * i) for i in range(18)]
    return rows[0:6], rows[6:12], rows[12:18]


T0, T1, T2 = image_tables()


# -------------------------------------------------------------------------------------------------- the models
def m_env(e, act, neg=False):
    """e = [p, v, c, k, f, b]; returns (eax, [p, v, c, b]) after 0x0061C040. neg "ge": advance on >= (one compare
    off); neg "flat": every act steps by 1 (the act 2 and act 3 extra steps left out)."""
    p, v, c, k, f, b = e
    p0, v0 = p, v
    c = s32(c + 1)
    if f == 0 and neg != "flat":
        if act == 3:
            c = s32(c + 15)
        elif T0[p][1] == 2:
            c = s32(c + 1)
            if act == 2:
                c = s32(c + 8)
    if c >= s32(k * 360):
        c = 0
    nxt = p + 1
    if nxt >= 6:
        nxt = 0
    tbl = T0 if f == 0 else (T1 if act == 3 else T2)
    lim = s32(tbl[nxt][0] * k)
    if (c >= lim) if neg == "ge" else (c > lim):
        p = p + 1
        if p >= 6:
            p = 0
        src = T0 if f == 0 else T2
        v = src[p][1]
        c = s32(src[p][0] * k)
    if k != 0:
        q = abs(c) // abs(k)                                # idiv: truncating division
        if (c < 0) != (k < 0):
            q = -q
        q = s32(q)
        dl = s32(q - b)
        if dl < 0:
            dl = s32(-dl)
        if dl > 16:
            return 1, [p, v, c, q]
    return (0 if (v0 == v and p0 == p) else 1), [p, v, c, b]


def m_mark(typ, room_kind, rflags, c4, head, neg=False):
    """room_kind: 'path', 'nopath', 'direct', 'directnull'. Returns (c4, e0, head, actword) after 0x0064C040.
    neg: the 0x2000 test left out (a unit already listed is pushed again)."""
    room = None
    if typ in (2, 4, 5):
        room = ROOM if room_kind == "direct" else None
    else:
        room = ROOM if room_kind == "path" else None
    if room is None or rflags & 4 or (c4 & 0x2000 and not neg):
        return c4, SENT, head, 0
    return c4 | 0x2000, head, UNITS, 1


def m_clear(n, c4s, neg=False):
    """n units listed; returns ([(c4, e0)...], head). neg: the head kept."""
    out = [(c & ~0x2000 & 0xFFFFFFFF, 0) for c in c4s[:n]]
    return out, (UNITS if (neg and n) else 0)


# ------------------------------------------------------------------------------------------------- the cases
def mem_spec():
    return ["guard %08x" % a for a in FATAL + ALLOC]


def gen_env(rnd):
    cases, meta = [], []
    scales = [1, 2, 3, 5, 10, 25, 40, 100, 250, 1000]
    for i in range(400):
        act = i % 5
        f = 0 if i % 4 else 1
        k = rnd.choice(scales) if i % 10 else rnd.randrange(1, 5000)
        p = rnd.randrange(0, 6)
        src = T0 if f == 0 else T2
        v = src[p][1] if i % 7 else rnd.randrange(0, 4)
        mode = i % 3
        if mode == 0:     # just below the next period's start
            nxt = (p + 1) % 6
            tbl = T0 if f == 0 else (T1 if act == 3 else T2)
            c = tbl[nxt][0] * k - rnd.randrange(0, 20)
        elif mode == 1:   # just below the wrap
            c = k * 360 - rnd.randrange(1, 20)
        else:
            c = rnd.randrange(0, max(1, k * 360))
        c = max(c, -5)
        bq = (c // k) if k else 0
        b = bq + rnd.choice([0, 1, -1, 15, 16, 17, -16, -17, 40, -40])
        e = [p, v, c, k, f, b]
        meta.append(("clock", act, e))
    for i in range(20):
        meta.append(("null", i % 5, None))
    for kind, act, e in meta:
        lines = []
        if kind == "null":
            lines.append("w %08x %s" % (ACT + 4, hx32(0)))
        else:
            p, v, c, k, f, b = e
            lines.append("w %08x %s" % (ACT + 4, hx32(ENV)))
            lines.append("w %08x %s%s%s" % (ENV, hx32(p), hx32(v), hx32(c)))
            lines.append("w %08x %s" % (ENV + 0x28, hx32(k)))
            lines.append("w %08x %s%s" % (ENV + 0x30, hx32(f), hx32(b)))
            lines.append("s %08x %d" % (ENV + 0x0C, 0x1C))
            lines.append("d %08x %d" % (ENV, 0x38))
        lines.append("s %08x %d" % (TABLES, TABLE_LEN))
        lines.append("call 0061c040 %08x %08x %08x %08x" % (0, 0, ACT, act))
        cases.append(lines)
    return cases, meta, mem_spec()


def gen_mark(rnd):
    cases, meta = [], []
    for i in range(300):
        typ = i % 6
        if typ in (2, 4, 5):
            room_kind = "direct" if i % 9 else "directnull"
        else:
            room_kind = "path" if i % 11 else "nopath"
        rflags = rnd.choice([0, 0, 0, 1, 2, 4, 5, 0xFFFFFFFB, 0xFFFFFFFF])
        c4 = rnd.getrandbits(32)
        if i % 3 == 0:
            c4 |= 0x2000
        elif i % 3 == 1:
            c4 &= ~0x2000 & 0xFFFFFFFF
        head = rnd.choice([0, UNITS + 0x1000, UNITS + 0x2000, rnd.getrandbits(32) | 1])
        meta.append((typ, room_kind, rflags, c4, head))
    for typ, room_kind, rflags, c4, head in meta:
        u = UNITS
        lines = ["w %08x %s" % (u, hx32(typ)),
                 "w %08x %s" % (u + 0xC4, hx32(c4)),
                 "w %08x %s" % (u + 0xE0, hx32(SENT)),
                 "w %08x %s" % (ROOM + 0x1C, hx32(head)),
                 "w %08x %s" % (ROOM + 0x2C, hx32(ACT)),
                 "w %08x %s" % (ROOM + 0x34, hx32(rflags)),
                 "w %08x %s" % (ACT, hx32(0))]
        if typ in (2, 4, 5):
            lines.append("w %08x %s" % (u + 0x2C, hx32(DROOM)))
            lines.append("w %08x %s" % (DROOM, hx32(ROOM if room_kind == "direct" else 0)))
        else:
            lines.append("w %08x %s" % (u + 0x2C, hx32(PATH if room_kind == "path" else 0)))
            lines.append("w %08x %s" % (PATH + 0x1C, hx32(ROOM)))
        lines += ["d %08x 4" % (u + 0xC4), "d %08x 4" % (u + 0xE0), "d %08x 4" % (ROOM + 0x1C), "d %08x 4" % ACT]
        lines.append("call 0064c040 %08x %08x %08x" % (0, 0, u))
        cases.append(lines)
    return cases, meta, mem_spec()


def gen_clear(rnd):
    cases, meta = [], []
    for i in range(120):
        n = i % 8
        c4s = [rnd.getrandbits(32) | (0x2000 if rnd.random() < 0.8 else 0) for _ in range(8)]
        meta.append((n, c4s))
    for n, c4s in meta:
        lines = ["w %08x %s" % (ROOM + 0x1C, hx32(UNITS if n else 0)),
                 "w %08x %s" % (ROOM + 0x2C, hx32(ACT)),
                 "w %08x %s" % (ACT, hx32(0))]
        for j in range(8):
            u = UNITS + 0x1000 * j
            nxt = (UNITS + 0x1000 * (j + 1)) if j + 1 < n else 0
            lines.append("w %08x %s" % (u + 0xC4, hx32(c4s[j])))
            lines.append("w %08x %s" % (u + 0xE0, hx32(nxt if j < n else SENT)))
            lines += ["d %08x 4" % (u + 0xC4), "d %08x 4" % (u + 0xE0)]
        lines += ["d %08x 4" % (ROOM + 0x1C), "d %08x 4" % ACT]
        lines.append("call 0064c160 %08x %08x %08x" % (0, 0, ROOM))
        cases.append(lines)
    return cases, meta, mem_spec()


GEN = {"env": gen_env, "mark": gen_mark, "clear": gen_clear}


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rnd = random.Random("r55-" + fam)
        cases, meta, mem = GEN[fam](rnd)
        with open(os.path.join(d, fam + ".cases"), "w") as f:
            for c in cases:
                f.write("\n".join(c) + "\n")
        with open(os.path.join(d, fam + ".mem"), "w") as f:
            f.write("\n".join(mem) + "\n")
        print("CASES %s %d" % (fam, len(cases)))


# ------------------------------------------------------------------------------------------------- the output
def read_out(path):
    calls, traced = [], []
    for ln in open(path):
        p = ln.split()
        if not p:
            continue
        if p[0] == "C":
            c = {"n": int(p[1]), "dumps": {}}
            if p[3] == "STOP":
                c["stop"] = " ".join(p[4:])
            elif p[3] == "OBS":
                c["stop"] = "unexpected OBS " + " ".join(p[4:])
            else:
                kv = dict(x.split("=") for x in p[3:])
                c["eax"] = int(kv["eax"], 16)
                c["pop"] = int(kv["pop"])
            calls.append(c)
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def dw(c, a):
    b = c["dumps"].get(a)
    return struct.unpack("<I", b[:4])[0] if b else None


def check_case(fam, c, m):
    """(model matches, the negative control predicts differently, the negative control matches the binary)."""
    if fam == "env":
        kind, act, e = m
        if kind == "null":
            return c.get("eax") == 0 and c.get("pop") == 8, False, False
        want = m_env(e, act)
        nwant = m_env(e, act, neg=ENV_NEG)
        raw = c["dumps"].get(ENV)
        got_f = list(struct.unpack_from("<3i", raw, 0)) + [struct.unpack_from("<i", raw, 0x34)[0]]
        got = (c.get("eax"), got_f)
        ok = got == want and c.get("pop") == 8
        k = struct.unpack_from("<i", raw, 0x28)[0]
        f = struct.unpack_from("<i", raw, 0x30)[0]
        ok = ok and k == e[3] and f == e[4]
        return ok, nwant != want, got == nwant
    if fam == "mark":
        typ, room_kind, rflags, c4, head = m
        want = m_mark(typ, room_kind, rflags, c4, head)
        nwant = m_mark(typ, room_kind, rflags, c4, head, neg=True)
        got = (dw(c, UNITS + 0xC4), dw(c, UNITS + 0xE0), dw(c, ROOM + 0x1C), dw(c, ACT))
        return got == want and c.get("pop") == 4, nwant != want, got == nwant
    if fam == "clear":
        n, c4s = m
        want = m_clear(n, c4s)
        nwant = m_clear(n, c4s, neg=True)
        units = [(dw(c, UNITS + 0x1000 * j + 0xC4), dw(c, UNITS + 0x1000 * j + 0xE0)) for j in range(n)]
        rest_ok = all(dw(c, UNITS + 0x1000 * j + 0xC4) == c4s[j] and dw(c, UNITS + 0x1000 * j + 0xE0) == SENT
                      for j in range(n, 8))
        got = (units, dw(c, ROOM + 0x1C))
        ok = got == want and rest_ok and dw(c, ACT) == 0 and c.get("pop") == 4
        return ok, nwant != want, got == nwant
    raise ValueError(fam)


ENV_NEG = "ge"


def check_family(fam, d):
    rnd = random.Random("r55-" + fam)
    _, meta, _ = GEN[fam](rnd)
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops, nsep, npass = [], 0, 0, 0, 0
    if len(calls) != len(meta):
        bad.append("case count %d != %d" % (len(calls), len(meta)))
    for c, m in zip(calls, meta):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        ok, sep, negok = check_case(fam, c, m)
        match += ok
        if not ok:
            bad.append("case %d mismatch %r" % (c["n"], m))
        nsep += sep
        npass += sep and negok
    line = "FR55 %s cases=%d match=%d bad=%d stopped=%d traced=%d neg_separating=%d neg_passed=%d" % (
        fam, len(meta), match, len(bad), stops, len(traced), nsep, npass)
    return line, bad[:20], traced[:20]


def env_counts():
    """Separating cases of the env family, by what they exercise (for the record)."""
    rnd = random.Random("r55-env")
    _, meta, _ = gen_env(rnd)
    adv = wrap = ret1 = bucket = 0
    for kind, act, e in meta:
        if kind != "clock":
            continue
        r, after = m_env(e, act)
        adv += after[0] != e[0]
        ret1 += r == 1
        bucket += after[3] != e[5]
    return "FR55 env advances=%d returns1=%d bucket_moves=%d" % (adv, ret1, bucket)


def cmd_check(d):
    global ENV_NEG
    allok = True
    runs = [(f, None) for f in FAMILIES] + [("env", "flat")]
    for fam, neg in runs:
        if neg:
            ENV_NEG = neg
        line, bad, traced = check_family(fam, d)
        if neg:
            line += " neg=" + neg
        elif fam == "env":
            line += " neg=ge"
        print(line)
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced:
            allok = False
    print(env_counts())
    print("FR55 result=%s" % ("ok" if allok else "FAIL"))


def cmd_manifest(d, write):
    rows = []
    for fam in FAMILIES:
        for ext in ("cases", "mem", "out"):
            p = os.path.join(d, "%s.%s" % (fam, ext))
            if os.path.exists(p):
                rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), os.path.basename(p)))
    p = os.path.join(d, "check.txt")
    if os.path.exists(p):
        rows.append("%s  %s" % (hashlib.sha256(open(p, "rb").read()).hexdigest(), "check.txt"))
    text = "\n".join(rows) + "\n"
    if write:
        with open(os.path.join(d, "manifest.sha256"), "w") as f:
            f.write(text)
    sys.stdout.write(text)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["cases", "check", "manifest"])
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir)
    elif a.cmd == "check":
        cmd_check(a.dir)
    else:
        cmd_manifest(a.dir, a.write)


if __name__ == "__main__":
    main(sys.argv[1:])

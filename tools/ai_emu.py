#!/usr/bin/env python3
"""Plan 0052 phase 1.1 (the monster AI machinery, `lane/r52`): five machinery functions of the pinned image run under
Ghidra's p-code emulator (ADR-0015, ADR-0021) with re/ghidra_scripts/EmuBoundary.java and compared with the models
below. No game run, no slot.

    python3 -I tools/ai_emu.py cases [--dir D]      write D/<family>.cases and D/<family>.mem for every family
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/ai_emu.py check [--dir D]      compare every D/<family>.out with its model, account for every
                                                    traced access, run the negative and site controls
    python3 -I tools/ai_emu.py manifest [--dir D] [--write]   sha256 of every case, memory and output file

Default D: workspace/logs/r52/emu. Every case draw comes from random.Random("r52-<family>"), so `cases` regenerates
identical files.

Families (function, what the claim covers):
  entry   0x005B15D0 (sub_005B15D0_MonAiEntryGet; ECX monster, EDX state word): the AI table row returned, for
          states 0..9 and 13..17 (states 10..12 call 0x00623470 first and are left out) and the MonStats `AI`
          value at record +0x1E over the s16 range around the table bound 148.
  dist    0x005DC530 (ECX unit, EDX x, [esp+4] y): the AI distance from a unit's position to a point,
          (2·max(|dx|,|dy|) + min(|dx|,|dy|)) / 2 (signed division, values non-negative), the position read from the
          path (+0x02/+0x06 u16) for unit types 0, 1 and 3, from path +0x0C/+0x10 (dwords) for types 2, 4 and 5, and
          0 for a missing path of types 0, 1, 3.
  ring    0x005DE200 (ECX game, EDX unit, [esp+4] r): the ring point and its draws, up to the call of 0x005DEB60
          (observed boundary, site 0x005DE313): one coordinate offset is r & 0xFF, the other RNG_RangeB(seed, r & 0xFF),
          which one by the parity of a first step, then one step per sign; the call's arguments (0, 2, x+dx, y+dy, 1, 0)
          and the unit seed at the boundary.
  typedraw 0x005DF7D0 (ECX game, EDX unit; target, byte, flag): the step on the unit seed and the path type it picks
          (5 when the new low byte is below 0x80, else 6), up to the call of 0x005DE190 (observed, site 0x005DF818):
          ECX the unit, EDX the type, arguments (0, byte).
  flee    0x005DEFE0 (ECX game, EDX unit; other, d, flag): the point d & 0xFF subtiles away from the other unit on each
          axis (sign of own - other, 0 when equal); for d & 0xFF > 5 the first boundary is 0x005DE190 (site
          0x005DF105, EDX 0, arguments (0, d)), else 0x005DEB60 (site 0x005DF122, arguments (0, 2, x', y', 1,
          flag ? 4 : 0)); a null other returns 0 with no call.

Not covered (ADR-0021): every callee after a boundary (the mode command 0x005DEB60, the override setter
0x005DE190), so neither what the command does with the point nor the later draws of 0x005DEB60's failure branch.
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
DEFAULT_DIR = os.path.join(ROOT, "workspace", "logs", "r52", "emu")

MUL = 0x6AC690C5
GAME = 0x12000000
UNIT = 0x12100000
PATH = 0x12200000
OTHER = 0x12300000
OPATH = 0x12400000
MDATA = 0x12500000
MREC = 0x12600000
STK_LO = 0x7FEFFC00
AI_TABLE = 0x0073CA18
AI_STATES = 0x0073D358
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
ALLOC = (0x0040B4B0, 0x0040B430, 0x0040B480)
FAMILIES = ("entry", "dist", "ring", "typedraw", "flee")


# ---------------------------------------------------------------------------------------------------- the RNG
def step(s):
    t = s[0] * MUL + s[1]
    s[0], s[1] = t & 0xFFFFFFFF, (t >> 32) & 0xFFFFFFFF


def range_b(s, n):
    if n < 1:
        return 0
    step(s)
    return s[0] % n


def u32(v):
    return v & 0xFFFFFFFF


def hx32(v):
    return struct.pack("<I", u32(v)).hex()


def hx16(v):
    return struct.pack("<H", v & 0xFFFF).hex()


# ---------------------------------------------------------------------------------------------- unit positions
DIRECT = (2, 4, 5)


def put_unit(lines, base, path, typ, x, y, seed=None, has_path=True):
    lines.append("w %08x %s" % (base, hx32(typ)))
    lines.append("w %08x %s" % (base + 0x2C, hx32(path if has_path else 0)))
    if seed is not None:
        lines.append("w %08x %s%s" % (base + 0x20, hx32(seed[0]), hx32(seed[1])))
    if has_path:
        if typ in DIRECT:
            lines.append("w %08x %s" % (path + 0x0C, hx32(x)))
            lines.append("w %08x %s" % (path + 0x10, hx32(y)))
        else:
            lines.append("w %08x %s" % (path + 0x02, hx16(x)))
            lines.append("w %08x %s" % (path + 0x06, hx16(y)))


def pos(typ, x, y, has_path=True):
    if not has_path:
        return 0, 0
    if typ in DIRECT:
        return x, y
    return x & 0xFFFF, y & 0xFFFF


def rand_pos(rnd, typ):
    if typ in DIRECT:
        return rnd.randrange(0, 1 << 20), rnd.randrange(0, 1 << 20)
    return rnd.randrange(0, 1 << 16), rnd.randrange(0, 1 << 16)


def s32(v):
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v & 0x80000000 else v


# -------------------------------------------------------------------------------------------------- the models
def m_entry(state, ai, neg=False):
    if state != 0:
        return AI_STATES + 16 * state
    a = ai - 0x10000 if ai & 0x8000 else ai
    if neg:                      # control: no upper bound
        return AI_TABLE + 16 * a if a >= 0 else AI_TABLE
    if 0 <= a < 148:
        return AI_TABLE + 16 * a
    return AI_TABLE


def m_dist(ux, uy, x, y, neg=False):
    dx, dy = abs(s32(ux - x)), abs(s32(uy - y))
    if neg:                      # control: max + min
        return (dx + dy) // 2
    if dx > dy:
        return (dy + 2 * dx) // 2
    return (dx + 2 * dy) // 2


def m_ring(x, y, r, seed, neg=False):
    s = list(seed)
    r &= 0xFF
    step(s)
    even = (s[0] & 1) == 0
    if neg:
        even = not even
    if even:
        dy = r
        dx = range_b(s, r)
    else:
        dx = r
        dy = range_b(s, dx)
    step(s)
    if s[0] & 1:
        dx = -dx
    step(s)
    if s[0] & 1:
        dy = -dy
    return u32(x + dx), u32(y + dy), s


def m_typedraw(seed, neg=False):
    s = list(seed)
    step(s)
    t = 5 if (s[0] & 0xFF) < 0x80 else 6
    if neg:
        t = 11 - t
    return t, s


def sgn(v):
    return (v > 0) - (v < 0)


def m_flee(ox, oy, tx, ty, d, flag, neg=False):
    b = d & 0xFF
    sx, sy = sgn(s32(ox - tx)), sgn(s32(oy - ty))
    if neg:
        sx, sy = -sx, -sy
    pt = (u32(ox + b * sx), u32(oy + b * sy))
    if b > 5:
        return ("ovr", 0x005DF105, [0, d])
    return ("cmd", 0x005DF122, [0, 2, pt[0], pt[1], 1, 4 if flag else 0])


# --------------------------------------------------------------------------------------------- case writers
def mem_spec(observe=()):
    out = ["observe %08x" % a for a in observe]
    out += ["guard %08x" % a for a in FATAL + ALLOC]
    return out


def gen_entry(rnd):
    cases, meta = [], []
    states = [0] * 40 + list(range(1, 10)) + list(range(13, 18))
    ais = [0, 1, 61, 67, 146, 147, 148, 149, 0x7FFF, 0x8000, 0xFFFF, 0xFFFE]
    for st in states:
        for ai in (ais if st == 0 else [rnd.randrange(0, 148)]):
            meta.append((st, ai))
    for _ in range(60):
        meta.append((0, rnd.randrange(0, 0x10000)))
    for st, ai in meta:
        lines = ["w %08x %s" % (UNIT, hx32(1)), "w %08x %s" % (UNIT + 0x14, hx32(MDATA)),
                 "w %08x %s" % (MDATA, hx32(MREC)), "w %08x %s" % (MREC + 0x1E, hx16(ai)),
                 "call 005b15d0 %08x %08x" % (UNIT, st)]
        cases.append(lines)
    return cases, meta, mem_spec()


def gen_dist(rnd):
    cases, meta = [], []
    for k in range(240):
        typ = k % 6
        has_path = not (typ not in DIRECT and k % 17 == 0)
        ux, uy = rand_pos(rnd, typ)
        if k % 5 == 0:
            x, y = ux + rnd.randrange(-60, 61), uy + rnd.randrange(-60, 61)
        else:
            x, y = rnd.randrange(0, 1 << 16), rnd.randrange(0, 1 << 16)
        lines = []
        put_unit(lines, UNIT, PATH, typ, ux, uy, has_path=has_path)
        lines.append("call 005dc530 %08x %08x %08x" % (UNIT, u32(x), u32(y)))
        cases.append(lines)
        meta.append((typ, ux, uy, has_path, u32(x), u32(y)))
    return cases, meta, mem_spec()


def gen_ring(rnd):
    cases, meta = [], []
    for k in range(200):
        typ = (0, 1, 2, 4)[k % 4]
        ux, uy = rand_pos(rnd, typ)
        r = rnd.choice([0, 1, 2, 4, 5, 10, 12, 19, rnd.randrange(0, 256)])
        if k % 7 == 0:
            r |= rnd.randrange(1, 1 << 24) << 8          # high bits the code masks off
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        lines = []
        put_unit(lines, UNIT, PATH, typ, ux, uy, seed=seed)
        lines += ["d %08x 1024" % STK_LO, "d %08x 8" % (UNIT + 0x20),
                  "call 005de200 %08x %08x %08x" % (GAME, UNIT, r)]
        cases.append(lines)
        meta.append((typ, ux, uy, r, seed))
    return cases, meta, mem_spec([0x005DEB60])


def gen_typedraw(rnd):
    cases, meta = [], []
    for k in range(120):
        seed = (rnd.randrange(1 << 32), rnd.randrange(1 << 32))
        tgt, byte, flag = rnd.randrange(1, 1 << 31), rnd.randrange(0, 256), rnd.randrange(0, 2)
        lines = ["w %08x %s%s" % (UNIT + 0x20, hx32(seed[0]), hx32(seed[1])),
                 "d %08x 1024" % STK_LO, "d %08x 8" % (UNIT + 0x20),
                 "call 005df7d0 %08x %08x %08x %08x %08x" % (GAME, UNIT, tgt, byte, flag)]
        cases.append(lines)
        meta.append((seed, tgt, byte, flag))
    return cases, meta, mem_spec([0x005DE190])


def gen_flee(rnd):
    cases, meta = [], []
    for k in range(200):
        typ, otyp = (0, 1, 2, 4)[k % 4], (0, 1, 2, 4, 5, 3)[k % 6]
        ox, oy = rand_pos(rnd, typ)
        if k % 3 == 0:
            tx, ty = ox + rnd.choice([-3, -1, 0, 1, 3]), oy + rnd.choice([-2, 0, 2])
            if otyp not in DIRECT:
                tx, ty = tx & 0xFFFF, ty & 0xFFFF
        else:
            tx, ty = rand_pos(rnd, otyp)
        d = rnd.choice([0, 1, 3, 5, 6, 7, 19, 40, rnd.randrange(0, 256)])
        if k % 9 == 0:
            d |= rnd.randrange(1, 1 << 20) << 8
        flag = rnd.randrange(0, 2)
        null_other = k % 25 == 0
        lines = []
        put_unit(lines, UNIT, PATH, typ, ox, oy)
        if not null_other:
            put_unit(lines, OTHER, OPATH, otyp, tx, ty)
        lines += ["d %08x 1024" % STK_LO,
                  "call 005defe0 %08x %08x %08x %08x %08x" % (GAME, UNIT, 0 if null_other else OTHER, d, flag)]
        cases.append(lines)
        meta.append((typ, ox, oy, otyp, tx, ty, d, flag, null_other))
    return cases, meta, mem_spec([0x005DE190, 0x005DEB60])


GEN = {"entry": gen_entry, "dist": gen_dist, "ring": gen_ring, "typedraw": gen_typedraw, "flee": gen_flee}


def cmd_cases(d):
    os.makedirs(d, exist_ok=True)
    for fam in FAMILIES:
        rnd = random.Random("r52-" + fam)
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
                c["obs"] = int(p[4], 16)
                kv = dict(x.split("=") for x in p[5:])
                c["regs"] = {k: int(v, 16) for k, v in kv.items() if k != "steps"}
            else:
                kv = dict(x.split("=") for x in p[3:])
                c["eax"] = int(kv["eax"], 16)
                c["pop"] = int(kv["pop"])
            calls.append(c)
        elif p[0] == "A":
            calls[-1]["args"] = bytes.fromhex(p[1])
        elif p[0] == "D":
            calls[-1]["dumps"][int(p[1], 16)] = bytes.fromhex(p[2]) if len(p) > 2 else b""
        elif p[0] in ("R", "W"):
            traced.append(ln.strip())
    return calls, traced


def args_of(c, n):
    a = c.get("args", b"")
    return [struct.unpack_from("<I", a, 4 + 4 * i)[0] for i in range(n)], struct.unpack_from("<I", a, 0)[0]


def seed_of(c):
    b = c["dumps"].get(UNIT + 0x20)
    return list(struct.unpack("<II", b)) if b else None


def check_family(fam, d):
    rnd = random.Random("r52-" + fam)
    _, meta, _ = GEN[fam](rnd)
    calls, traced = read_out(os.path.join(d, fam + ".out"))
    bad, match, stops, nsep, npass, sites, spass = [], 0, 0, 0, 0, 0, 0
    if len(calls) != len(meta):
        bad.append("case count %d != %d" % (len(calls), len(meta)))
    for c, m in zip(calls, meta):
        if "stop" in c:
            stops += 1
            bad.append("case %d STOP %s" % (c["n"], c["stop"]))
            continue
        ok, sep, negok, site_ok = check_case(fam, c, m)
        match += ok
        if not ok:
            bad.append("case %d mismatch %r" % (c["n"], m))
        nsep += sep
        npass += sep and negok
        if site_ok is not None:
            sites += 1
            spass += site_ok
    line = "AI52 %s cases=%d match=%d bad=%d stopped=%d traced=%d neg_separating=%d neg_passed=%d" % (
        fam, len(meta), match, len(bad), stops, len(traced), nsep, npass)
    if fam in ("ring", "typedraw", "flee"):
        line += " boundary_cases=%d site_control_passed=%d" % (sites, spass)
    return line, bad[:20], traced[:20]


def check_case(fam, c, m):
    """(model matches, the negative control predicts differently, the negative control matches the binary,
    the site control (the expected call site moved by one byte) matches the binary; None without a boundary)."""
    if fam == "entry":
        st, ai = m
        want, nwant = m_entry(st, ai), m_entry(st, ai, neg=True)
        return c.get("eax") == want, want != nwant, c.get("eax") == nwant, None
    if fam == "dist":
        typ, ux, uy, hp, x, y = m
        px, py = pos(typ, ux, uy, hp)
        want, nwant = u32(m_dist(px, py, x, y)), u32(m_dist(px, py, x, y, neg=True))
        return c.get("eax") == want and c.get("pop") == 4, want != nwant, c.get("eax") == nwant, None
    if fam == "ring":
        typ, ux, uy, r, seed = m
        px, py = pos(typ, ux, uy)
        x, y, s = m_ring(px, py, r, seed)
        nx, ny, ns = m_ring(px, py, r, seed, neg=True)
        if c.get("obs") != 0x005DEB60:
            return False, False, False, None
        a, ret = args_of(c, 6)
        got = (a, seed_of(c))
        ok = got == ([0, 2, x, y, 1, 0], s) and ret == 0x005DE313
        sep = (nx, ny, ns) != (x, y, s)
        return ok, sep, got == ([0, 2, nx, ny, 1, 0], ns), got[0] == [0, 2, x, y, 1, 0] and ret == 0x005DE314
    if fam == "typedraw":
        seed, tgt, byte, flag = m
        t, s = m_typedraw(seed)
        nt, _ = m_typedraw(seed, neg=True)
        if c.get("obs") != 0x005DE190:
            return False, False, False, None
        a, ret = args_of(c, 2)
        ok = (c["regs"]["ecx"] == UNIT and c["regs"]["edx"] == t and a == [0, byte] and ret == 0x005DF818
              and seed_of(c) == s)
        return ok, True, c["regs"]["edx"] == nt, ret == 0x005DF819
    if fam == "flee":
        typ, ox, oy, otyp, tx, ty, d, flag, null_other = m
        if null_other:
            return c.get("eax") == 0 and "obs" not in c, False, False, None
        px, py = pos(typ, ox, oy)
        qx, qy = pos(otyp, tx, ty)
        kind, site, want = m_flee(px, py, qx, qy, d, flag)
        _, _, nwant = m_flee(px, py, qx, qy, d, flag, neg=True)
        exp_obs = 0x005DE190 if kind == "ovr" else 0x005DEB60
        if c.get("obs") != exp_obs:
            return False, False, False, None
        a, ret = args_of(c, len(want))
        ok = a == want and ret == site
        if kind == "ovr":
            ok = ok and c["regs"]["edx"] == 0 and c["regs"]["ecx"] == UNIT
        return ok, nwant != want, a == nwant and ret == site, ret == site + 1
    raise ValueError(fam)


def cmd_check(d):
    allok = True
    for fam in FAMILIES:
        line, bad, traced = check_family(fam, d)
        print(line)
        for b in bad:
            print("  BAD", b)
        for t in traced:
            print("  TRACED", t)
        if bad or traced:
            allok = False
    print("AI52 result=%s" % ("ok" if allok else "FAIL"))


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

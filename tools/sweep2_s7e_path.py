#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S7e part 2 (`lane/n66u`): small emulated reproductions (ADR-0015, ADR-0021) for the
path/README rows 4, 19 and 71 and the drlg/lifecycle wanderer rows 3, 72-76, run with re/ghidra_scripts/EmuBoundary.java and compared with the models below.

    python3 -I tools/sweep2_s7e_path.py cases [--dir D] [--tag T]
    GHIDRA_PROJ_DIR=... GHIDRA_HEADLESS_MAXMEM=3G tools/ghidra.sh emuboundary D/<f>.cases D/<f>.mem > D/<f>.out
    python3 -I tools/sweep2_s7e_path.py check [--dir D]
    python3 -I tools/sweep2_s7e_path.py manifest [--dir D] [--write]

Default D: workspace/logs/n66u/s7e/path. Case draws come from random.Random("<tag>-<family>") (default tag `n66u`).

Families:
  facing  sub_006488A0_PathSetFacing(path, dir), ret 8: a null path, and a declared path record with random bytes, dir
          any 32-bit value. The model: path = 0 -> nothing; else +0x64 and +0x65 <- dir & 0x3F (path/README H3).
  mreset  sub_00648DC0_PathMoveReset(path), ret 4: a declared path record with random bytes, its unit (+0x30) a declared
          unit whose type word is 0..4, flags +0x34 with bits 0x8000 and 0x2000 set or clear. PathSetType 0x00648CF0 is
          an observed boundary (ADR-0021): the checker asserts the boundary, its call site (the return address) and its
          two stack arguments (path, type). The model (path/README B4): under 0x8000, +0x7C <- +0x80; then a player
          (type 0) -> PathSetType(path, 7); else under 0x2000 -> PathSetType(path, +0x40); else return.
          Domain: a non-null unit (a null unit takes the fatal path 0x00648DCD, guarded, not a claim here).
  wtick   sub_0054F060_RoomWandererTick (ECX game, EDX room), plain ret: the room's seed (+0x6C low, +0x70 high), +0x78,
          the level id through +0x10 -> +0x58 -> +0x1D0 (sub_0061A1B0_RoomGetLevelId, 0x0066BAB0), LEVELS_GetRecord
          0x0061DB70 over a declared DataTables (g_pDataTables 0x00744304 -> +0xC58 records of 0x220, +0xC5C count) and the
          record's MonWndr byte +0x2E. WandererRoll 0x0054EFF0 is an observed boundary (EAX room; game, level, record).
          Model (drlg/lifecycle I1): Step(seed); low & 0x7FFF != 0 -> return; +0x78 != 0 -> return; MonWndr = 0 -> return;
          else the roll. Domain: a non-null room, a level id inside 1 .. count - 1 (else the record is 0 and +0x2E is
          read at 0x2E).
  wroll   sub_0054EFF0_WandererRoll (EAX room; game, level, record), ret 0xC: Step(seed); low mod 100 >= 3 (unsigned)
          -> return; region <- [game + 0xF0 + 4 level] (sub_00547BB0_MonRegionGet); region+0x2C4 >= 3 (signed) -> return;
          else WandererSpawn 0x0054EF50, an observed boundary (EAX record; region). Domain: a non-null region.
Controls (each must fail every case it separates): facing `mask7f`, `oneonly`; mreset `nospeedflag` (the copy made
always), `noplayer` (the type-0 test ignored), `flagfirst` (the 0x2000 test before the player test); wtick `mask16`
(0xFFFF), `no78` (+0x78 ignored), `nownd` (MonWndr ignored); wroll `unsignedcnt` (the count compared unsigned),
`cnt2` (the count bound 2), `roll4` (the roll bound 4).
Stdlib only.
"""
import argparse
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import frame_queue_emu as fq  # noqa: E402

M32 = 0xFFFFFFFF
DEFAULT_DIR = os.path.join("workspace", "logs", "n66u", "s7e", "path")
PATH, UNIT = 0x15000000, 0x15100000
F_FACING, F_MRESET, F_SETTYPE = 0x006488A0, 0x00648DC0, 0x00648CF0
SITE_PLAYER, SITE_FLAG = 0x00648E0F, 0x00648E25
FATAL = (0x00408090, 0x00408A60, 0x00681E09)
COUNTS = dict(facing=200, mreset=300, wtick=300, wroll=300)
CONTROLS = dict(facing=("mask7f", "oneonly"), mreset=("nospeedflag", "noplayer", "flagfirst"),
                wtick=("mask16", "no78", "nownd"), wroll=("unsignedcnt", "cnt2", "roll4"))
ROOM, DROOM, LEVEL, GAME, DT, LVLS, REGION = (0x15400000, 0x15400200, 0x15400400, 0x15500000, 0x15600000, 0x15700000,
                                              0x15800000)
NLEV = 40
F_TICK, F_ROLL, F_SPAWN = 0x0054F060, 0x0054EFF0, 0x0054EF50
SITE_ROLL, SITE_SPAWN = 0x0054F0C4, 0x0054F053
A = 0x6AC690C5


def step(lo, hi):
    x = lo * A + hi
    return x & M32, x >> 32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def mem_spec(f):
    out = ["guard %08x" % a for a in FATAL]
    if f in ("wtick", "wroll"):
        out += ["bytes %08x %s" % (ROOM, "00" * 0x600), "bytes %08x %s" % (GAME, "00" * 0x200),
                "bytes %08x %s" % (DT, "00" * 0x1000), "bytes %08x %s" % (LVLS, "00" * (0x220 * NLEV)),
                "bytes %08x %s" % (REGION, "00" * 0x300), "dword 00744304 %08x" % DT,
                "observe %08x" % (F_ROLL if f == "wtick" else F_SPAWN)]
        return out
    out += ["bytes %08x %s" % (PATH, "00" * 0x100), "bytes %08x %s" % (UNIT, "00" * 0x10)]
    if f == "mreset":
        out.append("observe %08x" % F_SETTYPE)
    return out


def seed_to(rnd, target):
    """A (low, high) whose step gives `target` as the new low word."""
    lo = rnd.getrandbits(32)
    return lo, (target - lo * A) & M32


def gen_wand(f, rnd):
    cases = []
    for i in range(COUNTS[f]):
        if f == "wtick":
            r = rnd.random()
            if r < 0.5:
                t = (rnd.getrandbits(17) << 15) & M32                    # low & 0x7FFF = 0, bit 15 either way
            elif r < 0.6:
                t = (rnd.getrandbits(16) << 16) | rnd.choice((0x8000, 0x4000, 1))
            else:
                t = rnd.getrandbits(32)
            lo, hi = seed_to(rnd, t)
            lev = rnd.randrange(1, NLEV)
            c = dict(f=f, lo=lo, hi=hi, r78=rnd.choice((0, 0, 0, 1, rnd.getrandbits(32))), lev=lev,
                     wndr=rnd.choice((0, 1, 1, 2, 0xFF)), cnt=NLEV)
        else:
            t = rnd.getrandbits(32)
            if rnd.random() < 0.7:
                t = (t // 100) * 100 + rnd.choice((0, 1, 2, 3, 3))
                t &= M32
                if t % 100 > 3:
                    t = 0
            lo, hi = seed_to(rnd, t)
            lev = rnd.randrange(0, 0x40)
            n = rnd.choice((0, 1, 2, 2, 3, 3, 4, 0xFFFFFFFF, 0x80000000, rnd.getrandbits(32)))
            c = dict(f=f, lo=lo, hi=hi, lev=lev, n=n, rec=LVLS + 0x220 * rnd.randrange(NLEV))
        cases.append(c)
    return cases


def wand_lines(c):
    L = []
    w = lambda a, v: L.append("w %08x %s" % (a, struct.pack("<I", v & M32).hex()))
    w(ROOM + 0x6C, c["lo"])
    w(ROOM + 0x70, c["hi"])
    if c["f"] == "wtick":
        w(ROOM + 0x78, c["r78"])
        w(ROOM + 0x10, DROOM)
        w(DROOM + 0x58, LEVEL)
        w(LEVEL + 0x1D0, c["lev"])
        w(DT + 0xC58, LVLS)
        w(DT + 0xC5C, c["cnt"])
        L.append("w %08x %02x" % (LVLS + 0x220 * c["lev"] + 0x2E, c["wndr"]))
        L.append("d %08x 8" % (ROOM + 0x6C))
        L.append("call %08x %08x %08x" % (F_TICK, GAME, ROOM))
    else:
        w(GAME + 0xF0 + 4 * c["lev"], REGION)
        w(REGION + 0x2C4, c["n"])
        L.append("d %08x 8" % (ROOM + 0x6C))
        L.append("r eax %08x" % ROOM)
        L.append("call %08x 00000000 00000000 %08x %08x %08x" % (F_ROLL, GAME, c["lev"], c["rec"]))
    return L


def wand_model(c, ctl=None):
    """-> (seed bytes after, boundary (pc, site, eax, [args]) or None, pop)."""
    lo, hi = step(c["lo"], c["hi"])
    sb = struct.pack("<II", lo, hi)
    if c["f"] == "wtick":
        if lo & (0xFFFF if ctl == "mask16" else 0x7FFF):
            return sb, None, 0
        if c["r78"] and ctl != "no78":
            return sb, None, 0
        if c["wndr"] == 0 and ctl != "nownd":
            return sb, None, 0
        return sb, (F_ROLL, SITE_ROLL, ROOM, [GAME, c["lev"], LVLS + 0x220 * c["lev"]]), None
    if lo % 100 >= (4 if ctl == "roll4" else 3):
        return sb, None, 0xC
    n = c["n"] if ctl == "unsignedcnt" else s32(c["n"])
    if n >= (2 if ctl == "cnt2" else 3):
        return sb, None, 0xC
    return sb, (F_SPAWN, SITE_SPAWN, c["rec"], [REGION]), None


def wand_compare(c, o, ctl=None):
    sb, obs, pop = wand_model(c, ctl)
    if "stop" in o:
        return False, "STOP " + o["stop"]
    if obs:
        pc, site, eax, args = obs
        if o.get("obs_pc") != pc:
            return False, "no boundary"
        st = o["stack"]
        got = list(struct.unpack_from("<%dI" % len(args), st, 4))
        if struct.unpack_from("<I", st, 0)[0] != site or got != args or int(o["regs"]["eax"], 16) != eax:
            return False, "boundary %08x %r eax %s" % (struct.unpack_from("<I", st, 0)[0], got, o["regs"].get("eax"))
    else:
        if "obs_pc" in o:
            return False, "unexpected boundary"
        if o.get("pop") != pop:
            return False, "pop %s" % o.get("pop")
    if o["dumps"].get(ROOM + 0x6C) != sb:
        return False, "seed differs"
    return True, ""


def wand_label(c):
    lo, _ = step(c["lo"], c["hi"])
    if c["f"] == "wtick":
        if lo & 0x7FFF:
            return "gate closed%s" % (" (bit 15 clear)" if not lo & 0xFFFF else "")
        if lo & 0x8000:
            k = "gate open bit15"
        else:
            k = "gate open"
        return "%s r78=%s wndr=%s" % (k, "0" if not c["r78"] else "set", "0" if not c["wndr"] else "set")
    if lo % 100 >= 3:
        return "roll %s" % ("3" if lo % 100 == 3 else ">3")
    return "roll<3 count %d" % s32(c["n"]) if -2 <= s32(c["n"]) <= 5 else "roll<3 count other %s" % ("neg" if s32(c["n"]) < 0 else "pos")


def gen(f, rnd):
    if f in ("wtick", "wroll"):
        return gen_wand(f, rnd)
    cases = []
    for i in range(COUNTS[f]):
        body = bytearray(rnd.getrandbits(8) for _ in range(0x100))
        if f == "facing":
            p = 0 if i % 10 == 0 else PATH
            d = rnd.choice([rnd.randrange(64), rnd.randrange(64, 256), rnd.getrandbits(32)])
            cases.append(dict(f=f, body=body.hex(), p=p, dir=d))
            continue
        utype = rnd.choice((0, 0, 1, 1, 2, 3, 4))
        struct.pack_into("<I", body, 0x30, UNIT)
        fl = struct.unpack_from("<I", body, 0x34)[0] & ~0xA000
        fl |= rnd.choice((0, 0x8000)) | rnd.choice((0, 0x2000))
        struct.pack_into("<I", body, 0x34, fl)
        cases.append(dict(f=f, body=body.hex(), utype=utype))
    return cases


def case_lines(c):
    if c["f"] in ("wtick", "wroll"):
        return wand_lines(c)
    lines = ["w %08x %s" % (PATH, c["body"])]
    if c["f"] == "facing":
        lines.append("d %08x %d" % (PATH, 0x100))
        lines.append("call %08x 00000000 00000000 %08x %08x" % (F_FACING, c["p"], c["dir"] & M32))
    else:
        lines.append("w %08x %s" % (UNIT, struct.pack("<I", c["utype"]).hex()))
        lines.append("d %08x %d" % (PATH, 0x100))
        lines.append("call %08x 00000000 00000000 %08x" % (F_MRESET, PATH))
    return lines


def model(c, ctl=None):
    """-> (path bytes after, boundary (site, [args]) or None, pop)."""
    if c["f"] in ("wtick", "wroll"):
        return wand_model(c, ctl)
    b = bytearray.fromhex(c["body"])
    if c["f"] == "facing":
        if c["p"]:
            v = c["dir"] & (0x7F if ctl == "mask7f" else 0x3F)
            b[0x64] = v & 0xFF
            if ctl != "oneonly":
                b[0x65] = v & 0xFF
        return bytes(b), None, 8
    fl = struct.unpack_from("<I", b, 0x34)[0]
    if fl & 0x8000 or ctl == "nospeedflag":
        b[0x7C:0x80] = b[0x80:0x84]
    player = c["utype"] == 0 and ctl != "noplayer"
    flag = fl & 0x2000
    if ctl == "flagfirst" and flag:
        return bytes(b), (SITE_FLAG, [PATH, struct.unpack_from("<I", b, 0x40)[0]]), None
    if player:
        return bytes(b), (SITE_PLAYER, [PATH, 7]), None
    if flag:
        return bytes(b), (SITE_FLAG, [PATH, struct.unpack_from("<I", b, 0x40)[0]]), None
    return bytes(b), None, 4


def compare(c, o, ctl=None):
    if c["f"] in ("wtick", "wroll"):
        return wand_compare(c, o, ctl)
    b, obs, pop = model(c, ctl)
    if "stop" in o:
        return False, "STOP " + o["stop"]
    if obs:
        if o.get("obs_pc") != F_SETTYPE:
            return False, "no boundary"
        st = o["stack"]
        site = struct.unpack_from("<I", st, 0)[0]
        args = list(struct.unpack_from("<2I", st, 4))
        if site != obs[0] or args != obs[1]:
            return False, "boundary site %08x args %r" % (site, args)
    else:
        if "obs_pc" in o:
            return False, "unexpected boundary"
        if o.get("pop") != pop:
            return False, "pop %s" % o.get("pop")
    if o["dumps"].get(PATH) != b:
        return False, "path bytes differ"
    return True, ""


def label(c):
    if c["f"] in ("wtick", "wroll"):
        return wand_label(c)
    if c["f"] == "facing":
        return "null path" if not c["p"] else ("dir<64" if c["dir"] < 64 else "dir>=64")
    fl = struct.unpack_from("<I", bytes.fromhex(c["body"]), 0x34)[0]
    return "type%d speed%d flag2000=%d" % (c["utype"], 1 if fl & 0x8000 else 0, 1 if fl & 0x2000 else 0)


def cmd_cases(d, tag):
    os.makedirs(d, exist_ok=True)
    for f in COUNTS:
        cs = gen(f, random.Random("%s-%s" % (tag, f)))
        with open(os.path.join(d, f + ".cases"), "w") as fh:
            for c in cs:
                fh.write("\n".join(case_lines(c)) + "\n")
        open(os.path.join(d, f + ".mem"), "w").write("\n".join(mem_spec(f)) + "\n")
        json.dump(dict(tag=tag), open(os.path.join(d, f + ".meta"), "w"))
        print("CASES %s %d" % (f, len(cs)))


def cmd_check(d):
    bad_total = 0
    for f in COUNTS:
        tag = json.load(open(os.path.join(d, f + ".meta")))["tag"]
        cs = gen(f, random.Random("%s-%s" % (tag, f)))
        outs, traced = fq.read_out(os.path.join(d, f + ".out"))
        bad = 0 if len(outs) == len(cs) else 1
        labels, sep, passed = {}, {k: 0 for k in CONTROLS[f]}, {k: 0 for k in CONTROLS[f]}
        for i, (c, o) in enumerate(zip(cs, outs)):
            ok, why = compare(c, o)
            if not ok:
                bad += 1
                if bad <= 10:
                    print("MISMATCH %s %d %s" % (f, i, why))
            k = label(c)
            labels[k] = labels.get(k, 0) + 1
            w = model(c)
            for ct in CONTROLS[f]:
                if model(c, ct) != w:
                    sep[ct] += 1
                    passed[ct] += compare(c, o, ct)[0]
        print("S7E-PATH %s cases=%d outputs=%d mismatches=%d traced=%d" % (f, len(cs), len(outs), bad, len(traced)))
        for k in sorted(labels):
            print("S7E-PATH %s outcome %s: %d" % (f, k, labels[k]))
        for ct in CONTROLS[f]:
            print("S7E-PATH %s control %s separating=%d passed=%d" % (f, ct, sep[ct], passed[ct]))
        for t in traced[:10]:
            print("UNACCOUNTED %s" % t)
        bad_total += bad + len(traced) + sum(passed.values())
    print("S7E-PATH result=%s" % ("ok" if bad_total == 0 else "BAD"))
    return 0 if bad_total == 0 else 1


def cmd_manifest(d, write):
    names = sorted(x for x in os.listdir(d) if not x.startswith("manifest") and os.path.isfile(os.path.join(d, x)))
    lines = ["%s  %s" % (hashlib.sha256(open(os.path.join(d, x), "rb").read()).hexdigest(), x) for x in names]
    if write:
        open(os.path.join(d, "manifest.sha256"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("cases", "check", "manifest"))
    ap.add_argument("--dir", default=DEFAULT_DIR)
    ap.add_argument("--tag", default="n66u")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "cases":
        cmd_cases(a.dir, a.tag)
        return 0
    if a.cmd == "check":
        return cmd_check(a.dir)
    cmd_manifest(a.dir, a.write)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

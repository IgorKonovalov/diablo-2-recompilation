#!/usr/bin/env python3
"""Static scans and derived models behind docs/findings/anim/0003-movement-gates.md (plan 0050 Phase 1, batch P1.3).

Usage:
  python3 -I tools/anim_moves.py tables <game.exe>     image tables and pinned instructions the finding cites
  python3 -I tools/anim_moves.py calls <game.exe>      call sites of the movement and gate functions, and the
                                                       object "FrameCnt >> 8" event-queue sites
  python3 -I tools/anim_moves.py model <merged root>   derived functions (the per-frame step, frames to a point,
                                                       the knockback point, the get-hit draw count), wrap bounds
                                                       and the data bounds they need (counts and maxima only)

Sections (one `SCAN <section> ...` summary line each):
  tables  DIR <i> x y idx: g_PathDirTable 0x006EB7E0 (128 x 12 B) with the norm range; GHD <hc> <divisor>: the
          get-hit divisor jump table 0x0057CBF8 (12 entries, hit class 1..12); HCE <i> <packet off> <class>: the
          element table 0x006E16D8 read by HitClassPick; PLAN <type> <fn>: the path planners 0x006EB6D8;
          LEAVE req/cur: the two byte tables of the mode-leave test 0x0057EDD0; OBJSHL: the eight `shl [edi+k],8`
          of the Objects loader at 0x00640E33; OBJEV <k> <fn>: g_ObjEventFns 0x006E19B0; PVS: the PathVelocityStep
          instructions (imul/sar) at 0x0065032A.
  calls   CALL <target> <site> in <function start>, CALLS <target> <n>; FC8 <site>: a `mov r,[r+0xdc]` followed
          within 11 instructions by `shr r,8` and a call of UnitQueueEvent 0x005417D0.
  model   STEP: per-frame step of a path speed v on the axis and the diagonal direction; WALK/RUN per class from
          CharStats; FRAMES: frames to a point d subtiles away; KB: the knockback point and its frames; GETHIT: draws
          and probability per damage band; EDGE: the 32-bit bounds of the step products.
Model rules are the code's (the finding's sections); every division is stated there. Stdlib plus objdump.
"""
import bisect
import csv
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_scan as AS  # noqa: E402

M32 = 0xFFFFFFFF
DIRT = 0x006EB7E0
GHD = 0x0057CBF8
HCE = 0x006E16D8
PLAN = 0x006EB6D8
LEAVE_REQ, LEAVE_REQ_T = 0x0057EE78, 0x0057EE70
LEAVE_CUR, LEAVE_CUR_T = 0x0057EEA8, 0x0057EE8C
OBJEV = 0x006E19B0

TARGETS = {
    0x00554CA0: "sub_00554CA0_UnitMoveStep",
    0x00650840: "sub_00650840_PathStep",
    0x006502D0: "sub_006502D0_PathVelocityStep",
    0x00648690: "sub_00648690_PathSetSpeed",
    0x006486D0: "sub_006486D0_PathSetMaxSpeed",
    0x00648700: "sub_00648700_PathSetAccel",
    0x0056E5B0: "sub_0056E5B0_UnitWalkVelocity",
    0x00620E80: "sub_00620E80_RunVelocityStat",
    0x0057F240: "sub_0057F240_RunStaminaDrain",
    0x0057CB00: "sub_0057CB00_GetHitRoll",
    0x0057CE30: "sub_0057CE30_HitClassPick",
    0x00623C20: "sub_00623C20_UnitBaseHitClass",
    0x0057CEE0: "COMBAT_GetHit",
    0x0057EEC0: "sub_0057EEC0_PlayerModeAllowed",
    0x0057EDD0: "sub_0057EDD0_PlrModeLeaveOk",
    0x0057ED70: "sub_0057ED70_PlrModeEndPending",
    0x005809D0: "sub_005809D0_PlayerModeCmd",
    0x00580A70: "PLAYER_ModeCmdUnit",
    0x0046C140: "sub_0046C140_MonModeAllowed",
    0x0057AAE0: "COMBAT_ApplyStun",
    0x0056EF90: "SKILLS_SetDelayState",
}


def h(v):
    return "0x%08X" % v


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def cdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


# ------------------------------------------------------------------------------------------------- tables
def cmd_tables(exe):
    pe = AS.PE(exe)
    lo, hi = None, None
    for i in range(128):
        x, y, idx = struct.unpack("<3i", pe.rd(DIRT + 12 * i, 12))
        n2 = x * x + y * y
        lo = n2 if lo is None else min(lo, n2)
        hi = n2 if hi is None else max(hi, n2)
        if i in (0, 1, 32, 64, 96, 126, 127):
            print("DIR %d x=%d y=%d idx=%d" % (i, x, y, idx))
    print("DIR norm2_min=%d norm2_max=%d (4096^2=%d)" % (lo, hi, 4096 * 4096))
    tgt = {0x57CB52: 8, 0x57CB59: 0x20, 0x57CB60: 0x40, 0x57CB67: 0x10}
    t = struct.unpack("<12I", pe.rd(GHD, 48))
    for k, a in enumerate(t):
        print("GHD hc=%d divisor=%d (case %s)" % (k + 1, tgt.get(a, -1), h(a)))
    for i in range(8):
        off, cls = struct.unpack("<2I", pe.rd(HCE + 8 * i, 8))
        print("HCE %d packet+0x%02X class=0x%02X" % (i, off, cls))
    for k in range(16):
        print("PLAN %d %s" % (k, h(pe.dw(PLAN + 4 * k))))
    req = list(pe.rd(LEAVE_REQ, 18))
    reqt = struct.unpack("<2I", pe.rd(LEAVE_REQ_T, 8))
    cur = list(pe.rd(LEAVE_CUR, 19))
    curt = struct.unpack("<7I", pe.rd(LEAVE_CUR_T, 28))
    print("LEAVE req=%s targets=%s" % (req, [h(x) for x in reqt]))
    print("LEAVE cur=%s targets=%s" % (cur, [h(x) for x in curt]))
    code = pe.rd(0x00640E33, 0x38)
    shl = [code[i:i + 7] for i in range(0, 0x38, 7)]
    offs = [struct.unpack("<I", c[2:6])[0] for c in shl if c[:2] == b"\xc1\xa7" and c[6] == 8]
    print("OBJSHL offsets=%s" % [hex(o) for o in offs])
    for k in range(13):
        print("OBJEV %d %s" % (k, h(pe.dw(OBJEV + 4 * k))))
    pvs = pe.rd(0x0065032A, 0x22).hex()
    print("PVS bytes=%s" % pvs)
    ok_pvs = pvs.startswith("8b487c8b506a0fafcfc1f9060fafd1c1fa0c")
    print("SCAN tables dir=128 ghd=12 hce=8 plan=16 objshl=%d objev=13 pvs_match=%d" % (len(offs), int(ok_pvs)))


# ------------------------------------------------------------------------------------------------- calls
def cmd_calls(exe):
    ins = AS.disasm(exe)
    st = AS.starts(ins)
    tot = 0
    for tgt, name in TARGETS.items():
        sites = [(a, t) for a, t in ins if re.match(r"(call|jmp)\s+0x%x$" % tgt, t)]
        for a, t in sites:
            i = bisect.bisect_right(st, a) - 1
            print("CALL", name, h(a), t.split()[0], "in", h(st[i]) if i >= 0 else "?")
        print("CALLS", name, h(tgt), len(sites))
        tot += len(sites)
    fc = 0
    for k, (a, t) in enumerate(ins):
        if re.match(r"mov\s+(e[a-z]{2}),DWORD PTR \[e[a-z]{2}\+0xdc\]$", t):
            win = [x for _, x in ins[k + 1:k + 12]]
            if any(re.match(r"shr\s+e[a-z]{2},0x8$", w) for w in win) and any(re.match(r"call\s+0x5417d0$", w)
                                                                             for w in win):
                i = bisect.bisect_right(st, a) - 1
                print("FC8", h(a), "in", h(st[i]) if i >= 0 else "?")
                fc += 1
    print("SCAN calls targets=%d sites=%d fc8=%d" % (len(TARGETS), tot, fc))


# ------------------------------------------------------------------------------------------------- model
def read_txt(path):
    with open(path, encoding="latin-1", newline="") as f:
        r = list(csv.reader(f, delimiter="\t"))
    return r[0], r[1:]


def step(v, d):
    """PathVelocityStep with ECX 0x400: s = (v * 0x400) >> 6 (imul, sar); out = (d * s) >> 12 (imul, sar)."""
    s = s32(v * 0x400) >> 6
    return s32(d * s) >> 12


def frames_to(rem_x, rem_y, sx, sy):
    """Frames until the snap test (both |remaining| <= max(|sx|, |sy|)) passes; each other frame adds the step."""
    m = max(abs(sx), abs(sy))
    if m == 0:
        return None
    k = 0
    while True:
        k += 1
        if abs(rem_x) <= m and abs(rem_y) <= m:
            return k
        rem_x -= sx
        rem_y -= sy


def cmd_model(root):
    ex = os.path.join(root, "data", "global", "excel")
    ch, cr = read_txt(os.path.join(ex, "charstats.txt"))
    ci = {c: i for i, c in enumerate(ch)}
    mh, mr = read_txt(os.path.join(ex, "monstats.txt"))
    mi = {c: i for i, c in enumerate(mh)}
    ah, ar = read_txt(os.path.join(ex, "armor.txt"))
    ai = {c: i for i, c in enumerate(ah)}
    pe_dir_axis, pe_dir_diag = 4096, 2896
    # walk and run per class: v = (W << 8) * X / 100 (signed), X = max(B_FRW + stat 67, 25)
    n = 0
    for row in cr:
        if not row or not row[ci["WalkVelocity"]].strip():
            continue
        cls = row[0]
        w = int(row[ci["WalkVelocity"]])
        r = int(row[ci["RunVelocity"]])
        run67 = (r * 100) // w - 100
        for mode, x in (("WALK", 100), ("RUN", 100 + run67)):
            v = cdiv((w << 8) * x, 100)
            print("%s %s W=%d R=%d run67=%d X=%d v=%d axis=%d diag=%d" % (
                mode, cls, w, r, run67, x, v, step(v, pe_dir_axis), step(v, pe_dir_diag)))
        n += 1
    # monster Velocity bounds (path base Velocity << 8)
    vel = [int(x[mi["Velocity"]]) for x in mr if x and x[mi["Velocity"]].strip().lstrip("-").isdigit()]
    print("MONVEL rows=%d min=%d max=%d" % (len(vel), min(vel), max(vel)))
    spd = [int(x[ai["speed"]]) for x in ar if x and x[ai["speed"]].strip().lstrip("-").isdigit()]
    print("ARMORSPEED rows=%d values=%s" % (len(spd), sorted(set(spd))))
    for s in sorted(set(spd)):
        print("DRAIN armor_speed=%d factor=%d" % (s, cdiv(s, 10) + 1))
    # the step at sample speeds
    for v in (0x600, 0x900, 0x1000, 3840 * 75 // 100):
        print("STEP v=%d axis=%d diag=%d" % (v, step(v, pe_dir_axis), step(v, pe_dir_diag)))
    # frames to a point d subtiles away, from a subtile centre, axis and diagonal
    for v in (0x600, 0x900, 0x1000):
        for d in (1, 2, 3, 6, 10):
            fa = frames_to(d << 16, 0, step(v, pe_dir_axis), 0)
            fd = frames_to(d << 16, d << 16, step(v, pe_dir_diag), step(v, pe_dir_diag))
            print("FRAMES v=%d d=%d axis=%d diag=%d" % (v, d, fa, fd))
    # knockback: n = (p >> 1) + 1 subtiles on the major axis, speed 0x1000
    for p in (5, 10):
        nn = (p >> 1) + 1
        fa = frames_to(nn << 16, 0, step(0x1000, pe_dir_axis), 0)
        fd = frames_to(nn << 16, nn << 16, step(0x1000, pe_dir_diag), step(0x1000, pe_dir_diag))
        print("KB p=%d n=%d axis_frames=%d diag_frames=%d" % (p, nn, fa, fd))
    # get-hit: D by hit class; bands of damage against max hp; draws and probability
    for dv in (8, 16, 32, 64):
        a, b, c = dv, dv // 2, dv >> 2
        print("GETHIT D=%d thresholds=maxhp/%d,maxhp/%d,maxhp/%d bands: <t1 draws=0 p=0; [t1,t2) draws=1..2 p=3/8; "
              "[t2,t3) draws=1 p=3/4; >=t3 draws=0 p=1" % (dv, a, b, c))
    # 32-bit bounds of PathVelocityStep's products (axis component 4096)
    vmax = (2 ** 31 - 1) // (4096 * 16)
    print("EDGE step_product v_max=%d (4096*16*%d=%d) first_wrap=%d (%d)" % (
        vmax, vmax, 4096 * 16 * vmax, vmax + 1, 4096 * 16 * (vmax + 1)))
    kmax = (2 ** 31 - 1) // 0x400
    print("EDGE speed_times_k v_max=%d (%d) first_wrap=%d (%d)" % (kmax, kmax * 0x400, kmax + 1, (kmax + 1) * 0x400))
    for base, lab in ((6 << 8, "player W=6"), (max(vel) << 8, "monster Velocity max")):
        x = 25
        while cdiv(base * x, 100) <= vmax:
            x += 1
        print("EDGE factor_to_wrap %s pbase=%d X=%d v=%d (X-1 gives %d)" % (
            lab, base, x, cdiv(base * x, 100), cdiv(base * (x - 1), 100)))
    print("SCAN model classes=%d monvel_max=%d armor_speeds=%d" % (n, max(vel), len(set(spd))))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "tables":
        cmd_tables(arg)
    elif cmd == "calls":
        cmd_calls(arg)
    elif cmd == "model":
        cmd_model(arg)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

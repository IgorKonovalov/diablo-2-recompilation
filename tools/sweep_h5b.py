#!/usr/bin/env python3
"""Plan 0038 batch H5b (objects): the static checks and the log counts behind the batch's rows.

Usage:
  python3 -I tools/sweep_h5b.py static [--excel DIR] [--exe GAME.EXE]     # table and image checks
  python3 -I tools/sweep_h5b.py logs LOG [LOG ...]                         # counts from objects-h5b logs

static:
  * orient  every Objects record an ObjGroup names as a member whose PopulateFn is 2 (OBJPOP_Shrine, the only caller
            of OBJ_PlaceByOrientation 0x00550A30, checked by a call scan of the image with GNU objdump), with its
            Orientation: objects row 20 (orientation 2) needs one with Orientation 2.
  * doors   every IsDoor record with BlocksVis 0, with BlockMissile: UNIT_GetCollMask's 0x804 needs IsDoor 1,
            BlocksVis 0 and BlockMissile 1 (drlg/collision row 37).
  * size0   every record with SizeX or SizeY 0 and HasCollision set for some mode (drlg/collision row 39).
  * traps   g_ObjTrapFns (0x00732CEC, count at 0x00732D14) read from the image, and the callers of OBJ_TrapFire
            0x00582510 and of the event queue at its 0x00582595.
  * shrinegroups  the levels whose ObjGroup slots hold PopulateFn-2 members, with each member's Parm0 (1 health,
            2 mana, other: classes 1/4) and the slot's ObjPrb: where the due rule (no code-2 shrine) can hold.
logs: per log, the object classes created that the batch looks for, the operates by OperateFn with the drop
outcome, the trap lines (TF type, TE0 type / level / frame delay, TT0 function), and the levels visited.
The last line of each mode is a `SWEEP_H5B ...` summary. Stdlib only, read-only.
"""
import collections
import json
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from obj_survey import decode, txt_col  # noqa: E402

IMAGE_BASE = 0x400000


def pe_reader(exe):
    data = open(exe, "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + opt + 40 * i
        vsz, va, rsz, rp = struct.unpack_from("<IIII", data, o + 8)
        secs.append((va, max(vsz, rsz), rp))

    def u32(addr):
        rva = addr - IMAGE_BASE
        for va, sz, rp in secs:
            if va <= rva < va + sz:
                return struct.unpack_from("<I", data, rp + rva - va)[0]
        raise ValueError(hex(addr))
    return u32


def calls_to(exe, targets):
    """{target: [call sites]} from a full objdump disassembly of .text (direct calls and jumps)."""
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", exe], capture_output=True, text=True,
                         check=True).stdout
    want = {"0x%x" % t: t for t in targets}
    res = {t: [] for t in targets}
    pat = re.compile(r"^\s*([0-9a-f]+):\s+(call|jmp)\s+(0x[0-9a-f]+)\s*$")
    for line in out.splitlines():
        m = pat.match(line)
        if m and m.group(3) in want:
            res[want[m.group(3)]].append((int(m.group(1), 16), m.group(2)))
    return res


def cmd_static(excel, exe):
    O = decode(excel, "objects")
    G = decode(excel, "objgroup")
    L = decode(excel, "levels")
    lname = txt_col(excel, "levels", "Name")
    tot = collections.Counter()
    # orient
    members = collections.defaultdict(set)
    for gi, g in enumerate(G):
        for k in range(8):
            c = g["ID%d" % k]
            if c and O[c]["PopulateFn"] == 2:
                members[c].add(gi)
    print("== orient: ObjGroup members with PopulateFn 2 (OBJPOP_Shrine), Orientation")
    by_or = collections.Counter()
    for c in sorted(members):
        by_or[O[c]["Orientation"]] += 1
        print("  class %3d %-14s Orientation %d  groups %s" % (c, O[c]["Name"], O[c]["Orientation"], sorted(members[c])))
    tot["shrine_members"] = len(members)
    for k in sorted(by_or):
        tot["shrine_members_orient%d" % k] = by_or[k]
    cs = calls_to(exe, [0x00550A30, 0x00582510, 0x005417D0])
    print("  call sites of OBJ_PlaceByOrientation 0x00550A30: %s" % ["%08x %s" % s for s in cs[0x00550A30]])
    tot["placebyorient_sites"] = len(cs[0x00550A30])
    # doors
    print("== doors: IsDoor 1 and BlocksVis 0")
    n804 = 0
    for i, o in enumerate(O):
        if o["IsDoor"] and not o["BlocksVis"]:
            print("  class %3d %-8s BlockMissile %d HasCollision %s" % (i, o["Name"], o["BlockMissile"],
                                                                     [o["HasCollision%d" % m] for m in range(8)]))
            tot["doors_no_blocksvis"] += 1
            n804 += 1 if o["BlockMissile"] else 0
    tot["doors_mask_0x804"] = n804
    tot["doors"] = sum(1 for o in O if o["IsDoor"])
    # size0
    print("== size0: SizeX or SizeY 0 with HasCollision set for some mode")
    for i, o in enumerate(O):
        if (o["SizeX"] == 0 or o["SizeY"] == 0) and any(o["HasCollision%d" % m] for m in range(8)):
            print("  class %3d %-24s size %dx%d HasCollision %s InitFn %d" % (
                i, o["Name"], o["SizeX"], o["SizeY"], [o["HasCollision%d" % m] for m in range(8)], o["InitFn"]))
            tot["size0_hascollision"] += 1
    # traps
    u32 = pe_reader(exe)
    n = u32(0x00732D14)
    fns = [u32(0x00732CEC + 4 * i) for i in range(n)]
    print("== traps: g_ObjTrapFns count %d: %s" % (n, ["%08x" % f for f in fns]))
    print("  callers of OBJ_TrapFire 0x00582510: %d %s" % (len(cs[0x00582510]), ["%08x" % s[0] for s in cs[0x00582510]]))
    tot["trapfns"] = n
    tot["trapfire_sites"] = len(cs[0x00582510])
    # shrine groups by level
    print("== shrinegroups: levels, slot, ObjPrb, group, members (class, Parm0, PROB)")
    for li, lv in enumerate(L):
        for k in range(8):
            gi, pr = lv["ObjGrp%d" % k], lv["ObjPrb%d" % k]
            if not gi or not pr:
                continue
            g = G[gi]
            mem = [(g["ID%d" % j], O[g["ID%d" % j]]["Parm0"], g["PROB%d" % j]) for j in range(8)
                   if g["ID%d" % j] and O[g["ID%d" % j]]["PopulateFn"] == 2]
            if mem:
                health = any(p == 1 for _, p, _ in mem)
                print("  level %3d %-28s slot %d prb %3d group %3d health member %-5s %s"
                      % (li, lname[li], k, pr, gi, health, mem))
                tot["shrine_slots"] += 1
                tot["shrine_slots_no_health_member"] += 0 if health else 1
    print("SWEEP_H5B static " + " ".join("%s=%d" % kv for kv in sorted(tot.items())))
    return 0


WATCH = {523: "red light (size 0, HasCollision)", 399: "fissure (InitFn 58, size 0)", 254: "diablo left light (size 0)",
         564: "summit door (size 0)", 321: "dummy (size 0)", 131: "seal glow (size 0)", 397: "sparklychest (InitFn 57)",
         455: "specialchest (InitFn 57)", 371: "level-25 chest (InitFn 47)", 459: "Drehya start (InitFn 66)",
         461: "Nihlathak start (InitFn 68)", 462: "Nihlathak outside (InitFn 69)", 385: "Cain start (InitFn 54)",
         255: "Diablo start (InitFn 55)", 473: "caged fellow (InitFn 62)", 179: "bookshelf", 180: "bookshelf",
         380: "trapped soul", 381: "trapped soul", 466: "evil urn", 1: "casket", 53: "casket", 79: "casket",
         13: "door gate L (no BlocksVis)", 14: "door gate R (no BlocksVis)", 160: "fire (trap)", 162: "fire (trap)",
         192: "teleport pad", 304: "teleport pad", 305: "teleport pad", 306: "teleport pad", 298: "arcane portal"}


def cmd_logs(paths):
    tot = collections.Counter()
    for p in paths:
        cre = collections.Counter()
        ops = collections.Counter()
        tf = collections.Counter()
        te = []
        lv = []
        pend = {}
        inop, after_tf = None, None
        for line in open(p, errors="replace"):
            tag, _, rest = line.partition(" ")
            # objects row 40: inside an operate (OO0 .. OOX), OBJ_TrapFire comes after every drop and draw
            if tag == "OO0":
                inop, after_tf = True, None
            elif tag == "OOX":
                if after_tf is not None:
                    tot["operates_with_trapfire"] += 1
                    tot["operates_trapfire_last"] += 0 if after_tf else 1
                inop, after_tf = None, None
            elif inop and tag == "TF":
                after_tf = False
            elif inop and after_tf is False and tag in ("OD", "OC0", "OCT", "OCX"):
                after_tf = True
            if tag not in ("OU0", "OO0", "TF", "TFQ", "TE0", "TT0", "PLR"):
                continue
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "OU0" and d["type"] == 2 and d["cls"] in WATCH:
                cre[d["cls"]] += 1
            elif tag == "OO0":
                ops[(d["fn"], d["cls"])] += 1
            elif tag == "TF":
                if d["t"]:
                    tf[d["t"]] += 1
                    pend[d["u"]] = d["f"]
            elif tag == "TE0":
                te.append([d["cls"], d["t"], d["lid"], d["f"] - pend.get(d["u"], d["f"]) if d["u"] in pend else None])
            elif tag == "TT0" and te:
                te[-1].append("%08x" % d["fn"])
            elif tag == "PLR":
                if not lv or lv[-1] != d["lid"]:
                    lv.append(d["lid"])
        print("== %s" % os.path.basename(p))
        print("  levels %s" % [x for i, x in enumerate(lv) if x not in lv[:i]])
        print("  watched classes created %s" % {"%d %s" % (k, WATCH[k]): v for k, v in sorted(cre.items())})
        print("  operates (OperateFn, class) %s" % dict(sorted(ops.items())))
        print("  OBJ_TrapFire with a trap %s; trap events (class, type, level, frames after TF, fn) %s" % (dict(tf), te))
        tot["logs"] += 1
        for k, v in cre.items():
            tot["created_%d" % k] += v
        for (fn, c), v in ops.items():
            tot["operate_fn%d" % fn] += v
        tot["trap_events"] += len(te)
    print("SWEEP_H5B logs " + " ".join("%s=%d" % kv for kv in sorted(tot.items())))
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] not in ("static", "logs"):
        print(__doc__)
        return 2
    excel = os.path.join(ROOT, "workspace", "merged", "data", "global", "excel")
    exe = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
    rest = []
    it = iter(argv[2:])
    for a in it:
        if a == "--excel":
            excel = next(it)
        elif a == "--exe":
            exe = next(it)
        else:
            rest.append(a)
    if argv[1] == "static":
        return cmd_static(excel, exe)
    return cmd_logs(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

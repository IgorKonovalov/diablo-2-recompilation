#!/usr/bin/env python3
"""Plan 0038 batch H2a checks (run:2026-10-20-sweep-items-tc; items/tc and items/quality rows).

    python3 -I tools/sweep_h2a.py logs <log> [<log> ...]       # the H2a lines of tools/gdb/tc-h2a.gdb
    python3 -I tools/sweep_h2a.py clamp <log> [<log> ...]      # the D6 minimum and its place (items/quality D4-D7)
    python3 -I tools/sweep_h2a.py static <game.exe>            # call sites and constants behind the H2a lines
    python3 -I tools/sweep_h2a.py killers <log> [<log> ...]    # killer kinds of the quality rolls (items/quality M3)
    python3 -I tools/sweep_h2a.py goldtypes                    # item records of type 4 through type, type2, Equiv

`logs` reads the lines tools/gdb/tc-h2a.gdb adds and checks, per log, in order:
  chain    every MONSTER_DropItems call (MDI) comes from 0x005A68D6 (sub_005A6830_MonDeathDrop, after MDDX, whose
           MDD0 return address is 0x005A702C in sub_005A6FF0_MonDeathEvent) or from 0x005A801C
           (sub_005A8000_MonDropNoNoDrop, whose MNN return address is 0x005D8894 in sub_005D8780_CorpseFindItem,
           after a CFI line); its noNoDrop argument is 0 on the first path and 1 on the second; every monster-source
           DROP line follows an MDI;
  deathx   each MDD0 ends in exactly one of: MDDB bit17=1 (and unit+0xC4 bit 17 set in MDD0), MDDC coll != 0, MDDX;
           bit 17 in MDD0 <=> MDDB bit17=1; no MDI follows a skipped death drop before the next MDD0, CFI or TCR;
  gold     for each created unit (CPOST), the GTY line names it and is4 = 1 exactly for item class `gld` (the only
           Misc record of type 4); a `gld` unit with a non-zero mul word gets GMUL/GMULX with v = (gold * mul) >> 8
           (signed 32-bit, arithmetic shift); GMAX follows with the count; when count < max, GF0 names the unit, GF1
           gives the unit's own type, and for type 4 GF5's factor = 100 + GF2 + GF4 (GF4 only when GF3 owner != 0) and
           GF6 v = trunc(gold * factor / 100) (signed); for other types no GF2 follows; when count >= max no GF0
           follows and TCEND ends the call; a GF0 with killer 0 returns before GF1;
  players  the TCR fields g6a and pover with the PLAYERS line: PLAYERS = max(alive, pover) when g6a is 1..3 (alive
           taken as 1: these are one-player games), else alive;
  objects  object-source TCR lines (stype 2): no CAP line, NDIN n = the party/players value;
  nonodrop TCR nonodrop=1: the first PICK range of the call equals the NDP total (nd computed, not added), and no
           pick is rejected by NoDrop;
  negstop  NEG lines: roll >= total ends the frame.
Exit 0 only when no check fails. Stdlib only. Read-only.
"""
import argparse
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import quality  # noqa: E402

M32 = 0xFFFFFFFF


def s32(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def kv(line):
    return dict(x.split("=", 1) for x in line.split()[1:] if "=" in x)


TAGS = ("MDD0", "MDDB", "MDDC", "MDDX", "MDI", "MNN", "CFI", "GTY", "GMUL", "GMULX", "GMAX", "GF0", "GF1", "GF2",
        "GF3", "GF4", "GF5", "GF6", "TCR", "DROP", "CPOST", "CPRE", "TCEND", "PLAYERS", "PARTY", "CAP", "NDIN", "NDP",
        "PICK", "NEG", "SEL", "SUB")


def lines_of(path):
    for ln in open(path, errors="replace"):
        tag = ln.split(" ", 1)[0].rstrip("\n")
        if tag in TAGS:
            yield tag, kv(ln.strip())


TYPES_SEEN = set()


def check_log(path, T, gld, tot, bad):
    L = list(lines_of(path))
    name = os.path.basename(path)
    c = Counter()

    def fail(i, msg):
        bad.append("%s line#%d: %s" % (name, i, msg))

    # chain and deathx
    i = 0
    last_mdi = None
    while i < len(L):
        tag, d = L[i]
        if tag == "MDD0":
            c["MDD0"] += 1
            c["MDD0 ret " + d["ret"]] += 1
            if d["ret"] != "005a702c":
                fail(i, "MDD0 ret %s" % d["ret"])
            bit = (int(d.get("c4", "0"), 16) >> 17) & 1
            j = i + 1
            ends = []
            while j < len(L) and L[j][0] in ("MDDB", "MDDC", "MDDX"):
                ends.append(L[j])
                j += 1
            kinds = [e[0] for e in ends]
            if not kinds or kinds[0] != "MDDB":
                fail(i, "MDD0 without MDDB")
            else:
                b = int(ends[0][1]["bit17"])
                if b != bit:
                    fail(i, "MDDB %d, MDD0 c4 bit 17 %d" % (b, bit))
                if b:
                    c["death drop skipped: bit 17"] += 1
                    c["bit-17 class %s" % d.get("cls")] += 1
                    if len(kinds) != 1:
                        fail(i, "bit 17 set but %s follow" % kinds[1:])
                else:
                    if len(kinds) < 2 or kinds[1] != "MDDC":
                        fail(i, "no MDDC after MDDB 0")
                    elif int(ends[1][1]["coll"], 16) != 0:
                        c["death drop skipped: collision"] += 1
                        if len(kinds) != 2:
                            fail(i, "collision fail but %s follow" % kinds[2:])
                    elif kinds[2:] != ["MDDX"]:
                        fail(i, "no MDDX after MDDC 0")
                    else:
                        c["death drop taken (MDDX)"] += 1
                        if j >= len(L) or L[j][0] != "MDI":
                            fail(i, "MDDX not followed by MDI")
            if not (kinds and kinds[-1] == "MDDX"):
                k = j
                while k < len(L) and L[k][0] not in ("MDD0", "CFI", "TCR", "MNN"):
                    if L[k][0] == "MDI":
                        fail(k, "MDI after a skipped death drop")
                    k += 1
            i = j
            continue
        if tag == "CFI":
            c["CFI"] += 1
            if i + 1 < len(L) and L[i + 1][0] == "MNN":
                if L[i + 1][1]["ret"] != "005d8894":
                    fail(i + 1, "MNN ret %s" % L[i + 1][1]["ret"])
                c["CFI -> MNN"] += 1
            else:
                c["CFI without MNN"] += 1
        if tag == "MNN" and (i == 0 or L[i - 1][0] != "CFI"):
            fail(i, "MNN without CFI")
        if tag == "MDI":
            last_mdi = d
            c["MDI ret " + d["ret"]] += 1
            prev = L[i - 1][0] if i else None
            if d["ret"] == "005a68d6":
                if prev != "MDDX" or d["nonodrop"] != "0":
                    fail(i, "MDI from the death drop: previous %s, nonodrop %s" % (prev, d["nonodrop"]))
            elif d["ret"] == "005a801c":
                if prev != "MNN" or d["nonodrop"] != "1" or L[i - 1][1]["mon"] != d["mon"]:
                    fail(i, "MDI from MonDropNoNoDrop: previous %s, nonodrop %s" % (prev, d["nonodrop"]))
            else:
                fail(i, "MDI ret %s" % d["ret"])
        if tag == "DROP":
            prev = L[i - 1][0] if i else None
            c["DROP"] += 1
            if prev != "MDI" or last_mdi is None or last_mdi["mon"] != d["src"]:
                c["DROP not right after its MDI"] += 1
        i += 1

    # per TCR call: players, objects, nonodrop, negstop, gold
    calls = []
    cur = None
    for i, (tag, d) in enumerate(L):
        if tag == "TCR":
            cur = {"tcr": d, "i": i, "ev": []}
            calls.append(cur)
        elif cur is not None:
            cur["ev"].append((i, tag, d))
            if tag == "TCEND":
                cur = None
    for call in calls:
        t = call["tcr"]
        ev = call["ev"]
        g6a, pover = int(t["g6a"]), int(t["pover"])
        stype = int(t["stype"])
        pl = [d for _, tag, d in ev if tag == "PLAYERS"]
        if pl:
            want = max(1, pover) if g6a in (1, 2, 3) else 1
            got = int(pl[0]["players"])
            c["PLAYERS g6a=%d pover=%d players=%d" % (g6a, pover, got)] += 1
            if got != want:
                fail(call["i"], "PLAYERS %d, want %d (g6a %d, pover %d)" % (got, want, g6a, pover))
        if stype == 2:
            c["object calls"] += 1
            if any(tag == "CAP" for _, tag, _ in ev):
                fail(call["i"], "CAP line in an object call")
            for _, tag, d in ev:
                if tag == "NDIN":
                    c["object NDIN n=%s" % d["n"]] += 1
                    if pover == 8 and g6a in (1, 2, 3) and d["n"] != "4":
                        fail(call["i"], "object NDIN n %s with /players 8" % d["n"])
        if t["nonodrop"] == "1":
            c["nonodrop calls"] += 1
            ndp = [d for _, tag, d in ev if tag == "NDP"]
            pk = [d for _, tag, d in ev if tag == "PICK"]
            if ndp and pk:
                if int(pk[0]["range"]) != int(ndp[0]["total"]):
                    fail(call["i"], "nonodrop: PICK range %s, NDP total %s" % (pk[0]["range"], ndp[0]["total"]))
                else:
                    c["nonodrop: range = total (nd %s not added)" % ndp[0]["ndp"]] += 1
                    if int(ndp[0]["ndp"]) > 0:
                        c["nonodrop with nd' > 0"] += 1
        for k, (_, tag, d) in enumerate(ev):
            if tag == "NEG":
                r, tt = int(d["roll"]), int(d["total"])
                nxt = ev[k + 1][1] if k + 1 < len(ev) else None
                if r >= tt:
                    c["NEG stop (roll >= total)"] += 1
                    if nxt == "SEL":
                        fail(call["i"], "NEG roll %d >= total %d but an entry is selected" % (r, tt))
                else:
                    c["NEG pick"] += 1
        # gold and max, per created unit
        for k, (i, tag, d) in enumerate(ev):
            if tag != "CPOST" or d.get("unit", "00000000") == "00000000":
                continue
            unit, ucls = d["unit"], int(d.get("uclass", -1))
            rest = ev[k + 1:]
            nxt = [r for r in rest if r[1] in ("GTY", "GMUL", "GMULX", "GMAX", "GF0", "GF1", "GF2", "GF3", "GF4",
                                                 "GF5", "GF6", "CPOST", "CPRE", "TCEND")]
            if not nxt or nxt[0][1] != "GTY" or nxt[0][2]["unit"] != unit:
                fail(i, "CPOST %s without its GTY" % unit)
                continue
            is4 = int(nxt[0][2]["is4"])
            c["created units"] += 1
            if is4 != (1 if ucls == gld else 0):
                fail(i, "GTY is4 %d for item class %d" % (is4, ucls))
            if is4:
                c["gold units"] += 1
            j = 1
            if j < len(nxt) and nxt[j][1] == "GMUL":
                g, m = int(nxt[j][2]["gold"]), int(nxt[j][2]["mul"])
                if j + 1 >= len(nxt) or nxt[j + 1][1] != "GMULX":
                    fail(i, "GMUL without GMULX")
                else:
                    v = int(nxt[j + 1][2]["v"])
                    if v != s32(g * m) >> 8:
                        fail(i, "mul: %d * %d >> 8 = %d, log %d" % (g, m, s32(g * m) >> 8, v))
                    else:
                        c["mul= products reproduced"] += 1
                        c["mul word %d" % m] += 1
                j += 2
            if j >= len(nxt) or nxt[j][1] != "GMAX":
                fail(i, "no GMAX")
                continue
            cnt, mx = int(nxt[j][2]["count"]), int(nxt[j][2]["max"])
            after = nxt[j + 1:]
            if cnt >= mx:
                c["max reached (count %d)" % cnt] += 1
                if is4:
                    c["max reached on a gold unit"] += 1
                if after and after[0][1] == "GF0":
                    fail(i, "GF0 after the count reached max")
                if not after or after[0][1] != "TCEND":
                    fail(i, "count reached max but %s follows" % (after[0][1] if after else None))
                continue
            if not after or after[0][1] != "GF0" or after[0][2]["unit"] != unit or after[0][2]["ret"] != "0055af5e":
                fail(i, "no GF0 for unit %s below max" % unit)
                continue
            if after[0][2]["killer"] == "00000000":
                c["gold find skipped: no killer (EBX 0)"] += 1
                if len(after) > 1 and after[1][1] == "GF1":
                    fail(i, "GF1 with no killer")
                continue
            ty = int(after[1][2]["type"]) if len(after) > 1 and after[1][1] == "GF1" else None
            if ty != T.type_of(ucls):
                fail(i, "GF1 type %s, item class %d has type %d" % (ty, ucls, T.type_of(ucls)))
            if ty != 4:
                c["gold find skipped: own type not 4"] += 1
                c["gold find skipped, own types seen"] += 0
                TYPES_SEEN.add(ty)
                if len(after) > 2 and after[2][1] == "GF2":
                    fail(i, "GF2 for type %s" % ty)
                continue
            seq = {r[1]: r[2] for r in after[2:7]}
            kgf = int(seq["GF2"]["kgf"])
            own = int(seq["GF3"]["owner"], 16)
            ogf = int(seq["GF4"]["ogf"]) if own else 0
            if bool(own) != ("GF4" in seq):
                fail(i, "GF4 presence and owner %x disagree" % own)
            g, f = int(seq["GF5"]["gold"]), int(seq["GF5"]["factor"])
            if f != 100 + kgf + ogf:
                fail(i, "factor %d != 100 + %d + %d" % (f, kgf, ogf))
            v = int(seq["GF6"]["v"])
            want = quality.cdiv(s32(g * f), 100)
            if v != want:
                fail(i, "gold find: %d * %d / 100 = %d, log %d" % (g, f, want, v))
            else:
                c["gold find products reproduced"] += 1
                c["gold find factor %d" % f] += 1
                if f != 100:
                    c["gold find with factor != 100"] += 1
    for k, v in c.items():
        tot[k] += v
    tot["logs"] += 1


def cmd_logs(ns):
    T = quality.Tables(ns.excel)
    gld = [i for i in range(len(T.items)) if T.items[i][0x80:0x84] == b"gld "]
    if len(gld) != 1:
        print("expected one gld record, got %s" % gld)
        return 1
    tot, bad = Counter(), []
    for p in ns.logs:
        check_log(p, T, gld[0], tot, bad)
    ity = quality.recs(ns.excel, "itemtypes")
    print("itemtypes record 4 code %r; item class of `gld` %d, its type %d" % (
        ity[4][0:4].decode(errors="replace"), gld[0], T.type_of(gld[0])))
    tot["gold find skipped, own types seen"] = len(TYPES_SEEN)
    for k in sorted(tot):
        print("  %-60s %d" % (k, tot[k]))
    for b in bad:
        print("BAD " + b)
    print("%d bad" % len(bad))
    return 1 if bad else 0


def cmd_clamp(ns):
    T = quality.Tables(ns.excel)
    tot = 0
    acts, brk, rows, model_fail = Counter(), Counter(), Counter(), 0
    for path in ns.logs:
        for q, extra, o, tcr, err in quality.pairs_of(path):
            if q is None or err:
                continue
            item, ilvl = int(q["item"]), int(q["ilvl"])
            ratio = [int(x) for x in q["ratio"].split(",")]
            mf, _ = quality.magic_find(extra, tcr, ns.mf)
            seed = quality.seedpair(q["seed"])
            want = (int(o["q"]), quality.seedpair(o["seed"]))
            pre = []
            code, after, _, _, ri = quality.roll(T, item, ilvl, ratio, seed, mf, False, None, {"pre": pre})
            tot += 1
            if (code, after) != want:
                model_fail += 1
                continue
            hit = [x for x in pre if x[1] <= x[2]]
            if not hit:
                continue
            rows["rolls with the clamp acting"] += 1
            for name, cpre, mn, w in hit:
                acts["%s, ratio word %s" % (name, "non-zero" if w else "zero")] += 1
                if w and cpre < mn and quality.s32(cpre - quality.cdiv(quality.s32(w * cpre), 1024)) != \
                        quality.s32(mn - quality.cdiv(quality.s32(w * mn), 1024)):
                    acts["%s: ratio word non-zero and pre-clamp c < min" % name] += 1
            for how in ("off", "after-ratio", "before-mf"):
                c2, a2, _, _, _ = quality.roll(T, item, ilvl, ratio, seed, mf, False, None, {"clamp": how})
                if (c2, a2) != want:
                    brk[how] += 1
    print("quality pairs %d, model reproduces %d (%d not: logs whose magic find is not logged; skipped)" % (
        tot, tot - model_fail, model_fail))
    for k in sorted(rows):
        print("  %-60s %d" % (k, rows[k]))
    for k in sorted(acts):
        print("  clamp acted: %-47s %d" % (k, acts[k]))
    print("  counterfactual: no D6 minimum breaks %d of these rolls" % brk["off"])
    print("  counterfactual: D6 after the ratio word (D7) breaks %d of these rolls" % brk["after-ratio"])
    print("  counterfactual: D6 before magic find (D5) breaks %d of these rolls" % brk["before-mf"])
    return 0 if model_fail == 0 or ns.allow_unlogged_mf else 1


def cmd_killers(ns):
    c = Counter()
    for path in ns.logs:
        for q, extra, o, tcr, err in quality.pairs_of(path):
            if q is None or err:
                continue
            kt = tcr.get("ktype")
            key = "killer none" if kt is None else "ktype %s kclass %s" % (kt, tcr.get("kclass"))
            if "QKMF" in extra:
                key += ", QKMF"
            if "QOWN" in extra:
                key += ", QOWN otype %s oclass %s" % (extra["QOWN"]["otype"], extra["QOWN"]["oclass"])
            if "QMF" in extra and "QKMF" in extra:
                s = int(extra["QKMF"]["kmf"]) + (int(extra["QOMF"]["omf"]) if "QOMF" in extra else 0)
                key += ", mf = kmf + omf" if s == int(extra["QMF"]["mf"]) else ", mf MISMATCH"
            c[key] += 1
    for k in sorted(c):
        print("  %-80s %d" % (k, c[k]))
    return 0


def cmd_static(ns):
    b = open(ns.exe, "rb").read()
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    n = struct.unpack_from("<H", b, pe + 6)[0]
    opt = struct.unpack_from("<H", b, pe + 20)[0]
    secs = []
    for k in range(n):
        o = pe + 24 + opt + 40 * k
        nm = b[o:o + 8].rstrip(b"\0").decode()
        vs, va, rs, ro = struct.unpack_from("<IIII", b, o + 8)
        secs.append((nm, 0x400000 + va, rs, ro))

    def off(va):
        for nm, v, rs, ro in secs:
            if v <= va < v + rs:
                return ro + va - v
        raise ValueError(hex(va))

    text = [s for s in secs if s[0] == ".text"][0]
    t0, tlen = text[3], text[2]

    def rel_calls(target):
        out = []
        for i in range(t0, t0 + tlen - 5):
            if b[i] in (0xE8, 0xE9):
                va = text[1] + i - t0
                if (va + 5 + struct.unpack_from("<i", b, i + 1)[0]) & M32 == target:
                    out.append((va, "call" if b[i] == 0xE8 else "jmp"))
        return out

    def abs_refs(target):
        p = struct.pack("<I", target)
        out, i = [], b.find(p)
        while i >= 0:
            for nm, v, rs, ro in secs:
                if ro <= i < ro + rs:
                    out.append((v + i - ro, nm))
            i = b.find(p, i + 1)
        return out

    fns = [(0x005A6830, "sub_005A6830_MonDeathDrop"), (0x005A6600, "MONSTER_DropItems"),
           (0x005A8000, "sub_005A8000_MonDropNoNoDrop"), (0x005D8780, "sub_005D8780_CorpseFindItem"),
           (0x005A6FF0, "sub_005A6FF0_MonDeathEvent"), (0x005589A0, "sub_005589A0_DropGoldFind")]
    for a, nm in fns:
        rc = rel_calls(a)
        ar = abs_refs(a)
        print("%s 0x%08X: rel32 %s; absolute %s" % (nm, a, ", ".join("%s 0x%08X" % (k, v) for v, k in rc) or "none",
                                                     ", ".join("0x%08X (%s)" % (v, s) for v, s in ar) or "none"))
    for va, want, what in ((0x0055AEF2, b"\x6a\x04\x57\xe8", "push 4; push edi; call (ITEMS_UnitIsType)"),
                           (0x005589AE, b"\x83\xf8\x04", "cmp eax, 4 (DropGoldFind own type)"),
                           (0x0055AF24, b"\xc1\xf8\x08", "sar eax, 8 (mul=)"),
                           (0x005589E9, b"\xb8\x1f\x85\xeb\x51\xf7\xe9\xc1\xfa\x05", "imul 0x51EB851F; sar edx, 5 (/100)"),
                           (0x0055AF4F, b"\x39\x08\x7d\x2d", "cmp [eax], ecx; jge exit (max before gold find)"),
                           (0x005A6867, b"\xc1\xe8\x11\x83\xe0\x01\x75", "shr eax, 0x11; and eax, 1; jnz exit"),
                           (0x005A687F, b"\x68\x01\x08\x00\x00", "push 0x801 (collision mask)")):
        got = b[off(va):off(va) + len(want)]
        print("0x%08X %s: %s" % (va, what, "ok" if got == want else "DIFFERS (%s)" % got.hex()))
    return 0


def cmd_goldtypes(ns):
    """Full-table check: which item records are of itemtypes record 4 by their own type, by type2, or through the
    Equiv1/Equiv2 ancestors of either (the type-equivalence half of items/tc H8-H9)."""
    T = quality.Tables(ns.excel)
    own, any_ = [], []
    for i, r in enumerate(T.items):
        t1, t2 = struct.unpack_from("<h", r, 0x11E)[0], struct.unpack_from("<h", r, 0x120)[0]
        if t1 == 4:
            own.append(i)
        todo, seen = [t1, t2], set()
        while todo:
            x = todo.pop()
            if x <= 0 or x >= len(T.itypes) or x in seen:
                continue
            seen.add(x)
            todo += [struct.unpack_from("<H", T.itypes[x], 4)[0], struct.unpack_from("<H", T.itypes[x], 6)[0]]
        if 4 in seen:
            any_.append(i)
    code = lambda i: T.items[i][0x80:0x84].decode(errors="replace").strip()  # noqa: E731
    print("item records %d, itemtypes records %d" % (len(T.items), len(T.itypes)))
    print("own type 4: %d %s" % (len(own), [code(i) for i in own]))
    print("type 4 through type, type2 or Equiv: %d %s" % (len(any_), [code(i) for i in any_]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("logs", "clamp", "killers"):
        a = sub.add_parser(name)
        a.add_argument("logs", nargs="+")
        a.add_argument("--excel", default=quality.EXCEL)
        if name == "clamp":
            a.add_argument("--allow-unlogged-mf", action="store_true")
            a.add_argument("--mf", type=int, default=0, help="magic find for rolls whose log has no QMF line")
    a = sub.add_parser("goldtypes")
    a.add_argument("--excel", default=quality.EXCEL)
    a = sub.add_parser("static")
    a.add_argument("exe")
    ns = ap.parse_args(argv)
    return {"logs": cmd_logs, "clamp": cmd_clamp, "static": cmd_static, "killers": cmd_killers, "goldtypes": cmd_goldtypes}[ns.cmd](ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

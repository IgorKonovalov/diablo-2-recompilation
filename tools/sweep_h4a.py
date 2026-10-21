"""Plan 0038 batch H4a (monsters-a): the checker of the superunique tails, the special-mod handler walk, the Chaos
Sanctuary gate, the boss-class monster level and the fixed client names, on logs of tools/gdb/mon-h4a.gdb (and, for
the parts whose tags older loggers already wrote, on kept logs of tools/gdb/mon-stats.gdb, mon-special.gdb and
chain.gdb).

Usage:
  python3 -I tools/sweep_h4a.py check <run.log> [...] [-v]
  python3 -I tools/sweep_h4a.py <part> <run.log> [...] [-v]      one part only

Parts (the inventory rows each serves are in docs/findings/monsters/0001-0004 and items/0010, sections "Plan 0038
batch H4a"):
  su        every SuperUniqueSpawn window (SU0 .. SUX): the placed bit against the record's Stacks byte (+0x26, the
            byte 0x005A4A09 reads), Mod1..Mod3 written without 24 (thief), the second
            UModAura call of a record with a fixed 30 (aura) after SpecialModsApply's exit with the same draw and row,
            Lord De Seis's override (AUR2 idx 5 after a drawn r), the AUR draw r = Range(Init(name seed), n), and mod 22
            appended last (special 9, 10, 25, 30, 31, 38, 48, 50, 51)
  tails     SUC / SUCR / SURD (tools/gdb/mon-h4a.py) between SUT and SUX against the tail table read from
            0x005A4BFE..0x005A4E43: callee and pushed arguments per record index, Radament's count Range(us, 5) + 2 of
            class 4 then 0x114, 0x17E, 0x181, 0x185, the EscortSpawn arguments and the units it creates (SI0 between
            its call and its return); without SUC lines (older loggers) only the units created inside the tail
            (special 46, 52, 54, 55, 56, 58, 59, 60)
  handlers  every SpecialModsApply window (SMA0 .. SMAX): the HD0 mods equal [1, 2, 3, 4] then the unit's list up to
            the first 0, each kept only when g_UModHandlers (0x0073C008) holds a pointer; counts per null row (10, 11,
            12, 13, 14, 15, 24 ...) (special 34, 35)
  gate      GQ (level 108 only) against the next PG of the same pass: a non-zero quest byte gives PG 0 (no
            population), a zero byte lets the gate return 1 (spawn 11)
  boss      SI0 / SI2 of the MonStats classes with the boss flag (+0x0C bit 0x40) in an expansion game at d > 0: the
            level is MonStats Level[d] (+0xAA + 2d), and the cases where the area level (Levels MonLvlEx[d]) differs
            are counted apart (pool 12, quest-drops 48)
  names     the client names of tools/sweep_h4b.py's part (mod 12, superuniques, champions, uniques) and the
            fixed-name classes against the string index each class's jump-table entry loads at 0x004AC9EE.. (read
            from game.exe here: mov ecx, imm32) (special 35, 68, 69)
  wander    WRL lines (the wanderer roll past its 1/32768 gate) against the RTK0 ticks logged (spawn 5, 47-49)

Each part prints one `H4A <part> key=value ...` line and a few detail lines (all of them with -v). A part exits 1 when
an observation contradicts the model (`bad=` above 0); a case the logs never met is a zero count, not a failure.
Stdlib only. Read-only.
"""
import collections
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import drlg  # noqa: E402
import sweep_h4b as H  # noqa: E402
from rng import INIT_HIGH, rng_range  # noqa: E402

EXE = drlg.DEFAULT_EXE
parse, T = H.parse, H.T


class Report(H.Report):
    def out(self):
        kv = " ".join("%s=%s" % (k.replace(" ", "_"), v) for k, v in sorted(self.c.items()))
        print("H4A %s bad=%d %s" % (self.part, len(self.bad), kv))
        for m in self.bad[:None if H.VERBOSE else 20]:
            print("  BAD " + m)
        for m in self.notes[:None if H.VERBOSE else 30]:
            print("  " + m)
        return 1 if self.bad else 0

# the tail cases read from the disassembly (0x005A4BF7: jump table 0x005A4E7C by the byte table 0x005A4EA4 on
# record +0x08 - 6); each entry: (callee, the pushed arguments the call must carry, or None for "not checked")
QH, Q545, STATE, AIM, APP, RANGE, NEAR, ESC = (0x005436B0, 0x00545B50, 0x00639DB0, 0x005B0E00, 0x005A4850, 0x0045C390,
                                               0x005B23C0, 0x005B24E0)
TAILS = {
    6: [(STATE, ("u", 0x76, 1)), (QH, (5,)), (AIM, (None, 0x0D))],
    10: "radament",
    26: [(QH, (0x13,)), (Q545, ())], 27: [(QH, (0x13,)), (Q545, ())], 29: [(QH, (0x13,)), (Q545, ())],
    36: [(QH, (0x17,))], 37: [(QH, (0x17,))], 38: [(QH, (0x17,))],
    39: [(QH, (4,))],
    42: [(ESC, (0x1C5, 1, 0x14, 0x14, 0)), (QH, (0x1F,)), (Q545, ()), (STATE, ("u", 0x76, 1))],
    43: [(QH, (0x23,)), (Q545, ())], 44: [(QH, (0x23,)), (Q545, ())], 45: [(QH, (0x23,)), (Q545, ())],
    60: [(0x0058F030, None), (0x00620BB0, None), (0x0063EC70, None), (ESC, ("cls", 1, 0x0A, 0x14, 0x40)),
         (QH, (0x22,))],
    62: [(ESC, (0x17D, 1, 0x14, 0x0A, 0x40))],
}
RADAMENT_ESC = [0x114, 0x17E, 0x181, 0x185]


def su_rec(t, i):
    return t.su[i] if 0 <= i < len(t.su) else None


def su_mods(t, i):
    r = su_rec(t, i)
    return [struct.unpack_from("<I", r, 0x0C + 4 * j)[0] for j in range(3)] if r else []


def su_stacks(t, i):
    return su_rec(t, i)[0x26]


def su_hc(t, i):
    return struct.unpack_from("<i", su_rec(t, i), 0x08)[0]


def windows(path, open_tag, close_tag, key_open, key_close):
    """Yield (open line, [(tag, d, n) ...], close line or None) per window of one unit."""
    cur = {}
    for tag, d, n in parse(path):
        if tag == open_tag:
            cur[key_open(d)] = [d, [], n]
        else:
            for w in cur.values():
                w[1].append((tag, d, n))
            if tag == close_tag:
                k = key_close(d)
                if k in cur:
                    o, body, n0 = cur.pop(k)
                    yield o, body, d, n0


def su_windows(path):
    """SU0 .. SUX in order (they do not nest: SuperUniqueSpawn is called from PresetMonSpawn, which SUX closes)."""
    cur = None
    for tag, d, n in parse(path):
        if tag == "SU0":
            cur = [d, [], n]
        elif cur is not None:
            if tag == "SUX":
                yield cur[0], cur[1], d, cur[2]
                cur = None
            else:
                cur[1].append((tag, d, n))


def aur_model(ns, n):
    r, _, _ = rng_range(ns, INIT_HIGH, n)
    return r


# --- superunique windows -------------------------------------------------------------------------------------------
def part_su(paths):
    R, t = Report("su"), T.get()
    for p in paths:
        b = os.path.basename(p)
        for s0, body, sx, n0 in su_windows(p):
            sid = s0["id"]
            R.n("SU0")
            if su_rec(t, sid) is None:
                continue
            st = su_stacks(t, sid)
            su1 = [d for tag, d, _ in body if tag == "SU1"]
            if s0["placed"]:
                if st == 0:
                    if sx.get("u") is not None or su1:
                        R.fail("%s:%d SU0 id %d placed, Stacks 0, still placed" % (p, n0, sid))
                    else:
                        R.n("placed bit set, Stacks 0: refused")
                        R.note("%s:%d id %d (%s) placed 1, Stacks 0 -> no unit, no SU1" % (b, n0, sid, t.name(
                            struct.unpack_from("<h", su_rec(t, sid), 0x04)[0])))
                else:
                    R.n("placed bit set, Stacks %d: %s" % (st, "placed" if sx.get("u") else "none"))
                continue
            if not su1 or not sx.get("u"):
                R.n("SU0 placed 0 without a unit")
                continue
            u = sx["u"]
            fixed = [m for m in su_mods(t, sid) if m][:3]
            k = fixed.index(0) if 0 in fixed else len(fixed)
            fixed = fixed[:k]
            written = [m for m in fixed if m != 24]
            mods1 = [m for m in su1[0]["mods"] if m]
            # the fixed mods are the first written after any post-create mods; extras follow
            if 24 in fixed:
                R.n("records with a fixed 24 (thief)")
                if 24 in mods1 or 24 in [m for m in u["mods"] if m]:
                    R.fail("%s:%d id %d: mod 24 written %s" % (p, n0, sid, mods1))
                else:
                    R.n("thief not written")
                    R.note("%s:%d id %d fixed %s -> SU1 %s SUX %s" % (b, n0, sid, fixed, mods1, u["mods"]))
            if not is_sub(written, mods1):
                R.fail("%s:%d id %d fixed %s not in SU1 %s" % (p, n0, sid, written, mods1))
            else:
                R.n("fixed mods written in order")
            # mod 22 last
            um = [m for m in u["mods"] if m]
            if um and um[-1] == 22 and um[:-1] == mods1:
                R.n("mod 22 appended last")
            else:
                R.fail("%s:%d id %d SUX mods %s after SU1 %s" % (p, n0, sid, um, mods1))
            aurs = [d for tag, d, _ in body if tag == "AUR" and d["u"] == u["u"]]
            aur2 = [d for tag, d, _ in body if tag == "AUR2" and d["u"] == u["u"]]
            smax = [i for i, (tag, d, _) in enumerate(body) if tag == "SMAX" and d.get("boss") == u["u"]]
            for a in aurs:
                if a["r"] != aur_model(a["ns"], a["n"]):
                    R.fail("%s:%d AUR r %d, model %d" % (p, n0, a["r"], aur_model(a["ns"], a["n"])))
                else:
                    R.n("AUR r = Range(Init(name seed), n)")
            if 30 in written:
                R.n("records with a fixed 30 (aura)")
                pos = [i for i, (tag, d, _) in enumerate(body) if tag == "AUR" and d["u"] == u["u"]]
                rows = [d["row"] for tag, d, _ in body if tag == "AURS" and d["u"] == u["u"]]
                ok = (len(aurs) == 2 and aurs[0]["r"] == aurs[1]["r"] and aurs[0]["ns"] == aurs[1]["ns"] and smax
                      and pos[0] < smax[0] < pos[1] and len(set(rows)) == 1 and len(rows) == 2)
                if not ok:
                    R.fail("%s:%d id %d aura calls %s rows %s (SMAX at %s, AUR at %s)" % (p, n0, sid, aurs, rows, smax, pos))
                else:
                    R.n("aura twice: same draw, same row, the second after SpecialModsApply")
                    R.note("%s:%d id %d (hc %d) AUR r %d x2, AURS rows %s" % (b, n0, sid, su_hc(t, sid), aurs[0]["r"], rows))
            if su_hc(t, sid) == 37:
                R.n("Lord De Seis")
                if not aur2 or any(d["idx"] != 5 for d in aur2):
                    R.fail("%s:%d De Seis AUR2 %s" % (p, n0, aur2))
                else:
                    R.n("De Seis index forced to 5")
                    R.note("%s:%d De Seis: drawn r %s, index %s" % (b, n0, [a["r"] for a in aurs],
                                                                    [d["idx"] for d in aur2]))
                    if any(a["r"] != 5 for a in aurs):
                        R.n("De Seis draws that the override changed")
            elif aur2 and any(d["idx"] != a["r"] for d, a in zip(aur2, aurs)):
                R.fail("%s:%d id %d AUR2 %s != AUR r %s" % (p, n0, sid, aur2, aurs))
    return R.out()


def is_sub(a, b):
    """a appears in b as a contiguous run."""
    if not a:
        return True
    for i in range(len(b) - len(a) + 1):
        if b[i:i + len(a)] == a:
            return True
    return False


# --- tails ---------------------------------------------------------------------------------------------------------
def part_tails(paths):
    R, t = Report("tails"), T.get()
    for p in paths:
        b = os.path.basename(p)
        for s0, body, sx, n0 in su_windows(p):
            sut = [(i, d) for i, (tag, d, _) in enumerate(body) if tag == "SUT"]
            if not sut or not sx.get("u"):
                continue
            i0, sd = sut[0]
            idx, u = sd["idx"], sx["u"]["u"]
            tail = body[i0 + 1:]
            sucs = [d for tag, d, _ in tail if tag == "SUC"]
            si0 = [d for tag, d, _ in tail if tag == "SI0"]
            R.n("tails: record %d" % idx)
            if not sucs:
                # an older logger: only the units the tail created
                if idx == 42 or idx in (10, 60, 62):
                    R.note("%s:%d record %d (no SUC lines): %d units created in the tail, classes %s" % (
                        b, n0, idx, len(si0), dict(collections.Counter(d["cls"] for d in si0))))
                    if idx == 42:
                        if len(si0) == 20 and all(d["cls"] == 0x1C5 for d in si0):
                            R.n("tail 42 (kept log): 20 escorts of class 453")
                        else:
                            R.fail("%s:%d tail 42 escorts %s" % (p, n0, [d["cls"] for d in si0]))
                elif si0:
                    R.fail("%s:%d record %d created units in a no-spawn tail" % (p, n0, idx))
                continue
            calls = [(d["to"], d["st"], d) for d in sucs]
            if not calls or calls[-1][0] != APP or calls[-1][1][:2] != [0x16, 1]:
                R.fail("%s:%d record %d: the last call %s is not ModAppendApply(22, 1)" % (p, n0, idx, calls[-1:]))
                continue
            calls = calls[:-1]
            want = TAILS.get(idx, [])
            if want == "radament":
                surd = [d for tag, d, _ in tail if tag == "SURD"]
                rc = [d for d in sucs if d["to"] == RANGE]
                if len(surd) != 1 or len(rc) != 1:
                    R.fail("%s:%d Radament SURD %s" % (p, n0, surd))
                    continue
                # the seed before the draw: SUT's (0x005A4BE4; nothing draws between the switch and 0x005A4CD9),
                # and the call's ECX is the unit's seed field
                if rc[0]["ecx"] != u + 0x20 or rc[0]["edx"] != 5:
                    R.fail("%s:%d Radament Range(ecx %#x, edx %d)" % (p, n0, rc[0]["ecx"], rc[0]["edx"]))
                    continue
                lo, hi = (int(x, 16) for x in sd["us"].split(":"))
                r, lo2, hi2 = rng_range(lo, hi, 5)
                after = "%08x:%08x" % (lo2, hi2)
                near = [d for d in sucs if d["to"] == NEAR]
                cls = [d["st"][0] for d in near]
                want_cls = [4] * (r + 2) + RADAMENT_ESC
                if surd[0]["eax"] != r or surd[0]["us"] != after or cls != want_cls:
                    R.fail("%s:%d Radament r %d (model %d), us %s (model %s), classes %s" % (
                        p, n0, surd[0]["eax"], r, surd[0]["us"], after, cls))
                    continue
                if any(d["st"][1:4] != [1, 4, 0x40] for d in near):
                    R.fail("%s:%d Radament SpawnNearUnitNoBox args %s" % (p, n0, [d["st"] for d in near]))
                rets = [d["eax"] for tag, d, _ in tail if tag == "SUCR"]
                made = [d["cls"] for d in si0]
                R.n("tail 10 reproduced")
                R.note("%s:%d Radament: Range(us, 5) = %d -> %d x class 4, then %s; units created %d %s, returns %d "
                       "non-zero" % (b, n0, r, r + 2, RADAMENT_ESC, len(made), dict(collections.Counter(made)),
                                     sum(1 for x in rets if x)))
                continue
            got = [c[0] for c in calls]
            if got != [w[0] for w in want]:
                R.fail("%s:%d record %d calls %s, model %s" % (p, n0, idx, [hex(c) for c in got],
                                                              [hex(w[0]) for w in want]))
                continue
            ok = True
            esc_cls = None
            for (to, stk, d), (_, args) in zip(calls, want):
                if args is None:
                    continue
                for k, a in enumerate(args):
                    if a is None:
                        continue
                    if a == "u":
                        a = u
                    if a == "cls":
                        rets = [x for tag, x, _ in tail if tag == "SUCR" and x["at"] == 0x005A4DE9]
                        esc_cls = rets[0]["eax"] if rets else None
                        a = esc_cls
                    if stk[k] != a:
                        ok = False
                        R.fail("%s:%d record %d call %#x arg %d = %#x, model %#x" % (p, n0, idx, to, k, stk[k], a))
                if to in (QH, Q545) and d["edx"] != u:
                    ok = False
                    R.fail("%s:%d record %d call %#x on unit %#x, not the superunique %#x" % (p, n0, idx, to, d["edx"], u))
            if not ok:
                continue
            R.n("tail %d calls reproduced" % idx)
            esc = [i for i, (tag, d, _) in enumerate(tail) if tag == "SUC" and d["to"] == ESC]
            if esc:
                j0 = esc[0]
                j1 = next((i for i, (tag, d, _) in enumerate(tail) if i > j0 and tag == "SUCR"), None)
                made = [d["cls"] for tag, d, _ in tail[j0:j1] if tag == "SI0"]
                cnt = tail[j0][1]["st"][3]
                want_c = tail[j0][1]["st"][0]
                R.note("%s:%d record %d EscortSpawn(class %d, count %d, radius %d, flags %#x): %d units %s, return %#x" % (
                    b, n0, idx, want_c, cnt, tail[j0][1]["st"][2], tail[j0][1]["st"][4], len(made),
                    dict(collections.Counter(made)), tail[j1][1]["eax"] if j1 is not None else -1))
                if any(c != want_c for c in made) or len(made) > cnt:
                    R.fail("%s:%d record %d escorts %s" % (p, n0, idx, made))
                else:
                    R.n("tail %d escorts: class as passed, at most the count" % idx)
                    if len(made) == cnt:
                        R.n("tail %d escorts: the full count" % idx)
            other = [d["cls"] for tag, d, _ in tail if tag == "SI0"]
            if not esc and idx != 10 and other:
                R.fail("%s:%d record %d created %s" % (p, n0, idx, other))
            R.note("%s:%d record %d: %s" % (b, n0, idx, ", ".join("%#x%s" % (c[0], c[1][:5] if c[0] != Q545 else "")
                                                                for c in calls)))
    return R.out()


# --- the handler walk ----------------------------------------------------------------------------------------------
def part_handlers(paths):
    R, t = Report("handlers"), T.get()
    always = [1, 2, 3, 4]
    null = [i for i, h in enumerate(t.handler) if h == 0]
    R.note("g_UModHandlers null rows: %s" % null)
    for p in paths:
        b = os.path.basename(p)
        cur = {}
        for tag, d, n in parse(p):
            if tag == "SMA0":
                cur[d["boss"]] = (n, [])
            elif tag == "HD0" and d["u"] in cur:
                cur[d["u"]][1].append(d["m"])
            elif tag == "SMAX" and d.get("boss") in cur:
                n0, got = cur.pop(d["boss"])
                if "u" not in d:
                    R.n("SMAX without the unit's list (older logger)")
                    continue
                mods = []
                for m in d["u"]["mods"]:
                    if m == 0:
                        break
                    mods.append(m)
                want = [m for m in always + mods if t.handler[m]]
                R.n("SpecialModsApply windows")
                if got != want:
                    R.fail("%s:%d unit %d mods %s: HD0 %s, model %s" % (p, n0, d["boss"], mods, got, want))
                    continue
                R.n("HD0 sequence = non-null rows of [1..4] + list")
                for m in mods:
                    if not t.handler[m]:
                        R.n("null row %d skipped" % m)
                        if m in (10, 11, 12, 13, 14, 15) and R.c["null row %d skipped" % m] <= 3:
                            R.note("%s:%d unit %d (class %d) mods %s: HD0 %s" % (b, n0, d["boss"], d["u"]["cls"],
                                                                                  mods, got))
    return R.out()


# --- the Chaos Sanctuary gate --------------------------------------------------------------------------------------
def part_gate(paths):
    R = Report("gate")
    for p in paths:
        b = os.path.basename(p)
        gq = None
        for tag, d, n in parse(p):
            if tag == "GQ":
                gq = (d, n)
            elif tag == "PG" and gq is not None:
                q, n0 = gq
                gq = None
                want = 0 if q["eax"] else 1
                R.n("GQ byte %d" % q["eax"])
                if d["r"] != want:
                    R.fail("%s:%d GQ %d then PG %d" % (p, n0, q["eax"], d["r"]))
                else:
                    R.n("gate result as the byte gives (byte %d -> %d)" % (q["eax"], want))
                    if q["eax"] and R.c["gate closed shown"] < 5:
                        R.note("%s:%d room %#x: byte %d, gate 0" % (b, n0, q["room"], q["eax"]))
                    if q["eax"]:
                        R.n("gate closed shown")
    return R.out()


# --- the boss-class monster level ----------------------------------------------------------------------------------
def part_boss(paths):
    R, t = Report("boss"), T.get()
    import monpool
    mp = monpool.Tables(H.EXCEL)
    boss = {c for c, r in enumerate(t.ms) if r[0x0C] & 0x40}
    R.note("boss-flag classes (%d): %s" % (len(boss), sorted(boss)))
    for p in paths:
        b = os.path.basename(p)
        last = None
        for tag, d, n in parse(p):
            if tag == "SI0":
                last = d
            elif tag == "SI2" and last is not None and last["u"] == d["u"]:
                c = last["cls"]
                if c not in boss:
                    continue
                exp, dd = last.get("exp", last.get("g70")), min(last.get("g6d", 0), 2)
                want = struct.unpack_from("<h", t.ms[c], 0xAA + 2 * dd)[0]
                if d["lvl"] != want:
                    R.fail("%s:%d boss class %d d %d level %d, MonStats %d" % (p, n, c, dd, d["lvl"], want))
                    continue
                key = "%s d%d" % ("expansion" if exp else "classic", dd)
                R.n("boss level = MonStats Level[d]: " + key)
                if exp and dd > 0:
                    area = mp.monlvl(last["lid"], dd, 1) if mp else None
                    sep = area is not None and area != want
                    R.n("expansion d>0 class %d%s" % (c, " (area level differs)" if sep else " (area level equal)"))
                    R.note("%s:%d class %d (%s) level id %d d %d: level %d, MonStats %d, area MonLvlEx %s" % (
                        b, n, c, t.name(c), last["lid"], dd, d["lvl"], want, area))
                last = None
    return R.out()


# --- the fixed client names ----------------------------------------------------------------------------------------
def fixed_names():
    """class -> string index, from the builder's two jump tables (0x004ACB80 by the byte table 0x004ACB98 for classes
    156..333, 0x004ACC4C for 704..709) and the 0x220 (544) compare; each target begins with mov ecx, imm32."""
    out = {}
    tb = drlg.exe_read(EXE, 0x004ACB98, 0xB2)
    jt = struct.unpack("<6I", drlg.exe_read(EXE, 0x004ACB80, 24))
    for i, k in enumerate(tb):
        a = jt[k]
        if a != 0x004ACAF6:
            code = drlg.exe_read(EXE, a, 5)
            assert code[0] == 0xB9, hex(a)
            out[156 + i] = struct.unpack_from("<I", code, 1)[0]
    j2 = struct.unpack("<6I", drlg.exe_read(EXE, 0x004ACC4C, 24))
    for i, a in enumerate(j2):
        if a != 0x004ACAF6:
            code = drlg.exe_read(EXE, a, 5)
            assert code[0] == 0xB9
            out[0x2C0 + i] = struct.unpack_from("<I", code, 1)[0]
    code = drlg.exe_read(EXE, 0x004ACAAC, 5)
    out[0x220] = struct.unpack_from("<I", code, 1)[0]
    return out


def part_names(paths):
    rc = H.part_names(paths)
    R, t = Report("names-fixed"), T.get()
    fx = fixed_names()
    R.note("fixed-name classes -> string: %s" % ", ".join("%d:%d" % kv for kv in sorted(fx.items())))
    if set(fx) != set(t.sp.name_fixed):
        R.fail("fixed classes %s, monspecial.py %s" % (sorted(fx), sorted(t.sp.name_fixed)))
    for p in paths:
        b = os.path.basename(p)
        exp = H.game_exp(p)[0]
        G = t.strings(exp)
        pend = None
        for tag, d, n in parse(p):
            if tag == "CNB":
                pend = None
                if d["special"] and not d["mf"] & 0x06 and (d["m"] == 12 or d["cls"] in fx):
                    pend = {"d": d, "cns": [], "cnt": [], "n": n, "k": "mod12" if d["m"] == 12 else "fixed"}
            elif tag == "CNS" and pend is not None:
                pend["cns"].append(d["idx"])
            elif tag == "CNT" and pend is not None:
                pend["cnt"].append(d["text"])
                c = pend["d"]
                idx = 3111 if pend["k"] == "mod12" else fx[c["cls"]]
                want_t = G.by_index(idx)[3]
                if pend["cns"] != [idx] or pend["cnt"] != [want_t]:
                    R.fail("%s:%d class %d mod %d: strings %s text %s, model %d %r" % (
                        p, pend["n"], c["cls"], c["m"], pend["cns"], pend["cnt"], idx, want_t))
                else:
                    R.n("%s name reproduced: class %d" % (pend["k"], c["cls"]))
                    if R.c["%s name reproduced: class %d" % (pend["k"], c["cls"])] == 1:
                        R.note("%s:%d class %d (%s) mod %d: string %d %r" % (b, pend["n"], c["cls"], t.name(c["cls"]),
                                                                           c["m"], idx, want_t))
                pend = None
    return max(rc, R.out())


# --- wanderers -----------------------------------------------------------------------------------------------------
def part_wander(paths):
    R = Report("wander")
    for p in paths:
        acts = collections.Counter()
        for tag, d, n in parse(p):
            if tag == "RTK0":
                R.n("RTK0 ticks")
                lid = d.get("lid")
                if lid is not None:
                    acts["act %d" % (1 if lid < 40 else 2 if lid < 75 else 3 if lid < 103 else 4 if lid < 109 else 5)] += 1
            elif tag == "WRL":
                R.n("WRL (roll past the 1/32768 gate)")
                R.note("%s:%d WRL %s" % (os.path.basename(p), n, d))
        for k, v in acts.items():
            R.n("RTK0 " + k, v)
    return R.out()


PARTS = {"su": part_su, "tails": part_tails, "handlers": part_handlers, "gate": part_gate, "boss": part_boss,
         "names": part_names, "wander": part_wander}


def main(argv):
    if "-v" in argv:
        H.VERBOSE = True
        argv = [a for a in argv if a != "-v"]
    if len(argv) < 2 or (argv[0] not in PARTS and argv[0] != "check"):
        print(__doc__)
        return 2
    paths = argv[1:]
    parts = list(PARTS) if argv[0] == "check" else [argv[0]]
    rc = 0
    for part in parts:
        rc = max(rc, PARTS[part](paths))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

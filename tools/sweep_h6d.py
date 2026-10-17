#!/usr/bin/env python3
"""Checker for plan 0038 batch H6d (quest-b6): the quest-TC switch with a mercenary, a summon and the five boss
classes, the death order, Warriv's report, Andariel's gems by game type, the Hellforge's stat-356 boundary and Baal's
gold, over tools/gdb/quests.gdb logs; plus two static reads of the pinned game.exe.

    python3 -I tools/sweep_h6d.py logs <log> [<log> ...] [-v]
    python3 -I tools/sweep_h6d.py static <game.exe>
    python3 -I tools/sweep_h6d.py copies <log> [<log> ...]

logs (the model is docs/findings/items/0010-quest-drops.md; tools/questdrops.py and tools/tc.py check the rest):
- B6 groups (B60 .. B6X) through tools/tc.py's b6_model; for a non-player killer the owner (B6O) must be the unit
  whose record B6P reads, and B6X must pass the B60 killer on (the unresolved killer, step B7). Counted by killer
  kind (player, hireling, summon, other) and outcome.
- QME (the quest death event): its player must be the killer when the killer is a player, else the owner B6O found
  for the same kill (a quest-hooked monster without a B6 group: any non-zero player is counted only).
- Death order: for each B6X of a TCQuestId class, the MMR line of that monster (mode 0) comes first with the standard
  record 0x006E2260 and start 0x005A6FF0, no quest-bit write of the class's word lies between MMR and B6X, and the
  QME of the monster comes after B6X; the writes of the class's word after it are listed by return address.
- Warriv: writes of word 6 from sub_00595C60_A1Q6_NpcMessage (return 0x00595C60 .. 0x00596000): clear bit 1 and
  set bit 0, each on a word whose bit 1 was set.
- Andariel's gems: the QDI creations from 0x005966B2 / 0x0059672B counted by difficulty and game type.
- Hellforge strikes: FOP lines with the forge in mode 2; the strike count must rise by one per FOP while the player
  holds the hammer, and word 27 must get bits 13 and 1 at the third strike.
- Baal's gold: BG0's bounds are 6000 d + 1500 and min(6000 d + 3000, 0xFFFF); each BGR amount is
  RandLoHi(qs, lo, hi) on the quest seed of the QGS before it (return 0x0058E057), the quest seed after it is the
  model's, and each GLD pile carries the amount (stat 14 too); the number of draws is BG0's count.
static: the death-mode table choice of sub_005A78A0_MonModeRecord for mode 0 of every class it can be called with,
  from its code and jump tables; and the callers of sub_00530F40_ItemCreateFromOldRec (the only writer of a record
  restore flag, +0x2C = 1) and of sub_0055A2A0_ItemCopy's creation (sub_00558CB0_ItemCreateFromSave).
copies: in logs of tools/gdb/quests.gdb, the item creations (IC0, ItemCreateByQuality) between each NPC service call
  (MA) and its result line (LZ0 / PZ / IMB0): the copies Larzuk and Anya work on are made without one.
Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
import tc  # noqa: E402

QWORD = {156: 6, 211: 14, 242: 22, 243: 26, 544: 40}       # TCQuestId of the five classes (MonStats)
HIRELINGS = {271, 338, 359, 560, 561}                      # MonStats classes of the hireling rows (Hireling.txt)
SUMMONS = {351, 352, 353, 289, 290, 291, 292, 357, 363, 364, 420, 421, 428}   # hydra1-3, golems, valkyrie, ...
MODE0_REC, MODE0_START = 0x006E2260, 0x005A6FF0
ANDARIEL_GEMS = (0x005966B2, 0x0059672B)
WARRIV = (0x00595C60, 0x00596000)
TAGS = {"B60", "B6O", "B6E", "B6F", "B6P", "B6G", "B6X", "QME", "MMR", "QS", "QC", "QGS", "QDI", "FOP", "BG0", "BGR",
        "GLD", "QI1"}


def sp(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def rand_lohi(seed, lo, hi):
    """RNG_RandLoHi (0x004BC500): hi <= lo (signed) gives lo; else one step, lo + (low & (n - 1)) for a power of two
    n = hi - lo, else lo + low mod n."""
    if hi <= lo:
        return lo, seed
    n = hi - lo
    s = rng.step(*seed)
    r = s[0] & (n - 1) if n & (n - 1) == 0 else s[0] % n
    return lo + r, s


def kind(u):
    if not u:
        return "none"
    if u[0] == 0:
        return "player"
    if u[0] == 1 and u[1] in HIRELINGS:
        return "hireling"
    if u[0] == 1 and u[1] in SUMMONS:
        return "summon"
    return "type %d class %d" % (u[0], u[1])


class Bad(Exception):
    pass


def read(path):
    ev = []
    for k, line in enumerate(open(path, errors="replace")):
        tag, _, rest = line.strip().partition(" ")
        if tag not in TAGS or not rest.startswith("{"):
            continue
        try:
            ev.append((k + 1, tag, json.loads(rest)))
        except ValueError:
            continue
    return ev


def check_logs(paths, verbose):
    n = collections.Counter()
    bad = 0

    def fail(where, msg):
        nonlocal bad
        bad += 1
        print("BAD %s: %s" % (where, msg))

    for path in paths:
        name = os.path.basename(path)
        ev = read(path)
        n["logs"] += 1
        q = None
        pend = None
        baal = None
        words = {}
        b6 = None
        kills = []              # (index of B60, index of B6X, group)
        for i, (ln, tag, d) in enumerate(ev):
            where = "%s:%d %s" % (name, ln, tag)
            try:
                if tag == "QI1":
                    q = sp(d["qs"])
                elif tag in ("QS", "QC"):
                    if d["old"] is not None:
                        words[(d["rec"], d["w"])] = d["old"]
                    ret = int(d["ret"], 16)
                    if d["w"] == 6 and WARRIV[0] <= ret < WARRIV[1]:
                        old = d["old"]
                        want = (tag, d["b"]) in (("QC", 1), ("QS", 0))
                        if not want or old is None or not (old >> 1) & 1 and (tag, d["b"]) == ("QC", 1):
                            raise Bad("Warriv write %s bit %d on word 0x%04x" % (tag, d["b"], old or 0))
                        n["warriv: %s bit %d (word before 0x%04x)" % (tag, d["b"], old)] += 1
                elif tag == "B60":
                    b6 = [(tag, d, i)]
                elif tag in ("B6O", "B6E", "B6F", "B6P", "B6G"):
                    if b6 is not None:
                        b6.append((tag, d, i))
                elif tag == "B6X":
                    if b6 is None:
                        raise Bad("B6X without B60")
                    b6.append((tag, d, i))
                    grp = [(t, v) for t, v, _ in b6]
                    want, taken, why = tc.b6_model(grp)
                    b0 = grp[0][1]
                    k0 = b0["killer"]
                    one = {t: v for t, v in grp[1:-1] if t != "B6G"}
                    if k0 and k0[0] != 0:
                        own = one.get("B6O", {}).get("owner")
                        if own and own[0] == 0 and one.get("B6P", {}).get("unit") != own:
                            raise Bad("owner %s, but B6P reads %s" % (own, one.get("B6P")))
                    if d["killer"] != k0:
                        raise Bad("B6X killer %s, B60 killer %s: not the unresolved killer" % (d["killer"], k0))
                    cls = b0["mon"][1]
                    lab = "B6 class %d diff %d killer %s%s: %s" % (
                        cls, b0["diff"], kind(k0),
                        " -> owner %s" % kind(one["B6O"]["owner"]) if "B6O" in one else "",
                        "taken" if taken else "not taken (%s)" % why)
                    n[lab] += 1
                    if verbose:
                        print("%s: %s word %s tc %d" % (where, lab, one.get("B6P", {}).get("word"), want))
                    kills.append((b6[0][2], i, grp, one))
                    b6 = None
                elif tag == "QGS":
                    pend = (int(d["ret"], 16), sp(d["qs"]))
                elif tag == "QDI":
                    ret = int(d["ret"], 16)
                    if ret in ANDARIEL_GEMS:
                        n["andariel gem %s diff %d %s" % (d["code"].strip(), d["diff"],
                                                          "expansion" if d["exp"] else "classic")] += 1
                elif tag == "BG0":
                    dd = d["diff"]
                    lo, hi = 6000 * dd + 1500, min(6000 * dd + 3000, 0xFFFF)
                    if (d["lo"], d["hi"]) != (lo, hi):
                        raise Bad("Baal gold bounds %d..%d, model %d..%d" % (d["lo"], d["hi"], lo, hi))
                    baal = {"lo": lo, "hi": hi, "n": d["n"], "draws": 0, "amt": None}
                    n["baal gold loops (diff %d, %d players)" % (dd, d["n"])] += 1
                elif tag == "BGR":
                    if baal is None or pend is None or pend[0] != 0x0058E057:
                        raise Bad("BGR without BG0 and its QGS (0x0058E057)")
                    amt, s = rand_lohi(pend[1], baal["lo"], baal["hi"])
                    if d["amt"] != amt or sp(d["qs"]) != s:
                        raise Bad("Baal gold %d qs %s, model %d %08x:%08x" % (d["amt"], d["qs"], amt, s[0], s[1]))
                    baal["draws"] += 1
                    baal["amt"] = amt
                    pend = None
                    n["baal gold draws reproduced"] += 1
                elif tag == "GLD":
                    if baal is None or baal["amt"] is None:
                        raise Bad("GLD outside a Baal gold draw")
                    if d["amt"] != baal["amt"] or d["s14"] != baal["amt"]:
                        raise Bad("gold pile %s stat 14 %s, drawn %d" % (d["amt"], d["s14"], baal["amt"]))
                    n["baal gold piles (one per draw, stat 14 = the amount)"] += 1
                    if baal["draws"] == baal["n"]:
                        baal = None
                elif tag == "FOP":
                    pass
            except (Bad, tc.Mismatch, KeyError, TypeError) as e:
                fail(where, e)
                if tag == "B6X":
                    b6 = None
        if baal is not None and baal["draws"] != baal["n"]:
            fail(name, "Baal gold: %d draws, count %d" % (baal["draws"], baal["n"]))
        # death order and the death event's player, per kill
        for (i0, ix, grp, one) in kills:
            b0, bx = grp[0][1], grp[-1][1]
            mon, cls = b0["mon"], b0["mon"][1]
            w = QWORD.get(cls)
            where = "%s:%d kill of %s" % (name, ev[ix][0], mon)
            mmr = [j for j in range(i0 - 1, max(-1, i0 - 400), -1) if ev[j][1] == "MMR" and ev[j][2]["mon"] == mon]
            if not mmr:
                fail(where, "no MMR (mode 0) line before the B6 test")
                continue
            m = ev[mmr[0]][2]
            if int(m["rec"], 16) != MODE0_REC or int(m["start"], 16) != MODE0_START:
                fail(where, "mode 0 record %s start %s" % (m["rec"], m["start"]))
            between = [ev[j] for j in range(mmr[0], ix) if ev[j][1] in ("QS", "QC") and ev[j][2]["w"] == w]
            if between:
                fail(where, "quest word %d written before the drop: %s" % (w, between[0][2]))
            qme = [j for j in range(ix, min(len(ev), ix + 4000)) if ev[j][1] == "QME" and ev[j][2]["mon"] == mon]
            if not qme:
                fail(where, "no QME after the drop")
                continue
            qd = ev[qme[0]][2]
            k0 = b0["killer"]
            want = k0 if k0 and k0[0] == 0 else one.get("B6O", {}).get("owner") or 0
            if qd["killer"] != k0 or qd["player"] != want:
                fail(where, "QME killer %s player %s, model %s %s" % (qd["killer"], qd["player"], k0, want))
                continue
            after = collections.Counter()
            for j in range(ix, len(ev)):
                if ev[j][1] == "B60":
                    break
                if ev[j][1] in ("QS", "QC") and ev[j][2]["w"] == w:
                    after["%s %s b%d" % (ev[j][1], ev[j][2]["ret"], ev[j][2]["b"])] += 1
            n["order: class %d MMR (mode 0 standard) < B6X < QME (player %s)" % (cls, kind(want))] += 1
            if verbose or after:
                print("%s: word %d writes after the drop: %s" % (where, w, dict(after)))
        # Hellforge strikes
        prev = None
        for i, (ln, tag, d) in enumerate(ev):
            if tag != "FOP":
                continue
            if prev is not None and d["mode"] == 2 and prev["mode"] == 2 and prev["strikes"] is not None:
                if d["strikes"] not in (prev["strikes"], prev["strikes"] + 1):
                    fail("%s:%d FOP" % (name, ln), "strikes %s after %s" % (d["strikes"], prev["strikes"]))
            prev = d
        st = [d for _, t, d in ev if t == "FOP"]
        if st:
            n["forge: FOP %d, strikes seen %s, word 27 after %s" % (
                len(st), sorted({d["strikes"] for d in st if d["strikes"] is not None}),
                ["0x%04x" % d["w27"] for d in st if d["w27"] is not None][-1:])] += 1
    for k in sorted(n):
        print("%-90s %d" % (k, n[k]))
    print("sweep_h6d logs: %d bad" % bad)
    return 0 if bad == 0 else 1


# ---------------------------------------------------------------- static reads of the pinned game.exe
class PE:
    def __init__(self, path):
        self.d = open(path, "rb").read()
        d = self.d
        pe = struct.unpack_from("<I", d, 0x3C)[0]
        ns = struct.unpack_from("<H", d, pe + 6)[0]
        osz = struct.unpack_from("<H", d, pe + 20)[0]
        self.secs = []
        for i in range(ns):
            o = pe + 24 + osz + 40 * i
            vs, va, rs, ra = struct.unpack_from("<IIII", d, o + 8)
            self.secs.append((va, max(vs, rs), ra, rs))

    def off(self, va):
        r = va - 0x400000
        for a, sz, ra, rs in self.secs:
            if a <= r < a + sz:
                return ra + r - a
        raise KeyError(hex(va))

    def rd(self, va, n):
        o = self.off(va)
        return self.d[o:o + n]

    def calls_to(self, target):
        """E8 rel32 calls whose destination is target, in the executable sections."""
        out = []
        for a, sz, ra, rs in self.secs[:1]:
            blob = self.d[ra:ra + rs]
            k = blob.find(b"\xE8")
            while k != -1 and k + 5 <= len(blob):
                rel = struct.unpack_from("<i", blob, k + 1)[0]
                src = 0x400000 + a + k
                if (src + 5 + rel) & 0xFFFFFFFF == target:
                    out.append(src)
                k = blob.find(b"\xE8", k + 1)
        return out


def check_static(path):
    pe = PE(path)
    bad = 0
    # sub_005A78A0_MonModeRecord: class ranges 0xF3..0x1A2 (byte table 0x5A79C4, jumps 0x5A79B4) and 0x220..0x2C5
    # (0x5A7A80, 0x5A7A74), and 0x21F straight to 0x5A7991; the case blocks and the modes they return a special
    # record for (read from the code below the jumps, 0x005A792A .. 0x005A799D)
    case_modes = {0x5A792A: {4, 5, 8, 9}, 0x5A794E: {11}, 0x5A7977: {10, 11}, 0x5A7991: {10}, 0x5A799E: set()}
    expect = {0x5A792A: b"\x83\xF8\x04", 0x5A794E: b"\x83\xF8\x0B", 0x5A7977: b"\x83\xF8\x0B",
              0x5A7984: b"\x83\xF8\x0A", 0x5A7991: b"\x83\xF8\x0A", 0x5A799E: b"\xC1\xE0\x04"}
    for a, want in expect.items():
        if pe.rd(a, 3) != want:
            print("BAD static: %08x does not start with %s" % (a, want.hex()))
            bad += 1
    if pe.rd(0x5A79A2, 5) != b"\x05\x60\x22\x6E\x00":
        print("BAD static: the default record base is not 0x006E2260")
        bad += 1
    if pe.rd(0x5A78EF, 7) != b"\x80\xB9\xA5\x01\x00\x00\x00":
        print("BAD static: the MonStats+0x1A5 test is not at 0x005A78EF")
        bad += 1
    seen = collections.defaultdict(list)
    for base, cnt, bt, jt in ((0xF3, 0xB0, 0x5A79C4, 0x5A79B4), (0x220, 0xA6, 0x5A7A80, 0x5A7A74)):
        for k in range(cnt):
            i = pe.rd(bt + k, 1)[0]
            t = struct.unpack("<I", pe.rd(jt + 4 * i, 4))[0]
            seen[t].append(base + k)
    seen[0x5A7991].append(0x21F)
    for t in sorted(seen):
        if t not in case_modes:
            print("BAD static: jump target %08x not read" % t)
            bad += 1
            continue
        cl = seen[t]
        print("MonModeRecord case %08x: modes %s -> special record; %d classes (%s)" % (
            t, sorted(case_modes[t]) or "none", len(cl), ", ".join(str(c) for c in cl if c in QWORD) or "-"))
    mode0 = [t for t in seen if 0 in case_modes.get(t, {0})]
    print("mode 0 special for any class: %s" % ("yes: %s" % mode0 if mode0 else "no (every case falls to 0x006E2260)"))
    if mode0:
        bad += 1
    # the restore flag: the only constant store of 1 to a record's +0x2C before ItemCreate is ItemCreateFromOldRec
    c = pe.calls_to(0x00530F40)
    print("callers of sub_00530F40_ItemCreateFromOldRec: %s" % ", ".join("%08x" % x for x in c))
    if pe.rd(0x00530FDA, 7) != b"\xC7\x45\xA4\x01\x00\x00\x00":
        print("BAD static: no `mov [ebp-0x5c], 1` (record +0x2C) at 0x00530FDA")
        bad += 1
    c2 = pe.calls_to(0x00558CB0)
    print("callers of sub_00558CB0_ItemCreateFromSave: %s" % ", ".join("%08x" % x for x in c2))
    c3 = pe.calls_to(0x00558D90)
    print("callers of sub_00558D90_ItemCreate: %d" % len(c3))
    print("sweep_h6d static: %d bad" % bad)
    return 0 if bad == 0 else 1


def check_copies(paths):
    n = collections.Counter()
    for path in paths:
        ma = None
        ic = 0
        for line in open(path, errors="replace"):
            tag = line.split(" ", 1)[0]
            if tag == "MA":
                ma, ic = True, 0
            elif tag == "IC0" and ma:
                ic += 1
            elif tag in ("LZ0", "PZ", "IMB0") and ma:
                n["%s after MA with %d IC0 between" % (tag, ic)] += 1
                ma = None
    for k in sorted(n):
        print("%-50s %d" % (k, n[k]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("logs")
    a.add_argument("logs", nargs="+")
    a.add_argument("-v", "--verbose", action="store_true")
    s = sub.add_parser("static")
    s.add_argument("exe")
    c = sub.add_parser("copies")
    c.add_argument("logs", nargs="+")
    ns = ap.parse_args(argv)
    if ns.cmd == "logs":
        return check_logs(ns.logs, ns.verbose)
    if ns.cmd == "static":
        return check_static(ns.exe)
    return check_copies(ns.logs)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

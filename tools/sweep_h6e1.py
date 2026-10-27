#!/usr/bin/env python3
"""Checker for plan 0038 batch H6e1 (quest-npc): the given items, the NPC item services, their tests, the cursor
item each consumes and the shared tail, against the readings of docs/findings/items/0010-quest-drops.md § 6 and the
service branches of NPC_MenuAction (0x00579D60). Reads logs of tools/gdb/quest-npc.gdb.

Usage:
  python3 -I tools/sweep_h6e1.py check <excel-dir> <game.exe> <log> [<log> ...]
  python3 -I tools/sweep_h6e1.py static <game.exe>     the direct callers of the functions the run reads (objdump)

Models (every model input is the logged game state, the stock excel tables or the pinned game.exe's data):
  can      each CAN line (ItemCanImbue 0x0062C590, ItemCanPersonalize 0x0062C6A0, ItemCanQuestSocket 0x0062C770):
           the tests of § 6 in code order, each step value against the table value it reads (the base type index,
           ItemTypes Throwable, bitfield1 bit 0, the record's quest, compactsave, Nameable, the item code, the
           children count, flag 0x800 / 0x100, ItemMaxSockets = min(gemsockets, MaxSock1/25/40 by ilvl), the socket
           count, the quality), the steps the function ran (it returns at the first failing test) and the result
  socket   LZ0..LZY: n = 1 + RangeB(item seed, min(max, 2)) for quality 4 (the draw re-done on the logged seed),
           1 for 5..9, max for 1..3; stat 194 after ITEMS_SetSockets = n
  imbue    IMB0..IMBX: ilvl = max(clvl, 1), + 4 when > 5; flags +0x80 = 0x20 | (ethereal ? 0x04 : 0x02); quality 6;
           the new item ethereal exactly when the old one was
  cursor   CIC: the consumed item is the player's cursor item; CICR 1
  tail     RPA/RPX: a repaired item has durability = its maximum and a stackable one the base's maxstack after the
           call; an unidentified item (the imbue's new rare) is left as it was; IDA/IDX: identified (flag 0x10) after
  give     QGV/QGC/QGD/QGX by the caller's return: Akara's and Ormus's rings (code, ilvl and quality by difficulty),
           Qual-Kehk's runes (the first n of r07 r08 r09, n by word 36 bits 6 and 7), Malah's ice and tr2 and Anya's
           item (ilvl 0 = clvl, quality); the created item's code, ilvl and quality; durability = maximum after QGD;
           (the created quality 7 for a base with `unique` 1, the pre-switch override); every call through
           ITEMS_CreateForStore (CF0 from 0x00546700, kind 4, noEthereal 1); Anya's code is
           entry r of the logged table, the table the one of the difficulty
"""
import csv
import json
import os
import struct
import sys
from collections import Counter

IMAGE_BASE = 0x400000
RNG_A = 0x6AC690C5


def rows(excel, name):
    with open(os.path.join(excel, name), encoding="latin1") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


class Tables:
    def __init__(self, excel):
        self.items = []
        for t in ("weapons.txt", "armor.txt", "misc.txt"):
            self.items += [r for r in rows(excel, t) if r.get("code")]
        self.types = [r for r in rows(excel, "itemtypes.txt") if r["ItemType"] != "Expansion"]   # the .txt separator
        # row, which the game's table does not have (the logged type indices of gsv, jew: 96, 58)
        self.tidx = {r["Code"]: i for i, r in enumerate(self.types) if r["Code"]}

    def rec(self, cls):
        return self.items[cls]

    def code(self, cls):
        return self.items[cls]["code"]

    def type_index(self, cls):
        return self.tidx.get(self.rec(cls)["type"], 0)

    def throwable(self, cls):
        return num(self.types[self.type_index(cls)]["Throwable"])

    def nameable(self, cls):
        r = self.rec(cls)
        return num(r.get("nameable", r.get("Nameable")))

    def max_sockets(self, cls, ilvl):
        t = self.types[self.type_index(cls)]
        m = num(t["MaxSock1"]) if ilvl <= 25 else num(t["MaxSock25"]) if ilvl <= 40 else num(t["MaxSock40"])
        return min(num(self.rec(cls)["gemsockets"]), m)


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


def parse(path):
    out = []
    with open(path, errors="replace") as f:
        for ln in f:
            tag, _, rest = ln.partition(" ")
            if rest.startswith("{"):
                try:
                    out.append((tag, json.loads(rest)))
                except ValueError:
                    pass
    return out


def fl(it):
    return int(it.get("fl") or "0", 16)


def can_model(T, d):
    """[(site, expected value or None)], expected r, expected return site"""
    it = d["item"]
    cls, q, f = it["u"][1], it["q"], fl(it)
    rec = T.rec(cls)
    ty = T.type_index(cls)
    quest, code = num(rec.get("quest")), rec["code"].ljust(4)
    kids = it.get("kids", 0)
    steps = []
    fn = d["fn"]
    if fn == "0062c590":                                   # ItemCanImbue
        R0, R1, RG = "0062c686", "0062c67b", "0062c68e"
        steps.append(("0062c5ca", ty))
        if ty == 4 or f & 0x1000:
            return steps, 0, RG
        steps.append(("0062c5f7", num(rec["bitfield1"]) & 1))
        if not num(rec["bitfield1"]) & 1:
            return steps, 0, R0
        if not int(d["c8"], 16) >> 25 & 1:
            steps.append(("0062c613", T.throwable(cls)))
            if T.throwable(cls):
                return steps, 0, R0
        steps.append(("0062c61d", {"quest": quest}))
        if quest:
            steps.append(("0062c62c", code))
            if code != "leg ":
                return steps, 0, R0
        steps.append(("0062c63a", None if kids else 0))
        if kids:
            return steps, 0, R0
        steps.append(("0062c653", None if f & 0x800 else 0))
        if f & 0x800:
            return steps, 0, R0
        steps.append(("0062c65d", q))
        if 4 <= q <= 9:
            return steps, 0, R0
        return steps, 1, R1
    if fn == "0062c6a0":                                   # ItemCanPersonalize
        R0 = "0062c766"
        steps.append(("0062c6da", ty))
        if ty == 4 or f & 0x1000:
            return steps, 0, R0
        for s, k in (("0062c6ff", 7), ("0062c70a", 5), ("0062c715", 6)):
            steps.append((s, ty))
            if ty == k:
                return steps, 0, R0
        steps.append(("0062c72f", None if f & 0x100 else 0))
        if f & 0x100:
            return steps, 0, R0
        steps.append(("0062c739", f))
        if f & 0x1000000:
            return steps, 0, R0
        cs = num(rec.get("compactsave"))
        steps.append(("0062c747", cs))
        if cs:
            return steps, 0, R0
        nm = T.nameable(cls)
        steps.append(("0062c754", {"compact": cs, "nameable": nm}))
        return steps, int(nm != 0), "0062c762"
    if fn == "0062c770":                                   # ItemCanQuestSocket
        R0 = "0062c83e"
        steps.append(("0062c7aa", ty))
        if ty == 4 or f & 0x1000:
            return steps, 0, R0
        steps.append(("0062c7d2", {"quest": quest}))
        if quest:
            steps.append(("0062c7e1", code))
            if code != "leg ":
                return steps, 0, R0
        if f & 0x100:
            return steps, 0, R0
        steps.append(("0062c805", None if kids else 0))
        if kids:
            return steps, 0, R0
        steps.append(("0062c81e", None if f & 0x800 else 0))
        if f & 0x800:
            return steps, 0, R0
        m = T.max_sockets(cls, it["ilvl"])
        steps.append(("0062c828", m))
        if not m:
            return steps, 0, R0
        s = it.get("st", {}).get("194", 0)
        steps.append(("0062c832", s))
        return steps, int(s == 0), "0062c83a"
    return None, None, None


def same_value(want, got):
    if want is None:                    # a non-zero test result
        return got not in (0, None)
    if isinstance(want, dict):
        return isinstance(got, dict) and all(got.get(k) == v for k, v in want.items())
    return want == got


def rng_step(seed):
    lo, hi = (int(x, 16) for x in seed.split(":"))
    v = lo * RNG_A + hi
    return v & 0xFFFFFFFF, (v >> 32) & 0xFFFFFFFF


NPC_RET = {"00592417": "akara", "005b9424": "ormus", "00587c88": "qualkehk", "00589654": "malah-ice",
           "005896e4": "malah-tr2", "0058995f": "anya", "005ba58c": "alkor", "005ba666": "meshif"}
PLAIN = {"malah-ice": "ice ", "malah-tr2": "tr2 ", "alkor": "xyz ", "meshif": "g34 "}   # ilvl 0 (clvl), quality 2
RING = {"akara": ({0: 7, 1: 30, 2: 60}, {0: 4, 1: 6, 2: 6}), "ormus": ({0: 21, 1: 35, 2: 75}, {0: 6, 1: 6, 2: 6})}
ANYA_TBL = {0: 0x00735F6C, 1: 0x00735EFC, 2: 0x00735F34}


def check(excel, exe, logs):
    T = Tables(excel)
    u32 = pe_reader(exe)
    c = Counter()
    bad = []

    def miss(log, what):
        bad.append("%s: %s" % (os.path.basename(log), what))

    for log in logs:
        L = parse(log)
        base = os.path.basename(log)
        # ---- the service tests
        for tag, d in L:
            if tag != "CAN":
                continue
            steps, r, at = can_model(T, d)
            name = {"0062c590": "imbue", "0062c6a0": "personalize", "0062c770": "socket"}[d["fn"]]
            who = "client" if d["ret"] in ("004bfd44", "004bfd5a", "004bfd70") else "server"
            code = T.code(d["item"]["u"][1])
            got = d["steps"]
            ok = [s for s, _ in steps] == [s for s, _ in got] and all(
                same_value(w, g[1]) for (_, w), g in zip(steps, got)) and r == d["r"] and at == d["at"]
            c["can %s %s checks" % (name, who)] += 1
            c["can %s %s %s r=%d exit %s" % (name, who, code, d["r"], d["at"])] += 1
            if not ok:
                miss(log, "CAN %s %s: model steps %s r %s at %s, logged %s r %s at %s" % (
                    name, code, steps, r, at, got, d["r"], d["at"]))
        # ---- the cursor item
        cic = [(t, d) for t, d in L if t in ("CIC", "CICR") and d.get("ret", d.get("site")) in (
            "0057a098", "0057a369", "0057a573")]
        for t, d in cic:
            if t == "CIC":
                c["cursor consume checks"] += 1
                if not d["same"]:
                    miss(log, "CIC: the consumed item is not the cursor item: %s" % d)
            else:
                c["cursor consume result checks"] += 1
                if d["r"] != 1:
                    miss(log, "CICR r %s" % d["r"])
        c["cursor consume calls %s" % sorted({d["ret"] for t, d in cic if t == "CIC"})] += 0
        # ---- sockets
        cur = None
        for tag, d in L:
            if tag == "LZ0":
                cur = {"q": d["q"], "max": d["max"]}
            elif tag == "LZS" and cur:
                cur["bound"], cur["seed"] = d["bound"], d["seed"]
            elif tag == "LZR" and cur:
                cur["r"] = d["r"]
                cur["after"] = d["seed"]
            elif tag == "LZX" and cur:
                cur["n"] = d["n"]
            elif tag == "LZY" and cur:
                q, mx = cur["q"], cur["max"]
                if q == 4:
                    b = min(mx, 2)
                    lo, _ = rng_step(cur["seed"]) if "seed" in cur else (None, None)
                    want = 1 + (lo % b) if lo is not None else None
                    st1 = rng_step(cur["seed"]) if "seed" in cur else None
                    ok = cur.get("bound") == b and cur.get("r") == (lo % b if lo is not None else None) and \
                        st1 is not None and cur.get("after") == "%08x:%08x" % st1   # one item-seed step, any bound
                    kind = "magic (draw, bound %d)" % b
                elif 5 <= q <= 9:
                    want, ok, kind = 1, "seed" not in cur, "quality %d (1)" % q
                else:
                    want, ok, kind = mx, "seed" not in cur, "quality %d (max %d)" % (q, mx)
                ok = ok and cur.get("n") == want and d["sockets"] == want
                c["socket checks"] += 1
                c["socket %s n=%s" % (kind, cur.get("n"))] += 1
                if not ok:
                    miss(log, "socket: %s, model n %s, logged %s" % (cur, want, d))
                cur = None
        # ---- imbue
        im = {}
        for tag, d in L:
            if tag == "IMB0":
                im = {"eth": fl(d["item"]) >> 22 & 1, "q0": d["item"]["q"]}
            elif tag == "IMBL":
                im["clvl"] = d["clvl"]
            elif tag == "IMB1" and im:
                im["rec"] = d
            elif tag == "IMBX" and im:
                lv = max(im["clvl"], 1)
                want_ilvl = lv + 4 if lv > 5 else lv
                f80 = 0x20 | (0x04 if im["eth"] else 0x02)
                rec, new = im["rec"], d["item"]
                ok = rec["ilvl"] == want_ilvl and int(rec["f80"], 16) & 0x26 == f80 and rec["q"] == 6 and \
                    new["q"] == 6 and new["ilvl"] == want_ilvl and (fl(new) >> 22 & 1) == im["eth"]
                c["imbue checks"] += 1
                c["imbue clvl %d -> ilvl %d, ethereal %d, f80 %s" % (im["clvl"], rec["ilvl"], im["eth"], rec["f80"])] += 1
                if not ok:
                    miss(log, "imbue: model ilvl %d f80 %x, logged %s / %s" % (want_ilvl, f80, rec, new))
                im = {}
        # ---- the shared tail
        for tag, d in L:
            if tag in ("RPX", "IDX"):
                it = d["item"]
                svc = d["svc"]
                if tag == "RPX":
                    st = it.get("st", {})
                    rec = T.rec(it["u"][1])
                    ident = fl(it) & 0x10
                    c["tail repair checks %s" % svc] += 1
                    if not ident:
                        c["tail repair %s: unidentified, left as it was" % svc] += 1
                        prev = [x for t2, x in L if t2 == "RPA" and x["item"]["u"] == it["u"]]
                        if prev and prev[-1]["item"].get("st") != st:
                            miss(log, "tail: an unidentified item changed in ItemRepairAll: %s" % d)
                        continue
                    if "73" in st and st.get("72") != st["73"]:
                        miss(log, "tail: durability %s of %s after ItemRepairAll" % (st.get("72"), st["73"]))
                    if num(rec.get("stackable")) and st.get("70") != num(rec.get("maxstack")):
                        miss(log, "tail: quantity %s, maxstack %s" % (st.get("70"), rec.get("maxstack")))
                    pre = [x for t2, x in L if t2 == "RPA" and x["item"]["u"] == it["u"]]
                    p = pre[-1]["item"].get("st", {}) if pre else {}
                    c["tail repair %s durability %s/%s -> %s, quantity %s -> %s" % (
                        svc, p.get("72"), p.get("73"), st.get("72"), p.get("70"), st.get("70"))] += 1
                else:
                    c["tail identify checks %s" % svc] += 1
                    if not fl(it) & 0x10:
                        miss(log, "tail: not identified after ItemIdentifyAttach: %s" % d)
        # ---- given items
        open_ = None
        qk = []
        for tag, d in L:
            if tag == "QGV":
                who = NPC_RET.get(d["ret"])
                open_ = dict(d, who=who, cf=None)
                if who is None:
                    miss(log, "QGV from an unknown caller %s" % d["ret"])
            elif tag == "CF0" and open_ and d["ret"] == 0x00546700:
                open_["cf"] = d
            elif tag == "QGC" and open_:
                open_["item"] = d["item"]
            elif tag == "QGD" and open_:
                open_["dur"] = d["item"].get("st", {})
            elif tag == "QGX" and open_:
                g, it = open_, open_.get("item") or {}
                who, diff = g["who"], g["diff"]
                code = T.code(it["u"][1]).ljust(4) if it and it.get("u") else None
                want_ilvl = g["ilvl"] if g["ilvl"] else g["clvl"]
                # the base `unique` column turns the asked quality into 7 before the builders (items/0004 us 13)
                want_q = 7 if it and it.get("u") and num(T.rec(it["u"][1]).get("unique")) else g["q"]
                ok = d["site"] == "0054676d" and code == g["code"] and it.get("ilvl") == want_ilvl and \
                    it.get("q") == want_q
                cf = g["cf"]
                ok = ok and cf is not None and cf["kind"] == 4 and cf["noeth"] == 1 and cf["q"] == g["q"] and \
                    cf["ilvl"] == want_ilvl
                dur = g.get("dur", {})
                if "73" in dur and dur.get("72") != dur["73"]:
                    ok = False
                if who in RING:
                    ok = ok and g["code"] == "rin " and g["ilvl"] == RING[who][0][diff] and g["q"] == RING[who][1][diff]
                elif who == "qualkehk":
                    qk.append((g, code))
                elif who in PLAIN:
                    ok = ok and g["ilvl"] == 0 and g["q"] == 2 and g["code"] == PLAIN[who]
                elif who == "anya":
                    any_ = [x for t2, x in L if t2 == "ANY"]
                    a = any_[-1] if any_ else None
                    tbl = ANYA_TBL[diff]          # single player: game type 3 takes the difficulty's table (F5)
                    ok = ok and a is not None and int(a["tbl"], 16) == tbl and a["g6a"] == 3 and g["q"] == 6 and \
                        g["ilvl"] == g["clvl"]
                    if a is not None:
                        codes = u32(tbl + 8 * a["cls"])
                        n = u32(tbl + 8 * a["cls"] + 4)
                        want = struct.pack("<I", u32(codes + 4 * a["r"])).decode("latin1")
                        ok = ok and n == a["n"] and want == g["code"] == a["code"]
                c["give checks"] += 1
                c["give %s diff %d: %s ilvl %s q %s" % (who, diff, g["code"].strip(), it.get("ilvl"), it.get("q"))] += 1
                if not ok:
                    miss(log, "give %s: %s / item %s / %s" % (who, {k: v for k, v in g.items() if k != "rec"}, it, d))
                open_ = None
        # Anya's draw: one RNG_Range(quest seed, n) on the seed QUESTS_GetSeed returned (0x0058992E)
        last_qgs = None
        for tag, d in L:
            if tag == "QGS" and d.get("ret") == "0058992e":
                last_qgs = d["qs"]
            elif tag == "ANY":
                c["give anya draw checks"] += 1
                st1 = rng_step(last_qgs) if last_qgs else None
                if st1 is None or "%08x:%08x" % st1 != d["qs"] or st1[0] % d["n"] != d["r"]:
                    miss(log, "anya draw: seed %s, logged %s" % (last_qgs, d))
                last_qgs = None
        if qk:
            # after the runes: word 36 bit 0 set (0x00587CB0), bit 1 cleared (0x00587CBF)
            w = [(t, d["b"]) for t, d in L if t in ("QS", "QC") and d.get("w") == 36 and d.get("ret") in (
                "00587cb0", "00587cbf")]
            c["give qualkehk word 36 writes %s" % w] += 1
            if w != [("QS", 0), ("QC", 1)]:
                miss(log, "qualkehk: word 36 writes %s" % w)
            rec = qk[0][0]["rec"]
            w36 = rec[36] if rec else 0
            n = 2 if w36 >> 6 & 1 else 1 if w36 >> 7 & 1 else 3
            codes = [g["code"] for g, _ in qk]
            c["give qualkehk checks"] += 1
            c["give qualkehk word 36 %04x: %s" % (w36, " ".join(x.strip() for x in codes))] += 1
            if codes != ["r07 ", "r08 ", "r09 "][:n]:
                miss(log, "qualkehk: word 36 %04x, model n %d, given %s" % (w36, n, codes))
        c["logs"] += 1
        c["LOGERR lines"] += sum(1 for ln in open(log, errors="replace") if ln.startswith("LOGERR"))
    for k in sorted(c):
        print("%-90s %d" % (k, c[k]))
    for b in bad:
        print("MISMATCH " + b)
    print("SUMMARY logs=%d mismatches=%d" % (c["logs"], len(bad)))
    return 1 if bad else 0


STATIC = {0x0062C590: "ItemCanImbue", 0x0062C6A0: "ItemCanPersonalize", 0x0062C770: "ItemCanQuestSocket",
          0x0055EEA0: "CursorItemConsume", 0x005761C0: "ItemRepairAll", 0x0055FE00: "ItemIdentifyAttach",
          0x005466B0: "QUESTS_GiveItem", 0x0062A270: "ItemHoldsItem", 0x0062A2B0: "ItemCompactSave"}


def static(exe):
    import re
    import subprocess
    out = subprocess.run(["objdump", "-d", "--no-show-raw-insn", "-M", "intel", exe], capture_output=True, text=True,
                         check=True).stdout
    want = {"0x%x" % t: t for t in STATIC}
    calls = {t: [] for t in STATIC}
    for ln in out.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+(call|jmp)\s+(0x[0-9a-f]+)\s*$", ln)
        if m and m.group(3) in want:
            calls[want[m.group(3)]].append("%s %s" % (m.group(2), m.group(1)))
    raw = open(exe, "rb").read()
    for t, name in STATIC.items():
        ptr = raw.count(struct.pack("<I", t))          # the VA as a 32-bit value anywhere in the file (a pointer)
        print("0x%08X %-20s %d: %s; VA in the file %d time(s)" % (t, name, len(calls[t]), " ".join(calls[t]), ptr))
    return 0


def main(argv):
    if len(argv) == 2 and argv[0] == "static":
        return static(argv[1])
    if len(argv) < 4 or argv[0] != "check":
        print(__doc__)
        return 2
    return check(argv[1], argv[2], argv[3:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

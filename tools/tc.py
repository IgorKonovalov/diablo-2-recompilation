#!/usr/bin/env python3
"""Treasure-class resolution model (plan 0004 Phase 2), checked against tc-drops.gdb logs.

    python3 -I tools/tc.py replay <log> [--excel DIR] [-v]
    python3 -I tools/tc.py show <tc-index|name> [--excel DIR]
    python3 -I tools/tc.py nodrop <nd> <total> <n> [--pc 24|53|64]

replay rebuilds the runtime TC table from the compiled .bin tables (tools/excel_bin.py), then replays
every TC_ResolveDrops call in the log (TCR ... TCEND) from its logged inputs, drawing through
tools/rng.py. sub_00558640_DropRollQuality is a boundary oracle (ADR-0004): the model asserts the
predicted source seed (and item, ratio words) at each QIN, then takes the logged quality and exit seed
from QOUT. It also asserts the NoDrop' of every pick (x87 model at the logged precision control), every
pick roll, the item/quality/unique index/flags at CPRE, that creation leaves the source seed alone
(CPRE seed == CPOST seed), the output count and the final seed at TCEND. A call with a QIN and no QOUT,
or with no TCEND, fails. Exit 0 only when every call reproduces.

Model: docs/findings/items/0001-tc-resolution.md sections 1, 4-9. Stdlib only. Read-only.
"""
import argparse
import os
import struct
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import rng  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
F_UNIQUE, F_SET, F_TC, F_EXPONLY = 0x01, 0x02, 0x04, 0x10


# ---------------------------------------------------------------- tables

def recs(excel, table):
    r, _ = excel_bin.read_bin(excel_bin.find_file(excel, table, ".bin"))
    return r


def cstr(b):
    return b.split(b"\0", 1)[0].decode("latin1")


class Tables:
    def __init__(self, excel):
        it = recs(excel, "itemtypes")
        self.itypes = [dict(code=r[0:4].decode("latin1"), equiv=(struct.unpack_from("<H", r, 4)[0],
                                                                  struct.unpack_from("<H", r, 6)[0]),
                            tc=r[0x1D], rarity=r[0x1E]) for r in it]
        self.items = []
        for t in ("weapons", "armor", "misc"):
            for r in recs(excel, t):
                self.items.append(dict(
                    code=r[0x80:0x84].decode("latin1"), version=struct.unpack_from("<H", r, 0xF6)[0],
                    level=r[0xFD], type=struct.unpack_from("<H", r, 0x11E)[0],
                    type2=struct.unpack_from("<H", r, 0x120)[0], quest=r[0x12A], spawnable=r[0x133]))
        self.code2item = {}
        for i, it_ in enumerate(self.items):
            self.code2item.setdefault(it_["code"], i)
        self.tcs = [None]  # index 0: the empty TC
        self.names = {}
        self._auto()
        self._tcex(recs(excel, "treasureclassex"))

    def is_type(self, item, t):
        """ITEMS_IsType: the item's type or type2 is t or has t among its Equiv ancestors."""
        def up(x, seen):
            if x == 0 or x in seen or x >= len(self.itypes):
                return False
            if x == t:
                return True
            seen.add(x)
            return any(up(e, seen) for e in self.itypes[x]["equiv"])
        it_ = self.items[item]
        return up(it_["type"], set()) or up(it_["type2"], set())

    @staticmethod
    def new_tc(name, picks, group, level, ratio, nodrop):
        return dict(name=name, picks=picks, group=group, level=level, ratio=list(ratio), nodrop=nodrop,
                    entries=[], tclassic=0, texp=0)

    @staticmethod
    def add(tc, index, flags, prob, aux=0):
        tc["entries"].append(dict(index=index, flags=flags, aux=aux, cumc=tc["tclassic"], cume=tc["texp"],
                                  prob=prob))
        tc["texp"] += prob
        if not flags & F_EXPONLY:
            tc["tclassic"] += prob

    def _alloc(self, tc):
        self.names.setdefault(tc["name"].lower(), len(self.tcs))
        self.tcs.append(tc)

    def _auto(self):
        """TC_BuildAutoTCs (items/0001 section 9)."""
        self.n_auto_types = 0
        for t, ty in enumerate(self.itypes):
            if not ty["tc"]:
                continue
            self.n_auto_types += 1
            code = ty["code"].split(" ")[0]
            for L in range(3, 97, 3):
                tc = self.new_tc("%s%d" % (code, L), 1, 0, L - 3, [0] * 6, 0)
                for i, it_ in enumerate(self.items):
                    if it_["quest"] or not it_["spawnable"] or not self.is_type(i, t):
                        continue
                    if t != 38 and self.is_type(i, 38):
                        continue
                    if not (L - 3 < it_["level"] <= L):
                        continue
                    prob = max(1, self.itypes[it_["type"]]["rarity"])
                    self.add(tc, i, F_EXPONLY if it_["version"] >= 100 else 0, prob)
                self._alloc(tc)

    def _tcex(self, rows):
        """TC_LoadTreasureClassEx + TC_ParseItemCell (data/0001 section 7)."""
        self.unresolved = []
        for r in rows:
            name = cstr(r[0:32])
            if not name:
                break
            picks = struct.unpack_from("<i", r, 0x20)[0] or 1
            group, level = struct.unpack_from("<HH", r, 0x24)
            ratio = list(struct.unpack_from("<4H", r, 0x28)) + list(struct.unpack_from("<HH", r, 0x30))
            nodrop = struct.unpack_from("<i", r, 0x34)[0]
            tc = self.new_tc(name, picks, group + self.n_auto_types if group else 0, level, ratio, nodrop)
            self._alloc(tc)
            for k in range(10):
                cell = cstr(r[0x38 + 64 * k: 0x78 + 64 * k]).replace('"', "")
                if not cell:
                    break
                prob = struct.unpack_from("<i", r, 0x2B8 + 4 * k)[0]
                if prob < 1:
                    continue
                nm, _, mods = cell.partition(",")
                aux = 0
                for m in mods.split(",") if mods else []:
                    key, _, val = m.partition("=")
                    if key in ("mul", "ma", "mg"):
                        aux = int(val)
                    else:
                        raise SystemExit("modifier %r in %s not modelled" % (m, name))
                if len(nm) <= 4 and (nm + "    ")[:4] in self.code2item:
                    i = self.code2item[(nm + "    ")[:4]]
                    self.add(tc, i, F_EXPONLY if self.items[i]["version"] >= 100 else 0, prob, aux)
                elif self.names.get(nm.lower(), 0) >= 1:
                    s = self.names[nm.lower()]
                    self.add(tc, s, F_TC | (F_EXPONLY if self.tcs[s]["tclassic"] == 0 else 0), prob, aux)
                else:
                    self.unresolved.append((name, nm))  # unique/set names: not modelled (none hit so far)

    def get(self, idx, lvl):
        """TC_GetByIndex with the forward group/level walk (items/0001 section 4)."""
        if idx == 0 or idx >= len(self.tcs):
            return None
        t = idx
        if lvl > 0 and self.tcs[t]["group"] and t + 1 < len(self.tcs) and self.tcs[t + 1]["group"] == self.tcs[t]["group"]:
            while True:
                if lvl < self.tcs[t + 1]["level"]:
                    return t
                t += 1
                if t + 1 >= len(self.tcs) or self.tcs[t + 1]["group"] != self.tcs[t]["group"]:
                    return t
        return t


# ---------------------------------------------------------------- x87 NoDrop

def x87_round(x, bits):
    """Round a Fraction to `bits` significand bits, round-to-nearest-even (x87 PC + RC=00)."""
    if x == 0:
        return x
    sign = -1 if x < 0 else 1
    x = abs(x)
    e = x.numerator.bit_length() - x.denominator.bit_length()
    if Fraction(2) ** e > x:
        e -= 1
    scale = Fraction(2) ** (bits - 1 - e)
    m = x * scale
    q, r = divmod(m.numerator, m.denominator)
    rem = Fraction(r, m.denominator)
    if rem > Fraction(1, 2) or (rem == Fraction(1, 2) and q & 1):
        q += 1
    return sign * Fraction(q) / scale


def nodrop_scaled(nd, total, n, bits):
    """0x0055A93B..0x0055A9D7: x87 evaluation, every operation rounded to the precision control."""
    if n <= 1:
        return nd
    rnd = lambda v: x87_round(v, bits)  # noqa: E731
    r = rnd(Fraction(nd) / Fraction(nd + total))
    p = r
    for _ in range(n - 1):
        p = rnd(p * r)
    q = rnd(1 - p)
    if q == 0:
        return 0
    v = rnd(1 - q)
    v = rnd(v * total)
    v = rnd(v / q)
    return int(v)  # CRT_ftol2 truncates toward zero


PC_BITS = {0: 24, 2: 53, 3: 64}


# ---------------------------------------------------------------- log replay

def parse(line):
    head, *rest = line.split()
    kv = {}
    for tok in rest:
        if "=" in tok:
            k, v = tok.split("=", 1)
            kv[k] = v
    return head, kv


def seedpair(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


class Mismatch(Exception):
    pass


def replay_call(T, call, verbose=False):
    """call: list of (head, kv) from TCR to TCEND inclusive. Returns a summary dict; raises Mismatch."""
    events = list(call)
    tcr = events[0][1]
    pos = [1]

    def expect(head):
        while pos[0] < len(events) and events[pos[0]][0] in ("GAME", "DROP"):
            pos[0] += 1
        if pos[0] >= len(events):
            raise Mismatch("missing %s line" % head)
        h, kv = events[pos[0]]
        if h != head:
            raise Mismatch("expected %s, log has %s %s" % (head, h, kv))
        pos[0] += 1
        return kv

    def eq(what, model, logged):
        if model != logged:
            raise Mismatch("%s: model %r, log %r" % (what, model, logged))

    lo, hi = seedpair(tcr["seed"])
    exp = int(tcr["exp"])
    nonodrop = int(tcr["nonodrop"])
    mx = int(tcr["max"])
    mx = 6 if mx < 1 else mx
    fq = int(tcr["fq"])
    stype = int(tcr["stype"])
    root = int(tcr["tc"])
    t0 = T.tcs[root]
    frames = [dict(tc=root, left=max(1, abs(t0["picks"])), ratio=list(t0["ratio"]))]
    cur = 0
    count = 0
    ndps = []
    picks = 0
    qcalls = 0
    while True:
        f = frames[cur]
        t = T.tcs[f["tc"]] if f["tc"] else None
        if t and (t["texp"] if exp else t["tclassic"]):
            while frames[cur]["left"]:
                f = frames[cur]
                t = T.tcs[f["tc"]]
                total = t["texp"] if exp else t["tclassic"]
                if not total:
                    break
                if t["picks"] < 0:
                    roll = abs(t["picks"]) - f["left"]
                    kv = expect("NEG")
                    eq("NEG roll", roll, int(kv["roll"]))
                    eq("NEG total", total, int(kv["total"]))
                    if roll >= total:
                        break
                else:
                    nd = t["nodrop"]
                    if nd:
                        party = int(expect("PARTY")["party"])  # 1 unless the killer resolves to a player
                        if tcr.get("ktype") is None:
                            eq("PARTY without killer", 1, party)
                        players = int(expect("PLAYERS")["players"])
                        d = players - party
                        n = party + (abs(d) // 2) * (1 if d >= 0 else -1)  # C signed division
                        if stype == 1:
                            cap = int(expect("CAP")["cap"])
                            n = min(n, cap)
                        if n > 1:
                            kv = expect("NDIN")
                            eq("NDIN n", n, int(kv["n"]))
                            fctrl = int(kv["fctrl"], 16)
                            bits = PC_BITS[(fctrl >> 8) & 3]
                            if (fctrl >> 10) & 3:
                                raise Mismatch("rounding control %x not modelled" % fctrl)
                            nd = nodrop_scaled(nd, total, n, bits)
                        ndps.append((t["nodrop"], total, n, nd))
                    kv = expect("NDP")
                    eq("NDP", nd, int(kv["ndp"]))
                    rng_n = total if nonodrop else total + nd
                    roll, lo, hi = rng.rng_range(lo, hi, rng_n & 0xFFFFFFFF)
                    kv = expect("PICK")
                    picks += 1
                    eq("PICK roll", roll, int(kv["roll"]))
                    eq("PICK seed", (lo, hi), seedpair(kv["seed"]))
                    if not nonodrop:
                        if roll < nd:
                            f["left"] -= 1
                            continue
                        roll -= nd
                f["left"] -= 1
                ents = t["entries"]
                if exp:
                    i = next((k for k in range(len(ents)) if ents[k]["cume"] <= roll < ents[k]["cume"] + ents[k]["prob"]), 0)
                else:
                    raise Mismatch("classic selection not modelled")
                eq("SEL", i, int(expect("SEL")["i"]))
                if i >= len(ents):
                    continue
                e = ents[i]
                if e["flags"] & F_TC:
                    sub = e["index"]
                    eq("SUB", sub, int(expect("SUB")["tc"]))
                    parent = cur
                    if f["left"] > 0:
                        cur += 1
                    if cur >= 64:
                        raise Mismatch("stack overflow")
                    st = T.tcs[sub]
                    pr = frames[parent]["ratio"]
                    nr = [st["ratio"][k] if (pr[k] == 0 or st["ratio"][k] > pr[k]) else pr[k] for k in range(6)]
                    fr = dict(tc=sub, left=max(1, abs(st["picks"])), ratio=nr)
                    if cur < len(frames):
                        frames[cur] = fr
                    else:
                        frames.append(fr)
                    continue
                if e["index"] == 0xFFFF:
                    continue
                if e["flags"] & F_UNIQUE:
                    q, uidx = 7, e["aux"] + 1
                elif e["flags"] & F_SET:
                    q, uidx = 5, e["aux"] + 1
                else:
                    uidx = 0
                    if fq:
                        q = fq
                    else:
                        kv = expect("QIN")
                        qcalls += 1
                        eq("QIN item", e["index"], int(kv["item"]))
                        eq("QIN seed", (lo, hi), seedpair(kv["seed"]))
                        eq("QIN ratio", f["ratio"], [int(x) for x in kv["ratio"].split(",")])
                        eq("QIN ilvl", int(tcr["ilvl"]), int(kv["ilvl"]))
                    kv = expect("QOUT")  # the oracle's answer (also logged for a forced quality)
                    q = int(kv["q"])
                    lo, hi = seedpair(kv["seed"])
                up = 0
                for k, bit in ((4, 0x04), (5, 0x10)):
                    if f["ratio"][k]:
                        lo, hi = rng.step(lo, hi)
                        if (lo & 0x3FF) < f["ratio"][k]:
                            up |= bit
                if not exp:
                    raise Mismatch("classic throwable path not modelled")
                kv = expect("CPRE")
                eq("CPRE item", e["index"], int(kv["item"]))
                eq("CPRE quality", q, int(kv["q"]))
                eq("CPRE uidx", uidx, int(kv["uidx"]))
                eq("CPRE flags", up, int(kv["up"]))
                eq("CPRE seed", (lo, hi), seedpair(kv["seed"]))
                kv = expect("CPOST")
                eq("creation leaves the source seed", (lo, hi), seedpair(kv["seed"]))
                if int(kv["unit"], 16) == 0:
                    continue
                count += 1
                if count >= mx:
                    break
            if count >= mx:
                break
        if cur == 0:
            break
        cur -= 1
    kv = expect("TCEND")
    eq("TCEND count", count, int(kv["count"]))
    eq("TCEND seed", (lo, hi), seedpair(kv["seed"]))
    if pos[0] != len(events):
        raise Mismatch("unconsumed lines: %s" % [h for h, _ in events[pos[0]:]])
    return dict(tc=root, name=t0["name"], count=count, picks=picks, qcalls=qcalls, ndps=ndps,
                src="%s/%s" % (tcr["stype"], tcr["sclass"]), mflags=tcr.get("mflags"), diff=tcr["diff"])


def cmd_replay(ns):
    T = Tables(ns.excel)
    calls, cur, drops = [], None, []
    for line in open(ns.log, errors="replace"):
        line = line.strip()
        if not line or line[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or line.startswith("Breakpoint"):
            continue
        head, kv = parse(line)
        if head == "DROP":
            drops.append(kv)
        if head == "TCR":
            if cur is not None:
                calls.append((cur, None))
            cur = [(head, kv)]
            cur_drop = drops[-1] if drops else None
            drops = []
            cur.append(("_DROP", cur_drop))
            continue
        if cur is None:
            continue
        cur.append((head, kv))
        if head == "TCEND":
            calls.append((cur, None))
            cur = None
    if cur is not None:
        calls.append((cur, "no TCEND (log ends inside the call)"))
    ok = bad = 0
    for k, (call, err) in enumerate(calls):
        drop = call.pop(1)[1]
        try:
            if err:
                raise Mismatch(err)
            if drop:
                up = T.get(int(drop["base"]), int(drop["lvl"]))
                if up != int(call[0][1]["tc"]):
                    raise Mismatch("level upgrade: model TC %s, log %s" % (up, call[0][1]["tc"]))
            s = replay_call(T, call)
            ok += 1
            if ns.verbose:
                b = (" base=%s lvl=%s" % (drop["base"], drop["lvl"])) if drop else ""
                print("ok   #%d tc=%d %r src=%s mflags=%s diff=%s%s picks=%d q=%d count=%d nodrop=%s" % (
                    k, s["tc"], s["name"], s["src"], s["mflags"], s["diff"], b, s["picks"], s["qcalls"],
                    s["count"], sorted(set(s["ndps"]))))
        except Mismatch as ex:
            bad += 1
            print("FAIL #%d %s: %s" % (k, call[0][1].get("tc"), ex))
    print("%d calls, %d reproduced, %d failed" % (ok + bad, ok, bad))
    return 0 if bad == 0 and ok > 0 else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("replay")
    a.add_argument("log")
    a.add_argument("--excel", default=EXCEL)
    a.add_argument("-v", "--verbose", action="store_true")
    b = sub.add_parser("show")
    b.add_argument("tc")
    b.add_argument("--excel", default=EXCEL)
    c = sub.add_parser("nodrop")
    c.add_argument("nd", type=int)
    c.add_argument("total", type=int)
    c.add_argument("n", type=int)
    c.add_argument("--pc", type=int, default=53)
    ns = ap.parse_args(argv)
    if ns.cmd == "replay":
        return cmd_replay(ns)
    if ns.cmd == "nodrop":
        print(nodrop_scaled(ns.nd, ns.total, ns.n, ns.pc))
        return 0
    T = Tables(ns.excel)
    idx = int(ns.tc) if ns.tc.isdigit() else T.names[ns.tc.lower()]
    t = T.tcs[idx]
    print("#%d %r picks=%d group=%d level=%d nodrop=%d ratio=%s classic=%d exp=%d" % (
        idx, t["name"], t["picks"], t["group"], t["level"], t["nodrop"], t["ratio"], t["tclassic"], t["texp"]))
    for e in t["entries"]:
        nm = T.tcs[e["index"]]["name"] if e["flags"] & F_TC else T.items[e["index"]]["code"]
        print("  %-24s idx=%-4d flags=%02x prob=%-4d cume=%d aux=%d" % (nm, e["index"], e["flags"], e["prob"],
                                                                     e["cume"], e["aux"]))
    print("unresolved cells:", len(T.unresolved), T.unresolved[:5])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

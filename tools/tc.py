#!/usr/bin/env python3
"""Treasure-class resolution model (plan 0004 Phase 2), checked against tc-drops.gdb logs.

    python3 -I tools/tc.py replay <log> [--excel DIR] [-v] [--quality oracle|model [--mf N] [--mf-linear]]
    python3 -I tools/tc.py show <tc-index|name> [--excel DIR]
    python3 -I tools/tc.py nodrop <nd> <total> <n> [--pc 24|53|64]

replay rebuilds the runtime TC table from the compiled .bin tables (tools/excel_bin.py), then replays
every TC_ResolveDrops call in the log (TCR ... TCEND) from its logged inputs, drawing through
tools/rng.py. With --quality oracle (the default) ITEMS_DropRollQuality is a boundary oracle
(ADR-0004): the model asserts the predicted source seed (and item, ratio words) at each QIN, then takes
the logged quality and exit seed from QOUT. With --quality model (plan 0010 Phase 2) there is no oracle:
the roll is tools/quality.py's model, run from the model's own seed, item, ilvl and ratio words, and the
model's quality and exit seed are carried on; QOUT is only asserted against them (as is a QROW itemratio
row, when logged). The roll's magic find is the logged QMF value when the log has one (tc-drops.gdb from
plan 0010 Phase 2 on), 0 when the call has no killer, else the --mf input (default 0; NOT in older logs,
so the caller must know it, e.g. from the character's save). It also asserts the NoDrop' of every pick (x87 model at the logged precision control), every
pick roll, the item/quality/unique index/flags at CPRE, that creation leaves the source seed alone
(CPRE seed == CPOST seed), the output count and the final seed at TCEND. A call with a QIN and no QOUT,
or with no TCEND, fails. Exit 0 only when every call reproduces.

For a monster source (TCR stype=1 with a DROP line before it) replay also checks the base TC and the
upgrade level against the tables (items/0001 sections 3-4): a superunique (mflags 0x02 and 0x08) takes
superuniques row `suid`, column TC / TC(N) / TC(H) by difficulty; any other monster takes monstats record
`sclass`, TreasureClass2 if mflags & 0x04 (champion), TreasureClass3 if mflags & 0x08, else
TreasureClass1, from the difficulty's (N)/(H) group. A set TCQuestId with a TreasureClass4 also accepts
TreasureClass4 (the quest state is not logged), unless the log has the B60 .. B6X lines of tools/gdb/quests.py
(plan 0032 Phase 2) before the DROP: then b6_model decides (items/0010 section 2: the killer resolved to its owner,
or to the caster of an `exp` state; a player's record word TCQuestId read at bits 15, 1 and TCQuestCP in that order,
stopping at the first set bit; TreasureClass4 only when all three are clear) and every logged step is compared. DROP base must equal that TC. DROP lvl must be the
source's level (TCR ilvl) in an expansion game above Normal for a monstats row with neither noRatio nor
boss, and 0 otherwise. monstats is read from monstats.bin (TC columns at +0x86 + 8*diff + 2*k hold the
runtime TC index, flags byte +0x0C bit 2 noRatio, bit 6 boss, TCQuestId +0x9E); superuniques has no
.bin layout yet, so its TC columns are read by name from superuniques.txt and resolved through the TC
name table. The summary counts monster sources by kind (normal, minion, champion, unique, superunique).

Party check (plan 0011, logs of tools/gdb/tc-party.gdb): the PLR (player units: id, position, level,
mode, dead flag), PTY (party list) and KILL (source and killer position) lines logged at TC_DropByIndex
entry come before the call's DROP/TCR. When they are present and the killer is a player, every PARTY
line of the call must equal the model of items/0001 section 6: the members of the killer's party
(the killer included) whose level id equals the killer's and that are alive (mode not 0/17 and +0xC6
bit 0 clear) are counted, k >= 2 gives min(k, 8), anything else 1; and every PLAYERS line must equal the
alive players (or the /players override when it is larger and g6a is 1..3; the playerbody state is not
logged). -v prints, per call, the party, the players, and the distance in subtiles from the killer to
each other player with their level ids.

Classic games (TCR exp=0, plan 0020 Phase 2): totals are totalClassic, the entry is chosen by the classic
linear scan (items/0001 section 5.1), item records with version >= 100 are rejected with the pick consumed,
and a throwable item type refunds its pick for the first 10 in the call, later ones drop 'lsd ' (section 8).
The summary then adds a line of classic events (CLASSIC_KEYS).

Lines in the "TAG {json}" form (the JSON loggers of later plans, e.g. tools/gdb/uniques.gdb) are skipped.

Model: docs/findings/items/0001-tc-resolution.md sections 1, 4-9. Stdlib only. Read-only.
"""
import argparse
import json
import os
import struct
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin  # noqa: E402
import quality  # noqa: E402
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
                            throwable=r[0x10], tc=r[0x1D], rarity=r[0x1E]) for r in it]
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
        # the uniqueitems and setitems name links (data/0001 section 7 steps 3-4, items/0004 section 6): lower-cased
        # name truncated to 32 bytes; the first row of a duplicated name wins
        self.unames, self.snames = {}, {}
        for links, table, coff in ((self.unames, "uniqueitems", 0x28), (self.snames, "setitems", 0x28)):
            for row, r in enumerate(recs(excel, table)):
                nm = r[2:0x22].split(b"\0")[0].decode("latin1").lower()
                if nm:
                    links.setdefault(nm, (row, r[coff:coff + 4].decode("latin1")))
        self._auto()
        self._tcex(recs(excel, "treasureclassex"))
        self.excel = excel
        self._mon = self._su = None

    def monstats(self, cls):
        if self._mon is None:
            self._mon = recs(self.excel, "monstats")
        return self._mon[cls]

    def superunique_tc(self, suid, diff):
        if self._su is None:
            path = excel_bin.find_file(self.excel, "superuniques", ".txt")
            with open(path, encoding="latin1") as f:
                rows = [ln.rstrip("\r\n").split("\t") for ln in f]
            cols = [rows[0].index(c) for c in ("TC", "TC(N)", "TC(H)")]
            # the "Expansion" marker row takes no record (excel_bin.py), so later suids would be off by one
            self._su = [[r[c] if c < len(r) else "" for c in cols] for r in rows[1:]
                        if r and r[0] and r[0] != "Expansion"]
        name = self._su[suid][diff]
        return self.names.get(name.lower(), 0) if name else 0

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
                elif self.unames.get(nm.lower()[:32], (0,))[0] >= 1:
                    # a TC-named unique: flags 0x11, index = the row's base, aux = the row (fn:TC_ParseItemCell@0x00654440)
                    row, code = self.unames[nm.lower()[:32]]
                    self.add(tc, self.code2item[code], F_UNIQUE | F_EXPONLY, prob, row)
                elif nm.lower()[:32] in self.snames:
                    row, code = self.snames[nm.lower()[:32]]
                    self.add(tc, self.code2item[code], F_SET | F_EXPONLY, prob, row)
                else:
                    self.unresolved.append((name, nm))

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


def nodrop_ptq(nd, total, n, bits):
    """Counterfactual of nodrop_scaled: the algebraically equal p*T/(1-p) (p reused, 1 - q not computed)."""
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
    return int(rnd(rnd(p * total) / q))


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


def party_model(ctx, tcr):
    """(party, players, notes) from the PLR/PTY/KILL lines before a call, or None when not logged."""
    if not ctx:
        return None
    plr = {int(kv["id"]): kv for h, kv in ctx if h == "PLR"}
    ptys = [kv for h, kv in ctx if h == "PTY"]
    kill = next((kv for h, kv in ctx if h == "KILL"), None)
    alive = lambda kv: int(kv["mode"]) not in (0, 17) and kv["dead"] == "0"  # noqa: E731
    players = sum(1 for kv in plr.values() if alive(kv))
    pover = int(tcr.get("pover", "0"))
    if int(tcr.get("g6a", "0")) in (1, 2, 3) and pover > players:
        players = pover
    if not kill or kill.get("ktype") != "0":
        return dict(party=None, players=players, notes="killer not a player")
    kid = int(kill["kid"])
    me = plr.get(kid)
    party = 1
    notes = []
    for pty in ptys:
        ids = [int(x) for x in pty["members"].split(",") if x not in ("-", "")]
        if kid in ids and me is not None and me["lvl"] != "-1":
            k = sum(1 for i in ids if i in plr and plr[i]["lvl"] == me["lvl"] and alive(plr[i]))
            party = min(k, 8) if k >= 2 else 1
    for i, kv in sorted(plr.items()):
        if i == kid or me is None:
            continue
        dx, dy = int(kv["x"]) - int(me["x"]), int(kv["y"]) - int(me["y"])
        inp = any(kid in [int(x) for x in p["members"].split(",") if x not in ("-", "")] and
                  i in [int(x) for x in p["members"].split(",") if x not in ("-", "")] for p in ptys)
        notes.append("p%d lvl=%s/%s %s d=%.1f (dx=%d dy=%d)" % (i, kv["lvl"], me["lvl"],
                                                              "partied" if inp else "unpartied",
                                                              (dx * dx + dy * dy) ** 0.5, dx, dy))
    return dict(party=party, players=players, notes="; ".join(notes))


def replay_call(T, call, verbose=False, ctx=None, qmodel=None, st=None, cf=None):
    """call: list of (head, kv) from TCR to TCEND inclusive. Returns a summary dict; raises Mismatch.

    qmodel None: the quality roll is an oracle (QOUT taken). Else (quality.Tables, mf input, linear): the roll is
    modelled and QOUT only asserted.

    st, if a dict, receives event counts (tools/tc_sweep.py, plan 0038 batch S2a); cf, if a dict, switches on a
    counterfactual of the model, which must then FAIL on the calls the switched-off rule decides:
    nomax (no MAX_DROP stop), nodrop ("ptq" = p*T/(1-p), or 24/64 = another precision control), noskip (the classic
    scan does not skip expansion-only entries), cumexp (classic games select by the expansion search over cumExp),
    nopop (an exhausted frame ends the call instead of resuming its parent), notail (a sub-TC always takes a new
    frame), qtype (a callable replacing quality.roll's type reads, see tools/tc_sweep.py)."""
    cf = cf or {}

    def bump(k, n=1):
        if st is not None:
            st[k] = st.get(k, 0) + n
    events = list(call)
    tcr = events[0][1]
    pos = [1]
    pm = party_model(ctx, tcr)
    seen = []

    def expect(head):
        while pos[0] < len(events) and events[pos[0]][0] in ("GAME", "DROP", "PLR", "PTY", "KILL"):
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
    if mx < 1:
        bump("max.default6")
    mx = 6 if mx < 1 else mx
    if cf.get("nomax") and int(tcr["max"]) < 1:
        mx = 1 << 30
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
    mfsrc = {}
    throw_retries = 0
    cls = dict.fromkeys(CLASSIC_KEYS, 0)
    bump("calls")
    bump("calls.exp%d.diff%s.stype%d" % (exp, tcr.get("diff"), stype))
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
                    bump("pick.neg")
                    if roll >= total:
                        bump("neg.stop")
                        break
                else:
                    nd = t["nodrop"]
                    if nd:
                        party = int(expect("PARTY")["party"])  # 1 unless the killer resolves to a player
                        if tcr.get("ktype") is None:
                            eq("PARTY without killer", 1, party)
                        if pm and pm["party"] is not None:
                            eq("PARTY (party model from PLR/PTY)", pm["party"], party)
                        players = int(expect("PLAYERS")["players"])
                        if pm:
                            eq("PLAYERS (alive player units)", pm["players"], players)
                        seen.append((party, players))
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
                            nd0 = nd
                            if cf.get("nodrop") == "ptq":
                                nd = nodrop_ptq(nd, total, n, bits)
                            elif cf.get("nodrop") in (24, 64):
                                nd = nodrop_scaled(nd, total, n, cf["nodrop"])
                            else:
                                nd = nodrop_scaled(nd, total, n, bits)
                            bump("nodrop.x87")
                            bump("nodrop.x87.%s" % ("monster" if stype == 1 else "object"))
                            if st is not None:
                                st.setdefault("_ndtriples", set()).add((nd0, total, n, nd, bits))
                        ndps.append((t["nodrop"], total, n, nd))
                    kv = expect("NDP")
                    eq("NDP", nd, int(kv["ndp"]))
                    rng_n = total if nonodrop else total + nd
                    roll, lo, hi = rng.rng_range(lo, hi, rng_n & 0xFFFFFFFF)
                    kv = expect("PICK")
                    picks += 1
                    eq("PICK roll", roll, int(kv["roll"]))
                    eq("PICK seed", (lo, hi), seedpair(kv["seed"]))
                    bump("pick.pos")
                    if not nonodrop:
                        if roll < nd:
                            f["left"] -= 1
                            bump("pick.nodrop")
                            continue
                        roll -= nd
                f["left"] -= 1
                ents = t["entries"]
                if exp or cf.get("cumexp"):
                    i = next((k for k in range(len(ents)) if ents[k]["cume"] <= roll < ents[k]["cume"] + ents[k]["prob"]), 0)
                else:
                    # classic linear scan (0x0055AAED-0x0055AB33): skip expansion-only entries; take the first
                    # other entry that is the last one or whose successor's cumClassic is > roll (signed); a scan
                    # that runs off the end gives nEntries, a miss
                    i = len(ents)
                    for k in range(len(ents)):
                        if ents[k]["flags"] & F_EXPONLY and not cf.get("noskip"):
                            continue
                        if k >= len(ents) - 1 or ents[k + 1]["cumc"] > roll:
                            i = k
                            break
                    cls["scan"] += 1
                    cls["miss" if i >= len(ents) else "skip" if any(
                        ents[k]["flags"] & F_EXPONLY for k in range(i)) else "plain"] += 1
                    if any(e_["flags"] & F_EXPONLY for e_ in ents):
                        bump("classic.sel.in_tc_with_exponly")
                        if i < len(ents) and any(ents[k]["flags"] & F_EXPONLY for k in range(i + 1, len(ents))):
                            bump("classic.sel.exponly_after")
                eq("SEL", i, int(expect("SEL")["i"]))
                if f["tc"] <= T.n_auto_types * 32:
                    bump("sel.autotc")
                if i >= len(ents):
                    bump("consume.miss")
                    continue
                e = ents[i]
                if e["flags"] & F_TC:
                    sub = e["index"]
                    eq("SUB", sub, int(expect("SUB")["tc"]))
                    parent = cur
                    if f["left"] > 0 or cf.get("notail"):
                        cur += 1
                        bump("push.new")
                    else:
                        bump("push.tail")
                    if cur >= 64:
                        raise Mismatch("stack overflow")
                    stc = T.tcs[sub]
                    pr = frames[parent]["ratio"]
                    nr = [stc["ratio"][k] if (pr[k] == 0 or stc["ratio"][k] > pr[k]) else pr[k] for k in range(6)]
                    if parent == cur and any(pr):
                        bump("push.tail.parent_ratio_nz")
                        if nr != list(stc["ratio"]):
                            bump("push.tail.parent_ratio_kept")
                    if any(pr[k] and stc["ratio"][k] and pr[k] != stc["ratio"][k] for k in range(6)):
                        bump("push.ratio_max_of_two")
                    bump("consume.sub")
                    if st is not None:
                        st["depth.max"] = max(st.get("depth.max", 0), cur)
                    fr = dict(tc=sub, left=max(1, abs(stc["picks"])), ratio=nr)
                    if cur < len(frames):
                        frames[cur] = fr
                    else:
                        frames.append(fr)
                    continue
                if e["index"] == 0xFFFF:
                    bump("consume.ffff")
                    continue
                if not exp:
                    # classic (0x0055AC75-0x0055AC9B): an item record with version >= 100 is rejected, the pick
                    # stays consumed. The cm=..cg= ratio raises that follow are all zero: _tcex stops on any of them
                    rec = T.items[e["index"]] if e["index"] < len(T.items) else None
                    if rec is None or rec["version"] >= 100:
                        cls["vreject"] += 1
                        bump("consume.vreject")
                        continue
                if e["flags"] & F_UNIQUE:
                    q, uidx = 7, e["aux"] + 1
                    bump("entry.unique")
                elif e["flags"] & F_SET:
                    q, uidx = 5, e["aux"] + 1
                    bump("entry.set")
                else:
                    uidx = 0
                    if fq:
                        q = fq
                        bump("quality.forced")
                    else:
                        kv = expect("QIN")
                        qcalls += 1
                        eq("QIN item", e["index"], int(kv["item"]))
                        eq("QIN seed", (lo, hi), seedpair(kv["seed"]))
                        eq("QIN ratio", f["ratio"], [int(x) for x in kv["ratio"].split(",")])
                        eq("QIN ilvl", int(tcr["ilvl"]), int(kv["ilvl"]))
                        extra = {}
                        while pos[0] < len(events) and events[pos[0]][0] in quality.QEXTRA:
                            extra[events[pos[0]][0]] = events[pos[0]][1]
                            pos[0] += 1
                        if qmodel:
                            QT, mf_in, linear = qmodel
                            mf, src = quality.magic_find(extra, tcr, mf_in)
                            seed_in = (lo, hi)
                            q, (lo, hi), why, ndraw, ri = quality.roll(QT, e["index"], int(tcr["ilvl"]), f["ratio"],
                                                                       (lo, hi), mf, linear, cf=cf.get("qcf"))
                            src = src if ri is not None else "unused"  # early returns read no magic find
                            mfsrc[src] = mfsrc.get(src, 0) + 1
                            bump("quality.model")
                            bump("quality.model.draws%d" % ndraw)
                            if st is not None and "qhook" in st:
                                st["qhook"](QT, e["index"], int(tcr["ilvl"]), list(f["ratio"]), seed_in, mf, q,
                                            why, ndraw, ri, tcr, extra)
                            if "QROW" in extra:
                                eq("QROW itemratio row", -1 if ri is None else ri, int(extra["QROW"]["row"]))
                                bump("quality.qrow")
                        else:
                            bump("quality.oracle")
                    kv = expect("QOUT")  # logged for a rolled and for a forced quality
                    if qmodel:
                        eq("QOUT quality (model, no oracle)", q, int(kv["q"]))
                        eq("QOUT seed (model, no oracle)", (lo, hi), seedpair(kv["seed"]))
                    else:  # the oracle's answer
                        q = int(kv["q"])
                        lo, hi = seedpair(kv["seed"])
                up = 0
                for k, bit in ((4, 0x04), (5, 0x10)):
                    if f["ratio"][k]:
                        bump("upgrade.draw")
                        lo, hi = rng.step(lo, hi)
                        if (lo & 0x3FF) < f["ratio"][k]:
                            up |= bit
                item = e["index"]
                if not exp and T.itypes[T.items[item]["type"]]["throwable"]:
                    # classic (0x0055AE6E-0x0055AEC2): the item's own type is throwable. The first 10 in this
                    # call refund the pick (after the quality roll and the upgrade draws); later ones drop 'lsd '
                    throw_retries += 1
                    if throw_retries <= 10:
                        f["left"] += 1
                        cls["refund"] += 1
                        continue
                    item = T.code2item["lsd "]
                    cls["lsd"] += 1
                kv = expect("CPRE")
                eq("CPRE item", item, int(kv["item"]))
                eq("CPRE quality", q, int(kv["q"]))
                eq("CPRE uidx", uidx, int(kv["uidx"]))
                eq("CPRE flags", up, int(kv["up"]))
                eq("CPRE seed", (lo, hi), seedpair(kv["seed"]))
                bump("create.call")
                kv = expect("CPOST")
                eq("creation leaves the source seed", (lo, hi), seedpair(kv["seed"]))
                if int(kv["unit"], 16) == 0:
                    bump("create.nounit")
                    continue
                count += 1
                if count >= mx:
                    bump("max.reached")
                    if any(frames[k]["left"] for k in range(cur + 1)):
                        bump("max.reached.picks_left")
                    break
            if count >= mx:
                break
        if cur == 0:
            break
        if cf.get("nopop"):
            break
        cur -= 1
        bump("pop")
        if frames[cur]["left"]:
            bump("pop.parent_resumes")
    kv = expect("TCEND")
    eq("TCEND count", count, int(kv["count"]))
    eq("TCEND seed", (lo, hi), seedpair(kv["seed"]))
    if pos[0] != len(events):
        raise Mismatch("unconsumed lines: %s" % [h for h, _ in events[pos[0]:]])
    return dict(tc=root, name=t0["name"], count=count, picks=picks, qcalls=qcalls, ndps=ndps, mfsrc=mfsrc,
                cls=cls,
                src="%s/%s" % (tcr["stype"], tcr["sclass"]), mflags=tcr.get("mflags"), diff=tcr["diff"],
                party=sorted(set(seen)), pm=pm)


MON_KINDS = ("normal", "minion", "champion", "unique", "superunique")
# classic-game events (items/0001 sections 5.1 and 8): scan = linear selections, of which plain (no
# expansion-only entry before the pick), skip (one or more skipped), miss (ran off the end); vreject = item
# records with version >= 100 rejected; refund = throwable picks refunded; lsd = throwables made a Long Sword
CLASSIC_KEYS = ("scan", "plain", "skip", "miss", "vreject", "refund", "lsd")


B6_TAGS = ("B60", "B6O", "B6E", "B6F", "B6P", "B6G", "B6X")


def b6_model(group):
    """The quest-TC switch of MONSTER_DropItems (items/0010 section 2) from one B60 .. B6X group of
    tools/gdb/quests.py: the killer chain (B6O owner, B6E exp state, B6F its caster) and the resolved player's quest
    word (B6P). Returns (tc, taken, why); raises Mismatch when a logged step differs from the model (a GetState
    result, a resolution step logged or missing, the B6X tc)."""
    tags = [t for t, _ in group]
    if not tags or tags[0] != "B60" or tags[-1] != "B6X":
        raise Mismatch("B6 group %s: want B60 .. B6X" % tags)
    b0, bx = group[0][1], group[-1][1]
    rest = group[1:-1]
    one = {t: v for t, v in rest if t != "B6G"}
    gets = [v for t, v in rest if t == "B6G"]
    tc, tc4, cp, k = b0["tc"], b0["tc4"], b0["cp"], b0["killer"]
    want, taken, why = tc, False, None
    if not tc4 or not b0["ctx"] or not k:
        why = "no TreasureClass4" if not tc4 else "no kill context" if not b0["ctx"] else "no killer"
        if rest:
            raise Mismatch("B6 %s, but lines %s" % (why, [t for t, _ in rest]))
    else:
        if k[0] != 0:
            if "B6O" not in one or "B6E" not in one:
                raise Mismatch("B6: a non-player killer %s without B6O/B6E" % (k,))
            p = one["B6O"]["owner"]
            if one["B6E"]["exp"]:
                if "B6F" in one:
                    p = one["B6F"]["caster"]
            elif "B6F" in one:
                raise Mismatch("B6F without an exp state")
            if p:
                k = p
        elif "B6O" in one or "B6E" in one:
            raise Mismatch("B6: a player killer resolved again")
        if k[0] != 0:
            why = "killer %s is not a player" % (k,)
            if "B6P" in one:
                raise Mismatch("B6P for a non-player")
        else:
            if "B6P" not in one or one["B6P"]["unit"] != k:
                raise Mismatch("B6P: want the record of %s, log %s" % (k, one.get("B6P")))
            w = one["B6P"]["word"]
            if not one["B6P"]["rec"] or w is None:
                why = "no record"
            else:
                order = [(15, 15), (1, 1), ("cp", cp)]
                why = None
                for i, (lab, bit) in enumerate(order):
                    r = (w >> bit) & 1
                    if i >= len(gets) or gets[i]["k"] != lab or gets[i]["r"] != r:
                        raise Mismatch("B6 GetState %s (bit %d of word 0x%04x): model %d, log %s" % (
                            lab, bit, w, r, gets[i] if i < len(gets) else None))
                    if r == 1:
                        why = "bit %d set" % bit
                        break
                n_exp = i + 1
                if len(gets) != n_exp:
                    raise Mismatch("B6: %d GetState lines, model %d" % (len(gets), n_exp))
                if why is None:
                    want, taken, why = tc4, True, "bits 15, 1, %d clear" % cp
    if bx["tc"] > 0xFFFF:
        pass    # logs before the B6X fix of 2026-10-16 logged ECX (the game) there: the DROP base still decides
    elif bx["tc"] != want:
        raise Mismatch("B6X tc %s, model %s (%s)" % (bx["tc"], want, why))
    return want, taken, why


def check_monster_source(T, tcr, drop, b6=None):
    """Base TC and upgrade level of a monster drop from the tables (MONSTER_DropItems, TC_DropByIndex). With the B6
    lines of tools/gdb/quests.py before the drop (plan 0032 Phase 2) the quest TC is no longer just accepted: the base
    must be the tc of b6_model."""
    diff, mflags, cls = int(tcr["diff"]), int(tcr.get("mflags", "0"), 16), int(tcr["sclass"])
    rec = T.monstats(cls)
    col = lambda k: struct.unpack_from("<H", rec, 0x86 + 8 * diff + 2 * k)[0]  # noqa: E731
    if mflags & 0x02 and mflags & 0x08:
        kind, base = "superunique", T.superunique_tc(int(tcr["suid"]), diff) or col(2)
    elif mflags & 0x04:
        kind, base = "champion", col(1)
    elif mflags & 0x08:
        kind, base = "unique", col(2)
    else:
        kind, base = ("minion" if mflags & 0x10 else "normal"), col(0)
    ok = {base}
    if rec[0x9E] and col(3):
        if b6 is not None:
            want, taken, why = b6_model(b6)
            if group_tc(b6) != base:
                raise Mismatch("B60 tc %s, tables %s" % (group_tc(b6), base))
            ok = {want}
            B6_COUNT[(cls, diff, taken)] = B6_COUNT.get((cls, diff, taken), 0) + 1
        else:
            ok.add(col(3))  # quest TC: the killer's quest state is not logged
    if int(drop["base"]) not in ok:
        raise Mismatch("base TC (%s, sclass %d): tables %s, DROP %s" % (kind, cls, sorted(ok), drop["base"]))
    upgrade = int(tcr["exp"]) and diff > 0 and not rec[0x0C] & 0x04 and not rec[0x0C] & 0x40
    lvl = int(tcr["ilvl"]) if upgrade else 0
    if int(drop["lvl"]) != lvl:
        raise Mismatch("upgrade level (%s, diff %d): model %d, DROP %s" % (kind, diff, lvl, drop["lvl"]))
    return kind


B6_COUNT = {}


def group_tc(group):
    return group[0][1]["tc"]


def read_calls(path):
    """The resolver calls of a log: a list of (call, err), call = [(head, kv), ...] from TCR to TCEND with the
    call's DROP (or None) and party context (list) at positions 1 and 2, err a string when the call is cut off."""
    calls, cur, drops, ctx = [], None, [], []
    b6 = None
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line or line[0] not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" or line.startswith("Breakpoint"):
            continue
        if line.partition(" ")[2].startswith("{"):
            tag = line.partition(" ")[0]
            if tag in B6_TAGS:      # tools/gdb/quests.py (plan 0032 Phase 2): the quest-TC test before the DROP
                if tag == "B60":
                    b6 = []
                b6.append((tag, json.loads(line.partition(" ")[2])))
            continue  # a "TAG {json}" line of another logger (e.g. tools/gdb/uniques.gdb, plan 0019): not a TC event
        head, kv = parse(line)
        if head == "DROP":
            kv["_b6"] = b6 if b6 and b6[-1][0] == "B6X" else None
            b6 = None
            drops.append(kv)
        if head in ("PLR", "PTY", "KILL") and cur is None:
            if head == "PLR" and ctx and ctx[-1][0] != "PLR":
                ctx = []  # a new TC_DropByIndex entry
            ctx.append((head, kv))
            continue
        if head == "TCR":
            if cur is not None:
                calls.append((cur, None))
            cur = [(head, kv)]
            # a DROP belongs to this call only if it names the same source (a TC_DropByIndex whose TC
            # resolves to none, e.g. base 0, logs a DROP and no TCR)
            cur_drop = drops[-1] if drops and drops[-1].get("src") == kv.get("src") else None
            drops = []
            cur.append(("_DROP", cur_drop))
            cur.append(("_CTX", ctx if cur_drop else []))
            ctx = []
            continue
        if cur is None:
            continue
        cur.append((head, kv))
        if head == "TCEND":
            calls.append((cur, None))
            cur = None
    if cur is not None:
        calls.append((cur, "no TCEND (log ends inside the call)"))
    return calls


def replay_calls(T, calls, qmodel=None, verbose=False, st=None, cf=None, quiet=False, onsrc=None):
    """Replay the calls of read_calls. Returns (ok, bad, kinds, classic counts, classic calls, rolls by mf source).
    onsrc, if given, is called as onsrc(tcr, drop, kind) for every monster call whose source check passed."""
    ok = bad = 0
    kinds = {}
    ccount = dict.fromkeys(CLASSIC_KEYS, 0)
    ncls = 0
    rolls = {}
    for k, (call0, err) in enumerate(calls):
        call = list(call0)
        drop = call.pop(1)[1]
        ctx = call.pop(1)[1] if len(call) > 1 and call[1][0] == "_CTX" else []
        try:
            if err:
                raise Mismatch(err)
            if drop and call[0][1]["stype"] == "1":
                kind = check_monster_source(T, call[0][1], drop, drop.get("_b6"))
                kinds[kind] = kinds.get(kind, 0) + 1
                if onsrc:
                    onsrc(call[0][1], drop, kind)
            if drop:
                up = T.get(int(drop["base"]), int(drop["lvl"]))
                if up != int(call[0][1]["tc"]):
                    raise Mismatch("level upgrade: model TC %s, log %s" % (up, call[0][1]["tc"]))
            s = replay_call(T, call, ctx=ctx, qmodel=qmodel, st=st, cf=cf)
            ok += 1
            if call[0][1]["exp"] == "0":
                ncls += 1
                for kk, vv in s["cls"].items():
                    ccount[kk] += vv
            for kk, vv in s["mfsrc"].items():
                rolls[kk] = rolls.get(kk, 0) + vv
            if verbose:
                b = (" base=%s lvl=%s" % (drop["base"], drop["lvl"])) if drop else ""
                print("ok   #%d tc=%d %r src=%s mflags=%s diff=%s%s picks=%d q=%d count=%d nodrop=%s" % (
                    k, s["tc"], s["name"], s["src"], s["mflags"], s["diff"], b, s["picks"], s["qcalls"],
                    s["count"], sorted(set(s["ndps"]))))
                if s["pm"]:
                    print("     party/players logged %s; %s" % (s["party"] or "-", s["pm"]["notes"]))
        except Mismatch as ex:
            bad += 1
            if not quiet:
                print("FAIL #%d %s: %s" % (k, call[0][1].get("tc"), ex))
    return ok, bad, kinds, ccount, ncls, rolls


def cmd_replay(ns):
    T = Tables(ns.excel)
    qmodel = (quality.Tables(ns.excel), ns.mf, ns.mf_linear) if ns.quality == "model" else None
    ok, bad, kinds, ccount, ncls, rolls = replay_calls(T, read_calls(ns.log), qmodel, ns.verbose)
    if qmodel:
        qdesc = "quality: model, no oracle (mf input %d%s; rolls by mf source: %s)" % (
            ns.mf, ", LINEAR counterfactual" if ns.mf_linear else "",
            ", ".join("%s %d" % kv_ for kv_ in sorted(rolls.items())) or "none")
    else:
        qdesc = "quality: oracle"
    print("%d calls, %d reproduced, %d failed; monster sources checked: %s; %s" % (
        ok + bad, ok, bad, ", ".join("%s %d" % (n, kinds.get(n, 0)) for n in MON_KINDS), qdesc))
    if B6_COUNT:
        print("quest-TC test (B6) reproduced: %s" % ", ".join(
            "class %d diff %d %s %d" % (c, d, "taken" if t else "not taken", n) for (c, d, t), n in sorted(B6_COUNT.items())))
    if ncls:
        print("classic calls reproduced %d: %s" % (ncls, ", ".join("%s %d" % (k, ccount[k]) for k in CLASSIC_KEYS)))
    return 0 if bad == 0 and ok > 0 else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("replay")
    a.add_argument("log")
    a.add_argument("--excel", default=EXCEL)
    a.add_argument("-v", "--verbose", action="store_true")
    a.add_argument("--quality", choices=("oracle", "model"), default="oracle",
                   help="oracle: take QOUT (ADR-0004); model: tools/quality.py, QOUT only asserted")
    a.add_argument("--mf", type=int, default=0,
                   help="--quality model: magic find of a player/monster killer when the log has no QMF line")
    a.add_argument("--mf-linear", action="store_true",
                   help="--quality model: counterfactual linear magic find (no diminishing returns)")
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

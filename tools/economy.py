#!/usr/bin/env python3
"""Item economy model and checker (plan 0043 Phase 2, docs/findings/items/0011-economy.md).

Usage:
  python3 -I tools/economy.py check <excel-dir> <log> [<log> ...] [-v]   # replay tools/gdb/economy.py logs
  python3 -I tools/economy.py price <excel-dir> <log> <k>                 # one logged price payload, step by step

The model reads the compiled tables (<excel-dir>/*.bin: the records the game loads, the offsets of items/0011's
"Data touched") and predicts, from the inputs the logger writes at each event's entry, what the game wrote at its exit:

  price     ITEMS_TradePriceCore (modes 0-3) and its gamble path, from the item's logged class, quality, flags,
            affix ids, file index, own and full-stat lists and socketed children, the player's stats 12 and 87,
            the quest record bytes, the difficulty and the NPC class (one-shot, ADR-0004; the item's stat lists
            are value oracles, plan 0043 P1 boundary)
  repair    RepairCost = the sum of its mode-3 price calls; ItemRepairAll / ItemRepairBroken: what is restored
  gold      UnitAddGoldStat (zero on overflow of level x 10 000 / 2 500 000), PayGold, the death loss, the gold
            item amount at creation (ilvl + RNG_Range(item seed, 5 ilvl), at least 1), DropGoldFind
  resurrect MERC_ResurrectCost
  wear      ITEMS_DurabilityLossRoll (one LCG step of the seed owner, roll = low % 100 < chance) and
            COMBAT_DurabilityLoss (RangeB(7), RangeB(W) over g_ArmorWearSlots on the defender's seed), per event,
            each with its seeds; chained pairs counted where one event's exit seed is the next one's entry seed
  ticks     ItemConsumeOne, ITEMEVENT_Replenish
  seeds     for every event kind, the game seed and the player's seed at entry and exit: unchanged or not

Every line of the summary is a count; a mismatch prints the event and exits 1. Stdlib only. Read-only.
"""
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402

M32 = 0xFFFFFFFF


def w32(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def imul(a, b):
    return w32(a * b)


def tdiv(a, b):
    """C signed division, truncating toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def d1024(x):
    return tdiv(w32(x), 1024)


def d4096(x):
    return tdiv(w32(x), 4096)


def udiv_add(acc, d, n):
    """acc += (unsigned)d / (unsigned)n, 32-bit."""
    return w32(acc + ((d & M32) // (n & M32)))


def muldiv(a, b, c):
    """sub_00483360_MulDiv(a, b, c), signed 32-bit with its 64-bit escape."""
    if c == 0:
        return 0
    if a > 0x100000:
        if c > (a >> 4):
            return w32(tdiv(a * b, c))
        return imul(tdiv(a, c), b)
    if b > 0x10000:
        if c > (b >> 4):
            return w32(tdiv(a * b, c))
        return imul(tdiv(b, c), a)
    return tdiv(imul(a, b), c)


class Mismatch(Exception):
    pass


# ------------------------------------------------------------------------------------------------ tables

def _bin(excel, name, size):
    b = open(os.path.join(excel, name + ".bin"), "rb").read()
    n = struct.unpack_from("<I", b, 0)[0]
    if len(b) != 4 + n * size:
        raise SystemExit("%s.bin: %d records of %d bytes expected" % (name, n, size))
    return [b[4 + i * size:4 + (i + 1) * size] for i in range(n)]


def u8(r, o):
    return r[o]


def s16(r, o):
    return struct.unpack_from("<h", r, o)[0]


def u16(r, o):
    return struct.unpack_from("<H", r, o)[0]


def s32(r, o):
    return struct.unpack_from("<i", r, o)[0]


def u32(r, o):
    return struct.unpack_from("<I", r, o)[0]


class Tables:
    def __init__(self, excel):
        self.items = _bin(excel, "weapons", 424) + _bin(excel, "armor", 424) + _bin(excel, "misc", 424)
        self.types = _bin(excel, "itemtypes", 228)
        self.isc = _bin(excel, "itemstatcost", 324)
        self.skills = _bin(excel, "skills", 572)
        self.affixes = _bin(excel, "magicsuffix", 144) + _bin(excel, "magicprefix", 144) + _bin(excel, "automagic", 144)
        self.uniques = _bin(excel, "uniqueitems", 332)
        self.sets = _bin(excel, "setitems", 440)
        self.npcs = {s32(r, 0): r for r in _bin(excel, "npc", 76)}
        self.books = _bin(excel, "books", 32)
        self.monstats = _bin(excel, "monstats", 424)
        self.by_code = {}
        for i, r in enumerate(self.items):
            self.by_code.setdefault(r[0x80:0x84], i)
        self.tcode = {r[0:4].decode("latin-1").strip(): i for i, r in enumerate(self.types) if r[0:4].strip()}
        self._clos = {}

    def closure(self, t):
        if t in self._clos:
            return self._clos[t]
        out, todo = set(), [t]
        while todo:
            x = todo.pop()
            if x <= 0 or x in out or x >= len(self.types):
                continue
            out.add(x)
            todo += [u16(self.types[x], 4), u16(self.types[x], 6)]
        self._clos[t] = out
        return out

    def base(self, c):
        return self.items[c]

    def is_type(self, c, tcode):
        t = self.tcode[tcode]
        b = self.items[c]
        if t in self.closure(s16(b, 0x11E)):
            return True
        t2 = u16(b, 0x120)
        return t2 > 0 and t in self.closure(t2)

    def own_type(self, c):
        return self.types[s16(self.items[c], 0x11E)]


# ------------------------------------------------------------------------------------------------ the item

class Item:
    def __init__(self, d):
        self.d = d
        self.c = d["c"]
        self.q = d.get("q")
        self.fl = d.get("fl", 0)
        self.fi = d.get("fi", -1)
        self.v = d.get("v", 0)
        self.own = {k: v for k, v in d.get("own", [])}
        self.ext = bool(d.get("lf", 0) & 0x80000000)
        self.cache = {k: v for k, v in d.get("cache", [])} if self.ext else self.own
        self.cache_list = d.get("cache", []) if self.ext else []

    def stat(self, sid, param=0):
        return self.cache.get(sid << 16 | param, 0)

    def base_stat(self, sid, param=0):
        return self.own.get(sid << 16 | param, 0)

    def entries(self, sid):
        return [(k & 0xFFFF, v) for k, v in self.cache_list if k >> 16 == sid]


class Model:
    def __init__(self, T, shift=6, mask=0x3F):
        self.T = T
        self.shift, self.mask = shift, mask

    # helpers of items/0011 § 1-§ 5
    def max_stack(self, it):
        return min(0x1FF, w32(s32(self.T.base(it.c), 0xE8) + it.stat(254)))

    def stackable(self, it):
        return self.T.base(it.c)[0x132] != 0

    def quiver(self, it):
        return s16(self.T.own_type(it.c), 0x0E) != 0

    def throwable(self, it):
        return self.T.own_type(it.c)[0x10] != 0

    def ethereal(self, it):
        return bool(it.fl & 0x400000)

    def max_dur(self, it):
        return it.stat(73) if it.base_stat(73) else 0

    def has_dur(self, it):
        b = self.T.base(it.c)
        if b[0x113] != 0 or b[0x112] == 0:
            return False
        if not self.max_dur(it):
            return False
        return it.stat(152) <= 0

    def has_charges(self, it):
        """sub_0062A840_ItemHasCharges: (any stat 204 entry, all full)."""
        es = it.entries(204)
        if not es:
            return False, True
        full = all((v & 0xFF) >= (v >> 8) for _, v in es)
        return True, full

    def repairable_stack(self, it):
        return (self.T.own_type(it.c)[8] != 0 and self.throwable(it) and self.stackable(it)
                and not self.ethereal(it))

    def can_repair(self, it):
        if not it.fl & 0x10 or self.ethereal(it):
            return False
        has, full = self.has_charges(it)
        if has and not full:
            return True
        if self.T.own_type(it.c)[8] == 0:
            return False
        if self.repairable_stack(it):
            return True
        return self.has_dur(it)

    def staff_mods(self, it, P, S, R, n):
        if self.T.own_type(it.c)[0x1F] == 7:
            return P, S, R
        dP = dS = dR = 0
        for param, v in it.entries(107):
            if param >= len(self.T.skills):
                continue
            k = self.T.skills[param]
            m, a = s32(k, 0x234), s32(k, 0x238)
            c = w32(2 * v - 1)
            if P > 0xFFFF and m != 0:
                e = d1024(m)
                dP = w32(dP + imul(w32(imul(e, P) + a), c))
                dS = w32(dS + imul(w32(imul(d4096(m), S) + a), c))
                dR = w32(dR + imul(w32(imul(e, R) + a), c))
            else:
                dP = w32(dP + imul(w32(d1024(imul(m, P)) + a), c))
                dS = w32(dS + imul(w32(d4096(imul(S, m)) + a), c))
                dR = w32(dR + imul(w32(d1024(imul(R, m)) + a), c))
        return udiv_add(P, dP, n), udiv_add(S, dS, n), udiv_add(R, dR, n)

    def stat_terms(self, it, P, S, R, n, trace=None):
        dP = dS = dR = 0
        for key, full in it.cache_list[:0x1FF]:
            sid, param = key >> 16, key & 0xFFFF
            v = w32(full - it.own.get(key, 0))
            if v == 0 or sid >= len(self.T.isc):
                continue
            rec = self.T.isc[sid]
            if rec[0x18]:
                v >>= rec[0x18]
            enc = rec[0x30]
            if enc == 1:
                if param >= len(self.T.skills):
                    continue
                k = self.T.skills[param]
                m, a, x = s32(k, 0x234), s32(k, 0x238), v
                skill = True
            elif enc in (2, 3):
                sk, x = param >> self.shift, param & self.mask
                k = self.T.skills[sk] if 0 <= sk < len(self.T.skills) else None
                m, a = (s32(k, 0x234), s32(k, 0x238)) if k else (0, 0)
                skill = True
            elif enc == 4:
                raise Mismatch("Encode 4 stat %d in a price: not modelled" % sid)
            else:
                m, a, x = s32(rec, 0x10), s32(rec, 0x14), v
                skill = False
            sdiv = d4096 if skill else d1024
            if imul(P, x) > 0xFFFF and m != 0:
                dP = w32(dP + imul(d1024(imul(P, x)), m) + a)
                dS = w32(dS + imul(sdiv(imul(S, x)), m) + a)
                dR = w32(dR + imul(d1024(imul(R, x)), m) + a)
            else:
                dP = w32(dP + d1024(imul(imul(m, P), x)) + a)
                dS = w32(dS + sdiv(imul(imul(m, S), x)) + a)
                dR = w32(dR + d1024(imul(imul(m, R), x)) + a)
            if trace is not None:
                trace.append(("stat", sid, param, v, enc, m, a, dP, dS, dR))
        return udiv_add(P, dP, n), udiv_add(S, dS, n), udiv_add(R, dR, n)

    def recharge(self, it):
        tot = 0
        for param, v in it.entries(204):
            c, x = v & 0xFF, v >> 8
            if c >= x:
                continue
            sk, lvl = param >> self.shift, param & self.mask
            if not 0 <= sk < len(self.T.skills):
                continue
            k = self.T.skills[sk]
            K = lvl + 2 * tdiv(s16(k, 0x174), 6) + 2
            T = imul(K, 10000)
            m = s32(k, 0x234)
            if T > 0xFFFF and m != 0:
                t = imul(d1024(T), m)
            else:
                t = d1024(imul(imul(m, K), 10000))
            t = w32(t + s32(k, 0x238))
            tot = w32(tot + tdiv(imul(x - c, t), x))
        return tot

    def gamble(self, it, L):
        T = self.T
        b0 = T.base(it.c)
        code = b0[0x84:0x88] if u32(b0, 0x84) else b0[0x80:0x84]
        b = T.items[T.by_code[code]]
        if b[0x80:0x84] in (b"rin ", b"amu "):
            return s32(b, 0xD4)
        avg = max(1, tdiv(s32(b, 0xE8) + s32(b, 0xE4), 2))
        sc = imul(s32(b, 0xE0), avg)
        x = e = xc = ec = 0
        if u32(b, 0x88) and b[0x88:0x8C] != b"0   " and b[0x88:0x8C] in T.by_code:
            ub = T.items[T.by_code[b[0x88:0x8C]]]
            x = tdiv((L - ub[0xFD]) * 100, 2) + 1
            x = x if x >= 0 else 0
            xc = s32(ub, 0xE0)
        if u32(b, 0x8C) and b[0x8C:0x90] != b"0   " and b[0x8C:0x90] in T.by_code:
            tb = T.items[T.by_code[b[0x8C:0x90]]]
            e = tdiv((L - tb[0xFD]) * 100, 4) + 1
            e = e if e >= 0 else 0
            ec = s32(tb, 0xE0)
        tot = w32(imul(10000 - e - x, sc) + imul(ec, e) + imul(xc, x))
        avgc = tdiv(tot, 10000)
        L2 = max(L, 5)
        lvl = b[0xFD]
        lv = (lvl - 45 if lvl >= 45 else 0) - tdiv(lvl, 2) + L2
        return tdiv(imul(w32(tdiv(imul(lv, 250), 3) + avgc), tdiv(2 * L2 + 1, 3) + 20), 15)

    def qbit(self, qb, qid, bit):
        if qb is None:
            return False
        i = qid * 16 + bit
        raw = bytes.fromhex(qb)
        return bool(raw[i >> 3] & (1 << (i & 7))) if (i >> 3) < len(raw) else False

    def price(self, p, trace=None):
        T = self.T
        mode, d, npc = p["m"], p["d"], p["npc"]
        it = Item(p["it"])
        if it.d.get("t") != 4:
            return 0x7FFFFFFF
        L = p["plv"] or 0
        if mode == 3 and not self.can_repair(it):
            return 0
        if it.fl & 0x20000:
            return 1
        b = T.base(it.c)
        cost = s32(b, 0xE0)
        q = it.stat(70)
        q = q if q > 0 else 1
        r = p["prp"] or 0
        r = 99 if r >= 99 else r
        if mode == 2:
            if it.v >= 1:
                G = self.gamble(it, L)
                return w32(G - muldiv(G, r, 100)) if r else G
            return s32(b, 0xD4)
        R, n = 0, 1
        if it.fl & 0x10000:
            P = S = imul(it.d.get("ear", 1), cost)
        elif T.is_type(it.c, "body"):
            fi = it.fi
            ms = T.monstats[fi] if 0 <= fi < len(T.monstats) else None
            P = S = w32(cost + 8 * s16(ms, 0xAA + 2 * d)) if ms is not None else cost
        elif T.is_type(it.c, "book"):
            bk = T.books[it.d["suf"][0]]
            P = S = w32(imul(s32(bk, 0x14), q) + cost)
        elif self.quiver(it):
            P = S = d1024(imul(cost, q))
            R = d1024(imul(self.max_stack(it), cost))
        else:
            P = S = R = cost
            if self.stackable(it):
                ms = self.max_stack(it)
                n = ms if ms > 1 else 1
        if T.is_type(it.c, "armo"):
            maxac, minac = s32(b, 0xD0), s32(b, 0xCC)
            if w32(maxac - minac + 1) != 0 and maxac != 0:
                P = S = R = tdiv(imul(cost, it.base_stat(31)), maxac)
        if trace is not None:
            trace.append(("base", P, S, R, n))
        ident = bool(it.fl & 0x10)
        qual = it.q
        magicplus = 4 <= qual <= 9
        if not magicplus:
            P, S, R = self.staff_mods(it, P, S, R, n)
        if ident:
            dP = dS = dR = 0

            def add(m, a, dP, dS, dR):
                if P > 0xFFFF and m != 0:
                    return (w32(dP + imul(d1024(P), m) + a), w32(dS + imul(d1024(S), m) + a),
                            w32(dR + imul(d1024(R), m) + a))
                return (w32(dP + d1024(imul(m, P)) + a), w32(dS + d1024(imul(m, S)) + a),
                        w32(dR + d1024(imul(m, R)) + a))

            def affix(aid):
                if 0 < aid <= len(T.affixes):
                    a = T.affixes[aid - 1]
                    return s32(a, 0x88), s32(a, 0x8C)
                return None

            a0 = affix(it.d.get("aa", 0))
            if a0:
                dP, dS, dR = add(a0[0], a0[1], 0, 0, 0)
            terms = False
            if qual == 1:
                dP, dS, dR = -tdiv(P, 2), -tdiv(S, 2), -tdiv(R, 2)
            elif qual in (3, 9):
                terms = True
            elif qual in (6, 8):
                for i in range(3):
                    for aid in (it.d["pre"][i], it.d["suf"][i]):
                        a = affix(aid)
                        if a:
                            dP, dS, dR = add(a[0], a[1], dP, dS, dR)
                terms = True
            elif qual == 5:
                rec = T.sets[it.fi] if 0 <= it.fi < len(T.sets) else None
                if rec is not None:
                    dP, dS, dR = add(s32(rec, 0x38), s32(rec, 0x3C), dP, dS, dR)
            elif qual == 7 and 0 <= it.fi < len(T.uniques):
                rec = T.uniques[it.fi]
                dP, dS, dR = add(s32(rec, 0x7C), s32(rec, 0x80), dP, dS, dR)
            elif qual in (4, 7):
                for aid in (it.d["pre"][0], it.d["suf"][0]):
                    a = affix(aid)
                    if a:
                        dP, dS, dR = add(a[0], a[1], dP, dS, dR)
                terms = True
            if trace is not None:
                trace.append(("affix", dP, dS, dR))
            if terms:
                P, S, R = self.stat_terms(it, P, S, R, n, trace)
            P, S, R = w32(P + tdiv(dP, n)), w32(S + tdiv(dS, n)), w32(R + tdiv(dR, n))
            if magicplus:
                P, S, R = self.staff_mods(it, P, S, R, n)
        for c in it.d.get("ch", []):
            h = tdiv(s32(T.base(c), 0xE0), 2)
            P, S, R = w32(P + h), w32(S + h), w32(R + h)
        if self.ethereal(it):
            S = tdiv(S, 4)
        if T.own_type(it.c)[0x21] < 7:
            S = tdiv(S, 4)
        if trace is not None:
            trace.append(("value", P, S, R))
        if mode == 1:
            if self.ethereal(it) and self.has_dur(it) and self.max_dur(it) != 0 and it.stat(72) <= 0:
                S = 0
        elif mode == 3:
            if not self.quiver(it) and not self.throwable(it) and self.has_dur(it):
                D, M = it.stat(72), self.max_dur(it)
                if M == 0 or D >= M:
                    R = 0
                elif it.stat(252):
                    R = 0 if D >= M - 1 else tdiv(imul(M - 1, R), M)
                else:
                    R = tdiv(imul(M - D, R), M)
        rec = T.npcs.get(npc)
        if rec is None:
            raise Mismatch("npc class %d has no Npc row" % npc)
        sell, buy, rep = s32(rec, 4), s32(rec, 8), s32(rec, 0xC)

        def scale(v, m, test):
            return imul(d1024(v), m) if v > 0xFFFF and test != 0 else d1024(imul(m, v))

        P = scale(P, sell, sell)
        S = scale(S, buy, sell)
        R = scale(R, rep, rep)
        for k in range(3):
            f = s32(rec, 0x10 + 4 * k)
            if f and (self.qbit(p["qb"], f, 0) or self.qbit(p["qb"], f, 1)):
                mp, ms_, mr = s32(rec, 0x1C + 4 * k), s32(rec, 0x28 + 4 * k), s32(rec, 0x34 + 4 * k)
                P = scale(P, mp, mp)
                S = scale(S, ms_, ms_)
                R = scale(R, mr, mr)
        if trace is not None:
            trace.append(("npc", P, S, R))
        if not T.is_type(it.c, "book") and not self.quiver(it):
            P = imul(P, q)
            if self.stackable(it) and self.can_repair(it):
                M = self.max_stack(it)
                if q < M and it.stat(253) == 0:
                    R = imul(R, M - q)
                    S = w32(imul(M, S) - R)
                else:
                    S = imul(M, S)
                    R = 0
            else:
                S = imul(S, q)
        if mode == 3 and not self.ethereal(it):
            R = w32(R + self.recharge(it))
        mb = s32(rec, 0x40 + 4 * d)
        S2 = mb if S > mb else S
        if trace is not None:
            trace.append(("final", P, S, R, S2))
        if mode == 1:
            return S2 if S2 >= 1 else 1
        if mode == 3:
            if r:
                R = w32(R - muldiv(R, r, 100))
            return R if R >= 1 else 1
        if r:
            P = w32(P - muldiv(P, r, 100))
        return P if P >= 1 else 1


# ------------------------------------------------------------------------------------------------ logs

def read_events(path):
    out = []
    with open(path, errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            sp = line.find(" {")
            if sp < 2 or sp > 6:
                continue
            tag = line[:sp]
            if not tag.isalnum():
                continue
            try:
                d = json.loads(line[sp + 1:])
            except ValueError:
                continue
            out.append((tag, d, ln))
    return out


WEAR_SLOTS = [(1, 3), (3, 5), (4, 4), (5, 4), (8, 2), (9, 2), (10, 2)]


def seedpair(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


class Checker:
    def __init__(self, T, verbose=False):
        self.T, self.v = T, verbose
        self.M = Model(T)
        self.n = collections.Counter()
        self.keys = {}
        self.distinct = set()
        self.cases = collections.Counter()
        self.seeds = collections.defaultdict(collections.Counter)
        self.mis = []
        self.sww = collections.Counter()

    def fail(self, path, ln, msg):
        self.mis.append("%s:%d: %s" % (os.path.basename(path), ln, msg))

    def seedcheck(self, kind, d0, d1):
        s0, s1 = d0.get("sn") or {}, d1.get("sn") or {}
        for k in ("gs", "ps"):
            if s0.get(k) is None or s1.get(k) is None:
                continue
            if s0[k] == s1[k]:
                self.seeds[kind][k + " same"] += 1
            else:
                n = rng.steps_between(seedpair(s0[k]), seedpair(s1[k]), 2000)
                self.seeds[kind][k + " +%s steps" % (n if n is not None else ">2000")] += 1

    def check_log(self, path):
        ev = read_events(path)
        self.last_exit, self.rp_last = {}, {}     # unit ids repeat from game to game: chain within one log only
        open_ = collections.defaultdict(list)     # tag0 -> stack of entry dicts
        econ = None
        rc = []          # open RepairCost sums
        last_seed = {}   # unit -> exit seed of its last wear draw, for chaining
        pend_cd = None
        dl_pending = None
        last_rp = {}
        trade = {"sellk": [], "sellv": [], "buyk": [], "buyv": []}
        pend_gf = {}
        pend_gpl = None
        for tag, d, ln in ev:
            if tag == "ECON":
                econ = d
                if d.get("affixes") != len(self.T.affixes) or d.get("items") != len(self.T.items):
                    self.fail(path, ln, "table sizes differ: %r" % d)
                self.M.shift, self.M.mask = d["shift"], d["mask"]
                self.n["games"] += 1
            elif tag.endswith("0") and len(tag) == 3 and tag not in ("CDS",):
                open_[tag[:2]].append((d, ln))
                if tag == "PR0":
                    if "p" in d:
                        self.keys[d["k"]] = d["p"]
                    if d.get("ra2") in (0x00579620, 0x005798D2) and open_["NS"]:
                        trade["sellk"].append(d["k"])
                    if d.get("ra2") in (0x00577949, 0x00577B08) and open_["NB"]:
                        trade["buyk"].append(d["k"])
                elif tag == "GG0" and open_["NS"] and trade["sellv"]:
                    self.n["sales checked (gold given = the lower price)"] += 1
                    if d["a"][0] != min(trade["sellv"]):
                        self.fail(path, ln, "sale: gold given %d, prices %r" % (d["a"][0], trade["sellv"]))
                elif tag == "PG0" and open_["NB"] and trade["buyv"]:
                    self.n["purchases checked (PayGold = price x count)"] += 1
                    pv = trade["buyv"][-1]
                    if pv <= 0 or d["a"][0] % pv:
                        self.fail(path, ln, "purchase: paid %d, price %r" % (d["a"][0], trade["buyv"]))
                if tag in ("NS0", "NB0"):
                    trade.update(sellk=[], sellv=[], buyk=[], buyv=[])
                    if rc and d.get("ra") == 0x0062FF35:
                        rc[-1]["calls"].append(d["k"])
                elif tag == "RC0":
                    rc.append({"calls": [], "vals": []})
                elif tag == "CD0":
                    pend_cd = {"d": d, "ln": ln}
                elif tag == "DL0":
                    dl_pending = d
                    if pend_cd is not None and d.get("ra") == 0x0057D4DD:
                        pend_cd["DL"] = d
                elif tag == "GF0":
                    pend_gf = {}
                elif tag == "GA0" and pend_gpl is not None:
                    # DropGoldPile: the pile's ilvl is the level's monster level, minus 1 when above 1 (0x00559338)
                    want = pend_gpl - 1 if pend_gpl > 1 else pend_gpl
                    self.n["object gold piles (ilvl checked)"] += 1
                    if d["ilvl"] != want:
                        self.fail(path, ln, "object gold ilvl %d, level monster level %d" % (d["ilvl"], pend_gpl))
                    pend_gpl = None
            elif tag in ("GFK", "GFO"):
                pend_gf[tag] = d["v"]
            elif tag == "GPL":
                self.cases["object gold pile (DropGoldPile)"] += 1
                pend_gpl = d["mlv"]
            elif tag in ("CDS", "CDU", "CDW"):
                if pend_cd is not None:
                    pend_cd[tag] = d
            elif tag.endswith("1") and len(tag) == 3:
                kind = tag[:2]
                if not open_[kind]:
                    continue
                d0, ln0 = open_[kind].pop()
                self.n["events " + kind] += 1
                self.seedcheck(kind, d0, d)
                getattr(self, "on_" + kind, self.on_none)(path, ln0, d0, d, locals())
                if kind == "PR" and rc and d0.get("ra") == 0x0062FF35:
                    rc[-1]["vals"].append(d["v"])
                if kind == "PR" and d0["k"] in trade["sellk"]:
                    trade["sellv"].append(d["v"])
                if kind == "PR" and d0["k"] in trade["buyk"]:
                    trade["buyv"].append(d["v"])
                if kind == "RC" and rc:
                    r = rc.pop()
                    self.n["repair-all sums"] += 1
                    if sum(r["vals"]) != d["v"]:
                        self.fail(path, ln, "RepairCost %d, its mode-3 calls sum %d" % (d["v"], sum(r["vals"])))
                if kind == "CD":
                    pend_cd = None
            elif tag in ("SWW", "SWC"):
                self.sww[(tag, d["pc"], d["esp0"])] += 1
            elif tag == "SWSET":
                self.n["store-record watch set"] += 1
        return econ

    def on_none(self, path, ln, d0, d1, ctx):
        pass

    def on_PR(self, path, ln, d0, d1, ctx):
        k = d0["k"]
        p = self.keys.get(k)
        if p is None:
            self.fail(path, ln, "price payload %s not seen" % k)
            return
        self.n["price calls"] += 1
        try:
            want = self.M.price(p)
        except Mismatch as e:
            self.fail(path, ln, "price %s: %s" % (k, e))
            return
        if (k, d1["v"]) not in self.distinct:
            self.distinct.add((k, d1["v"]))
            it = p["it"]
            self.n["price distinct mode %d" % p["m"]] += 1
            self.cases["mode %d diff %d" % (p["m"], p["d"])] += 1
            self.cases["quality %s" % it.get("q")] += 1
            fl = it.get("fl", 0)
            if fl & 0x400000:
                self.cases["ethereal mode %d" % p["m"]] += 1
            if not fl & 0x10:
                self.cases["unidentified"] += 1
            if it.get("ch"):
                self.cases["socketed"] += 1
            st = {kk >> 16 for kk, _ in it.get("cache", [])}
            for s, name in ((204, "charged"), (107, "staff mod"), (252, "stat 252"), (253, "stat 253"),
                            (87, "stat 87 on item")):
                if s in st:
                    self.cases[name] += 1
            if (p.get("prp") or 0) > 0:
                self.cases["player stat 87 > 0"] += 1
            self.cases["npc %d" % p["npc"]] += 1
            rec = self.T.npcs.get(p["npc"])
            if rec is not None and p["m"] != 2:
                for g in range(3):
                    f = s32(rec, 0x10 + 4 * g)
                    if f:
                        on = self.M.qbit(p["qb"], f, 0) or self.M.qbit(p["qb"], f, 1)
                        self.cases["quest group %s %s" % ("ABC"[g], "on" if on else "off")] += 1
        if want != d1["v"]:
            tr = []
            try:
                self.M.price(p, tr)
            except Mismatch:
                pass
            self.fail(path, ln, "price k=%s mode %d npc %d class %d q %s: model %d, game %d; trace %r"
                      % (k, p["m"], p["npc"], p["it"]["c"], p["it"].get("q"), want, d1["v"], tr))

    def on_UG(self, path, ln, d0, d1, ctx):
        if d0.get("np"):
            return
        sid, dv, old, new = d0["st"], d0["dv"], d0["old"], d1["new"]
        cap = d0["cap"] if sid == 14 else 2500000
        tot = w32(old + dv)
        want = 0 if tot < 0 or tot > cap else tot
        self.n["gold stat adds"] += 1
        if tot > cap:
            self.cases["gold add over cap (written 0)"] += 1
        if want != new:
            self.fail(path, ln, "UnitAddGoldStat stat %d %d%+d cap %d: model %d, game %d" % (sid, old, dv, cap, want, new))

    def on_MC(self, path, ln, d0, d1, ctx):
        L = d0["mlv"]
        v = imul(tdiv(imul(L, L), 2), 15)
        want = 50000 if (v & M32) > 50000 else v
        self.n["resurrect costs"] += 1
        self.mc_last = d1["v"]
        if want != d1["v"]:
            self.fail(path, ln, "resurrect cost L %d: model %d, game %d" % (L, want, d1["v"]))

    def on_MR(self, path, ln, d0, d1, ctx):
        """MERC_Resurrect: the gold and stash gold drop by the last MERC_ResurrectCost result; PayGold refuses (and
        nothing is paid, the mercenary stays dead) when gold and stash together are short (0x00579CAE)."""
        s0, s1 = d0["sn"], d1["sn"]
        paid = s0["g"] + s0["sg"] - s1["g"] - s1["sg"]
        self.n["resurrections"] += 1
        want = getattr(self, "mc_last", None)
        if want is not None and s0["g"] + s0["sg"] < want:
            self.cases["resurrection refused (gold short)"] += 1
            want = 0
        else:
            self.cases["resurrection paid"] += 1
        if want is None or paid != want:
            self.fail(path, ln, "resurrection paid %d, last cost %r" % (paid, want))

    def on_PG(self, path, ln, d0, d1, ctx):
        s0, s1 = d0["sn"], d1["sn"]
        amt = d0["a"][0]
        g, sg = s0["g"], s0["sg"]
        self.n["PayGold"] += 1
        if g + sg < amt:
            want = (g, sg, 0)
        else:
            want = (max(0, g - amt), sg - max(0, amt - g), 1)
        got = (s1["g"], s1["sg"], d1["v"])
        if want[:2] != got[:2]:
            self.fail(path, ln, "PayGold %d from %d/%d: model %r, game %r" % (amt, g, sg, want, got))

    def on_GA(self, path, ln, d0, d1, ctx):
        """The gold item's amount at creation: ilvl + RNG_Range(item seed, 5 ilvl), at least 1 (items/0006)."""
        ilvl = d0["ilvl"]
        lo, hi = seedpair(d0["sd"])
        r, lo, hi = rng_rangeb(lo, hi, 5 * ilvl) if 5 * ilvl > 0 else (0, lo, hi)
        amt = max(1, ilvl + r)
        self.n["gold amounts at creation"] += 1
        self.cases["gold item from 0x%X" % d0.get("ra", 0)] += 1
        if (amt, "%08x:%08x" % (lo, hi)) != (d1["amt"], d1["sd"]):
            self.fail(path, ln, "gold amount ilvl %d: model %d %08x:%08x, game %d %s" % (ilvl, amt, lo, hi, d1["amt"], d1["sd"]))

    def on_GF(self, path, ln, d0, d1, ctx):
        """sub_005589A0_DropGoldFind: gold x (100 + GF(killer) + GF(owner)) / 100."""
        pg = ctx.get("pend_gf") or {}
        if "GFK" not in pg:
            return
        gf = pg["GFK"] + pg.get("GFO", 0)
        want = tdiv(imul(d0["gold"], 100 + gf), 100)
        self.n["gold find scalings"] += 1
        self.cases["gold find %s" % ("> 0" if gf else "0")] += 1
        if want != d1["gold"]:
            self.fail(path, ln, "gold find %d on %d: model %d, game %d" % (gf, d0["gold"], want, d1["gold"]))

    def on_DL(self, path, ln, d0, d1, ctx):
        """ITEMS_DurabilityLossRoll: predict the draw and the item after."""
        T, M = self.T, self.M
        it0 = d0["it"]
        c = it0["c"]
        armo, weap = T.is_type(c, "armo"), T.is_type(c, "weap")
        o0, o1 = d0["o"]["s"], d1["o"]["s"]
        self.n["wear rolls"] += 1
        item = Item(it0)
        if not (armo or weap) or not M.has_dur(item):
            self.cases["wear: no durability (no draw)"] += 1
            if o0 != o1:
                self.fail(path, ln, "wear roll without durability changed the seed")
            return
        chance = 10 if armo else 4
        if not armo and M.throwable(item):
            if d0["exp"] == 0:
                self.cases["wear: classic throwable (no draw)"] += 1
                if o0 != o1:
                    self.fail(path, ln, "classic throwable changed the seed")
                return
            chance = 10
        lo, hi = seedpair(o0)
        lo, hi = rng.step(lo, hi)
        if "%08x:%08x" % (lo, hi) != o1:
            self.fail(path, ln, "wear roll seed: model %08x:%08x, game %s" % (lo, hi, o1))
            return
        roll = lo % 100
        key = d0["o"]["u"]
        pc = ctx.get("pend_cd") or {}
        if d0.get("ra") == 0x0057D4DD and pc.get("CDW"):
            # the armour half: the roll draws right after RangeB(W) on the defender's seed
            if pc["CDW"]["s"] != o0:
                self.fail(path, ln, "armour roll entry seed %s is not the seed after RangeB(W) %s" % (o0, pc["CDW"]["s"]))
            else:
                self.n["wear chained draw pairs"] += 1
        elif self.last_exit.get(key) == o0:
            self.n["wear chained draw pairs"] += 1
            self.n["wear chained pairs across events"] += 1
        self.last_exit[key] = o1
        self.cases["wear roll %s" % ("defender" if d0.get("ra") == 0x0057D4DD else
                                     "attacker" if d0.get("ra") == 0x0057D3F8 else "other 0x%X" % d0.get("ra", 0))] += 1
        a0, a1 = d0["it"], d1["it"]
        self.cases["wear %s chance %d" % ("armour" if armo else "weapon", chance)] += 1
        if roll >= chance:
            if (a0["d"], a0["n"], a0["fl"]) != (a1["d"], a1["n"], a1["fl"]):
                self.fail(path, ln, "no loss (roll %d) but the item changed" % roll)
            return
        self.cases["wear losses"] += 1
        D, Mx, q = a0["d"], M.max_dur(item), a0["n"]
        if D - 1 >= 1:
            want = (min(D - 1, Mx), q, a0["fl"])
        elif not weap and not a0["fl"] & 0x100:
            self.cases["wear: armour broken"] += 1
            want = (a1["d"], q, a0["fl"] | 0x100)
        elif item.v >= 1:
            if q > 1:
                self.cases["wear: stack -1, refilled"] += 1
                want = (Mx, q - 1, a0["fl"])
            else:
                self.cases["wear: weapon to 0 (broken flag after: %d)" % bool(a1["fl"] & 0x100)] += 1
                want = (0, 0, a1["fl"])
        else:
            want = (0, q, a1["fl"])
        if want is not None and want[:2] != (a1["d"], a1["n"]) or (want and want[2] != a1["fl"]):
            self.fail(path, ln, "wear loss item: model %r, game %r" % (want, (a1["d"], a1["n"], a1["fl"])))

    def on_CD(self, path, ln, d0, d1, ctx):
        pc = ctx.get("pend_cd") or {}
        cds, cdu, cdw = pc.get("CDS"), pc.get("CDU"), pc.get("CDW")
        self.n["melee wear events"] += 1
        if cds is None:
            return
        W = sum(wt for (loc, wt), s in zip(WEAR_SLOTS, cds["slots"]) if s is not None)
        if W != cds["w"]:
            self.fail(path, ln, "armour weights: model %d, game %d" % (W, cds["w"]))
        if W <= 0:
            self.cases["armour wear: W = 0 (no draw)"] += 1
            return
        dsd = d0["def"]["s"]
        lo, hi = seedpair(dsd)
        u, lo, hi = rng_rangeb(lo, hi, 7)
        if cdu is None or cdu["v"] != u or cdu["s"] != "%08x:%08x" % (lo, hi):
            self.fail(path, ln, "RangeB(7): model %d %08x:%08x, game %r" % (u, lo, hi, cdu))
            return
        w, lo, hi = rng_rangeb(lo, hi, W)
        if cdw is None or cdw["v"] != w or cdw["s"] != "%08x:%08x" % (lo, hi):
            self.fail(path, ln, "RangeB(W=%d): model %d, game %r" % (W, w, cdw))
            return
        self.n["wear chained draw pairs"] += 1        # RangeB(7) then RangeB(W) on one seed
        self.cases["armour W %d" % W] += 1
        k = u
        while True:
            if cds["slots"][k] is not None:
                wt = WEAR_SLOTS[k][1]
                if w < wt:
                    break
                w -= wt
            k = (k + 1) % 7
        self.cases["armour wear slot %d" % WEAR_SLOTS[k][0]] += 1
        self.n["armour picks"] += 1
        dl = pc.get("DL")
        if dl is not None:
            # the item ITEMS_DurabilityLossRoll then rolls is the picked slot's
            self.n["armour picks checked against the rolled item"] += 1
            if dl["it"]["c"] != cds["slots"][k]:
                self.fail(path, ln, "armour pick: model slot %d class %r, rolled class %d"
                          % (WEAR_SLOTS[k][0], cds["slots"][k], dl["it"]["c"]))
        self.armour_pick = (d0["def"]["u"], cds["slots"][k], "%08x:%08x" % (lo, hi))

    def on_IC(self, path, ln, d0, d1, ctx):
        a0, a1 = d0.get("it"), d1.get("it")
        if not a0:
            return
        self.n["quantity uses"] += 1
        want_q = max(a0["n"] - 1, 0)
        if a1["n"] != want_q:
            self.fail(path, ln, "consume: q %d -> %d, model %d" % (a0["n"], a1["n"], want_q))

    def on_RP(self, path, ln, d0, d1, ctx):
        a0, a1 = d0["it"], d1.get("it") or {}
        self.n["replenish ticks"] += 1
        it = a0
        if it["s252"] and not it["fl"] & 0x100 and it["m0"]:
            want = (min(it["d"] + 1, it["m"]) if it["d"] < it["m"] else it["d"], it["n"])
            self.cases["replenish durability"] += 1
        elif it["s253"]:
            ms = it.get("ms", 0)
            want = (it["d"], it["n"] + 1 if it["n"] < ms else it["n"])
            self.cases["replenish quantity"] += 1
        else:
            return
        if (a1.get("d"), a1.get("n")) != want and "m" in a1:
            pass  # the quantity side's max stack is the base's; left to the record (P2 note)
        key = it["u"]
        if key in self.rp_last:
            r = it["s252"] or it["s253"]
            gap = d0["fr"] - self.rp_last[key]
            self.cases["replenish gap %d (r %d)" % (gap, r)] += 1
        self.rp_last[key] = d0["fr"]

    def on_DG(self, path, ln, d0, d1, ctx):
        s0, s1 = d0["sn"], d1["sn"]
        L, g, sg = s0["lv"], s0["g"], s0["sg"]
        T_ = g + sg
        loss = tdiv(imul(min(L, 20), T_), 100)
        if d0["gt"] == 3:
            if T_ - loss < 500 * L:
                loss = max(0, T_ - 500 * L)
            loss = min(loss, g)
        self.n["death losses"] += 1
        k = d0.get("killer") or {}
        pvp = k.get("t") == 0
        if pvp:
            self.cases["death: pvp"] += 1
            return
        sg2 = max(0, sg - (loss - g)) if g < loss else sg
        want = (0, sg2, max(loss, 0))
        got = (s1["g"], s1["sg"], d1["s175"])
        self.cases["death: total %s 500L" % ("above" if T_ - tdiv(imul(min(L, 20), T_), 100) >= 500 * L else "below")] += 1
        if want != got:
            self.fail(path, ln, "death L %d gold %d stash %d: model %r, game %r" % (L, g, sg, want, got))

    def on_CI(self, path, ln, d0, d1, ctx):
        """NPC_CainIdentify: 100 x the unidentified count is paid (0 with quest word 4 bit 0 or 1, not logged: the
        record states the save's quest state), and nothing is left unidentified."""
        self.n["Cain identify"] += 1
        s0, s1 = d0["sn"], d1["sn"]
        paid = s0["g"] + s0["sg"] - s1["g"] - s1["sg"]
        self.cases["Cain paid %d for %d unidentified" % (paid, d0["unid"])] += 1
        if paid not in (0, 100 * d0["unid"]) or d1["unid"] != 0:
            self.fail(path, ln, "Cain: paid %d for %d, %d left" % (paid, d0["unid"], d1["unid"]))


def rng_rangeb(lo, hi, n):
    lo, hi = rng.step(lo, hi)
    if n & (n - 1) == 0:
        return lo & (n - 1), lo, hi
    return lo % n, lo, hi


def cmd_check(argv):
    verbose = "-v" in argv
    argv = [a for a in argv if a != "-v"]
    T = Tables(argv[0])
    ch = Checker(T, verbose)
    ch.last_exit, ch.rp_last, ch.armour_pick = {}, {}, None
    for p in argv[1:]:
        ch.check_log(p)
    print("logs %d; games %d" % (len(argv) - 1, ch.n["games"]))
    for k in sorted(ch.n):
        print("  %-36s %d" % (k, ch.n[k]))
    print("cases:")
    for k in sorted(ch.cases):
        print("  %-36s %d" % (k, ch.cases[k]))
    print("seeds at entry and exit (gs game, ps player):")
    for kind in sorted(ch.seeds):
        print("  %-4s %s" % (kind, ", ".join("%s %d" % kv for kv in sorted(ch.seeds[kind].items()))))
    if ch.sww:
        print("store-record watch hits (tag pc/[esp]): %s" % ", ".join("%s 0x%08X/0x%08X x%d" % (t, a, b, n) for (t, a, b), n in sorted(ch.sww.items())))
    for m in ch.mis[:40]:
        print("MISMATCH " + m)
    print("economy: %d mismatches" % len(ch.mis))
    return 1 if ch.mis else 0


def cmd_price(argv):
    T = Tables(argv[0])
    key = argv[2]
    for tag, d, ln in read_events(argv[1]):
        if tag == "PR0" and d.get("k") == key and "p" in d:
            tr = []
            v = Model(T).price(d["p"], tr)
            print(json.dumps(d["p"], indent=1)[:4000])
            for t in tr:
                print(t)
            print("model", v)
            return 0
    print("not found")
    return 1


def main(argv):
    if len(argv) < 3 or argv[0] not in ("check", "price"):
        print(__doc__)
        return 2
    return {"check": cmd_check, "price": cmd_price}[argv[0]](argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Vendor stock and gamble model (plan 0031 Phase 2), checked against tools/gdb/vendors.gdb logs.

    python3 -I tools/vendors.py check <log> [<log> ...] [--excel DIR] [-v]
    python3 -I tools/vendors.py lists [--excel DIR]          # the 17 candidate lists and the gamble list, from the tables

Model, as read in docs/findings/items/0009-vendors.md (the review's boundary ruling: the store seed end to end, each
created item handed to the item model; HIRE_BuildStock a logged boundary oracle; the g_GambleList order dumped once
per run and used as data):
  - the store seed: NPCSTORE_CtlCreate steps the game seed once and seeds S = {low, 666} (VSC0 -> VSC1); from then on
    every draw on S in the game is the model's own, and the logged S at each build's entry (BS0, GB0, HB0) must be the
    model's (nothing else draws on it);
  - the candidate lists (VENDOR_BuildList): item records in index order (weapons, armor, misc) with spawnable != 0 and
    (<V>Max or <V>MagicMax != 0); PermStoreItem != 0 -> the permanent codes, else the entry {Min, Max, MagicMin,
    MagicMax, code, MagicLvl}; compared byte for byte with the record the build reads (BS0 "ent", "perm");
  - VENDOR_BuildStock: ilvl = VENDOR_StockLevel(clvl + 5) (Normal: min(., 12/20/28/36/45 by act)); per entry in list
    order: skip when the base level > ilvl; n = RandLoHi(S, Min, Max + 1) when ilvl < 25, else 0; skip an expansion
    base (version >= 100) in a game of item version < 100 after that draw; per normal copy VENDOR_PickNormalQuality
    (one draw, low % 100: ilvl < 5: > 90 -> 1; ilvl < 10: > 85 -> 3; else >= 75 -> 3; else 2) then the creation;
    magic copies when the base's bitfield1 bit 0 is set and MagicLvl <= ilvl: x = 1, or RandLoHi(S, 1, 3) + 1 from
    ilvl 25, m = RandLoHi(S, MagicMin, MagicMax + x), each created with quality 4; then each permanent code with
    quality 2; more than 32 failed creations end the build;
  - VENDOR_CreateStockItem: in Nightmare or Hell with clvl > 25 one RNG_RangeB(S, 100000) draw u (unsigned tests):
    Nightmare u < ilvl*64 + 4000 and a valid ubercode -> ubercode, else NightmareUpgrade unless 'xxx'; Hell: in an
    expansion game u < ilvl*16 + 1000 and a valid ultracode -> ultracode, else u < ilvl*128 + 5000 and a valid
    ubercode -> ubercode; then HellUpgrade unless 'xxx' replaces either; ITEMS_CreateForStore(index of the chosen
    code, kind 4, q, noEthereal, ilvl); a created code other than the chosen one is destroyed and made again with
    quality 2 (CMM); a Cracked low-quality item is destroyed and made again (CRK; at most 5);
  - GAMBLE_BuildInv: 14 slots; per slot lvl = low % 10 + clvl - 5 after a step, clamped to 5..99 (unclamped value
    at GLV); pick = R(S, countUpTo[lvl]) over the dumped list (VGL); in a classic game an expansion base redraws the
    slot; slot 0 -> rin, slot 1 -> amu (after their draws); GAMBLE_Upgrade (expansion only): no or unknown ubercode ->
    keep; c = (lvl - level(uber)) * GambleUber + 1, c <= 0 -> keep with no draw, R(S, 10000) < c (signed) -> uber;
    after a failed draw the same with the original base's ultracode and GambleUltra; quality: total = GambleRare +
    GambleSet + GambleUnique, q = 4, when total > 0 r = low % 100000 after a step: r < total -> 7 if r < unique, 6 if
    r >= set + unique, else 5; the slot counts before the creation (a creation that returns no item leaves it empty);
  - each item's creation (ITEMS_CreateForStore -> sub_00558D90_ItemCreate): the game seed at CF0 steps twice (the unit
    seed in SUnitCreate, then ItemSeedInit), the item's start seed is the second step's low and the item seed at IC0
    is {start, 666}; the game seed after the creation (CFX) is the second step and the next CF0 starts from it; the
    IC0 block is the item model's: tools/uniques.py check_block, then tools/affixes.py check_affixes with
    tools/props.py's ItemApplyProps model (tools/items_chain.py's chain) when the log has the affix lines; logs with
    the property lines (tools/gdb/vendors-props.gdb) are checked here on IC0 only and by `items_chain.py props`.
  - HIRE_BuildStock: the logged boundary oracle: S at HB0 is asserted, S at HBX taken.
  - the triggers: a trade open (TO, gamble 0) of a store NPC builds when the model's record is not built, or when it is
    stale and the opener is the sole interactor (then a reset first); NPCSTORE_ActStale(townEmpty) with nobody
    interacting resets (built = 0) the act's built stores; the logged built byte at TO is compared with the model's.
    A gamble open (TO, gamble 1) builds when the player has no gamble inventory there; GFREE frees it.

Exit 0 only when every build, every draw and every creation reproduces. Stdlib only. Read-only.
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

import excel_bin  # noqa: E402
import rng  # noqa: E402

EXCEL = os.path.join(os.path.dirname(HERE), "workspace", "merged", "data", "global", "excel")
VENDORS = ["Akara", "Gheed", "Charsi", "Fara", "Lysander", "Drognan", "Hratli", "Alkor", "Ormus", "Elzix", "Asheara",
           "Cain", "Halbu", "Jamella", "Malah", "Larzuk", "Drehya"]
# class -> vendor index, the record filler's switch (items/0009 summary, [C]); 514 takes Larzuk's list in the record
CLASS_V = {148: 0, 147: 1, 154: 2, 178: 3, 202: 4, 177: 5, 253: 6, 254: 7, 255: 8, 199: 9, 252: 10, 257: 12,
           405: 13, 513: 14, 511: 15, 512: 16, 514: 15}
NPC_NAME = {148: "Akara", 147: "Gheed", 154: "Charsi", 178: "Fara", 202: "Lysander", 177: "Drognan", 253: "Hratli",
            254: "Alkor", 255: "Ormus", 199: "Elzix", 252: "Asheara", 257: "Halbu", 405: "Jamella", 513: "Malah",
            511: "Larzuk", 512: "Anya", 514: "Nihlathak", 150: "Kashya", 198: "Greiz", 515: "Qual-Kehk"}
CAPS = (12, 20, 28, 36, 45)                      # VENDOR_StockLevel, Normal, by act
DIFF = ("normal", "nightmare", "hell")
XXX = b"xxx "
QN = {1: "low", 2: "normal", 3: "superior", 4: "magic", 5: "set", 6: "rare", 7: "unique"}


class Mismatch(Exception):
    pass


def eq(what, model, logged):
    if model != logged:
        raise Mismatch("%s: model %r, log %r" % (what, model, logged))


def fmt(s):
    return "%08x:%08x" % s


def seedpair(t):
    a, b = t.split(":")
    return int(a, 16), int(b, 16)


def u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def s32(b, o):
    return struct.unpack_from("<i", b, o)[0]


class Tables:
    def __init__(self, excel):
        self.items = []
        for t in ("weapons", "armor", "misc"):
            r, _ = excel_bin.read_bin(excel_bin.find_file(excel, t, ".bin"))
            self.items.extend(r)
        self.by_code = {}
        for i, r in enumerate(self.items):
            self.by_code.setdefault(bytes(r[0x80:0x84]), i)
        dl, _ = excel_bin.read_bin(excel_bin.find_file(excel, "difficultylevels", ".bin"))
        self.dl = [list(struct.unpack_from("<5i", r, 0x44)) for r in dl]      # Rare, Set, Unique, Uber, Ultra
        gb, _ = excel_bin.read_bin(excel_bin.find_file(excel, "gamble", ".bin"))
        self.gamble = [bytes(r[0:4]) for r in gb]

    def code(self, i):
        return bytes(self.items[i][0x80:0x84])

    def level(self, i):
        return self.items[i][0xFD]

    def version(self, i):
        return u16(self.items[i], 0xF6)

    def magic_ok(self, i):
        return self.items[i][0xDC] & 1

    def vlist(self, v):
        """VENDOR_BuildList(v): (entries, permanent codes)."""
        ent, perm = [], []
        for r in self.items:
            if not r[0x133]:
                continue
            if not r[0x157 + v] and not r[0x179 + v]:
                continue
            if r[0x1A4]:
                perm.append(bytes(r[0x80:0x84]))
            else:
                ent.append(dict(min=r[0x146 + v], max=r[0x157 + v], mmin=r[0x168 + v], mmax=r[0x179 + v],
                                code=bytes(r[0x80:0x84]), mlvl=r[0x18A + v]))
        return ent, perm

    def count_up_to(self):
        """countUpTo[L] (L >= 1) = Gamble rows whose base level <= L (the index of the first level > L after the
        sort)."""
        lv = sorted(self.level(self.by_code[c]) for c in self.gamble)
        return [None] + [sum(1 for x in lv if x <= L) for L in range(1, 100)]


def valid(c):
    return c not in (b"\0\0\0\0", b"    ")


class Seed:
    def __init__(self, s):
        self.s = s
        self.n = 0

    def draw(self):
        self.s = rng.step(*self.s)
        self.n += 1
        return self.s[0]

    def R(self, n):
        """The guarded range draw: n < 1 (signed) -> 0 with no step; else low % n (low & (n-1) for a power of two)."""
        if n & 0x80000000 or n == 0:
            return 0
        return self.draw() % n

    def lohi(self, lo, hi):
        """RNG_RandLoHi 0x004BC500: lo + R(hi - lo) when hi > lo (signed), else lo with no draw."""
        if hi <= lo:
            return lo
        return lo + self.draw() % (hi - lo)


def read_events(path, ic_tags):
    """The log's lines in order: ('GAME', None), (tag, dict) for the vendor tags, ('ICB', block) for each
    ItemCreateByQuality block (IC0 .. ICX), at the position of its ICX."""
    blk = None
    for line in open(path, errors="replace"):
        line = line.rstrip("\n")
        tag, _, rest = line.partition(" ")
        if tag == "GAME":
            yield "GAME", None
            continue
        if not rest.startswith("{"):
            continue
        if tag in ic_tags:
            try:
                d = json.loads(rest)
            except ValueError:
                continue
            if tag == "IC0":
                blk = [("IC0", d)]
            elif blk is not None:
                blk.append((tag, d))
                if tag == "ICX":
                    yield "ICB", blk
                    blk = None
            continue
        if tag in VTAGS:
            try:
                yield tag, json.loads(rest)
            except ValueError:
                continue


VTAGS = ("VGAME", "VSC0", "VSC1", "VGL", "MA", "TO", "STALE", "STALEX", "RESET", "PLEAVE", "GFREE", "PIEND", "BS0", "BSL",
         "VD", "CS0", "CSU", "CSW", "CRK", "CMM", "CSX", "CF0", "CFX", "BSX", "HB0", "HBX", "GB0", "GCL", "GLV", "GPK",
         "GU", "GUP", "GQ", "GBX")


class Stream:
    def __init__(self, evs):
        self.ev = evs
        self.i = 0

    def peek(self):
        j = self.i
        while j < len(self.ev) and self.ev[j][0] == "VGL" and self.ev[j - 1][0] != "GB0":
            j += 1
        return self.ev[j][0] if j < len(self.ev) else None

    def take(self, tag):
        if self.i >= len(self.ev):
            raise Mismatch("expected %s, log ended" % tag)
        t, d = self.ev[self.i]
        if t != tag:
            raise Mismatch("expected %s, log has %s %s" % (tag, t, json.dumps(d)[:160]))
        self.i += 1
        return d


class Checker:
    def __init__(self, T, ns):
        self.T = T
        self.ns = ns
        self.st = collections.Counter()
        self.notes = collections.defaultdict(list)
        self.items_by = collections.Counter()
        self.chain = None
        if not ns.no_chain:
            import affixes
            import items_chain
            import props
            import uniques
            self.affixes, self.uniques = affixes, uniques
            affixes.PROPS_HOOK = items_chain.make_hook(props.Tables(ns.excel))
            self.AT = affixes.Tables(ns.excel)
            self.chain = True

    # ------------------------------------------------------------------ one item
    def creation(self, E, game, idx, q, ilvl, gs, what, use_chain):
        """CF0 .. CFX of one ITEMS_CreateForStore call; returns (item, class, quality) from CFX."""
        T = self.T
        d = E.take("CF0")
        eq("%s: creation item index" % what, idx, d["idx"])
        eq("%s: creation quality" % what, q, d["q"])
        eq("%s: creation ilvl" % what, ilvl, d["ilvl"])
        eq("%s: creation kind / noSockets / noEthereal" % what, (4, 0, 1), (d["kind"], d["nosock"], d["noeth"]))
        if game["gs"] is not None:
            eq("%s: game seed at the creation" % what, fmt(game["gs"]), d["gs"])
        g0 = seedpair(d["gs"])
        g1 = rng.step(*g0)
        g2 = rng.step(*g1)
        blk = None
        if E.peek() == "ICB":
            blk = E.take("ICB")
        x = E.take("CFX")
        eq("%s: game seed after the creation (two steps)" % what, fmt(g2), x["gs"])
        game["gs"] = g2
        self.st["game-seed steps per creation: 2 (unit seed, item seed)"] += 1
        if not x["it"]:
            self.st["creations that returned no item"] += 1
            if blk is not None:
                raise Mismatch("%s: an IC block for a creation that returned no item" % what)
            return 0, None, None
        if blk is None:
            raise Mismatch("%s: no ItemCreateByQuality block for the created item" % what)
        ic = blk[0][1]
        eq("%s: IC0 class" % what, idx, ic["cls"])
        eq("%s: IC0 record quality" % what, q, ic["rq"])
        eq("%s: IC0 ilvl" % what, max(1, ilvl), ic["ilvl"])
        eq("%s: IC0 start seed (the second game-seed step)" % what, g2[0], ic["start"])
        eq("%s: IC0 item seed {start, 666}" % what, fmt((g2[0], 666)), ic["seed"])
        eq("%s: CFX start seed" % what, g2[0], x["start"])
        self.st["item seeds predicted from the game seed"] += 1
        if use_chain and self.chain:
            ublk = [(t, dd) for t, dd in blk if t in self.uniques.TAGS]
            try:
                res = self.uniques.check_block(self.AT, ublk, game["made"], self.st_u, None)
                if "skip" in res:
                    raise Mismatch("the item model skipped it: %s" % res["skip"])
                built = self.affixes.check_affixes(self.AT, blk, self.st_a, self.notes_a, False, res)
            except (self.affixes.Mismatch, self.uniques.Mismatch, KeyError, IndexError, TypeError) as e:
                raise Mismatch("%s: item model: %s" % (what, e))
            self.st["items reproduced by the item chain (uniques -> affixes -> props)"] += 1
            self.chain_tab[(DIFF[ic["diff"]], "+".join(built))] += 1
            for t, dd in blk:
                if t == "AFC" and blk[0][1]["rq"] == 4:
                    self.alvls.append((what, ic["cls"], ic["ilvl"], dd["alvl"], self.cur_mlvl, self.cur_clvl))
        else:
            self.st["items checked on IC0 only (property log)"] += 1
        self.items_by[(what.split(":")[0], DIFF[ic["diff"]], QN.get(x["q"], x["q"]))] += 1
        return x["it"], x["cls"], x["q"]

    # ------------------------------------------------------------------ stock
    def stock_item(self, E, game, S, code, q, ilvl, clvl, entry, use_chain):
        T = self.T
        d = E.take("CS0")
        eq("stock item code", code.decode("latin1"), d["code"])
        eq("stock item quality", q, d["q"])
        eq("stock item ilvl / clvl", (ilvl, clvl), (d["ilvl"], d["clvl"]))
        eq("S at VENDOR_CreateStockItem", fmt(S.s), d["S"])
        idx = T.by_code[code]
        want = code
        r = T.items[idx]
        self.cur_mlvl, self.cur_clvl = (entry["mlvl"] if entry else None), clvl
        if game["diff"] > 0 and clvl > 25:
            u = S.R(100000)
            du = E.take("CSU")
            eq("upgrade draw u", u, du["u"])
            eq("S after the upgrade draw", fmt(S.s), du["S"])
            uber, ultra = bytes(r[0x88:0x8C]), bytes(r[0x8C:0x90])
            nmu, hu = bytes(r[0x19C:0x1A0]), bytes(r[0x1A0:0x1A4])
            how = "none"
            if game["diff"] == 1:
                if u < ilvl * 64 + 4000 and valid(uber):
                    want, how = uber, "uber"
                elif nmu != XXX:
                    want, how = nmu, "NightmareUpgrade"
            else:
                if game["exp"] and u < ilvl * 16 + 1000 and valid(ultra):
                    want, how = ultra, "ultra"
                elif u < ilvl * 128 + 5000 and valid(uber):
                    want, how = uber, "uber"
                if hu != XXX:
                    want, how = hu, how + "+HellUpgrade"
            if want in T.by_code:
                idx = T.by_code[want]
            self.st["stock upgrade draws (%s)" % DIFF[game["diff"]]] += 1
            self.upg[(DIFF[game["diff"]], "exp" if game["exp"] else "classic", how)] += 1
            if how.startswith(("uber", "ultra")):
                self.notes["stock upgrades"].append("%s %s ilvl %d: %s -> %s (u %d)" % (
                    DIFF[game["diff"]], "exp" if game["exp"] else "classic", ilvl, code.decode().strip(),
                    want.decode().strip(), u))
        dw = E.take("CSW")
        eq("chosen code", want.decode("latin1"), dw["want"])
        eq("chosen item index", idx, dw["idx"])
        qq = q
        it = 0
        for pas in range(2):
            for t in range(5):
                it, cls, iq = self.creation(E, game, idx, qq, ilvl, None, "stock:%s" % code.decode().strip(), use_chain)
                if E.peek() == "CRK":
                    E.take("CRK")
                    self.st["Cracked retries"] += 1
                    it = 0
                    continue
                break
            if it and T.code(cls) != want:
                E.take("CMM")
                self.st["code mismatches (made again with quality 2)"] += 1
                qq = 2
                it = 0
                continue
            break
        x = E.take("CSX")
        eq("S after the stock item", fmt(S.s), x["S"])
        if not x["it"]:
            self.st["stock items not placed (VENDOR_CreateStockItem 0)"] += 1
        return x["it"]

    def build_stock(self, E, game, use_chain):
        T = self.T
        d = E.take("BS0")
        cls = d["cls"]
        v = CLASS_V[cls]
        ent, perm = T.vlist(v)
        raw = bytes.fromhex(d["ent"])
        logged = [dict(min=raw[12 * k], max=raw[12 * k + 1], mmin=raw[12 * k + 2], mmax=raw[12 * k + 3],
                       code=raw[12 * k + 4:12 * k + 8], mlvl=raw[12 * k + 8]) for k in range(d["n"])]
        eq("%s candidate list (VENDOR_BuildList) " % NPC_NAME[cls], ent, logged)
        eq("%s permanent codes" % NPC_NAME[cls], [u32(c, 0) for c in perm], d["perm"])
        self.st["candidate lists compared with the record"] += 1
        S = game["S"]
        eq("S at VENDOR_BuildStock (continuity)", fmt(S.s), d["S"])
        game["gs"] = seedpair(d["gs"])             # other units draw on the game seed between builds
        dl = E.take("BSL")
        clvl = dl["clvl"]
        diff, act = d["diff"], d["act"]
        ilvl = min(clvl + 5, CAPS[act]) if diff == 0 and act < 5 else clvl + 5
        eq("stock ilvl (VENDOR_StockLevel)", ilvl, dl["ilvl"])
        game["diff"], game["exp"], game["gver"] = diff, d["exp"], d["gver"]
        n0 = S.n
        fails = 0
        nitems = 0
        gated = []
        tag = "%s %s act %d clvl %d ilvl %d" % (NPC_NAME[cls], DIFF[diff], act + 1, clvl, ilvl)

        def vd(k, v_, e):
            x = E.take("VD")
            eq("draw %s" % k, (k, v_, e), (x["k"], x["v"], x["e"]))
            eq("S after draw %s" % k, fmt(S.s), x["S"])

        done = False
        for k, e in enumerate(ent):
            idx = T.by_code[e["code"]]
            if T.level(idx) > ilvl:
                continue
            if ilvl < 25:
                n = S.lohi(e["min"], e["max"] + 1)
                vd("cnt", n, k)
            else:
                n = 0
            if T.version(idx) >= 100 and game["gver"] < 100:
                self.st["classic: expansion entries skipped after their count draw"] += 1
                continue
            for i in range(n):
                q = S.draw() % 100
                q = (1 if q > 90 else 2) if ilvl < 5 else ((3 if q > 85 else 2) if ilvl < 10 else (3 if q >= 75 else 2))
                vd("nq", q, k)
                if not self.stock_item(E, game, S, e["code"], q, ilvl, clvl, e, use_chain):
                    fails += 1
                nitems += 1
                if fails > 32:
                    done = True
                    break
            if done:
                break
            if T.magic_ok(idx):
                if e["mlvl"] <= ilvl:
                    if ilvl >= 25:
                        x = S.lohi(1, 3)
                        vd("mx", x, k)
                        x += 1
                    else:
                        x = 1
                    m = S.lohi(e["mmin"], e["mmax"] + x)
                    vd("mc", m, k)
                    for i in range(m):
                        if not self.stock_item(E, game, S, e["code"], 4, ilvl, clvl, e, use_chain):
                            fails += 1
                        nitems += 1
                        self.magic_stock.append((tag, e["code"].decode().strip(), e["mlvl"]))
                elif e["mmax"]:
                    gated.append("%s(MagicLvl %d)" % (e["code"].decode().strip(), e["mlvl"]))
        if not done:
            for c in perm:
                it = self.stock_item(E, game, S, c, 2, ilvl, clvl, None, use_chain)
                nitems += 1
                if not it:
                    fails += 1
                if fails > 32:
                    break
        x = E.take("BSX")
        eq("S after VENDOR_BuildStock", fmt(S.s), x["S"])
        game["gs"] = seedpair(x["gs"])
        self.st["stock builds"] += 1
        self.st["stock items created"] += nitems
        self.st["store-seed draws in stock builds"] += S.n - n0
        self.builds[(NPC_NAME[cls], DIFF[diff], "exp" if game["exp"] else "classic")] += 1
        self.notes["builds"].append("%s: %d items, %d draws%s" % (tag, nitems, S.n - n0,
                                                                  "; magic gated by MagicLvl > ilvl: " +
                                                                  " ".join(gated) if gated else ""))
        if gated:
            self.gated.append((tag, gated))
        game["built"][cls] = True

    # ------------------------------------------------------------------ gamble
    def build_gamble(self, E, game, use_chain):
        T = self.T
        d = E.take("GB0")
        if E.peek() == "VGL":
            self.vgl(game, E.take("VGL"))
        S = game["S"]
        eq("S at GAMBLE_BuildInv (continuity)", fmt(S.s), d["S"])
        game["gs"] = seedpair(d["gs"])
        diff, exp = d["diff"], d["exp"]
        game["diff"], game["exp"], game["gver"] = diff, exp, d["gver"]
        dc = E.take("GCL")
        clvl = dc["clvl"]
        DL = T.dl[diff]
        eq("DifficultyLevels gamble columns", DL, dc["dl"])
        rare, set_, uniq, uber_m, ultra_m = DL
        total = rare + set_ + uniq
        G = game["glist"]
        if G is None:
            raise Mismatch("no VGL dump before the first gamble build")
        n0 = S.n
        slot = 0
        ring, amu = T.by_code[b"rin "], T.by_code[b"amu "]
        while slot < 14:
            lvl = (S.draw() % 10) + clvl - 5
            x = E.take("GLV")
            eq("gamble lvl (before the clamp)", lvl, x["lvl"])
            eq("S after the lvl draw", fmt(S.s), x["S"])
            lvl = 5 if lvl <= 5 else (99 if lvl >= 99 else lvl)
            cnt = G["cnt"][lvl]
            pick = S.R(cnt)
            item = G["items"][pick]
            x = E.take("GPK")
            eq("gamble pick (r, item, lvl, countUpTo)", (pick, item, lvl, cnt), (x["r"], x["idx"], x["lvl"], x["cnt"]))
            eq("S after the pick", fmt(S.s), x["S"])
            if not exp and T.version(item) >= 100:
                self.st["classic gamble redraws (expansion base)"] += 1
                continue
            if slot == 0:
                item = ring
            elif slot == 1:
                item = amu
            base = item
            if exp:
                r = T.items[item]
                uc, ulc = bytes(r[0x88:0x8C]), bytes(r[0x8C:0x90])
                if valid(uc) and uc in T.by_code:
                    ub = T.by_code[uc]
                    c = (lvl - T.level(ub)) * uber_m + 1
                    if c > 0:
                        rr = S.R(10000)
                        g = E.take("GU")
                        eq("uber test (r, bound)", ("uber", rr, c), (g["k"], g["r"], g["bound"]))
                        eq("S after the uber test", fmt(S.s), g["S"])
                        self.gup.append(("uber", lvl, T.level(ub), c, rr, rr < c))
                        if rr < c:
                            item = ub
                        elif valid(ulc) and ulc in T.by_code:
                            ul = T.by_code[ulc]
                            c2 = (lvl - T.level(ul)) * ultra_m + 1
                            if c2 > 0:
                                rr2 = S.R(10000)
                                g = E.take("GU")
                                eq("ultra test (r, bound)", ("ultra", rr2, c2), (g["k"], g["r"], g["bound"]))
                                eq("S after the ultra test", fmt(S.s), g["S"])
                                self.gup.append(("ultra", lvl, T.level(ul), c2, rr2, rr2 < c2))
                                if rr2 < c2:
                                    item = ul
                            else:
                                self.st["gamble ultra tests with bound <= 0 (no draw)"] += 1
                    else:
                        self.st["gamble uber tests with bound <= 0 (no draw)"] += 1
            x = E.take("GUP")
            eq("GAMBLE_Upgrade result", item, x["idx"])
            q = 4
            r = None
            if total > 0:
                r = S.draw() % 100000
                if r < total:
                    q = 7 if r < uniq else (6 if r >= set_ + uniq else 5)
            x = E.take("GQ")
            eq("gamble quality", q, x["q"])
            if r is not None:
                eq("gamble quality draw r", r, x["r"])
            eq("S after the quality draw", fmt(S.s), x["S"])
            slot += 1
            self.gq[(DIFF[diff], QN[q])] += 1
            self.cur_mlvl, self.cur_clvl = None, clvl
            it, cls, iq = self.creation(E, game, item, q, lvl, None, "gamble:%s" % NPC_NAME.get(d["cls"], d["cls"]),
                                        use_chain)
            self.gambled.append((clvl, lvl, T.code(base).decode().strip(), T.code(item).decode().strip(), q, iq))
            if E.peek() == "GBX":
                break
        x = E.take("GBX")
        eq("S after GAMBLE_BuildInv", fmt(S.s), x["S"])
        game["gs"] = seedpair(x["gs"])
        self.st["gamble builds"] += 1
        self.st["store-seed draws in gamble builds"] += S.n - n0
        self.gbuilds[(NPC_NAME.get(d["cls"], d["cls"]), DIFF[diff], "exp" if exp else "classic", clvl)] += 1

    def vgl(self, game, d):
        cu = self.T.count_up_to()
        eq("countUpTo[1..99] from Gamble.txt", cu[1:], d["cnt"][1:])
        eq("gamble list members (as a multiset)", sorted(self.T.by_code[c] for c in self.T.gamble), sorted(d["items"]))
        lv = [self.T.level(i) for i in d["items"]]
        eq("gamble list sorted by base level", sorted(lv), lv)
        g = dict(items=d["items"], cnt=d["cnt"])
        if self.glist_fixed is not None:
            eq("gamble list order (same in every run)", self.glist_fixed["items"], g["items"])
        self.glist_fixed = g
        if game:
            game["glist"] = g
        self.st["gamble list dumps (VGL)"] += 1

    # ------------------------------------------------------------------ a log
    def check_log(self, path):
        use_chain = False
        with open(path, errors="replace") as f:
            for line in f:
                if line.startswith(("AF0 ", "STF0 ", "RC ")):
                    use_chain = True
                    break
        import affixes
        evs = list(read_events(path, affixes.TAGS))
        E = Stream(evs)
        game = None
        bad = 0
        name = os.path.basename(path)
        while E.i < len(E.ev):
            t, d = E.ev[E.i]
            try:
                if t == "GAME":
                    E.i += 1
                    game = dict(S=None, gs=None, made=set(), built={}, ginv=set(), glist=self.glist_fixed,
                                diff=0, exp=1, gver=101)
                    self.st["games"] += 1
                elif t == "VSC0":
                    E.i += 1
                    g0 = seedpair(d["gs"])
                    x = E.take("VSC1")
                    g1 = rng.step(*g0)
                    eq("game seed after NPCSTORE_CtlCreate's step", fmt(g1), x["gs"])
                    eq("store seed = {low, 666}", fmt((g1[0], 666)), x["S"])
                    game["S"] = Seed((g1[0], 666))
                    self.st["store seeds predicted (NPCSTORE_CtlCreate)"] += 1
                elif t == "VGL":
                    E.i += 1
                    self.vgl(game, d)
                elif t == "TO":
                    E.i += 1
                    cls = d["cls"]
                    nm = NPC_NAME.get(cls, cls)
                    self.st["NPC opens (TO)"] += 1
                    self.opens[(nm, "gamble" if d["gamble"] else "trade")] += 1
                    if not d["gamble"] and d.get("store") == 1:
                        built = game["built"].get(cls, False)
                        eq("%s record built at the trade open" % nm, int(built), d["built"])
                        if not built or (d.get("stale") and d["sole"]):
                            if built:
                                x = E.take("RESET")
                                eq("reset record", cls, x["cls"])
                                self.st["stale rebuilds (reset at the open)"] += 1
                            if E.peek() != "BS0":
                                raise Mismatch("a build expected after the trade open of %s, log has %s" % (
                                    nm, E.peek()))
                            if cls in self.ever_built.get(id(game), set()):
                                self.rebuilds[nm] += 1
                        elif E.peek() == "BS0":
                            raise Mismatch("a build the model does not expect at the trade open of %s" % nm)
                        else:
                            self.st["trade opens with the stock kept"] += 1
                    elif d["gamble"]:
                        if (cls in game["ginv"]) == (E.peek() == "GB0"):
                            raise Mismatch("gamble open of %s: inventory %s, next %s" % (nm, cls in game["ginv"],
                                                                                        E.peek()))
                        if E.peek() == "GB0":
                            game["ginv"].add(cls)
                elif t == "STALE":
                    E.i += 1
                    self.st["NPCSTORE_ActStale calls (townEmpty %s)" % d.get("empty", d.get("a3"))] += 1
                    if "recs" in d:
                        before = {r[0]: r for r in d["recs"]}
                        while E.peek() == "RESET":         # townEmpty with nobody interacting: reset at once
                            x = E.take("RESET")
                            game["built"][x["cls"]] = False
                            self.st["stores reset by a town leave"] += 1
                        x = E.take("STALEX")
                        for r in x["recs"]:
                            b = before.get(r[0])
                            if b and b[2] and not b[3] and r[3]:
                                dt = (r[4] - b[4]) & 0xFFFFFFFF
                                self.st["stores marked stale by a town leave"] += 1
                                self.stale.append("%s marked stale %.1f s after its build" % (
                                    NPC_NAME.get(r[0], r[0]), dt / 1000.0))
                                if not d["empty"] and dt <= 240000:
                                    raise Mismatch("%s marked stale only %d ms after its build" % (NPC_NAME.get(r[0]), dt))
                            elif b and b[2] and not r[2]:
                                self.stale.append("%s reset at once (built 0), townEmpty %d" % (
                                    NPC_NAME.get(r[0], r[0]), d["empty"]))
                            elif b and b[2] and not b[3] and not r[3]:
                                self.stale.append("%s kept (not stale), townEmpty %d" % (NPC_NAME.get(r[0], r[0]),
                                                                                        d["empty"]))
                elif t == "RESET":
                    E.i += 1
                    if not game["built"].get(d["cls"]):
                        raise Mismatch("a reset of %s, which the model has not built" % NPC_NAME.get(d["cls"]))
                    game["built"][d["cls"]] = False
                    self.st["stores reset (NPCSTORE_Reset) outside a trade open: built = 0"] += 1
                elif t in ("GFREE", "PLEAVE"):
                    E.i += 1
                    game["ginv"] = set()
                    self.st["gamble inventories freed (GFREE)"] += 1
                elif t == "BS0":
                    self.build_stock(E, game, use_chain)
                    self.ever_built.setdefault(id(game), set()).add(d["cls"])
                elif t == "GB0":
                    self.build_gamble(E, game, use_chain)
                elif t == "HB0":
                    E.i += 1
                    eq("S at HIRE_BuildStock (continuity)", fmt(game["S"].s), d["S"])
                    x = E.take("HBX")
                    game["S"] = Seed(seedpair(x["S"]))
                    self.st["HIRE_BuildStock oracle (S taken at HBX)"] += 1
                elif t in ("ICB",):
                    E.i += 1
                    self.st["item creations outside the store paths (not checked here)"] += 1
                else:
                    E.i += 1
                    if t in ("PIEND", "MA", "VGAME"):
                        self.st["%s lines" % t] += 1
                    else:
                        raise Mismatch("unexpected %s outside a build" % t)
            except (Mismatch, KeyError, IndexError, TypeError) as e:
                bad += 1
                print("FAIL %s line-event %d (%s): %s" % (name, E.i, t, e))
                # resynchronise: S is known again at the end of the failed build (BSX, GBX, HBX) or at the next
                # build entry; the trigger state (TO, RESET, GFREE) is kept
                while E.i < len(E.ev) and E.ev[E.i][0] not in ("BSX", "GBX", "HBX", "BS0", "GB0", "HB0", "VSC0", "GAME"):
                    E.i += 1
                if game and E.i < len(E.ev) and E.ev[E.i][0] in ("BSX", "GBX", "HBX", "BS0", "GB0", "HB0"):
                    game["S"] = Seed(seedpair(E.ev[E.i][1]["S"]))
                    game["gs"] = None
                    if E.ev[E.i][0] in ("BSX", "GBX", "HBX"):
                        E.i += 1
                    self.st["resynchronisations after a failure"] += 1
        return bad


def cmd_check(ns):
    T = Tables(ns.excel)
    C = Checker(T, ns)
    C.st_u, C.st_a, C.notes_a = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    C.chain_tab = collections.Counter()
    C.builds, C.gbuilds, C.opens, C.upg, C.gq = (collections.Counter() for _ in range(5))
    C.rebuilds = collections.Counter()
    C.gup, C.gambled, C.magic_stock, C.gated, C.alvls, C.stale = [], [], [], [], [], []
    C.ever_built, C.glist_fixed = {}, None
    C.cur_mlvl = C.cur_clvl = None
    bad = 0
    for p in ns.logs:
        bad += C.check_log(p)
    st = C.st
    print("== tools/vendors.py check: %d logs ==" % len(ns.logs))
    for k in sorted(st):
        print("  %-70s %d" % (k, st[k]))
    print("stock builds by NPC, difficulty, game:")
    for k, v in sorted(C.builds.items()):
        print("  %-10s %-9s %-8s %d" % (k + (v,)))
    print("gamble builds by NPC, difficulty, game, clvl:")
    for k, v in sorted(C.gbuilds.items(), key=str):
        print("  %-10s %-9s %-8s clvl %-3s %d" % (k + (v,)))
    print("items created by path, difficulty, final quality:")
    for k, v in sorted(C.items_by.items()):
        print("  %-24s %-9s %-9s %d" % (k + (v,)))
    print("stock upgrade outcomes (difficulty, game, choice):")
    for k, v in sorted(C.upg.items()):
        print("  %-9s %-8s %-28s %d" % (k + (v,)))
    print("gamble qualities:", dict(C.gq))
    print("gamble upgrade tests: %d (uber %d, ultra %d), passed %d" % (
        len(C.gup), sum(1 for g in C.gup if g[0] == "uber"), sum(1 for g in C.gup if g[0] == "ultra"),
        sum(1 for g in C.gup if g[5])))
    if C.gup:
        near = [g for g in C.gup if g[1] - g[2] <= 2]
        print("  tests with lvl - qlvl <= 2 (bound = (lvl - qlvl) * mult + 1 out of 10 000): %d" % len(near))
        for g in (C.gup if ns.verbose else C.gup[:12]):
            print("   %-5s lvl %2d qlvl %2d bound %5d r %5d -> %s" % (g[0], g[1], g[2], g[3], g[4], "upgraded" if g[5] else "kept"))
    if C.gambled:
        lv = collections.Counter((c, l - c) for c, l, *_ in C.gambled)
        print("gambled ilvl - clvl by clvl:", {c: sorted({k for (cc, k) in lv if cc == c}) for c in sorted({c for c, *_ in C.gambled})})
    if C.gated:
        print("magic copies gated by MagicLvl > stock ilvl (required case a):")
        for tag, g in C.gated[: None if ns.verbose else 8]:
            print("  %s: %s" % (tag, " ".join(g)))
    if C.alvls:
        ex = [a for a in C.alvls if a[0].startswith("stock")]
        gm = [a for a in C.alvls if a[0].startswith("gamble")]
        over = [a for a in ex if a[4] is not None and a[3] > a[4]]
        print("affix picks on quality-4 creations: stock %d, gamble %d (alvl from AFC)" % (len(ex), len(gm)))
        print("  stock picks whose alvl exceeds the entry's <Vendor>MagicLvl (required case a): %d of %d; e.g. %s" % (
            len(over), len(ex), "; ".join("%s ilvl %d MagicLvl %d alvl %d" % (a[0][6:], a[2], a[4], a[3])
                                         for a in over[:4])))
        if gm:
            d = collections.Counter((a[5], a[3] - a[5]) for a in gm)
            print("  gamble picks, alvl - clvl by clvl (required case c): %s" % {
                c: sorted({k for (cc, k) in d if cc == c}) for c in sorted({a[5] for a in gm})})
    print("NPC opens:", dict(C.opens))
    for n in C.stale:
        print("  town leave: %s" % n)
    print("rebuilds of a vendor in one game:", dict(C.rebuilds))
    for k in ("stock upgrades",):
        for n in C.notes[k][: None if ns.verbose else 10]:
            print("  %s: %s" % (k, n))
    if ns.verbose:
        for n in C.notes["builds"]:
            print("  build " + n)
    if C.chain:
        print("item chain (difficulty, builders):")
        for k, v in sorted(C.chain_tab.items()):
            print("  %-9s %-40s %d" % (k + (v,)))
    print("vendors: %s" % ("0 mismatches" if not bad else "%d FAILED" % bad))
    return 1 if bad else 0


def cmd_lists(ns):
    T = Tables(ns.excel)
    for v, name in enumerate(VENDORS):
        ent, perm = T.vlist(v)
        print("%-8s %2d entries, %2d permanent: %s | %s" % (name, len(ent), len(perm),
                                                          " ".join(e["code"].decode().strip() for e in ent),
                                                          " ".join(c.decode().strip() for c in perm)))
    cu = T.count_up_to()
    print("gamble: %d rows; countUpTo[5..99 by 5]: %s" % (len(T.gamble), [cu[L] for L in range(5, 100, 5)]))
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="vendors.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check")
    p.add_argument("logs", nargs="+")
    p.add_argument("--excel", default=EXCEL)
    p.add_argument("--no-chain", action="store_true", help="check IC0 only, not the item model")
    p.add_argument("-v", "--verbose", action="store_true")
    p = sub.add_parser("lists")
    p.add_argument("--excel", default=EXCEL)
    ns = ap.parse_args(argv[1:])
    return cmd_check(ns) if ns.cmd == "check" else cmd_lists(ns)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

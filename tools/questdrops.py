#!/usr/bin/env python3
"""Quest drops, quest rewards and special drops (plan 0032 Phase 2), checked against tools/gdb/quests.gdb logs.

    python3 -I tools/questdrops.py check <log> [<log> ...] [-v]

The model is docs/findings/items/0010-quest-drops.md. Per log (one game process; a new QI0/QI1 pair starts a game):

- quest seed (section 1): at QUESTS_InitGame the game seed takes one step and the quest seed is RNG_SeedInit(low of
  that step): QI1 qs = (low, 666), QI1 gs = step(QI0 gs).
- quest-bit writes (QS / QC): each write's "old" word must equal the word as the earlier writes of the same record
  left it (the first write of a word is taken as read); the summary lists the writes by return address.
- B6 (section 2): every B60 .. B6X group through tools/tc.py's b6_model (tc.py replay also ties it to the DROP).
- scripted drops on the quest seed (section 4): a QGS line is a QUESTS_GetSeed call with the seed before its caller's
  draw. The first QGS of a script call is a boundary oracle (ADR-0004: other quest code draws the quest seed too); it
  is counted as "predicted" when it equals the quest seed the model already holds (QI1, or the last draw). Then:
    Andariel (QDI ret 0x005966B2 / 0x0059672B after QGS 0x0059664D / 0x005966C0): one LCG step, code =
      chipped / standard [low mod 7], quality 2;
    Hellforge wave (QDI ret 0x005B6865 after QGS 0x005B6772 / 0x005B67BE / 0x005B6807): one step, code =
      perfect (waves 4) / flawless (3, 2) / standard (1) [low mod 7], quality 2; the waves count down from 4, n
      creations per wave;
    Hellforge rune (QDI ret 0x005B68F2 after QGS 0x005B68C7): r = RNG_Range(qs, 11), code = runes[difficulty][r],
      only in an expansion game, after the last wave;
    Cow King (QDI ret inside sub_00593E70_A1Q4_CowKingDeath, code 'vps ', quality 0): eight, no draw;
    Hephasto's hammer (QDI ret 0x005B6603, sub_005B65D0_A4Q3_HammerDrop): 'hfh ', quality 7, no draw.
  Every QDI must keep the quest seed through the creation (QDX qs = QDI qs). Other QDI return addresses are listed.
- imbue (section 6): IMB0 item quality 1..3; IMB1 index = the item's class, quality 6, ilvl = clvl (+4 when > 5),
  flags80 has 0x20 and 0x04 (ethereal item) or 0x02; IMBX the new item with quality 6 and that ilvl. The rare build
  itself is tools/items_chain.py's (affixes), run on the same logs.
- socket (section 6): LZ0 quality q and max; q = 4: one RNG_RangeB(item seed, min(max, 2)) draw (LZS bound and seed,
  LZR draw and seed after), n = 1 + r; 5 <= q <= 9 with max >= 1: n = 1; else n = max; LZX n; LZY stat 194 = n.
- personalize: PZ flags have 0x1000000 and a name.

Exit 0 only if every check holds. Stdlib only. Read-only.
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rng  # noqa: E402
import tc  # noqa: E402

TAGS = {"QI0", "QI1", "QS", "QC", "QGS", "QDI", "QDX", "IMB0", "IMBL", "IMB1", "IMBX", "LZ0", "LZS", "LZR", "LZX",
        "LZY", "PZ", "IC0"} | set(tc.B6_TAGS)
CHIPPED = "gcv gcr gcb gcy gcg gcw skc".split()          # data:g_AndarielChippedGems@0x007361DC
STANDARD = "gsv gsr gsb gsy gsg gsw sku".split()         # data:g_AndarielStdGems@0x00736444, g_ForgeGemsStandard
PERFECT = "gpv gpr gpb gpy gpg gpw skz".split()          # data:g_ForgeGemsPerfect@0x0073E56C
FLAWLESS = "gzv glr glb gly glg glw skl".split()         # data:g_ForgeGemsFlawless@0x0073E588
RUNES = [["r%02d" % i for i in range(a, a + 11)] for a in (1, 12, 15)]   # g_ForgeRunes Normal / Nightmare / Hell
ANDARIEL = {0x005966B2: (0x0059664D, CHIPPED), 0x0059672B: (0x005966C0, STANDARD)}
FORGE_WAVE = {4: (0x005B6772, PERFECT), 3: (0x005B67BE, FLAWLESS), 2: (0x005B67BE, FLAWLESS), 1: (0x005B6807, STANDARD)}


class Mismatch(Exception):
    pass


def sp(s):
    lo, hi = s.split(":")
    return int(lo, 16), int(hi, 16)


def fmt(lo, hi):
    return "%08x:%08x" % (lo, hi)


def code4(c):
    return (c or "").strip()


class Checker:
    def __init__(self, verbose):
        self.v = verbose
        self.fail = 0
        self.n = collections.Counter()
        self.writes = collections.Counter()
        self.other = collections.Counter()
        self.items = collections.Counter()
        self.lines = []

    def bad(self, where, msg):
        self.fail += 1
        print("MISMATCH %s: %s" % (where, msg))

    def check(self, path):
        ev = []
        for k, line in enumerate(open(path, errors="replace")):
            tag, _, rest = line.strip().partition(" ")
            if tag not in TAGS or not rest.startswith("{"):
                continue
            try:
                ev.append((k + 1, tag, json.loads(rest)))
            except ValueError:
                continue
        name = os.path.basename(path)
        self.n["logs"] += 1
        words = {}              # (rec, word) -> value
        q = None                # the model's quest seed (lo, hi)
        pend = None             # the last QGS: (line, ret, seed before)
        call_q = None           # quest seed after the pending draw
        b6 = None
        imb = {}
        lz = {}
        forge_wave = None
        last_qdi = {}
        for i, (ln, tag, d) in enumerate(ev):
            where = "%s:%d %s" % (name, ln, tag)
            try:
                if tag == "QI0":
                    gs0 = sp(d["gs"])
                elif tag == "QI1":
                    lo, hi = rng.step(*gs0)
                    if sp(d["gs"]) != (lo, hi):
                        raise Mismatch("game seed after the step %s, model %s" % (d["gs"], fmt(lo, hi)))
                    if sp(d["qs"]) != (lo, rng.INIT_HIGH):
                        raise Mismatch("quest seed %s, model %s" % (d["qs"], fmt(lo, rng.INIT_HIGH)))
                    q = (lo, rng.INIT_HIGH)
                    words = {}
                    self.n["quest seed starts"] += 1
                elif tag in ("QS", "QC"):
                    key = (d["rec"], d["w"])
                    old = d["old"]
                    if key in words and old is not None and words[key] != old:
                        raise Mismatch("word %d before the write 0x%04x, model 0x%04x" % (d["w"], old, words[key]))
                    if old is not None:
                        m = 1 << d["b"]
                        words[key] = (old | m) if tag == "QS" else (old & ~m & 0xFFFF)
                    self.writes[(tag, d["ret"], d["w"], d["b"])] += 1
                    self.n["quest-bit writes"] += 1
                elif tag in tc.B6_TAGS:
                    if tag == "B60":
                        b6 = []
                    if b6 is None:
                        raise Mismatch("%s outside a B60 group" % tag)
                    b6.append((tag, d))
                    if tag == "B6X":
                        want, taken, why = tc.b6_model(b6)
                        k = b6[0][1]
                        self.n["B6 %s class %d diff %d" % ("taken" if taken else "not taken", k["mon"][1], k["diff"])] += 1
                        if self.v:
                            print("%s: B6 class %d killer %s: %s -> tc %d" % (where, k["mon"][1], k["killer"], why, want))
                        b6 = None
                elif tag == "QGS":
                    s = sp(d["qs"])
                    if pend is not None:
                        self.n["QGS without a modelled draw"] += 1
                    self.n["quest-seed fetches"] += 1
                    if q is not None and s == q:
                        self.n["quest seed on entry predicted"] += 1
                    else:
                        self.n["quest seed on entry taken (oracle)"] += 1
                    pend = (ln, int(d["ret"], 16), s)
                    q = s
                elif tag == "QDI":
                    ret = int(d["ret"], 16)
                    c = code4(d["code"])
                    qs_now = sp(d["qs"]) if d["qs"] else None
                    if ret in ANDARIEL or ret == 0x005B6865 or ret == 0x005B68F2:
                        if pend is None:
                            raise Mismatch("a scripted draw without its QGS")
                        _, gret, s = pend
                        if ret in ANDARIEL:
                            want_ret, table = ANDARIEL[ret]
                            lo, hi = rng.step(*s)
                            r = lo % 7
                            label = "andariel"
                        elif ret == 0x005B6865:
                            fw = d["forge"]
                            if fw["waves"] not in FORGE_WAVE:
                                raise Mismatch("forge waves %s" % fw["waves"])
                            want_ret, table = FORGE_WAVE[fw["waves"]]
                            if forge_wave is not None and fw["waves"] > forge_wave:
                                raise Mismatch("forge waves went up %d -> %d" % (forge_wave, fw["waves"]))
                            forge_wave = fw["waves"]
                            lo, hi = rng.step(*s)
                            r = lo % 7
                            label = "forge wave %d" % fw["waves"]
                        else:
                            want_ret, table = 0x005B68C7, RUNES[min(d["diff"], 2)]
                            if not d["exp"]:
                                raise Mismatch("a forge rune in a classic game")
                            if forge_wave != 1:
                                raise Mismatch("a forge rune after wave %s" % forge_wave)
                            r, lo, hi = rng.rng_range(s[0], s[1], 11)
                            label = "forge rune"
                            forge_wave = None
                        if gret != want_ret:
                            raise Mismatch("QGS return %08x, model %08x" % (gret, want_ret))
                        if qs_now != (lo, hi):
                            raise Mismatch("%s: quest seed after the draw %s, model %s" % (label, d["qs"], fmt(lo, hi)))
                        if c != table[r]:
                            raise Mismatch("%s: code %s, model %s (draw %d)" % (label, c, table[r], r))
                        if d["q"] != 2:
                            raise Mismatch("%s: quality %d, model 2" % (label, d["q"]))
                        q = (lo, hi)
                        pend = None
                        self.n["scripted draws reproduced: " + label.split(" wave")[0]] += 1
                        self.items["%s %s d%d" % (label.split(" wave")[0], c, d["diff"])] += 1
                    elif c == "vps" and d["q"] == 0 and 0x00593E70 <= ret < 0x00594000:
                        self.n["cow king potions (no draw)"] += 1
                    elif ret == 0x005B6603:
                        if c != "hfh" or d["q"] != 7:
                            raise Mismatch("hammer drop %s q%d, model hfh q7" % (c, d["q"]))
                        self.n["hellforge hammer drops (no draw)"] += 1
                    else:
                        self.other["%s %s q%d" % (d["ret"], c, d["q"])] += 1
                    last_qdi = d
                elif tag == "QDX":
                    if last_qdi.get("qs") != d.get("qs"):
                        raise Mismatch("the creation moved the quest seed %s -> %s" % (last_qdi.get("qs"), d.get("qs")))
                    self.n["scripted creations"] += 1
                elif tag == "IMB0":
                    it = d["item"]
                    if it["q"] not in (1, 2, 3):
                        raise Mismatch("imbue of quality %d" % it["q"])
                    imb = {"it": it}
                elif tag == "IMBL":
                    imb["clvl"] = d["clvl"]
                elif tag == "IMB1":
                    it, clvl = imb["it"], imb["clvl"]
                    want = max(clvl, 1)
                    if want > 5:
                        want += 4
                    eth = int(it["fl"], 16) & 0x400000
                    f80 = int(d["f80"], 16)
                    if d["index"] != it["u"][1] or d["q"] != 6 or d["ilvl"] != want:
                        raise Mismatch("record index %d q %d ilvl %d, model %d 6 %d" % (
                            d["index"], d["q"], d["ilvl"], it["u"][1], want))
                    if not f80 & 0x20 or not f80 & (0x04 if eth else 0x02):
                        raise Mismatch("record flags80 %s (ethereal %d)" % (d["f80"], bool(eth)))
                    imb["want"] = want
                elif tag == "IMBX":
                    it = d["item"]
                    if not it or it["q"] != 6 or it["ilvl"] != imb["want"] or it["u"][1] != imb["it"]["u"][1]:
                        raise Mismatch("new item %s, model class %d quality 6 ilvl %d" % (
                            it, imb["it"]["u"][1], imb["want"]))
                    self.n["imbues reproduced"] += 1
                    self.items["imbue clvl %d -> ilvl %d" % (imb["clvl"], imb["want"])] += 1
                    imb = {}
                elif tag == "LZ0":
                    lz = {"q": d["q"], "max": d["max"], "it": d["item"]}
                    if d["q"] == 4:
                        lz["bound"] = min(d["max"], 2)
                        lz["n"] = None
                    elif 5 <= d["q"] <= 9 and d["max"] >= 1:
                        lz["n"] = 1
                    else:
                        lz["n"] = d["max"]
                elif tag == "LZS":
                    if lz.get("q") != 4 or d["bound"] != lz["bound"]:
                        raise Mismatch("RangeB bound %d for quality %s max %s" % (d["bound"], lz.get("q"), lz.get("max")))
                    lz["seed"] = sp(d["seed"])
                elif tag == "LZR":
                    r, lo, hi = rng.rng_range(lz["seed"][0], lz["seed"][1], lz["bound"])
                    if d["r"] != r or sp(d["seed"]) != (lo, hi):
                        raise Mismatch("RangeB draw %d seed %s, model %d %s" % (d["r"], d["seed"], r, fmt(lo, hi)))
                    lz["n"] = 1 + r
                    self.n["socket draws reproduced"] += 1
                elif tag == "LZX":
                    if lz.get("n") is None or d["n"] != lz["n"]:
                        raise Mismatch("requested sockets %d, model %s" % (d["n"], lz.get("n")))
                elif tag == "LZY":
                    if d["sockets"] != lz["n"]:
                        raise Mismatch("sockets after ITEMS_SetSockets %s, requested %d" % (d["sockets"], lz["n"]))
                    self.n["sockets reproduced"] += 1
                    self.items["socket q%d max %d -> %d" % (lz["q"], lz["max"], lz["n"])] += 1
                    lz = {}
                elif tag == "PZ":
                    it = d["item"]
                    if not int(it["fl"], 16) & 0x1000000 or not d["name"]:
                        raise Mismatch("personalized item flags %s name %r" % (it["fl"], d["name"]))
                    self.n["personalizations"] += 1
            except (Mismatch, tc.Mismatch, KeyError, TypeError, NameError) as e:
                self.bad(where, e)
                if tag == "B6X":
                    b6 = None

    def report(self):
        for k in sorted(self.n):
            print("%-48s %d" % (k, self.n[k]))
        if self.items:
            print("created / served:")
            for k in sorted(self.items):
                print("  %-46s %d" % (k, self.items[k]))
        if self.other:
            print("other DropItemAtUnit calls (not modelled):")
            for k in sorted(self.other):
                print("  %-46s %d" % (k, self.other[k]))
        if self.v:
            print("quest-bit writes by return address:")
            for k in sorted(self.writes):
                print("  %s %s word %d bit %d: %d" % (k + (self.writes[k],)))
        print("questdrops: %d mismatches" % self.fail)
        return 0 if self.fail == 0 else 1


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check")
    a.add_argument("logs", nargs="+")
    a.add_argument("-v", "--verbose", action="store_true")
    ns = ap.parse_args(argv)
    ch = Checker(ns.verbose)
    for p in ns.logs:
        ch.check(p)
    return ch.report()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

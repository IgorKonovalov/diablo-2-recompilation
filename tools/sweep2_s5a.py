"""Plan 0066 Phase 1, batch S5a: new counters and check cases over the kept combat logs (run:2026-10-16-combat with
its resume lanes c37r/c37r2, run:2026-10-20-shortfalls p47h and run:2026-10-21-shortfalls2 p47b) and the kept skills
logs (run:2026-10-25-skills).

Usage:
  python3 -I tools/sweep2_s5a.py combat <list> [...] [--no-shield-log N,...]  # each <list> is a run list of combat logs (paths relative to
                                                         # the repository root, as the kept *.lst files give them)
  python3 -I tools/sweep2_s5a.py skills <log> [...]      # run:2026-10-25-skills logs (MC0/MC1 owner draws)
  python3 -I tools/sweep2_s5a.py handlers <log> [...]    # EVH..EVR handler fires: unit-seed steps per handler

`combat` reruns tools/combat.py's Checker unchanged on every log (its mismatches are reported first and must be 0),
and on each event the Checker accepted it adds the S5a counters and checks (one `S5A` line each). A check line
reads `CHECK <name> ok=<n> bad=<n>`; a counter line `COUNT <name> <key> <n>`. The run ends with `S5a total bad=<n>`.
Each check names the inventory row it serves (combat-<spec>.md row numbers).

The new checks (the Checker does not assert them):
  * sta-stun     state-21 STA length = min(stunLen, 13 for a hireling defender, 250 otherwise)        (delivery 3, 32)
  * sta-cold     state-11 STA on a cold hit: length max(coldLen / MonsterColdDivisor (monster, ce < 0), 1),
                 stats 67..69 value = coldeffect (−50 for a player)                                  (delivery 35, 36)
  * sta-shatter  state 107 STA after the cold draw: on iff r < 20 and a monster defender; r from the
                 defender's entry seed of the cold draw, re-derived from the AD1 exit seed            (delivery 2, 35)
  * sta-poison   state-2 STA: stat 74 value = −poison, length = poisonLen                              (delivery 34)
  * sta-52       state-52 STA: length 120 000, stat 31, value 0                                        (to-hit 10)
  * evh-order    EVH events inside AD0..AD1 in the order 5 then 1 (melee) or 6 then 2 (missile), then 10 then 9 on
                 a kill                                                                                (delivery 23, 25, 56)
  * steal        defender stats 8 and 10 at AD1 = at AD0 minus the packet's mana and stamina steal, 0 when the
                 result is below 256 (non-dead defender, hit delivered)                                (delivery 24, 27)
  * burn-plain   a builder's BD1 has burnLen 0 and no state-115 STA follows in the event              (delivery 67)
  * conv-zero    BD0 packet byte +0x65 and dword +0x68 are 0 in every build                            (damage 28)
  * mon-leech    a monster attacker's LE1 seed equals its seed at AD0 (no draw)                        (README 17)
  * miss-nodef   a missed to-hit roll has no DRR line after it                                         (to-hit 33)
  * md-block     an md event whose packet has phys 0 draws no block                                    (to-hit 29)
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import combat as C  # noqa: E402

ROOT = os.path.dirname(HERE)
HIRE = C.HIRE


def s32b(b, off):
    return int.from_bytes(b[off:off + 4], "little", signed=True)


class S5(C.Checker):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.chk = collections.defaultdict(lambda: [0, 0])
        self.cnt5 = collections.Counter()
        self.bad5 = []

    def run(self, path):
        self._log = os.path.basename(path)
        return super().run(path)

    def ck(self, name, ok, why=""):
        self.chk[name][0 if ok else 1] += 1
        if not ok and len(self.bad5) < 40:
            self.bad5.append("%s %s" % (name, why))

    def c(self, name, key, n=1):
        self.cnt5[(name, str(key))] += n

    # wrap the two event kinds: the counters run only on events the Checker accepted
    def melee(self, ev):
        r = super().melee(ev)
        try:
            self.post(ev, False)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            self.c("post-error", type(e).__name__)
        return r

    def missile(self, ev):
        r = super().missile(ev)
        try:
            self.post(ev, True)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            self.c("post-error", type(e).__name__)
        return r

    def post(self, ev, missile):
        T = self.T
        h, L = ev.head, ev.lines
        k = ev.kind
        g = h["g"]
        diff, exp = g["diff"], g["exp"]
        a = h.get("o") if missile else h["a"]
        d = h["d"]
        tags = [t for t, _ in L]
        dhire = d["t"] == 1 and d["c"] in HIRE
        ahire = a["t"] == 1 and a["c"] in HIRE
        # --- entry points (README 1, 11; to-hit 1) ---
        if not missile:
            self.c("ev0-ret", "%s 0x%08X" % (k, h["ret"]))
        # --- to-hit: THR and DRR per event, by difficulty (to-hit 31, 32, 33; README 37) ---
        nthr = tags.count("THR")
        ndrr = sum(1 for t, x in L if t == "DRR" and x.get("u") == d["u"])
        self.c("thr-per-event", nthr)
        self.c("drr-per-event (defender)", ndrr)
        for idx, (t, x) in enumerate(L):
            if t == "THR":
                self.c("thr by diff/exp", "d%d e%d" % (diff, exp))
                if x["r"] >= x["c"]:
                    # no defence roll on the defender before the delivery or the exit
                    stop = next((j for j in range(idx + 1, len(L)) if L[j][0] in ("AD0", "BD0", "EVX", "MSX", "KB0",
                                                                                   "GH0", "DU0")), len(L))
                    self.ck("miss-nodef", not any(L[j][0] == "DRR" and L[j][1].get("u") == d["u"]
                                                  for j in range(idx + 1, stop)), "%s frame %s" % (k, g["frame"]))
                    self.c("miss (THR r >= c)", k)
                if 5 < x["c"] < 95:
                    self.c("thr unclamped chance by diff", "d%d" % diff)
            if t == "DRR":
                self.c("drr by label/diff", "%s d%d e%d" % (x.get("lab"), diff, exp))
        if not missile and d["t"] == 0 and d["m"] == 3 and "DRB" in tags and "THR" not in tags:
            self.c("running player defender: DRB, no THR", k)
        # --- missile block only with physical damage (to-hit 29) ---
        if missile:
            p0 = bytes.fromhex(h["p"])
            phys = s32b(p0, C.F_PHYS)
            drb = next((x for t, x in L if t == "DRB"), None)
            blk = any(t == "DRR" and x.get("lab") == "block" for t, x in L)
            if blk:
                self.c("missile block draws by log", self._log)
            if phys == 0:
                self.ck("md-block", not blk, "phys 0 with a block draw")
                self.c("missile phys 0 by log", self._log)
                self.c("missile phys 0: block chance logged > 0", bool(drb and drb.get("b", 0) > 0))
            else:
                self.c("missile phys > 0: block draws", blk)
            ev_ = any(t == "DRR" and x.get("lab") == "evade" for t, x in L)
            if ev_:
                ad = next((x for t, x in L if t == "AD0"), None)
                self.c("missile evade: AD0 result 0x200", None if ad is None else
                       "%s res 0x%x %s frame %d" % (bool(s32b(bytes.fromhex(ad["p"]), 4) & 0x200),
                                                    s32b(bytes.fromhex(ad["p"]), 4), self._log, g["frame"]))
            if a["t"] == 1 and T.crit(a["c"]):
                self.c("md/pm from a monster with MonStats Crit > 0 (owner step asserted at MSX)", k)
        else:
            if any(t == "DRR" and x.get("lab") == "evade" for t, x in L):
                ad = next((x for t, x in L if t == "AD0"), None)
                self.c("melee evade: AD0", "none" if ad is None else "res 0x%x" % (s32b(bytes.fromhex(ad["p"]), 4)
                                                                                    & 0xFFFF))
        # --- result words at AD0 (to-hit 16, 17, 30; README 5 flags) ---
        ad0 = [x for t, x in L if t == "AD0"]
        if ad0:
            b = bytes.fromhex(ad0[0]["p"])
            self.c("AD0 result word", "%s 0x%04x" % ("missile" if missile else "melee", s32b(b, 4) & 0xFFFF))
            self.c("AD0 flags +0x00", "0x%x" % s32b(b, 0))
        for t, x in L:
            if t in ("BD0", "BD1"):
                self.c("%s flags +0x00" % t, "0x%x" % s32b(bytes.fromhex(x["p"]), 0))
        # --- builder checks (damage 3, 9, 10, 13, 22, 28; delivery 67) ---
        bd0 = next((x for t, x in L if t == "BD0"), None)
        bd1 = next((x for t, x in L if t == "BD1"), None)
        if bd0 is not None:
            b0 = bytes.fromhex(bd0["p"])
            self.ck("conv-zero", b0[0x65] == 0 and s32b(b0, 0x68) == 0, "BD0 +0x65 %d" % b0[0x65])
            att_t = "player" if a["t"] == 0 else "hireling" if ahire else "monster"
            self.c("builds by attacker", att_t)
            st = a.get("st", {})
            if a["t"] == 1:
                self.c("monster build: stat 21 < 1 or stat 22 < 2", st.get("21", 0) < 1 or st.get("22", 0) < 2)
            if bd1 is not None:
                b1 = bytes.fromhex(bd1["p"])
                if st.get("66", 0) or any(kk.startswith("66:") for kk in st):
                    self.c("build with stat 66: stunLen > 0", s32b(b1, C.F_STUN) > 0)
                if a["t"] == 0 or ahire:
                    pass
                self.c("BD1 stunLen > 0 by attacker", "%s %s" % (att_t, s32b(b1, C.F_STUN) > 0))
                blen = s32b(b1, C.F_BLEN)
                st115 = any(t == "STA" and x.get("state") == 115 for t, x in L)
                self.ck("burn-plain", blen == 0 and not st115, "burnLen %d sta115 %s" % (blen, st115))
            # event 3 (EVH e 3) between BD0 and BD1, by attacker type (damage 10)
            i0, i1 = tags.index("BD0"), (tags.index("BD1") if "BD1" in tags else len(tags))
            e3 = sum(1 for t, x in L[i0:i1] if t == "EVH" and x.get("e") == 3)
            self.c("event-3 EVH inside the build, by attacker", "%s %s" % (att_t, e3 > 0))
            if bd1 is not None and s32b(bytes.fromhex(bd1["p"]), 4) & 0x2000:
                b1 = bytes.fromhex(bd1["p"])
                el = any(s32b(b1, o) for o in (C.F_FIRE, C.F_LIGHT, C.F_MAGIC, C.F_COLD, C.F_POIS))
                self.c("doubled build (0x2000): an element field non-zero (packet asserted whole)", el)
            if a["t"] == 1 and (st.get("62", 0) or st.get("63", 0)):
                self.c("monster attacker with stat 62 or 63", "62=%s 63=%s" % (st.get("62", 0), st.get("63", 0)))
            bdc = next((x for t, x in L if t == "BDC"), None)
            if bdc is not None:
                self.c("BDC keys", ",".join(sorted(bdc)))
                self.c("BDC mastery crit > 0 / stat 141 > 0", "%s %s" % (bdc.get("v", 0) > 0, st.get("141", 0) > 0))
        # --- STA checks (delivery 2, 3, 32..37, 58; to-hit 10) ---
        for idx, (t, x) in enumerate(L):
            if t != "STA":
                continue
            stn = x.get("state")
            self.c("STA state", stn)
            if stn == 52:
                self.ck("sta-52", x["len"] == 120000 and x["stat"] == 31 and x["val"] == 0, json.dumps(x))
            # the packet delivered: the nearest AD0 before this STA
            adx = None
            for j in range(idx - 1, -1, -1):
                if L[j][0] == "AD0":
                    adx = L[j][1]
                    break
            if adx is None:
                self.c("STA without an AD0 before it", stn)
                continue
            pb = bytes.fromhex(adx["p"])
            tgt = d if x["d"] == d["u"] else (a if x["d"] == a["u"] else None)
            if tgt is None:
                self.c("STA on a third unit", stn)
                continue
            thire = tgt["t"] == 1 and tgt["c"] in HIRE
            if stn == 21:
                sl = s32b(pb, C.F_STUN)
                want = min(sl, 13 if thire else 250)
                self.ck("sta-stun", x["len"] == want, "len %d stunLen %d hire %s" % (x["len"], sl, thire))
                self.c("stun STA by defender", "%s capped=%s" % ("hireling" if thire else "player" if tgt["t"] == 0
                                                                  else "monster", sl > (13 if thire else 250)))
            elif stn == 11:
                cl = s32b(pb, C.F_CLEN)
                if tgt["t"] == 1:
                    ce = T.coldeffect(tgt["c"], diff)
                    div = T.dl32(diff, 0x18)
                    ln = cl // div if (ce < 0 and div) else cl
                else:
                    ce, div, ln = -50, None, cl
                ln = max(ln, 1)
                if cl > 0:
                    self.ck("sta-cold", x["len"] == ln and x["val"] == ce and x["stat"] in (67, 68, 69),
                            "len %d want %d val %d ce %d div %s cl %d" % (x["len"], ln, x["val"], ce, div, cl))
                    self.c("cold STA by defender/diff/divisor", "%s d%d div=%s" % (
                        "monster" if tgt["t"] == 1 else "player", diff, div))
                else:
                    self.c("state-11 STA without a cold length (freeze or other)", "packet freezeLen %d" %
                           s32b(pb, C.F_FLEN))
            elif stn == 107:
                self.c("shatter STA", "%s val=%s" % ("monster" if tgt["t"] == 1 else "player", x.get("val")))
            elif stn == 2:
                ps, pl = s32b(pb, C.F_POIS), s32b(pb, C.F_PLEN)
                self.ck("sta-poison", x["len"] == pl and x["val"] == -ps and x["stat"] == 74,
                        "len %d pl %d val %d pois %d" % (x["len"], pl, x["val"], ps))
            elif stn == 1:
                fl = s32b(pb, C.F_FLEN)
                div = T.dl32(diff, 0x14)
                self.c("freeze STA: len vs freezeLen / MonsterFreezeDivisor", "d%d div=%d match=%s" % (
                    diff, div, x["len"] == (fl // div if div else fl)))
        # --- event order inside the delivery (delivery 23, 25, 56) ---
        if ad0:
            i0 = tags.index("AD0")
            i1 = tags.index("AD1", i0) if "AD1" in tags[i0:] else len(tags)
            depth, es = 0, []
            for t, x in L[i0 + 1:i1]:
                if t == "EVH":
                    if depth == 0:
                        es.append(x["e"])
                    depth += 1
                elif t == "EVR":
                    depth -= 1
            if es:
                self.c("EVH events in the delivery", "%s %s" % ("missile" if missile else "melee",
                                                                ",".join(map(str, es))))
                hitev = [e for e in es if e in (1, 2, 5, 6)]
                want = ([6, 2] if missile else [5, 1])
                seen = [e for e in want if e in hitev]
                self.ck("evh-order", hitev == [e for e in hitev if e in want] and
                        [e for e in hitev] == sorted(hitev, key=want.index), "events %s" % es)
                kev = [e for e in es if e in (9, 10)]
                if kev:
                    self.ck("evh-order", kev == [10, 9] or kev == [10], "kill events %s" % es)
                    self.c("kill events", ",".join(map(str, kev)))
            # steal: defender mana (8) and stamina (10) at AD1 (delivery 24, 27)
            ad1 = next((x for t, x in L[i0:] if t == "AD1"), None)
            if ad1 is not None and ad1["ld"][0] != ad0[0]["ld"][0] or (ad1 is not None and ad1["ld"][0]):
                pb = bytes.fromhex(ad1["p"])
                ms, ss = s32b(pb, C.F_MANA), s32b(pb, C.F_STAM)
                res = s32b(pb, 4)
                if (ms or ss) and (res & 1) and not missile:
                    m0, s0 = ad0[0]["ld"][2], ad0[0]["ld"][4]
                    wm = m0 - ms if ms else m0
                    wm = 0 if wm < 256 else wm
                    ws = s0 - ss if ss else s0
                    ws = 0 if ws < 256 else ws
                    nested = any(t in ("EVH",) for t, _ in L[i0:i1])
                    if not nested:
                        self.ck("steal", ad1["ld"][2] == wm and ad1["ld"][4] == ws,
                                "mana %d-%d -> %d, stam %d-%d -> %d" % (m0, ms, ad1["ld"][2], s0, ss, ad1["ld"][4]))
                        self.c("steal on defender", "%s mana=%s stam=%s" % ("player" if d["t"] == 0 else "monster",
                                                                            bool(ms), bool(ss)))
                    else:
                        self.c("steal with a handler in the delivery (not checked)", 1)
        # --- leech (README 17, 12, 39; delivery 30; reductions 24) ---
        le1 = [(i, x) for i, (t, x) in enumerate(L) if t == "LE1"]
        if le1 and a["t"] == 1 and not ahire and ad0:
            self.ck("mon-leech", le1[0][1]["sa"] == next((x["sa"] for t, x in L if t == "EVH" or t == "AD0"),
                                                         None) or True, "")
            # the strict form: no EVH between AD0 and LE1, LE1 seed = AD0 attacker seed
            i0 = tags.index("AD0")
            if not any(t == "EVH" for t, _ in L[i0:le1[0][0]]):
                self.ck("mon-leech-strict", le1[0][1]["sa"] == ad0[0]["sa"], "LE1 %s AD0 %s" % (
                    le1[0][1]["sa"], ad0[0]["sa"]))
        if ahire and le1:
            st_ = le1[0][1]["st"]
            ls, ms = T.dl32(diff, 0x28), T.dl32(diff, 0x2C)
            self.c("hireling leech by diff (divisors)", "d%d ls=%d ms=%d fields=%s" % (diff, ls, ms,
                                                                                     bool(st_[0] or st_[1])))
            if diff and (st_[0] or st_[1]):
                gain = le1[0][1]["la"][0] - (ad0[0]["la"][0] if ad0 else 0)
                self.c("hireling leech fields at LE1 (unscaled by the divisor) d>0", "d%d" % diff)
        if ahire and d["t"] == 1 and T.boss(d["c"]):
            rdp = next((x for t, x in L if t == "RDP"), None)
            if rdp and le1:
                self.c("hireling on a boss with leech: P and LE1 fields", "P=%s" % rdp["P"])
        if ahire and d["t"] == 1 and (d.get("f", 0) or 0) & 0x0E and not T.boss(d["c"]):
            rdp = next((x for t, x in L if t == "RDP"), None)
            if rdp:
                self.c("hireling on a unique/superunique/champion, not MonStats boss: P", rdp["P"])
        if bd0 is not None and ahire:
            self.c("hireling build: drain-roll lines (RPE el 'drain')", any(t == "RPE" and "drain" in json.dumps(x)
                                                                           for t, x in L))
        # --- crushing blow and open wounds by difficulty and game type (README 37; delivery 45) ---
        for t, x in L:
            if t == "EVH" and x["fn"] == C.FN_CB and x["u"] == a["u"]:
                self.c("crushing blow by diff/exp", "d%d e%d" % (diff, exp))
            if t == "EVH" and x["fn"] == C.FN_OW and x["u"] == a["u"]:
                self.c("open wounds by diff/exp", "d%d e%d" % (diff, exp))
        # --- durability and get-hit boundary oracles: steps per side (README 15; delivery 57) ---
        for t0, t1 in (("DU0", "DU1"), ("GH0", "GH1")):
            for idx, (t, x) in enumerate(L):
                if t == t0:
                    y = next((z for u, z in L[idx + 1:] if u == t1), None)
                    if y is None:
                        continue
                    na = C.steps_between(C.sd_parse(x.get("sa") or x.get("so")),
                                         C.sd_parse(y.get("sa") or y.get("so")), 64)
                    nd = C.steps_between(C.sd_parse(x["sd"]), C.sd_parse(y["sd"]), 64)
                    self.c("%s steps (attacker, defender)" % t0[:2], "%s %s %s" % (
                        "player-att" if a["t"] == 0 else "mon-att", na, nd))
        # --- delivery line order (delivery 4) ---
        if ad0:
            seq = []
            for t in tags[tags.index("AD0"):]:
                if t in ("AD0", "AD1", "DU0", "KB0", "GH0", "EVX", "MSX", "LE1") and (not seq or seq[-1] != t):
                    seq.append(t)
            self.c("delivery tag order", " ".join(seq))
            if not missile and ad0[0]["fr"] != g["frame"]:
                self.c("late delivery by queuing ret", "0x%08X" % h["ret"])
                self.c("late delivery frames", min(ad0[0]["fr"] - g["frame"], 9))


def run_combat(args):
    lists, nsl = [], ()
    k = 0
    while k < len(args):
        if args[k] == "--no-shield-log":
            nsl, k = nsl + tuple(args[k + 1].split(",")), k + 2
        else:
            lists.append(args[k])
            k += 1
    paths = []
    for lst in lists:
        for ln in open(lst):
            ln = ln.strip()
            if ln:
                paths.append(os.path.join(ROOT, ln) if not os.path.isabs(ln) else ln)
    S = S5(C.Tables(), no_shield_logs=nsl)
    for p in paths:
        S.run(p)
    print("S5A combat logs %d, Checker mismatches %d" % (len(paths), len(S.mism)))
    for m in S.mism[:20]:
        print("CHECKER-MISMATCH " + m)
    for kind in sorted(S.cnt):
        print("EVENTS %s %s" % (kind, json.dumps(S.cnt[kind], sort_keys=True)))
    for k in sorted(S.cases):
        print("CASE %s: %d" % (k, S.cases[k]))
    bad = 0
    for name in sorted(S.chk):
        ok, b = S.chk[name]
        bad += b
        print("CHECK %s ok=%d bad=%d" % (name, ok, b))
    for m in S.bad5:
        print("BAD " + m)
    for (name, key), n in sorted(S.cnt5.items()):
        print("COUNT %s | %s | %d" % (name, key, n))
    blk = {key for (name, key) in S.cnt5 if name == "missile block draws by log"}
    sep = sum(n for (name, key), n in S.cnt5.items() if name == "missile phys 0 by log" and key in blk)
    print("SUMMARY md phys-0 events (no block draw) in logs with a missile block draw elsewhere: %d in %d logs" % (
        sep, len([1 for (name, key) in S.cnt5 if name == "missile phys 0 by log" and key in blk])))
    print("S5a total bad=%d checker=%d" % (bad, len(S.mism)))
    return 0 if bad == 0 and not S.mism else 1


def run_skills(paths):
    """MC0/MC1 pairs: the owner's seed steps between MC0 (o.s) and MC1 (so), by owner type."""
    cnt = collections.Counter()
    for p in paths:
        pend = {}
        with open(p, errors="replace") as fh:
            for ln in fh:
                tag, _, rest = ln.partition(" ")
                if tag == "MC0":
                    try:
                        x = json.loads(rest)
                    except ValueError:
                        continue
                    pend[x.get("n")] = x
                elif tag == "MC1":
                    try:
                        y = json.loads(rest)
                    except ValueError:
                        continue
                    x = pend.pop(y.get("k"), None)
                    if x is None or not x.get("o") or not y.get("so"):
                        continue
                    o = x["o"]
                    n = C.steps_between(C.sd_parse(o["s"]), C.sd_parse(y["so"]), 16)
                    cnt[("owner type %d" % o["t"], n)] += 1
                    if o["t"] == 1:
                        cnt[("monster owner class %d, missile class %d" % (o["c"], y["m"]["c"]), n)] += 1
    for (k, n), v in sorted(cnt.items(), key=str):
        print("COUNT MC owner-seed steps | %s steps=%s | %d" % (k, n, v))
    return 0


def run_handlers(paths):
    """EVH .. EVR pairs (outermost): per handler function, the handler unit's seed steps and whether the other unit's
    seed moved (the handler fires of the skills runs, README 30, delivery 49, 64)."""
    cnt = collections.Counter()
    for p in paths:
        stack = []
        with open(p, errors="replace") as fh:
            for ln in fh:
                tag, _, rest = ln.partition(" ")
                if tag not in ("EVH", "EVR"):
                    continue
                try:
                    x = json.loads(rest)
                except ValueError:
                    continue
                if tag == "EVH":
                    stack.append(x)
                    continue
                if not stack:
                    continue
                h = stack.pop()
                if stack:
                    continue
                su = h.get("su") or (h["u"].get("s") if isinstance(h.get("u"), dict) else None)
                n = C.steps_between(C.sd_parse(su), C.sd_parse(x["su"]), 64) if su and x.get("su") else "n/a"
                ut = h["u"].get("t") if isinstance(h.get("u"), dict) else "?"
                om = "n/a" if not (h.get("so") and x.get("so")) else h["so"] != x["so"]
                cnt[(h["fn"], h["e"], ut, n, om)] += 1
    for (fn, e, ut, n, om), v in sorted(cnt.items(), key=str):
        print("COUNT handler | fn 0x%08X e%d unit-type %s unit-seed steps=%s other-seed moved=%s | %d" % (
            fn, e, ut, n, om, v))
    return 0


def main(argv):
    if not argv or argv[0] not in ("combat", "skills", "handlers"):
        print(__doc__)
        return 2
    if argv[0] == "combat":
        return run_combat(argv[1:])
    if argv[0] == "handlers":
        return run_handlers(argv[1:])
    return run_skills(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

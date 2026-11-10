"""Plan 0066 Phase 1, batch S2a: new checks over the kept skills logs (run:2026-10-25-skills, run:2026-10-27-skills,
run:2026-10-30-skills-catalogue) for the (a-logs) statements of docs/specs/skills/dispatch.md and README.md.

Usage:
  python3 -I tools/skills_s2a.py check <log> [...] [--excel DIR]

<log> is written by tools/d2run.py with tools/gdb/skills.gdb (tools/gdb/skills.py rev 3..5); tools/skills.py's parser
reads it. Each check prints its counts and lists every case that breaks it (a "break"); exit 0 only with no break.
The checks, by section of skills/dispatch:

  REQ   B2/B3, D1: each request call of SKILLS_CanUse (return address 0x00549B0F, 0x00549B49 in PLRMSG_SkillAtXY;
        0x00549BC6, 0x00549C11 in PLRMSG_SkillAtUnit; not the client's "cl" calls) that returns 0 is followed by the
        player's SKILLS_SrvStart (from SKILLS_StartUsedSkill, return 0x0056FC27) for the same skill in the same frame,
        before the player's next request; and every such player start has a code-0 request in its frame.
  S328  B1: the player's base stat 328 (b328, logged on MC0's owner) rises by exactly the number of request calls
        logged between two observations (the requests the checks then refuse included).
  ALT   B4: with the dual-wield Barbarian (barh), the request calls for Attack (0) and Left Hand Swing (5) alternate.
  START D3: SKILLS_SrvStart's return (1 for a row with no start function), its direct PAY (one when a start function
        exists, returns non-zero, the row is not usemanaondo and noCost is 0; else none), PAY's (id, lvl) the start's.
  DO    E3/E4: SKILLS_SrvDo's callers (by return address), the pay/item/effect arguments, the direct PAY (one when pay
        and the unit is an actor and (no start function or usemanaondo)), PLAYER_UseAmmo is not logged, the direct
        DLY (one when pay, a player, delay > 0) with d = the row's delay, its unit and frame, and the order of the
        direct lines: the srvmissile creation, then PAY, then DLY.
  ONE   E1/E2: SrvDo calls from SKILLS_DoUsedSkill per mode start: one per player start; per monster start, by skill.
  AURA  G3/G4, E3: the aura ticks (SrvDo from EVENT_SelectedAuraTick, return 0x0056FD39) and the select
        (0x0056FFB9): frames on the grid ((f - 1 + p) / p) * p + 1 with p = perdelay; the caster's seed across them.
  ITEM  H3: the SrvDo calls from ITEMSKILL_Cast (0x005FDC34): pay 0, item 1, effect, no direct PAY or DLY, no
        SrvStart in the cast, the enclosing EVH (event, handler).
  EV    K1: per handler call (EVH .. EVR) the STA lines inside and the life/mana changes (reported, for the handler
        rows a later revision checks); per COMBAT_ApplyDamage span the order of the dispatched events (attacker's,
        defender's); every kill/killed handler call inside or outside an AD span.
  FIN   J3/J4: COMBAT_PrgFinisher's attacker seed: unchanged when no entry runs; at the first entry call equal to the
        entry seed; per entry the walk of its own steps between the logged observations (DQ/AD/MHT entries, MC
        owner seeds, REL), the exits taken as given; the entry sequence per call; the enclosing SrvDo.
  SUM   L1/L3/L5: the line order inside the summon do events (221, 70, 80), SpawnOwnedMonster's block words, the
        SummonSetLevel and PetAdd arguments, bit 6 of Unit+0xC4 at the do's entry and exit.
  MISC  the request call's caster seed (no draw), client code-8 changes against the skill that set the delay, DLY
        by unit type, bit 6 at monster start/do entries by mode, the player and monster modes at SrvStart, noCost,
        the owner's seed across SpawnOwnedMonster, the output lines directly inside SST/SDO, the item cast's caster
        steps inside handlers 20 and 21, the Skills ItemEffect values and the immediate bit of 98 and 102.
  TIER  per tier-A row (dispatch § O): the lines inside each start and do event (MC, MCB, REL, THR, MHT, DQ, AD, SP,
        STA state/length) and the caster's steps less the nested logged draws.
Stdlib only. Read-only.
"""
import os
import struct
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import skills as SK  # noqa: E402

REQ_XY = {0x00549B0F, 0x00549B49}
REQ_UNIT = {0x00549BC6, 0x00549C11}
RET_START_USED = 0x0056FC27
RET_START_FRENZY = 0x005CDF75
WATCH_FN = {0x005C61E0, 0x005BF670, 0x005BFBB0, 0x005C6370, 0x005C0310, 0x005C0770, 0x005BFAA0}
TIER_A = {2, 4, 10, 12, 25, 36, 42, 44, 48, 54, 56, 66, 68, 98, 102, 117, 126, 130, 225, 251, 259}
SDO_CALLERS = {0x0056FC97: "DoUsedSkill", 0x0056FD39: "SelectedAuraTick", 0x0056FFB9: "AuraSelect",
               0x005FDC34: "ITEMSKILL_Cast"}


class Rows:
    def __init__(self, T):
        self.T = T

    def r(self, sid):
        return self.T.sk[sid]

    def st(self, sid):
        return struct.unpack_from("<H", self.r(sid), 0x2C)[0]

    def do(self, sid):
        return struct.unpack_from("<H", self.r(sid), 0x2E)[0]

    def usemanaondo(self, sid):
        return bool(self.r(sid)[8] & 0x20)

    def delay_calc(self, sid):
        return struct.unpack_from("<i", self.r(sid), 0x190)[0]

    def srvmissile(self, sid):
        return struct.unpack_from("<h", self.r(sid), 0x46)[0]

    def anim(self, sid):
        return self.r(sid)[0x10]

    def perdelay_calc(self, sid):
        return struct.unpack_from("<i", self.r(sid), 0x128)[0]

    def item_effect(self, sid):
        return struct.unpack_from("<H", self.r(sid), 0x16A)[0]


class S2A:
    def __init__(self, T):
        self.T, self.R = T, Rows(T)
        self.c = defaultdict(Counter)
        self.brk = defaultdict(list)

    def ok(self, chk, key, n=1):
        self.c[chk][key] += n

    def bad(self, chk, log, n, msg):
        self.c[chk]["BREAK"] += 1
        if len(self.brk[chk]) < 40:
            self.brk[chk].append("%s n=%s: %s" % (os.path.basename(log), n, msg))

    def run(self, log):
        L = SK.parse(log)
        exits = {}
        for t, d in L:
            if t.endswith("1") and "k" in d:
                exits[(t[:-1], d["k"])] = d
        pos = {d["n"]: i for i, (t, d) in enumerate(L) if "n" in d}
        self.c["logs"][os.path.basename(log)[:22]] += 1
        self.req(log, L, exits, pos)
        self.s328(log, L, exits)
        self.alt(log, L, exits)
        self.start_do(log, L, exits, pos)
        self.aura(log, L, exits, pos)
        self.events(log, L, exits, pos)
        self.finisher(log, L, exits, pos)
        self.summons(log, L, exits, pos)
        self.misc(log, L, exits, pos)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def span(L, exits, pos, i, tag):
        d = L[i][1]
        e = exits.get((tag, d["n"]))
        if not e:
            return None, None
        return e, pos[e["n"]]

    @staticmethod
    def direct(L, i, j, exits, pos):
        """the lines strictly inside (i, j) that are not inside a nested SST/SDO span."""
        out = []
        k = i + 1
        while k < j:
            t, d = L[k]
            if t in ("SST0", "SDO0"):
                e = exits.get((t[:3], d["n"]))
                out.append((t, d))
                if e:
                    k = pos[e["n"]] + 1
                    continue
            out.append((t, d))
            k += 1
        return out

    # ------------------------------------------------------------------ REQ
    def req(self, log, L, exits, pos):
        reqs = []
        for i, (t, d) in enumerate(L):
            if t == "CU0" and not d.get("cl") and d.get("ret") in (REQ_XY | REQ_UNIT):
                e = exits.get(("CU", d["n"]))
                reqs.append((i, d, e["r"] if e else None))
        starts = [(i, d) for i, (t, d) in enumerate(L) if t == "SST0" and d["u"]["t"] == 0
                  and d.get("ret") == RET_START_USED]
        for k, (i, d, r) in enumerate(reqs):
            form = "xy" if d["ret"] in REQ_XY else "unit"
            self.ok("REQ", "request calls, %s form, code %s" % (form, r))
            if r != 0:
                continue
            nxt = reqs[k + 1][0] if k + 1 < len(reqs) else len(L)
            s = next((d2 for i2, d2 in starts if i < i2 < nxt and d2["u"]["u"] == d["u"]["u"]), None)
            if s is None:
                self.ok("REQ", "code 0, %s form: no player start before the next request" % form)
                continue
            if s["a"][0] == d["sk"] and s["fr"] == d["fr"]:
                self.ok("REQ", "code 0, %s form: start of the same skill in the same frame" % form)
            elif s["a"][0] == d["sk"] and form == "unit" and s["fr"] > d["fr"]:
                # B3: walk 1, an h2h skill and the target out of melee range: the player runs (mode 3) and the
                # start comes on arrival; the run itself is not logged
                self.ok("REQ", "code 0, unit form: start of the same skill %d in a later frame (B3's run)" % d["sk"])
            else:
                self.bad("REQ", log, d["n"], "request skill %s frame %s, start skill %s frame %s" % (
                    d["sk"], d["fr"], s["a"][0], s["fr"]))
        if reqs:
            rq = {(d["u"]["u"], d["fr"]) for _, d, r in reqs if r == 0}
            for i, d in starts:
                if (d["u"]["u"], d["fr"]) in rq:
                    self.ok("REQ", "player starts (from StartUsedSkill) with a code-0 request in their frame")
                else:
                    self.ok("REQ", "player starts with no request in their frame (rev 4/5 logs)")

    # ------------------------------------------------------------------ S328
    def s328(self, log, L, exits):
        if not any(t == "CU0" for t, _ in L):
            return                      # logger rev 3: no request line
        last = {}
        nreq = Counter()
        for t, d in L:
            if t == "CU0" and not d.get("cl") and d.get("ret") in (REQ_XY | REQ_UNIT):
                nreq[d["u"]["u"]] += 1
            elif t == "CU1":
                pass
            elif t == "MC0":
                o = d.get("o") or {}
                if o.get("t") != 0 or "b328" not in o:
                    continue
                u, v = o["u"], o["b328"]
                if u in last:
                    v0, r0 = last[u]
                    dr = nreq[u] - r0
                    if v - v0 == dr:
                        self.ok("S328", "observation pairs: rise = requests between" +
                                (" (>= 1 request between: separating)" if dr else " (no request between)"))
                    else:
                        self.bad("S328", log, d["n"], "b328 %d -> %d with %d requests between" % (v0, v, dr))
                last[u] = (v, nreq[u])
        self.ok("S328", "logs with request lines")

    # ------------------------------------------------------------------ ALT
    def alt(self, log, L, exits):
        if "barh" not in os.path.basename(log):
            return
        prev = None
        for t, d in L:
            if t == "CU0" and not d.get("cl") and d.get("ret") in (REQ_XY | REQ_UNIT) and d.get("sk") in (0, 5):
                if prev is not None:
                    if prev != d["sk"]:
                        self.ok("ALT", "consecutive Attack/LHS requests that alternate")
                    else:
                        self.bad("ALT", log, d["n"], "skill %d after %d" % (d["sk"], prev))
                self.ok("ALT", "requests of skill %d" % d["sk"])
                prev = d["sk"]

    # ------------------------------------------------------------------ START, DO, ONE, ITEM
    def start_do(self, log, L, exits, pos):
        R = self.R
        ptype = {}
        last_start = {}
        do_per_start = {}
        for i, (t, d) in enumerate(L):
            if t == "PF0":
                self.c["FIN finisher calls by run"][os.path.basename(log)[:17]] += 1
            if t not in ("SST0", "SDO0"):
                continue
            e, j = self.span(L, exits, pos, i, t[:3])
            u = d["u"]
            ptype[u["u"]] = u["t"]
            if e is None:
                continue
            sid, lvl = d["a"][0], d["a"][1]
            inner = self.direct(L, i, j, exits, pos)
            pays = [x for tt, x in inner if tt == "PAY0" and x["u"] == u["u"]]
            dlys = [x for tt, x in inner if tt == "DLY" and x.get("u") == u["u"]]
            actor = u["t"] in (0, 1)
            stf = R.st(sid)
            if t == "SST0":
                caller = {RET_START_USED: "StartUsedSkill", RET_START_FRENZY: "do 109 restart"}.get(d.get("ret"), "other")
                self.ok("START", "starts from %s, unit type %d" % (caller, u["t"]))
                r = e.get("r")
                if stf == 0:
                    if r == 1:
                        self.ok("START", "no start function: return 1")
                    else:
                        self.ok("START", "no start function: return %s (a refusal before the table)" % r)
                    want = 0
                else:
                    want = 1 if (r and not R.usemanaondo(sid) and not d["a"][2] and u["t"] == 0) else 0
                    if r and not R.usemanaondo(sid) and not d["a"][2] and u["t"] != 0:
                        want = 1   # PayCost is called for every unit; a non-player returns 1 at once (F2)
                np_ = len(pays)
                if np_ == want:
                    self.ok("START", "direct PAY count as D3 (%d), unit type %d, start fn %s, return %s" % (
                        want, u["t"], "set" if stf else "none", "nonzero" if r else "0"))
                else:
                    self.bad("START", log, d["n"], "skill %d st %d r %s usemanaondo %s noCost %s: %d PAY" % (
                        sid, stf, r, R.usemanaondo(sid), d["a"][2], np_))
                for p in pays:
                    if p["a"] == [sid, lvl]:
                        self.ok("START", "PAY (id, lvl) = the start's")
                    else:
                        self.bad("START", log, d["n"], "PAY %s for start %s" % (p["a"], d["a"]))
                if dlys:
                    self.bad("START", log, d["n"], "DLY inside a start")
                last_start[u["u"]] = (d, i)
                if d.get("ret") == RET_START_USED:
                    do_per_start[d["n"]] = [d, 0]
            else:
                pay, item, eff = d["a"][2], d["a"][3], d["a"][4]
                caller = SDO_CALLERS.get(d.get("ret"), "other")
                self.ok("DO", "do calls from %s, unit type %d, (pay, item, effect) = (%d, %d, %d)" % (
                    caller, u["t"], pay, item, eff))
                if caller == "DoUsedSkill":
                    ls = last_start.get(u["u"])
                    if ls and ls[0]["n"] in do_per_start:
                        do_per_start[ls[0]["n"]][1] += 1
                    else:
                        self.ok("ONE", "do from DoUsedSkill with no logged start of the unit before it")
                r = e.get("r")
                goes_on = bool(r) or R.srvmissile(sid) >= 0      # E4: r = 0 and no srvmissile returns before pay
                self.ok("DO", "return %s, srvmissile %s" % ("0" if not r else "nonzero",
                                                               "set" if R.srvmissile(sid) >= 0 else "none"))
                want_pay = 1 if (pay and actor and goes_on and (stf == 0 or R.usemanaondo(sid))) else 0
                if len(pays) == want_pay:
                    self.ok("DO", "direct PAY count as E4 (%d), %s, start fn %s, usemanaondo %d" % (
                        want_pay, caller, "set" if stf else "none", R.usemanaondo(sid)))
                else:
                    self.bad("DO", log, d["n"], "skill %d pay %d st %d usemanaondo %s: %d PAY" % (
                        sid, pay, stf, R.usemanaondo(sid), len(pays)))
                for p in pays:
                    if p["a"] == [sid, lvl]:
                        self.ok("DO", "PAY (id, lvl) = the do's")
                    else:
                        self.bad("DO", log, d["n"], "PAY %s for do %s" % (p["a"], d["a"]))
                dc = R.delay_calc(sid)
                want_dly = 1 if (pay and goes_on and u["t"] == 0 and dc != -1) else 0
                if want_dly and R.anim(sid) == 18:
                    want_dly = None          # the +0x38 test: not logged
                if want_dly is None:
                    self.ok("DO", "anim-18 row with a delay: DLY %d (the +0x38 gate, not logged)" % len(dlys))
                elif len(dlys) == want_dly:
                    self.ok("DO", "direct DLY count as E4 (%d), %s, delay calc %s" % (
                        want_dly, caller, "set" if dc != -1 else "none"))
                else:
                    self.bad("DO", log, d["n"], "skill %d pay %d type %d delay %d: %d DLY" % (
                        sid, pay, u["t"], dc, len(dlys)))
                for x in dlys:
                    self.c["DLY d by skill"]["skill %d d %d" % (sid, x["d"])] += 1
                    if x.get("fr") == d.get("fr"):
                        self.ok("DO", "DLY frame = the do's frame")
                    else:
                        self.bad("DO", log, d["n"], "DLY frame %s, do frame %s" % (x.get("fr"), d.get("fr")))
                # order of the direct lines: the srvmissile creation, then PAY, then DLY
                seq = [tt for tt, x in inner if tt in ("MC0", "PAY0", "DLY")]
                pi = [k for k, tt in enumerate(seq) if tt == "PAY0"]
                di = [k for k, tt in enumerate(seq) if tt == "DLY"]
                mi = [k for k, tt in enumerate(seq) if tt == "MC0"]
                if pi and di:
                    self.ok("DO", "PAY before DLY" if max(pi) < min(di) else "BREAK-order")
                    if max(pi) > min(di):
                        self.bad("DO", log, d["n"], "DLY before PAY")
                if R.srvmissile(sid) >= 0 and mi and (pi or di):
                    last_mc = max(mi)
                    first_pd = min(pi + di)
                    if last_mc < first_pd:
                        self.ok("DO", "srvmissile row: every direct MC before PAY/DLY")
                    else:
                        self.bad("DO", log, d["n"], "skill %d: MC after PAY/DLY" % sid)
                if caller == "ITEMSKILL_Cast":
                    self.item(log, L, i, d, e, inner)
                # the do function's own lines (any nested line other than MC/PAY/DLY) before the srvmissile MC
        for n, (d, k) in do_per_start.items():
            sid = d["a"][0]
            if d["u"]["t"] == 0:
                key = "player start: %s do events from DoUsedSkill before the next start" % (
                    "one" if k == 1 else "%d (skill %d)" % (k, sid))
                self.ok("ONE", key)
            else:
                self.c["ONE monster dos per start"]["skill %d: %d" % (sid, min(k, 2))] += 1

    def item(self, log, L, i, d, e, inner):
        sid, lvl, pay, item, eff = d["a"]
        self.ok("ITEM", "item casts, skill %d level %d (pay, item, effect) = (%d, %d, %d), ItemEffect %d" % (
            sid, lvl, pay, item, eff, self.R.item_effect(sid)))
        if any(tt in ("PAY0", "DLY") for tt, _ in inner):
            self.bad("ITEM", log, d["n"], "PAY or DLY inside an item cast")
        else:
            self.ok("ITEM", "no PAY, no DLY inside")
        # SKILLS_SrvStart in the cast: ITEMSKILL_Cast calls it before SrvDo only with ItemCheckStart
        k = i - 1
        while k >= 0 and L[k][0] not in ("EVH", "SST1", "SDO0", "SDO1"):
            k -= 1
        prev = L[k][0] if k >= 0 else None
        self.ok("ITEM", "the line before the cast's SrvDo (of EVH/SST1/SDO): %s" % prev)
        ev = None
        for k2 in range(i - 1, max(-1, i - 400), -1):
            if L[k2][0] == "EVH":
                ev = L[k2][1]
                break
        if ev is not None:
            self.ok("ITEM", "enclosing EVH: event %d handler 0x%08X" % (ev["e"], ev["fn"]))

    # ------------------------------------------------------------------ AURA
    def aura(self, log, L, exits, pos):
        ticks = defaultdict(list)
        for i, (t, d) in enumerate(L):
            if t == "SDO0" and d.get("ret") in (0x0056FD39, 0x0056FFB9):
                e = exits.get(("SDO", d["n"]))
                ticks[(d["u"]["u"], d["a"][0])].append((d, e))
        for (u, sid), lst in ticks.items():
            from calc import evaluate  # noqa: F401  (perdelay of the stock auras is the constant 50)
            p = 50
            prev = None
            for d, e in lst:
                caller = SDO_CALLERS[d["ret"]]
                fr = d["fr"]
                if caller == "SelectedAuraTick":
                    if (fr - 1) % p == 0:
                        self.ok("AURA", "skill %d ticks on the grid (frame = 1 mod %d)" % (sid, p))
                    else:
                        self.bad("AURA", log, d["n"], "skill %d tick at frame %d" % (sid, fr))
                    if prev is not None:
                        gap = fr - prev[0]["fr"]
                        self.c["AURA gaps"]["skill %d: %s" % (sid, gap if gap <= 200 else ">200")] += 1
                        if prev[1] and prev[1].get("s") == d["u"]["s"]:
                            self.ok("AURA", "caster seed unchanged from a tick's exit to the next tick's entry")
                        elif prev[1]:
                            k = SK.steps_between(SK.sd_parse(prev[1]["s"]), SK.sd_parse(d["u"]["s"]), 4096)
                            self.c["AURA seed steps between ticks"][k] += 1
                else:
                    self.ok("AURA", "skill %d select calls (frame mod %d = %d)" % (sid, p, fr % p))
                prev = (d, e)

    # ------------------------------------------------------------------ EV
    def events(self, log, L, exits, pos):
        """per handler call (EVH .. EVR): the STA lines inside, the handler unit's and the other unit's life and
        mana change; per COMBAT_ApplyDamage span (AD0 .. AD1): the order of the dispatched events by unit."""
        stack = []
        ad_open = []
        for i, (t, d) in enumerate(L):
            if t == "AD0":
                ad_open.append(d["n"])
            elif t == "AD1" and ad_open and d.get("k") in ad_open:
                ad_open.remove(d["k"])
            if t == "EVH":
                stack.append(i)
                if d["e"] in (9, 10):
                    self.c["EV kill/killed handler calls"]["event %d %s an AD span" % (
                        d["e"], "inside" if ad_open else "outside")] += 1
            elif t == "EVR" and stack:
                i0 = stack.pop()
                h = L[i0][1]
                fn, ev = h["fn"], h["e"]
                key = "0x%08X event %d" % (fn, ev)
                self.c["EV handler calls"][key] += 1
                sta = [x for tt, x in L[i0 + 1:i] if tt == "STA"]
                for x in sta:
                    who = "other" if x.get("d") == h.get("o") else ("self" if x.get("d") == h["u"]["u"] else "?")
                    self.c["EV STA in handler"]["%s: state %s stat %s len %s on %s" % (
                        key, x.get("state"), x.get("stat"), x.get("len"), who)] += 1
                    if x.get("stat") in (68, 69) and h.get("sv") is not None:
                        self.c["EV STA in handler"]["%s: stat %s val = -sv: %s" % (
                            key, x.get("stat"), x.get("val") == -h["sv"])] += 1
                if not sta:
                    self.c["EV STA in handler"]["%s: none" % key] += 1
                su, ou = h["u"].get("st") or {}, h.get("ot", {}).get("st") or {}
                sr, orr = d.get("st") or {}, d.get("ost") or {}
                dl = SK.stat(sr, 6) - SK.stat(su, 6)
                dm = SK.stat(sr, 8) - SK.stat(su, 8)
                odl = SK.stat(orr, 6) - SK.stat(ou, 6) if ("6" in orr or "6" in ou) else None
                self.c["EV deltas"]["%s: self life %+d mana %+d, other life %s, sv %s" % (
                    key, dl, dm, odl, h.get("sv"))] += 1 if fn in WATCH_FN else 0
            elif t == "AD0":
                e = exits.get(("AD", d["n"]))
                if not e:
                    continue
                j = pos[e["n"]]
                seq = []
                for tt, x in L[i + 1:j]:
                    if tt == "EVH":
                        who = "a" if x["u"]["u"] == d["a"] else ("b" if x["u"]["u"] == d["b"] else "?")
                        seq.append("%s%d" % (who, x["e"]))
                if seq:
                    sq = []
                    for x in seq:                       # fold repeats of one kind
                        if not sq or sq[-1] != x:
                            sq.append(x)
                    self.c["EV order inside AD (a attacker, b defender; event id)"][" ".join(sq)] += 1

    # ------------------------------------------------------------------ FIN
    def finisher(self, log, L, exits, pos):
        """COMBAT_PrgFinisher (PF0 .. PF1): the attacker's seed from the entry to the first entry call (PFC), and per
        entry call (PFC .. PFR) the steps the entry made of its own: the walk from PFC's seed through the nested
        logged spans (DQ, AD, MC exits taken; REL with n >= 1 one step; THR/DRR of the attacker one step)."""
        for i, (t, d) in enumerate(L):
            if t != "PF0":
                continue
            e = exits.get(("PF", d["n"]))
            if not e:
                continue
            j = pos[e["n"]]
            a = d["a"]
            inner = L[i + 1:j]
            calls = [(k, x) for k, (tt, x) in enumerate(inner) if tt == "PFC"]
            seq = " ".join("0x%08X" % x["fn"] for _, x in calls)
            self.c["FIN entry sequences"][seq or "(none)"] += 1
            if not calls:
                if e["sa"] == d["sa"]:
                    self.ok("FIN", "no entry called: attacker seed unchanged")
                else:
                    self.bad("FIN", log, d["n"], "no entry, seed moved")
                continue
            if calls[0][1]["sa"] == d["sa"]:
                self.ok("FIN", "seed at the first entry call = the entry seed")
            else:
                k = SK.steps_between(SK.sd_parse(d["sa"]), SK.sd_parse(calls[0][1]["sa"]), 64)
                self.bad("FIN", log, d["n"], "first entry after %s steps" % k)
            for c_i, (k0, x) in enumerate(calls):
                k1 = next((k for k, (tt, y) in enumerate(inner) if k > k0 and tt == "PFR"), None)
                if k1 is None:
                    continue
                r = inner[k1][1]
                own = self.walk(a, SK.sd_parse(x["sa"]), inner[k0 + 1:k1], exits, SK.sd_parse(r["sa"]))
                self.c["FIN own steps per entry"]["0x%08X: %s" % (x["fn"], own)] += 1
            last_r = [y for tt, y in inner if tt == "PFR"]
            if last_r and last_r[-1]["sa"] == e["sa"]:
                self.ok("FIN", "seed at the exit = the last entry's return")

    def walk(self, a, s, lines, exits, target):
        """the attacker's own steps between its logged observations in `lines`: a span entry naming it (DQ0, AD0,
        MHT0 sa; MC0 the owner's seed; REL the seed before its RangeB) is an observation, a span exit (DQ1, AD1, MHT1
        sa; MC1 so) a boundary taken as given, REL one step; THR/DRR of the attacker one step. Returns the pattern
        'k0 OBS k1 OBS ... kn end', each k the steps of no logged line before the next observation."""
        t = s
        out = []
        for tt, y in lines:
            obs = None
            if tt in ("DQ0", "AD0", "MHT0") and y.get("a") == a:
                obs = SK.sd_parse(y["sa"])
            elif tt == "MC0" and (y.get("o") or {}).get("u") == a:
                obs = SK.sd_parse(y["o"]["s"])
            elif tt == "REL" and y.get("u") == a:
                obs = SK.sd_parse(y["s"])
            if obs is not None:
                k = SK.steps_between(t, obs, 64)
                if k is None:
                    return "off stream before %s" % tt
                out.append("%d %s" % (k, tt))
                t = obs
                if tt == "REL":
                    t = SK.step(t)
                continue
            if tt in ("DQ1", "AD1", "MHT1") and "sa" in y and y.get("k") is not None:
                t = SK.sd_parse(y["sa"])
            elif tt == "MC1" and y.get("so"):
                t = SK.sd_parse(y["so"])
            elif tt == "THR" and y.get("a") == a:
                t = SK.step(t)
            elif tt == "DRR" and y.get("u") == a:
                t = SK.step(t)
        k = SK.steps_between(t, target, 64)
        out.append("%s end" % k)
        # fold the repeated "0 MC0" of a ring
        folded = []
        for x in out:
            if folded and folded[-1][0] == x:
                folded[-1][1] += 1
            else:
                folded.append([x, 1])
        return " ".join(x if c == 1 else "%s x%d" % (x, c) for x, c in folded)

    # ------------------------------------------------------------------ SUM
    def summons(self, log, L, exits, pos):
        for i, (t, d) in enumerate(L):
            if t != "SDO0" or d["a"][0] not in (221, 70, 80):
                continue
            e = exits.get(("SDO", d["n"]))
            if not e:
                continue
            j = pos[e["n"]]
            seq = []
            for tt, x in L[i + 1:j]:
                if tt in ("SP0", "SP1", "SL0", "SL1", "PA0", "PA1", "RSK0", "RSK1"):
                    seq.append(tt)
            self.c["SUM line order in the do (skill %d)" % d["a"][0]][" ".join(seq) or "(none)"] += 1
            sp = [x for tt, x in L[i + 1:j] if tt == "SP0"]
            sl = [x for tt, x in L[i + 1:j] if tt == "SL0"]
            pa = [x for tt, x in L[i + 1:j] if tt == "PA0"]
            for x in sp:
                blk = bytes.fromhex(x["blk"])
                w = struct.unpack_from("<10I", blk.ljust(40, b"\0"))
                self.c["SUM SP block words (skill %d)" % d["a"][0]][" ".join("%x" % v for v in w[2:])] += 1
            for x in sl:
                self.c["SUM SL args (skill %d): lvl, skill level" % d["a"][0]][
                    "%s, %s (do level %d)" % (x["a"][1], x["a"][2], d["a"][1])] += 1
            for x in pa:
                self.c["SUM PetAdd args (skill %d): type, max" % d["a"][0]]["%s, %s" % (x["a"][1], x["a"][2])] += 1
            if e.get("c4") is not None:
                self.c["SUM c4 bit 6 after the do (skill %d)" % d["a"][0]][
                    "entry %d exit %d" % (bool(d["c4"] & 0x40), bool(e["c4"] & 0x40))] += 1

    # ------------------------------------------------------------------ MISC
    def misc(self, log, L, exits, pos):
        last_dly = {}
        ptr2id = {}
        open_sdo = []
        for i, (t, d) in enumerate(L):
            if t in ("SST0", "SDO0"):
                ptr2id[d["u"]["u"]] = (d["u"]["t"], d["u"]["id"])
            if t == "CU0":
                e = exits.get(("CU", d["n"]))
                self.c["MISC CanUse"]["calls by unit type %d%s" % (d["u"]["t"], " (client)" if d.get("cl") else "")] += 1
                if e and not d.get("cl"):
                    self.c["MISC CanUse"]["request calls: caster seed at the exit %s the entry's" % (
                        "=" if e.get("s") == d["u"]["s"] else "!=")] += 1
                if e and d.get("cl") and e["r"] == 8:
                    ld = last_dly.get((d["u"]["t"], d["u"]["id"]))
                    if ld:
                        self.c["MISC CanUse"]["client code 8 for skill %s, last delay set by skill %s (same: %s)" % (
                            d["sk"], ld, d["sk"] == ld)] += 1
            elif t == "DLY":
                sdo = open_sdo[-1] if open_sdo else None
                key = ptr2id.get(d["u"], ("ptr", d["u"]))
                if sdo:
                    last_dly[key] = sdo["a"][0]
                self.c["MISC DLY"]["unit type %s" % (key[0],)] += 1
            elif t == "SDO0":
                open_sdo.append(d)
                if d["u"]["t"] == 1:
                    self.c["MISC monster do"]["bit 6 at the do entry: %d" % bool(d["c4"] & 0x40)] += 1
            elif t == "SDO1":
                if open_sdo and open_sdo[-1]["n"] == d.get("k"):
                    open_sdo.pop()
            if t == "SST0":
                self.c["MISC start modes"]["unit type %d mode %d" % (d["u"]["t"], d["u"]["m"])] += 1
                self.c["MISC start noCost"]["noCost %d" % d["a"][2]] += 1
                if d["u"]["t"] == 1:
                    self.c["MISC monster start"]["bit 6 at the start entry: %d" % bool(d["c4"] & 0x40)] += 1
                    self.c["MISC monster start by mode"]["mode %d bit 6 %d" % (d["u"]["m"], bool(d["c4"] & 0x40))] += 1
                    if d["u"]["m"] == 14:
                        self.c["MISC monster start by mode"]["mode 14: skill %d" % d["a"][0]] += 1
            if t == "SDO0":
                self.c["MISC do modes"]["unit type %d mode %d" % (d["u"]["t"], d["u"]["m"])] += 1
            if t == "PF0":
                sdo = open_sdo[-1] if open_sdo else None
                self.c["MISC finisher inside"]["%s" % ("SrvDo of skill %d" % sdo["a"][0] if sdo else "no SrvDo")] += 1
            if t == "SP0":
                e = exits.get(("SP", d["n"]))
                if e and e.get("so"):
                    self.c["MISC summon"]["owner seed at SpawnOwnedMonster's exit %s its entry" % (
                        "=" if e["so"] == d["o"]["s"] else "!=")] += 1
            if t in ("SST0", "SDO0") and d["a"][0] in TIER_A and d["u"]["t"] == 0:
                e = exits.get((t[:3], d["n"]))
                if e:
                    sig = Counter()
                    for tt, x in L[i + 1:pos[e["n"]]]:
                        if tt in ("MC0", "MCB0", "REL", "MHT0", "DQ0", "AD0", "SP0", "SST0", "SDO0"):
                            sig[tt] += 1
                        elif tt == "THR" and x.get("a") == d["u"]["u"]:
                            sig["THR"] += 1
                        elif tt == "STA":
                            sig["STA %s/%s" % (x.get("state"), x.get("len"))] += 1
                    self.c["TIER %s skill %d level-free line signature" % (t[:3], d["a"][0])][
                        " ".join("%s:%d" % kv for kv in sorted(sig.items())) or "(none)"] += 1
                    self.c["TIER levels"]["%s skill %d level %d" % (t[:3], d["a"][0], d["a"][1])] += 1
                    # the caster's steps from entry to exit less the nested logged draws (skills.py's SDO.seed walk:
                    # MC owner steps o.s -> so, THR/DRR of the caster, REL), as "total - logged = own"
                    u = d["u"]["u"]
                    tot = SK.steps_between(SK.sd_parse(d["u"]["s"]), SK.sd_parse(e["s"]), 4096)
                    lg = 0
                    for tt, x in L[i + 1:pos[e["n"]]]:
                        if tt == "MC0" and (x.get("o") or {}).get("u") == u:
                            ee = exits.get(("MC", x["n"]))
                            if ee and ee.get("so"):
                                lg += SK.steps_between(SK.sd_parse(x["o"]["s"]), SK.sd_parse(ee["so"]), 64) or 0
                        elif tt == "THR" and x.get("a") == u:
                            lg += 1
                        elif tt == "DRR" and x.get("u") == u:
                            lg += 1
                        elif tt == "REL" and x.get("u") == u:
                            lg += 1
                    own = None if tot is None else tot - lg
                    self.c["TIER own caster steps (total - logged)"]["%s skill %d: %s" % (t[:3], d["a"][0], own)] += 1
            if t in ("SST0", "SDO0"):
                e = exits.get((t[:3], d["n"]))
                if e:
                    kinds = Counter()
                    for tt, x in self.direct(L, i, pos[e["n"]], exits, pos):
                        if tt in ("DQ0", "AD0", "MC0", "STA", "SP0", "MHT0"):
                            kinds[tt] += 1
                    for k in kinds:
                        self.c["MISC output lines directly inside"]["%s %s" % (t[:3], k)] += 1
            if t == "EVH" and d["fn"] in (0x005C0470, 0x005C05A0):
                j = next((k for k in range(i + 1, min(len(L), i + 3000)) if L[k][0] == "EVR"
                          and L[k][1].get("k") == d["n"]), None)
                if j is None:
                    continue
                casts = [(k, x) for k, (tt, x) in enumerate(L[i + 1:j], i + 1) if tt == "SDO0"
                         and x.get("ret") == 0x005FDC34 and x["u"]["u"] == d["u"]["u"]]
                if len(casts) != 1:
                    continue
                k0, c0 = casts[0]
                c1 = exits.get(("SDO", c0["n"]))
                if not c1:
                    continue
                a = SK.steps_between(SK.sd_parse(d["u"]["s"]), SK.sd_parse(c0["u"]["s"]), 64)
                b = SK.steps_between(SK.sd_parse(c1["s"]), SK.sd_parse(L[j][1]["su"]), 64)
                between = [tt for tt, x in L[i + 1:k0] if tt in ("THR", "DRR", "REL", "MC0", "AD0", "DQ0", "SST0")]
                self.c["MISC item cast steps"]["handler 0x%08X: caster steps EVH->cast %s, cast exit->EVR %s, "
                                               "logged draw lines before the cast %d" % (d["fn"], a, b, len(between))] += 1

    def report(self):
        for sid in range(len(self.T.sk)):
            self.c["MISC table ItemEffect"]["value %d" % self.R.item_effect(sid)] += 1
        for sid in (98, 102):
            self.c["MISC table immediate"]["skill %d immediate %d" % (sid, bool(self.R.r(sid)[5] & 0x80))] += 1
        bad = 0
        for chk in sorted(self.c):
            print("== %s" % chk)
            for k, v in sorted(self.c[chk].items(), key=lambda kv: str(kv[0])):
                print("  %7d  %s" % (v, k))
            for b in self.brk.get(chk, ()):
                print("  break: %s" % b)
            bad += self.c[chk].get("BREAK", 0)
        print("SURVEY s2a breaks=%d" % bad)
        return bad


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    args = argv[1:]
    excel = SK.DEFAULT_EXCEL
    if "--excel" in args:
        i = args.index("--excel")
        excel = args[i + 1]
        del args[i:i + 2]
    C = S2A(SK.Tables(excel))
    for p in args:
        C.run(p)
    return 1 if C.report() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

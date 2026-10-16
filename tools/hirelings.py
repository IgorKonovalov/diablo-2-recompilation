#!/usr/bin/env python3
"""Hireling model and run checker (plan 0033 Phase 2), from docs/findings/hirelings/0001-hirelings.md.

    python3 -I tools/hirelings.py check  <excel-dir> LOG...          # every logged build, roll, hire, level, load
    python3 -I tools/hirelings.py list   <excel-dir> S SELLER VF DIFF PLVL [ACT]   # predict a hire list
    python3 -I tools/hirelings.py merc   <excel-dir> VF ID EXP           # a loaded mercenary: level and stats

The model (no game state beyond the logged inputs):
- HIRE_BuildStock(S, seller, vf): the seller's Normal row (HIRELING_NextBySeller, Difficulty 1) gives the name range
  first..last, n = last - first + 1; for i < n (and first + i <= last) entry i gets name first + i and the low word
  of one step of S; then 10 picks Range(S, n) with a +1 probe (wrapping) past entries listed or hired.
- HIRELING_RollEntry(vf, plvl, seed, act, diff): Init(seed); the rows of (version, act + 1, diff + 1) that share the
  first such row's Level; draw 1 Range over them; draw 2 a step, L = max(2, plvl - 5 + low mod 5); the 15-dword
  output (Id, L, life, str, dex, price, experience, defence, damage, share, resist, HireDesc, 1, 0).
- MERC_SetLevel(vf, id, L): the row of HIRELING_GetRecord(vf, id, L), d = L - Level, the stats with truncating
  division (eighths for Str/Dex/Dmg, quarters for Resist), clamps 10, 10, 40 life, 0/1 damage, 0; nextexp; the
  skills Level_i + floor(LvlPerLvl_i d / 32) capped at 32 when reqlevel <= L.
- D2S_ReadMercHeader: the name clamp, the level loop over ExpForLevel(L + 1, Exp/Lvl of band L) <= exp, L <= 99,
  and MERC_Create's classic act test.
The NPC seed S is a boundary (architect ruling, plan 0033 log): asserted at each HIRE_BuildStock entry against the
chain of this model's own draws since the last known S (VSC1, or the exit of a vendor build, whose draws are
plan 0031's model and an oracle here). One check per game that S = Init(low of the game seed's step at
NPCSTORE_CtlCreate), and which game-seed draw that is under -seed N.
Logs: tools/gdb/hirelings.gdb (tools/gdb/hirelings.py lines, with vendors.py and pilot.py). Stdlib only.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
import hireling_survey  # noqa: E402
from rng import INIT_HIGH, step  # noqa: E402

M32 = 0xFFFFFFFF
SELLERS = {150: "Kashya", 198: "Greiz", 252: "Asheara", 515: "Qual-Kehk"}
HIRE_CLASSES = {271, 338, 359, 560, 561}
RET_LIST_DRAW = 0x004B5EAC      # sub_004B5C60_ClientHireListDraw
RET_CLIENT_INIT = 0x004B10F8    # sub_004B1090_ClientMercInit
RET_MERC_INIT = 0x0057337B      # MERC_Init
RET_HIRE = 0x0057727F           # HIRE_Hire
RET_SL_LOAD = 0x0056ABC7        # MERC_SetLevel from D2S_ReadMercHeader
RET_SL_HIRE = 0x005733F8        # from MERC_Init (fresh hire)
RET_SL_ADDEXP = 0x0057E955      # from MERC_AddExp
RET_HB_SEND = 0x005767F0        # HIRE_BuildStock from HIRE_SendList
RET_HB_REBUILD = 0x005770CE     # from HIRE_RebuildIfEmpty
RET_HB_STORE = 0x00578C04       # from NPC_OpenStore


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def tdiv(a, b):
    """C division, truncating toward zero."""
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


class Seed:
    def __init__(self, low, high=INIT_HIGH):
        self.low, self.high = low & M32, high & M32

    def step(self):
        self.low, self.high = step(self.low, self.high)
        return self.low

    def range(self, n):
        if n & 0x80000000 or n == 0:
            return 0
        return self.step() % n

    def __str__(self):
        return "%08x:%08x" % (self.low, self.high)


def parse_seed(s):
    lo, hi = (int(x, 16) for x in s.split(":"))
    return Seed(lo, hi)


class Tables:
    def __init__(self, excel_dir):
        d = hireling_survey.Data(excel_dir)
        self.rows = d.rec
        for r in self.rows:
            r["first"], r["last"] = d.names(r)
        _, _, recs, _ = eb.load_table(excel_dir, "skills")
        self.reqlevel = [int.from_bytes(b[0x174:0x176], "little", signed=True) for b in recs]
        self.nskills = len(recs)
        self.skill_names = d.skills
        self.max_lvl = 99           # experience.txt MaxLvl, Amazon column (sub_00611830_ExpMaxLevel(0))
        with open(os.path.join(excel_dir, "experience.txt"), errors="replace") as fh:
            for ln in fh:
                c = ln.rstrip("\r\n").split("\t")
                if c[0] == "MaxLvl":
                    self.max_lvl = int(c[1])

    @staticmethod
    def ver(vf):
        return 100 if vf else 0

    def get_record(self, vf, hid, lvl):
        """HIRELING_GetRecord: the row index of Id hid (version of vf) whose Level band holds lvl."""
        if hid > 255:
            return None
        v = self.ver(vf)
        first = next((i for i, r in enumerate(self.rows) if r["Id"] == hid and r["Version"] == v), None)
        if first is None:
            return None
        prev = None
        for i in range(first, len(self.rows)):
            r = self.rows[i]
            if r["Id"] == hid and r["Version"] == v:
                if prev is not None and lvl < r["Level"]:
                    return prev
                prev = i
            elif hid < r["Id"]:
                return prev
        return prev

    def next_by_act_diff(self, vf, act, diff, prev):
        v = self.ver(vf)
        for i in range(0 if prev is None else prev + 1, len(self.rows)):
            r = self.rows[i]
            if (r["Version"] == v and r["Act"] == act + 1 and r["Difficulty"] == diff + 1
                    and (prev is None or r["Level"] == self.rows[prev]["Level"])):
                return i
        return None

    def type_rows(self, vf, act, diff):
        out, i = [], self.next_by_act_diff(vf, act, diff, None)
        while i is not None:
            out.append(i)
            i = self.next_by_act_diff(vf, act, diff, i)
        return out

    def seller_row(self, vf, seller, diff=0):
        v = self.ver(vf)
        return next((i for i, r in enumerate(self.rows) if r["Version"] == v and r["Seller"] == seller
                     and r["Difficulty"] == diff + 1), None)

    def get_act(self, vf, name):
        """HIRELING_GetAct(vf, 0, name): Act - 1 of the first row whose name range holds name, else 0."""
        for r in self.rows:
            if r["first"] <= name <= r["last"]:
                return r["Act"] - 1
        return 0


def exp_for_level(lvl, e):
    return s32(s32(s32((lvl + 1) * e) * lvl) * lvl)


def build_stock(t, S, seller, vf):
    """HIRE_BuildStock on a fresh table: [[name, seed, hired, listed] x 69], S stepped in place."""
    r = t.rows[t.seller_row(vf, seller)]
    first, last = r["first"], r["last"]
    n = last - first + 1
    tab = [[0, 0, 0, 0] for _ in range(69)]
    i = 0
    while i < n and first + i <= last:
        tab[i] = [first + i, S.step(), 0, 0]
        i += 1
    for _ in range(10):
        u = S.range(n)
        v = u
        while tab[v][3] or tab[v][2]:
            v += 1
            if v >= n:
                v = 0
            if v == u:
                return tab, n
        tab[v][3] = 1
    return tab, n


def parse_table(hexs):
    b = bytes.fromhex(hexs)
    return [[int.from_bytes(b[16 * i:16 * i + 2], "little"), int.from_bytes(b[16 * i + 4:16 * i + 8], "little"),
             int.from_bytes(b[16 * i + 8:16 * i + 12], "little"), int.from_bytes(b[16 * i + 12:16 * i + 16], "little")]
            for i in range(69)]


def roll_entry(t, vf, plvl, seed, act, diff):
    """HIRELING_RollEntry: (return value, 15 dwords) with the last dword's low word only (the code writes a word)."""
    s = Seed(seed)
    rows = t.type_rows(vf, act, diff)
    if not rows:
        return 0, None
    r = t.rows[rows[s.range(len(rows))]]
    low = s.step()
    lv = s32(plvl - 5 + (low % 5))
    if lv < 2:
        lv = 2
    d = s32(lv - r["Level"])
    hp = s32(r["HP"] + s32(r["HP/Lvl"] * d))
    st = s32(r["Str"] + (s32(r["Str/Lvl"] * d) >> 3))
    dx = s32(r["Dex"] + (s32(r["Dex/Lvl"] * d) >> 3))
    price = tdiv(s32(s32(15 * d + 100) * r["Gold"]), 100)
    ex = exp_for_level(lv, r["Exp/Lvl"])
    df = s32(r["Defense"] + s32(r["Def/Lvl"] * d))
    dmn = s32(r["Dmg-Min"] + (s32(r["Dmg/Lvl"] * d) >> 3))
    dmx = s32(r["Dmg-Max"] + (s32(r["Dmg/Lvl"] * d) >> 3))
    o = [r["Id"], lv, max(40, hp), max(10, st), max(10, dx), price if r["Gold"] <= price else r["Gold"],
         max(0, ex), max(0, df), max(0, dmn), max(1, dmx), max(0, r["Share"]), max(0, r["Resist"]),
         r["HireDesc"], 1, 0]
    return 1, o


def set_level(t, vf, hid, lvl):
    """MERC_SetLevel: (row index, {stat: value}, [[skill, level], ...]) or (None, None, None)."""
    ri = t.get_record(vf, hid, lvl)
    if ri is None:
        return None, None, None
    r = t.rows[ri]
    d = s32(lvl - r["Level"])
    st = {12: lvl}
    st[30] = exp_for_level(lvl + 1, r["Exp/Lvl"]) if lvl < t.max_lvl - 1 else 0
    st["13min"] = exp_for_level(lvl, r["Exp/Lvl"])
    st[0] = max(10, r["Str"] + tdiv(s32(r["Str/Lvl"] * d), 8))
    st[2] = max(10, r["Dex"] + tdiv(s32(r["Dex/Lvl"] * d), 8))
    hp = s32(s32(s32(r["HP/Lvl"] << 8) * d) + s32(r["HP"] << 8))
    st[7] = st[6] = max(0x2800, hp)
    st[31] = max(0, s32(r["Def/Lvl"] * d + r["Defense"]))
    st[23] = max(0, r["Dmg-Min"] + tdiv(s32(r["Dmg/Lvl"] * d), 8))
    st[24] = max(1, r["Dmg-Max"] + tdiv(s32(r["Dmg/Lvl"] * d), 8))
    st[19] = max(0, s32(r["AR/Lvl"] * d + r["AR"]))
    res = max(0, r["Resist"] + tdiv(s32(r["Resist/Lvl"] * d), 4))
    for k in (39, 41, 43, 45):
        st[k] = res
    st[74] = max(0, tdiv(st[7], 2000))
    sk = []
    for i in range(1, 7):
        sid = r["Skill%d" % i]
        if sid < 1 or sid >= t.nskills or r["Mode%d" % i] >= 16:
            break
        if lvl < t.reqlevel[sid]:
            continue
        sl = (s32(r["LvlPerLvl%d" % i] * d) >> 5) + r["Level%d" % i]
        sl = max(0, sl)
        sl = min(sl, 32)
        if sl > 0:
            sk.append([sid, sl])
    return ri, st, sk


def load_level(t, vf, hid, exp):
    """D2S_ReadMercHeader's level loop."""
    lvl = 1
    ri = t.get_record(vf, hid, 1)
    while ri is not None:
        nxt = lvl + 1
        if nxt > t.max_lvl or exp < exp_for_level(nxt, t.rows[ri]["Exp/Lvl"]) & M32:
            break
        lvl = nxt
        ri = t.get_record(vf, hid, lvl)
    return lvl


def parse_log(path):
    seed, events = None, []
    pat = re.compile(r"([A-Z][A-Z0-9]*) (\{.*\})\s*$")
    with open(path, errors="replace") as fh:
        for ln in fh:
            if ln.startswith("# d2run"):
                m = re.search(r"seed=(\d+)", ln)
                seed = int(m.group(1)) if m else None
                continue
            m = pat.match(ln)
            if not m:
                if ln.startswith("LOGERR"):
                    events.append(("LOGERR", {"text": ln.strip()}))
                continue
            try:
                events.append((m.group(1), json.loads(m.group(2))))
            except ValueError:
                pass
    return seed, events


class Checker:
    def __init__(self, t, verbose=False):
        self.t = t
        self.v = verbose
        self.n = collections.Counter()
        self.bad = 0
        self.notes = collections.Counter()
        self.lvl_off = collections.Counter()       # (L - plvl) of every list entry the client drew
        self.lists = collections.Counter()         # (seller, version, difficulty) -> builds
        self.stats_cases = collections.Counter()
        self.mf = []

    def fail(self, path, msg):
        self.bad += 1
        if self.bad <= 60:
            print("MISMATCH %s: %s" % (os.path.basename(path), msg))

    def ok(self, key, cond, path, msg):
        self.n[key] += 1
        if not cond:
            self.fail(path, msg())
        return cond

    def check(self, path):
        t = self.t
        nseed, ev = parse_log(path)
        S = None                 # predicted NPC seed (None: unknown, resynchronise at the next logged value)
        vf = diff = None
        tabs = {}                # seller -> model table
        pending_hb = None
        hire = None              # the current hire in progress
        merc = {}                # current mercenary: id, prev exp
        mrh = None
        vendor = False
        for i, (tag, d) in enumerate(ev):
            if tag == "LOGERR":
                self.fail(path, d["text"])
            elif tag == "VGAME":
                vf, diff = d["exp"], d["diff"]
                tabs, S, merc, hire = {}, None, {}, None
                self.n["games"] += 1
            elif tag == "VSC0":
                gs = parse_seed(d["gs"])
                k = None
                if nseed is not None:
                    s = Seed(nseed)
                    for j in range(64):
                        if (s.low, s.high) == (gs.low, gs.high):
                            k = j
                            break
                        s.step()
                low = gs.step()
                pred = Seed(low)
                nxt = ev[i + 1] if i + 1 < len(ev) else (None, {})
                if nxt[0] == "VSC1":
                    self.ok("NPC seed = Init(low of the game-seed step)", nxt[1]["S"] == str(pred), path,
                            lambda: "VSC1 S %s, model %s" % (nxt[1]["S"], pred))
                    self.ok("NPC seed from game-seed draw 3 (gs after 2 steps from Init(-seed))", k == 2, path,
                            lambda: "game seed at NPCSTORE_CtlCreate is draw index %s from Init(%s)" % (k, nseed))
                    S = parse_seed(nxt[1]["S"])
            elif tag in ("BS0", "GB0"):
                vendor = True            # vendor draws on S: plan 0031's model; an oracle here
            elif tag in ("BSX", "GBX"):
                if d.get("S"):
                    S = parse_seed(d["S"])
                    self.n["S resynchronised after a vendor build (oracle)"] += 1
                vendor = False
            elif tag == "HBS":
                if not vendor and S is not None:
                    self.ok("S at HIRE_BuildStock entry = the model's chain", d["S"] == str(S), path,
                            lambda: "HBS %s S %s, chain %s" % (d["cls"], d["S"], S))
                else:
                    self.n["S at HIRE_BuildStock entry taken from the log (chain broken)"] += 1
                S = parse_seed(d["S"])
                if d["built"] == 0 and d["tab"] == 0:
                    tab, n = build_stock(t, S, d["cls"], vf)
                    pending_hb = (d, tab, n)
                    self.lists[(SELLERS.get(d["cls"], d["cls"]), "exp" if vf else "classic", diff)] += 1
                    self.notes["build trigger %s" % {RET_HB_SEND: "HIRE_SendList (first interaction)",
                                                     RET_HB_REBUILD: "HIRE_RebuildIfEmpty",
                                                     RET_HB_STORE: "NPC_OpenStore"}.get(d["ret"], hex(d["ret"]))] += 1
                    if d["ret"] == RET_HB_REBUILD:
                        self.ok("rebuild only when no listed, unhired entry is left",
                                tabs.get(d["cls"]) is not None and not any(
                                    e[3] and not e[2] for e in tabs[d["cls"]]), path,
                                lambda: "rebuild of %s with entries left" % d["cls"])
                else:
                    pending_hb = None
            elif tag == "HBT" and pending_hb:
                hb, tab, n = pending_hb
                pending_hb = None
                got = parse_table(d["tab"])
                self.ok("hire table (69 entries: name, seed, hired, listed)", got == tab, path,
                        lambda: "HBT %s table differs at %s" % (
                            d["cls"], [k for k in range(69) if got[k] != tab[k]][:5]))
                self.ok("S after HIRE_BuildStock (n + 10 draws)", d["S"] == str(S), path,
                        lambda: "HBT %s S %s, model %s (n %d)" % (d["cls"], d["S"], S, n))
                self.n["draws on S in hire builds"] += n + 10
                tabs[d["cls"]] = got
                if hb["ret"] == RET_HB_SEND:
                    self.n["first builds"] += 1
            elif tag == "HBX":
                pass
            elif tag == "HRE":
                r, o = roll_entry(t, d["vf"], d["plvl"], d["seed"], d["act"], d["diff"])
                got = list(d["o"])
                got[14] &= 0xFFFF
                where = {RET_LIST_DRAW: "client list draw", RET_CLIENT_INIT: "client merc init",
                         RET_MERC_INIT: "MERC_Init", RET_HIRE: "HIRE_Hire"}.get(d["ret"], hex(d["ret"]))
                self.ok("HIRELING_RollEntry (%s)" % where, r == d["r"] and (r == 0 or o == got), path,
                        lambda: "HRE %s seed %d act %d diff %d plvl %d: model %s %s, log %s %s" % (
                            where, d["seed"], d["act"], d["diff"], d["plvl"], r, o, d["r"], got))
                if d["ret"] == RET_LIST_DRAW and o:
                    self.lvl_off[o[1] - d["plvl"]] += 1
                    listed = {e[1] for tb in tabs.values() for e in tb if e[3] and not e[2]}
                    self.ok("client list entry is a listed, unhired entry of the table", d["seed"] in listed, path,
                            lambda: "list draw of seed %d not listed" % d["seed"])
                if d["ret"] == RET_MERC_INIT and o:
                    merc["roll"] = o
                if d["ret"] == RET_HIRE and hire is not None:
                    hire["price"] = o[5] if o else None
            elif tag == "HHI":
                tb = tabs.get(d["cls"])
                e = next((e for e in tb if e[0] == d["name"]), None) if tb else None
                hire = {"cls": d["cls"], "name": d["name"], "entry": e, "gold": d["gold"], "bank": d["bank"]}
                if e is not None:
                    self.notes["hire of a %s entry" % ("listed" if e[3] else "not listed")] += 1
            elif tag == "HHX" and hire is not None:
                if d["r"]:
                    self.n["hires"] += 1
                    e = hire["entry"]
                    paid = hire["gold"] + hire["bank"] - d["gold"] - d["bank"]
                    self.ok("hire price paid = RollEntry price", paid == hire.get("price"), path,
                            lambda: "paid %d, price %s" % (paid, hire.get("price")))
                    self.ok("gold first, then the stash", d["gold"] == max(0, hire["gold"] - paid)
                            and d["bank"] == hire["bank"] - max(0, paid - hire["gold"]), path,
                            lambda: "gold %d -> %d, bank %d -> %d, price %d" % (
                                hire["gold"], d["gold"], hire["bank"], d["bank"], paid))
                else:
                    self.notes["hire refused"] += 1
                hire = None
            elif tag == "MIN":
                merc = {"cls": d["merc"]["cls"], "init": d}
                if d["id"] == -1 and hire is not None and hire["entry"] is not None:
                    self.ok("MERC_Init {name, seed} = the hired table entry", d["name"] == hire["name"]
                            and d["seed"] == hire["entry"][1], path,
                            lambda: "MIN name %d seed %d, entry %s" % (d["name"], d["seed"], hire["entry"]))
                    rr = t.rows[t.seller_row(vf, hire["cls"])]
                    self.ok("hired class = Class of the seller's Normal row", d["merc"]["cls"] == rr["Class"],
                            path, lambda: "class %d, row %d" % (d["merc"]["cls"], rr["Class"]))
                    merc["src"] = "hire"
                    hire["entry"][2] = 1        # hired before HIRE_RebuildIfEmpty runs (inside HIRE_Hire)
                elif d["id"] != -1:
                    merc["src"] = "load"
                    merc["id"] = d["id"]
            elif tag == "MRH":
                h = bytes.fromhex(d["hdr"])
                flags, seed = int.from_bytes(h[0:4], "little"), int.from_bytes(h[4:8], "little")
                name, hid = int.from_bytes(h[8:10], "little"), int.from_bytes(h[10:12], "little")
                exp = int.from_bytes(h[12:16], "little")
                if seed == 0 and name == 0 and exp == 0:
                    mrh = None
                    continue
                bi = t.get_record(vf, hid, 1)
                b = t.rows[bi]
                nm = (name + b["first"]) & 0xFFFF
                if nm > b["last"]:
                    nm = b["first"]
                mrh = {"id": hid, "exp": exp, "name": nm, "seed": seed, "dead": bool(flags & 0x10000),
                       "L": load_level(t, vf, hid, exp), "cls": b["Class"]}
                self.n["merc headers read"] += 1
            elif tag == "MCA" and mrh is not None:
                want_act = t.get_act(d["vf"], mrh["name"])
                self.ok("MERC_Create: the mercenary's act = HIRELING_GetAct(name)", d["mact"] == want_act, path,
                        lambda: "mact %d, model %d" % (d["mact"], want_act))
                mrh["created"] = bool(d["vf"]) or (d["mact"] >= 0 and d["pact"] == d["mact"])
                mrh["pact"] = d["pact"]
            elif tag == "MCX" and mrh is not None:
                got = d["merc"] is not None
                self.ok("MERC_Create made the mercenary (classic: only in its own act)",
                        got == mrh.get("created", True), path,
                        lambda: "created %s, model %s (pact %s)" % (got, mrh.get("created"), mrh.get("pact")))
                self.notes["load: %s %s" % ("expansion" if vf else "classic",
                                            "created" if got else "not created (act %s)" % mrh.get("pact"))] += 1
                if got:
                    self.ok("loaded class = the saved Id's row Class", d["merc"]["cls"] == mrh["cls"], path,
                            lambda: "class %d, model %d" % (d["merc"]["cls"], mrh["cls"]))
                    merc = {"cls": d["merc"]["cls"], "id": mrh["id"], "src": "load", "hdr": mrh}
                else:
                    mrh = None
            elif tag == "MSL":
                merc["L"], merc["ret"] = d["L"], d["ret"]
                if d["ret"] == RET_SL_LOAD and mrh is not None:
                    self.ok("loaded level from experience (ExpForLevel loop)", d["L"] == mrh["L"], path,
                            lambda: "L %d, model %d (id %d exp %d)" % (d["L"], mrh["L"], mrh["id"], mrh["exp"]))
                    merc["id"], merc["prev13"] = mrh["id"], mrh["exp"]
                elif d["ret"] == RET_SL_HIRE and merc.get("roll"):
                    merc["id"], merc["prev13"] = merc["roll"][0], merc["roll"][6]
                    self.ok("fresh hire level = RollEntry level", d["L"] == merc["roll"][1], path,
                            lambda: "L %d, roll %s" % (d["L"], merc["roll"]))
                elif d["ret"] == RET_SL_ADDEXP:
                    merc["prev13"] = None
                    self.notes["level-up in play (MERC_AddExp)"] += 1
            elif tag == "MSR":
                merc["row"] = d["row"]
            elif tag == "MSX":
                hid = merc.get("id")
                if hid is None:
                    self.notes["MERC_SetLevel with an unknown Id"] += 1
                    continue
                ri, want, sk = set_level(t, vf, hid, merc["L"])
                self.ok("MERC_SetLevel row (HIRELING_GetRecord band)", ri == merc.get("row"), path,
                        lambda: "row %s, model %s (id %d L %d)" % (merc.get("row"), ri, hid, merc["L"]))
                got = {s: v for s, p, v in d["b"] if p == 0}
                m13 = want.pop("13min")
                # a stat set to 0 has no entry in the list (the stat list keeps non-zero values only)
                bad = [(k, got.get(k), v) for k, v in sorted(want.items()) if got.get(k, 0) != v]
                self.n["stats clamped to 0 (absent from the list)"] += sum(1 for k, v in want.items()
                                                                        if v == 0 and k not in got)
                if merc.get("prev13") is not None:
                    w13 = max(merc["prev13"], m13)
                    if got.get(13) != w13:
                        bad.append((13, got.get(13), w13))
                r = t.rows[ri]
                dd = merc["L"] - r["Level"]
                self.stats_cases[("d<0" if dd < 0 else "d=0" if dd == 0 else "d>0", merc.get("src"))] += 1
                if dd > 0 and tdiv(r["Resist/Lvl"] * dd, 4) != tdiv(r["Resist/Lvl"] * dd, 8):
                    self.n["levels where Resist/Lvl /4 and /8 differ"] += 1
                if dd < 0 and any(tdiv(r[c] * dd, 8) != (r[c] * dd) >> 3 for c in ("Str/Lvl", "Dex/Lvl", "Dmg/Lvl")):
                    self.n["levels where truncation and floor differ (d < 0)"] += 1
                self.ok("MERC_SetLevel stats", not bad, path,
                        lambda: "id %d L %d (%s): [stat, log, model] %s" % (hid, merc["L"], merc.get("src"), bad))
                gsk = {a: b for a, b in d["sk"]}
                if merc.get("ret") != RET_SL_ADDEXP:
                    miss = [(a, gsk.get(a), b) for a, b in sk if gsk.get(a) != b]
                    self.ok("MERC_SetLevel skills", not miss, path,
                            lambda: "id %d L %d: [skill, log, model] %s; log %s" % (hid, merc["L"], miss, d["sk"]))
                    extra = sorted(set(gsk) - {a for a, _ in sk})
                    if extra:
                        self.notes["skills not from Hireling (MonStats): %s" % extra] += 1
                if merc.get("src") == "load":
                    mrh = None
            elif tag == "MFK":
                k = d.get("killer") or {}
                if k.get("type") == 1 and k.get("cls") in HIRE_CLASSES:
                    ow = d.get("owner") or {}
                    omf = ow.get("mfcall", ow.get("mf"))
                    self.mf.append((k["cls"], d.get("own"), ow.get("type"), omf, ow.get("mffull"), d["r"]))
                    self.ok("a mercenary's kill: magic find = its own stat 80 + its owner's (the player)",
                            ow.get("type") == 0 and d["r"] == (d.get("own") or 0) + (omf or 0)
                            and ("mffull" not in ow or ow["mffull"] == omf), path,
                            lambda: "MFK %s" % d)


def cmd_check(excel, paths, verbose):
    t = Tables(excel)
    c = Checker(t, verbose)
    for p in paths:
        c.check(p)
    print("logs %d" % len(paths))
    for k, v in sorted(c.n.items()):
        print("  %-80s %d" % (k, v))
    print("hire lists built (seller, game, difficulty):")
    for k, v in sorted(c.lists.items(), key=str):
        print("  %-40s %d" % (k, v))
    print("list entry level minus player level (client draws):",
          " ".join("%+d:%d" % kv for kv in sorted(c.lvl_off.items())))
    print("MERC_SetLevel cases (d sign, source):", dict(c.stats_cases))
    for k, v in sorted(c.notes.items()):
        print("  note: %s: %d" % (k, v))
    if c.mf:
        print("mercenary kills (class, own mf, owner type, owner mf read, owner full-list stat 80, total):",
              c.mf[:10], "... %d" % len(c.mf))
    print("hirelings: %d mismatches" % c.bad)
    return 0 if c.bad == 0 and sum(c.n.values()) else 1


def main(argv):
    if len(argv) >= 2 and argv[0] == "check":
        v = "-v" in argv
        args = [a for a in argv[1:] if a != "-v"]
        return cmd_check(args[0], args[1:], v)
    if len(argv) >= 7 and argv[0] == "list":
        t = Tables(argv[1])
        S = parse_seed(argv[2])
        seller, vf, diff, plvl = (int(x) for x in argv[3:7])
        tab, n = build_stock(t, S, seller, vf)
        act = int(argv[7]) if len(argv) > 7 else t.rows[t.seller_row(vf, seller)]["Act"] - 1
        for name, seed, _, listed in tab[:n]:
            if listed:
                print(name, seed, roll_entry(t, vf, plvl, seed, act, diff)[1])
        print("S after", S)
        return 0
    if len(argv) == 5 and argv[0] == "merc":
        t = Tables(argv[1])
        vf, hid, exp = (int(x) for x in argv[2:5])
        lvl = load_level(t, vf, hid, exp)
        print("L", lvl, set_level(t, vf, hid, lvl))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

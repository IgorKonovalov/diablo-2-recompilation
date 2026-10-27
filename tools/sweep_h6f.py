#!/usr/bin/env python3
"""Checker of plan 0038 batch H6f (hirelings, run:2026-10-27-sweep-hirelings) over tools/gdb/h6f.gdb logs.

    python3 -I tools/sweep_h6f.py check <excel-dir> LOG...

First runs tools/hirelings.py check on the same logs (the run:2026-10-16-hirelings model: tables, rolls, hires,
levels, loads; no regression), then compares the tools/gdb/h6f.py lines with the readings of
docs/findings/hirelings/0001-hirelings.md § Plan 0038 batch H6f:
- NPC_OpenStore's hire test (OSH) after the build at the first interaction (HBS from HIRE_SendList);
- the client's name string (CLN): name 1057 drawn as string 11021 (0x2B0D), every other name as itself;
- HIRE_Hire's gates (a hire is made when MERC_Init runs inside it; HIRE_Hire returns no value): VENDOR_StockLevel (Normal: min(level, {12, 20, 28, 36, 45}[act]), else the level) (HSV), the quest
  reads (HQS: word 36 for 515, word 2 for 150 only when the stock level is below 8), the refusal line (HRF) or none;
- the payment: PayGold's price = the HIRE_Hire roll's price (HPG), its result = gold + stash >= price (HPR), gold first
  then the stash (HHX), the refusal 0x6AE when short;
- HIRE_GiveFreeMerc: the pet tests (GFMP), the pick = the first entry in name order with hired != 1 and listed = 1
  (GFMK), MERC_Init with that {name, seed} and id 0xFFFF, HIRE_RebuildIfEmpty after (RBE) and a rebuild only at 0 left;
- MERC_Create's table write (MCT/MCT2): an entry not listed is marked hired, a listed one is left;
- D2S_ReadMercHeader: the name clamp (RMH name = saved + first, or first past last), the dead branch (RMD: unit flag
  0x10000 and mode 12 when the header's bit is set, POD/PODN: the pet node's bit 0 set);
- MERC_Resurrect: cost = min(50 000, (L·L)/2·15) (RESC), PayGold's result (RESP), the revive (RESX: flag 0x10000
  clear) or the refusal, gold and stash;
- the kill's award (KX0/KXG/KXS): the mercenary's gain scaled by 86/256 (truncating) unless it is the killer;
  MERC_CapExpGain (CEG0/CEGX): a player's gain unchanged, a mercenary's min(gain, (EFL(L+1) - EFL(L)) >> 6) with
  Exp/Lvl of the band row of L; MERC_AddExp (AX0/AXX): nothing when gain <= 0, L >= the owner's level or L >= 98,
  else experience + 2·gain and the level loop over EFL(i + 1) of the band row of L up to 98.
Prints one line per check family with its count; exit 0 when nothing fails. Stdlib only.
"""
import collections
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hirelings as h  # noqa: E402

STOCK_CAP = [12, 20, 28, 36, 45]
NPC_ACT = {150: 0, 198: 1, 252: 2, 515: 4}
LINE_QK, LINE_KASHYA, LINE_GOLD = 0x654, 0x65F, 0x6AE
RET_SEND, RET_STORE = 0x005767F0, 0x00578C04
RET_GFM_INIT, RET_GFM_RBE = 0x00579331, 0x0057933F
RET_LOAD_POD = 0x0056ABD7


class Check:
    def __init__(self, t):
        self.t = t
        self.n = collections.Counter()
        self.notes = collections.Counter()
        self.bad = []

    def ok(self, key, cond, path, msg):
        self.n[key] += 1
        if not cond:
            self.bad.append("%s: %s: %s" % (os.path.basename(path), key, msg))

    def cap(self, vf, hid, L):
        ri = self.t.get_record(vf, hid, L)
        if ri is None:
            return None
        e = self.t.rows[ri]["Exp/Lvl"]
        return (((h.exp_for_level(L + 1, e) & h.M32) - (h.exp_for_level(L, e) & h.M32)) & h.M32) >> 6, e

    def run(self, path):
        t = self.t
        _, ev = h.parse_log(path)
        vf, diff = 1, 0
        tabs, built_by = {}, {}
        hire = None
        mid = None          # the current mercenary's Hireling Id
        last_min = None     # the id argument of the last MERC_Init (-1: a fresh hire)
        hdr = None
        gfm = None
        mct = None
        res = None
        kill = None
        ceg = None
        ax = None
        plv_list = collections.defaultdict(set)     # entry seed -> client draw player levels
        for i, (tag, d) in enumerate(ev):
            if tag == "VGAME":
                vf, diff = d["exp"], d["diff"]
                tabs, built_by, hire = {}, {}, None
            elif tag == "HBS":
                if d["built"] == 0 and d["tab"] == 0:
                    built_by[d["cls"]] = d["ret"]
            elif tag == "HBT":
                if d.get("tab"):
                    tabs[d["cls"]] = h.parse_table(d["tab"])
            elif tag == "OSH":
                self.ok("NPC_OpenStore hire test: the table already built at the first interaction",
                        d["built"] == 1 and built_by.get(d["cls"]) == RET_SEND, path,
                        "OSH %s, built by %s" % (d, built_by.get(d["cls"])))
                self.notes["OpenStore hire test of NPC %d: built %d, trader %d" % (d["cls"], d["built"],
                                                                                   d["trader"])] += 1
            elif tag == "CLN":
                want = 0x2B0D if d["name"] == 0x421 else d["name"]
                self.ok("client name string (1057 -> 11021, else itself)", d["idx"] == want, path, str(d))
                if d["name"] == 0x421:
                    self.notes["name 1057 drawn as %d at the %s site" % (d["idx"], d["site"])] += 1
            elif tag == "HRE":
                if d["ret"] == h.RET_LIST_DRAW:
                    plv_list[d["seed"]].add(d["plvl"])
                    self.floor(d, "client list draw")
                elif d["ret"] == h.RET_HIRE and hire is not None:
                    hire["roll"] = d
                    self.floor(d, "HIRE_Hire")
                    lv = sorted(plv_list.get(d["seed"], ()))
                    if lv and any(x != d["plvl"] for x in lv):
                        self.notes["hire of an entry drawn at player level %s, rolled at %d: level %d" % (
                            lv, d["plvl"], d["o"][1])] += 1
                elif d["ret"] in (h.RET_MERC_INIT, h.RET_CLIENT_INIT):
                    self.floor(d, "MERC_Init" if d["ret"] == h.RET_MERC_INIT else "client merc init")
                if d["ret"] == h.RET_MERC_INIT and d["r"] and last_min == -1:
                    mid = d["o"][0]         # a fresh hire's Id; a load keeps the saved Id (PETS_SetInfo)
            elif tag == "HHI":
                hire = {"d": d, "hsv": None, "hqs": {}, "hrf": None, "hpg": None, "hpr": None, "roll": None, "min": False}
            elif tag == "HSV" and hire is not None:
                hire["hsv"] = d["v"]
                plvl, cls = hire["d"]["plvl"], hire["d"]["cls"]
                want = min(plvl, STOCK_CAP[NPC_ACT[cls]]) if diff == 0 else plvl
                self.ok("VENDOR_StockLevel(player level)", d["v"] == want, path, "v %d, model %d" % (d["v"], want))
            elif tag == "HQS" and hire is not None:
                hire["hqs"][d["word"]] = d["r"]
            elif tag == "HRF" and hire is not None:
                hire["hrf"] = d
            elif tag == "HPG" and hire is not None:
                hire["hpg"] = d["price"]
            elif tag == "HPR" and hire is not None:
                hire["hpr"] = d["r"]
            elif tag == "HHX" and hire is not None:
                self.hire(path, hire, d)
                hire = None
            elif tag == "GFM0":
                gfm = {"d": d, "tab": None, "pets": {}, "pick": None}
            elif tag == "GFMT" and gfm is not None:
                gfm["tab"] = h.parse_table(d["tab"]) if d["tab"] else None
            elif tag == "GFMP" and gfm is not None:
                gfm["pets"][d["dead"]] = d["r"]
            elif tag == "GFMK" and gfm is not None:
                tb = gfm["tab"]
                r = t.rows[t.seller_row(vf, gfm["d"]["seller"], diff)]
                n = r["last"] - r["first"] + 1
                want = next((k for k in range(n) if tb[k][2] != 1 and tb[k][3] == 1), None)
                self.ok("free mercenary: the first entry in name order with hired != 1 and listed = 1",
                        d["i"] == want and [d["name"], d["seed"], d["hired"], d["listed"]] == tb[want], path,
                        "GFMK %s, model index %s %s" % (d, want, tb[want] if want is not None else None))
                gfm["pick"] = d
                self.notes["free mercenary from seller %d (pets: %s)" % (gfm["d"]["seller"], gfm["pets"])] += 1
            if tag == "MIN":
                last_min = d["id"]
            if tag == "MIN" and hire is not None:
                hire["min"] = True
            elif tag == "MIN" and gfm is not None and d["ret"] == RET_GFM_INIT:
                p = gfm["pick"]
                self.ok("free mercenary: MERC_Init {name, seed} = the pick, id 0xFFFF",
                        p is not None and d["name"] == p["name"] and d["seed"] == p["seed"] and d["id"] == -1, path,
                        "MIN %s, pick %s" % (d, p))
            elif tag == "RBE":
                if gfm is not None and d["ret"] == RET_GFM_RBE:
                    want = 9 if gfm["pick"] else None
                    self.ok("free mercenary: HIRE_RebuildIfEmpty after it (listed, unhired left)",
                            want is None or d["left"] == want, path, "RBE %s, model %s" % (d, want))
                    gfm = None
                nxt = next(((tg, dd) for tg, dd in ev[i + 1:i + 40] if tg in ("HBS", "RBE", "HHI", "GFM0")), None)
                rebuilt = nxt is not None and nxt[0] == "HBS" and nxt[1]["ret"] == h.RET_HB_REBUILD
                self.ok("HIRE_RebuildIfEmpty rebuilds only at 0 left", rebuilt == (d["left"] == 0), path,
                        "RBE %s, rebuilt %s" % (d, rebuilt))
                self.notes["HIRE_RebuildIfEmpty from %#x, left %s" % (d["ret"], d["left"])] += 1
            elif tag == "MCE":
                self.notes["MERC_Create from %#x (id %#x)" % (d["ret"], d["id"])] += 1
                mct = d
            elif tag == "MCT":
                mct = dict(mct or {}, t0=d)
            elif tag == "MCT2" and mct is not None:
                b = mct.get("t0", {})
                want = 1 if b.get("listed") == 0 else b.get("hired")
                self.ok("MERC_Create: an entry not listed is marked hired, a listed one is left",
                        d["hired"] == want and d["listed"] == b.get("listed"), path,
                        "before %s after %s" % (b, d))
                self.notes["MERC_Create table entry from %#x: listed %s hired %s -> %s" % (
                    mct.get("ret", 0), b.get("listed"), b.get("hired"), d["hired"])] += 1
            elif tag == "MRH":
                hb = bytes.fromhex(d["hdr"])
                seed = int.from_bytes(hb[4:8], "little")
                name, hid = int.from_bytes(hb[8:10], "little"), int.from_bytes(hb[10:12], "little")
                exp = int.from_bytes(hb[12:16], "little")
                flags = int.from_bytes(hb[0:4], "little")
                hdr = None if (seed == 0 and name == 0 and exp == 0) else {
                    "name": name, "id": hid, "seed": seed, "exp": exp, "dead": flags & 0x10000}
            elif tag == "RMH" and hdr is not None:
                b = t.rows[t.get_record(vf, hdr["id"], 1)]
                nm = (hdr["name"] + b["first"]) & 0xFFFF
                clamped = nm > b["last"]
                if clamped:
                    nm = b["first"]
                self.ok("saved name: + NameFirst's index, reset to it past NameLast's", d["name"] == nm
                        and d["seed"] == hdr["seed"] and d["id"] == hdr["id"] and d["dead"] == hdr["dead"]
                        and d["cls"] == b["Class"], path, "RMH %s, model name %d (hdr %s)" % (d, nm, hdr))
                self.notes["saved name %d -> %d (%s)" % (hdr["name"], d["name"], "reset" if clamped else "kept")] += 1
                mid = hdr["id"]
                ld = h.load_level(t, vf, hdr["id"], hdr["exp"])
                self.notes["loaded mercenary id %d exp %d: level %d by the loop" % (hdr["id"], hdr["exp"], ld)] += 1
            elif tag == "RMD" and hdr is not None:
                dead = bool(hdr["dead"])
                self.ok("loaded dead mercenary: unit flag 0x10000 and mode 12 (living: neither)",
                        bool(d["flags"] & 0x10000) == dead and (d["mode"] == 12) == dead, path,
                        "RMD %s, header dead %s" % (d, dead))
                hdr = None
            elif tag == "POD":
                pod = {"d": d, "type": None, "before": None}
            elif tag == "PODT":
                pod["type"] = d["type"]
            elif tag == "PODN":
                if d["when"] == "before":
                    pod["before"] = d["flags"]
                else:
                    self.ok("PETS_OnDeath: a mercenary (pet type 7) node gets bit 0",
                            pod["type"] == 7 and d["flags"] == pod["before"] | 1, path,
                            "POD %s, after %#x" % (pod, d["flags"]))
                    self.notes["PETS_OnDeath from %#x: node flags %#x -> %#x" % (
                        pod["d"]["ret"], pod["before"], d["flags"])] += 1
            elif tag == "RES0":
                res = {"d": d}
            elif tag == "RESU" and res is not None:
                res["u"] = d
            elif tag == "RESC" and res is not None:
                L = res["u"]["L"]
                want = min(50000, ((L * L) // 2) * 15)
                self.ok("MERC_ResurrectCost = min(50 000, (L·L)/2·15) of the mercenary's level", d["cost"] == want,
                        path, "cost %d, L %s, model %d" % (d["cost"], L, want))
                res["cost"] = d["cost"]
            elif tag == "RESP" and res is not None:
                g, bk = res["d"]["gold"], res["d"]["bank"]
                self.ok("resurrection: PayGold = gold + stash >= cost", d["r"] == int(g + bk >= res["cost"]),
                        path, "r %d, gold %d bank %d cost %d" % (d["r"], g, bk, res["cost"]))
                res["paid"] = d["r"]
            elif tag == "RESX" and res is not None:
                g, bk, c = res["d"]["gold"], res["d"]["bank"], res.get("cost", 0)
                if res.get("paid"):
                    wg, wb = (g - c, bk) if c <= g else (0, bk - (c - g))
                    self.ok("resurrection paid: gold first, then the stash; flag 0x10000 cleared",
                            (d["gold"], d["bank"]) == (wg, wb) and not d["flags"] & 0x10000, path,
                            "RESX %s, model gold %d bank %d" % (d, wg, wb))
                    self.notes["resurrected: L %s cost %d, flags %#x -> %#x, mode %s -> %s, life %s" % (
                        res["u"]["L"], c, res["u"]["flags"], d["flags"], res["u"]["mode"], d["mode"],
                        d["hp"])] += 1
                res = None
            elif tag == "KX0":
                kill = {"d": d}
            elif tag == "KXG" and kill is not None:
                kill["g"] = d
            elif tag == "KXS" and kill is not None and "g" in kill:
                g = kill["g"]
                merc_kills = g["killer"] == (g["merc"] or {}).get("u")
                want = g["gain"] if merc_kills else h.tdiv(g["gain"] * 0x56, 256)
                self.ok("the mercenary's share: x 86/256 (truncating) unless it is the killer", d["gain"] == want,
                        path, "gain %d -> %d, model %d (merc kills %s)" % (g["gain"], d["gain"], want, merc_kills))
                kill["share"] = d["gain"]
                self.notes["kill award: %s" % ("the mercenary's kill" if merc_kills else "another's kill")] += 1
            elif tag == "CEG0":
                ceg = d
            elif tag == "CEGX" and ceg is not None:
                u = ceg["unit"] or {}
                if u.get("type") == 0:
                    want = ceg["gain"]
                    self.notes["MERC_CapExpGain for a player: unchanged"] += 1
                elif mid is not None:
                    c, e = self.cap(vf, mid, ceg["L"])
                    want = min(ceg["gain"], c)
                    if ceg["gain"] > c:
                        self.notes["MERC_CapExpGain capped (gain > cap)"] += 1
                    else:
                        self.notes["MERC_CapExpGain below the cap"] += 1
                else:
                    want = None
                self.ok("MERC_CapExpGain: min(gain, (EFL(L+1) - EFL(L)) >> 6), a player's gain unchanged",
                        want is None or d["r"] == want, path, "CEG %s -> %d, model %s (id %s)" % (
                            ceg, d["r"], want, mid))
                ceg = None
            elif tag == "AX0":
                ax = d
            elif tag == "AXX" and ax is not None:
                self.addexp(path, vf, mid, ax, d, kill)
                ax, kill = None, None
        return

    def floor(self, d, where):
        """Count the rolls whose unclamped level plvl - 5 + low mod 5 (draw 2) is below 2: the floor binds."""
        if not d["r"]:
            return
        s = h.Seed(d["seed"])
        s.range(len(self.t.type_rows(d["vf"], d["act"], d["diff"])))
        raw = h.s32(d["plvl"] - 5 + s.step() % 5)
        if raw < 2:
            self.notes["roll at the level floor (%s): unclamped %d, logged %d" % (where, raw, d["o"][1])] += 1

    def hire(self, path, hr, x):
        d, cls = hr["d"], hr["d"]["cls"]
        q = hr["hqs"]
        if cls == 515:
            self.ok("HIRE_Hire reads quest word 36 bit 0 for Qual-Kehk", 36 in q, path, str(hr))
        if cls == 150:
            self.ok("HIRE_Hire reads quest word 2 bit 0 for Kashya only when the stock level is below 8",
                    (2 in q) == (hr["hsv"] < 8), path, str(hr))
        if cls not in (150, 515):
            self.ok("HIRE_Hire reads no quest word for Greiz and Asheara", not q, path, str(hr))
        if cls == 515 and not q.get(36):
            want = LINE_QK
        elif cls == 150 and hr["hsv"] < 8 and not q.get(2):
            want = LINE_KASHYA
        else:
            want = None
        if want is not None:
            self.ok("HIRE_Hire quest gate refuses (line %#x)" % want, hr["hrf"] is not None and hr["hrf"]["line"]
                    == want and hr["hpg"] is None and not hr["min"], path, str(hr))
            self.notes["refused at the gate of %d: line %#x, stock level %s, quest %s" % (
                cls, want, hr["hsv"], q)] += 1
            self.ok("a refused hire pays nothing", (x["gold"], x["bank"]) == (d["gold"], d["bank"]), path, str(x))
            return
        if cls in (150, 515):
            self.notes["gate passed at %d: stock level %s, quest %s" % (cls, hr["hsv"], q)] += 1
        price = hr["roll"]["o"][5] if hr["roll"] else None
        self.ok("PayGold's price = the hire roll's price", hr["hpg"] == price, path, str(hr))
        can = int(d["gold"] + d["bank"] >= (price or 0))
        self.ok("PayGold: gold + stash >= price", hr["hpr"] == can, path, str(hr))
        if not can:
            self.ok("too little gold: refusal line 0x6AE, nothing paid", hr["hrf"] is not None
                    and hr["hrf"]["line"] == LINE_GOLD and not hr["min"]
                    and (x["gold"], x["bank"]) == (d["gold"], d["bank"]), path, str((hr, x)))
            self.notes["refused for gold: price %s, gold %d, stash %d" % (price, d["gold"], d["bank"])] += 1
        else:
            if price > d["gold"]:
                self.notes["paid from gold and the stash: price %d, gold %d, stash %d -> %d" % (
                    price, d["gold"], d["bank"], x["bank"])] += 1

    def addexp(self, path, vf, mid, a, x, kill):
        g, L, o12 = a["gain"], a["L"], a["o12"]
        m13 = a["m13"]
        if kill is not None and "share" in kill:
            self.ok("MERC_AddExp's gain = the award's share", g == kill["share"], path,
                    "AX0 gain %d, share %d" % (g, kill["share"]))
        if g <= 0 or L >= o12 or L >= 98 or mid is None:
            want = (a["m12"], m13)
            why = "gain <= 0" if g <= 0 else "L >= owner's level" if L >= o12 else "L >= 98" if L >= 98 else "?"
        else:
            nexp = (m13 + 2 * g) & h.M32
            ri = self.t.get_record(vf, mid, L)
            e = self.t.rows[ri]["Exp/Lvl"]
            i = L
            while True:
                if (h.exp_for_level(i + 1, e) & h.M32) > nexp:
                    break
                i += 1
                if i >= 98:
                    break
            want = (i, nexp)
            why = "level-up %d -> %d" % (L, i) if i > L else "added"
        self.ok("MERC_AddExp: experience + 2·gain and the level loop (nothing at L >= owner, L >= 98, gain <= 0)",
                (x["m12"], x["m13"]) == want, path, "AX0 %s AXX %s model %s" % (a, x, want))
        self.notes["MERC_AddExp: %s" % why] += 1


def main(argv):
    if len(argv) < 3 or argv[0] != "check":
        print(__doc__)
        return 2
    excel, logs = argv[1], argv[2:]
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "hirelings.py"), "check", excel] + logs,
                       capture_output=True, text=True)
    print("== tools/hirelings.py check (exit %d) ==" % r.returncode)
    print(r.stdout.rstrip())
    c = Check(h.Tables(excel))
    for p in logs:
        c.run(p)
    print("== H6f checks over %d logs ==" % len(logs))
    for k, v in sorted(c.n.items()):
        print("  %-100s %d" % (k, v))
    for k, v in sorted(c.notes.items()):
        print("  note: %s: %d" % (k, v))
    for b in c.bad:
        print("  FAIL " + b)
    print("h6f: %d comparisons, %d failing" % (sum(c.n.values()), len(c.bad)))
    return 0 if not c.bad and r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Checker for plan 0038 batch H6g (player; run:2026-10-27-sweep-player), over tools/gdb/h6g.gdb logs.

  python3 -I tools/sweep_h6g.py check <excel-dir> <game.exe> <log> [<log> ...]
  python3 -I tools/sweep_h6g.py static <game.exe>

check runs tools/player.py's checker on the logs first (the new characters, every XP_Compute, PLAYER_AddExperience and
PLAYER_LevelUp line, its own model: player/0001), then the H6g models, each against the logged lines of
tools/gdb/h6g.py (every model input is a logged game state, a stock excel table or the pinned game.exe's bytes):
  ncf      client +0x3D4 after sub_00537970 = the word at NC0 | 1; the bit-0 writers' order (C3W)
  kill     XP_OnMonsterKill: the monster's base stat 13 read (XKE) = the monster's stat 13 entry at XK0 = XP_Compute's
           input (XC0) for a positive value; no XC0 for a value <= 0
  xp85     XP_Compute's stat 85 (XC85) = uniqueitems.txt's addxp maximum of the item the recipe carries at max roll
           (Annihilus: max 10), and the term exp + MulDiv(exp, s85, 100) separating (non-zero) on the logged kills
           (player.py check reproduces XCX)
  cap      PLAYER_AddExperience at the cap: experience + add above T(MaxLvl - 1) gives T(MaxLvl - 1), lastexp the
           difference (player.py check reproduces it; counted here); XP_Compute at clvl >= MaxLvl returns 0 (XCX 0)
  stat     PLAYER_SpendStatPoint(which): statpts - 1 and the attribute + 1 (0 str, 2 dex); energy: maxmana and mana +
           ManaPerMagic x 64 (mana clamped to maxmana); vitality: maxhp, hp + LifePerVitality x 64, maxstamina,
           stamina + StaminaPerVitality x 64 (each clamped); every base entry 0..11 compared (SP0 -> SPX)
  skill    the skill-point path: newskills >= cost, newskills - cost (SKX), SKILLS_AddSkill: a player's entry with the
           same Skills record and item ref -1 raised by 1 when below the maximum (Skills maxlvl, 20 when <= 0), kept
           at the maximum; no entry: appended at level 1 (AS0 -> ASX)
  belt     sub_0063C600_BeltFreeSlot from the logged belt boxes (BFG) and the item's class: the column search over
           columns 0..3 whose box holds the same class (and column < box count), the first free box down it below
           the box count; else, with misc.txt autobelt set, the first free box of 0..3 (BFX); the next BFG shows the
           item in that box
  death    the gate (DG0: a monster killer, type 1, no owner -> PLAYER_DeathExpLoss); PLAYER_DeathExpLoss from the
           unit's level and experience (DL0), DifficultyLevels.txt DeathExpPenalty and experience.txt: span, loss
           (32-bit product / 100), the clamp at T(L-1) and the kept amount, the client value (DLC), the stat write
           (DLW, DLX); the corpse: CLIENT_GetDeathExpLoss = the kept amount (CC0), the share v*75/100 (v <= 0x100000)
           or (v/100)*75 (CCX); the pickup: the corpse's stat 13 (CPS) = the share, AddExperienceDirect's value, then
           PLAYER_AddExperience's add
static pins the instruction bytes the batch's statements cite (a second tool next to objdump) and reads
g_XpPenaltyBelow / g_XpPenaltyAbove from the image (player.py's constants compared).
Exit 0 only if nothing mismatches. Stdlib only. Read-only.
"""
import collections
import csv
import io
import json
import os
import struct
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

M32 = 0xFFFFFFFF
BASE = 0x400000

# (address, expected bytes, what): .text file offset = VA - 0x400000 (raw = virtual in this image)
PINS = [
    (0x00537993, "8389D403000001", "sub_00537970: or dword [ecx+0x3D4], 1"),
    (0x005397A3, "838ED403000001", "sub_00539760_ClientAddPlayerToGame: or dword [esi+0x3D4], 1"),
    (0x00569F8A, "E8E1D9FCFF", "NewCharFromStub: call sub_00537970 first"),
    (0x0057E9C5, "6A006A0D53E8E1690A00", "XP_OnMonsterKill: STATS_GetUnitBaseStat(monster, 13, 0)"),
    (0x0057E9CF, "85C08945F80F8ECC000000", "XP_OnMonsterKill: test eax, eax; jle (no XP_Compute for <= 0)"),
    (0x00570D74, "83FF037777", "PLAYER_SpendStatPoint: which <= 3"),
    (0x00570D79, "FF24BDF80D5700", "PLAYER_SpendStatPoint: jump table 0x00570DF8"),
    (0x00570DF8, "800D5700A60D5700B80D5700DE0D5700", "the table: str, energy, dex, vit"),
    (0x00570ADB, "0FB64B48", "PLAYER_SpendEnergy: CharStats +0x48 (ManaPerMagic)"),
    (0x00570BC3, "0FB64B46", "PLAYER_SpendVitality: CharStats +0x46 (LifePerVitality)"),
    (0x00570C1A, "0FB64347", "PLAYER_SpendVitality: CharStats +0x47 (StaminaPerVitality)"),
    (0x005700FA, "6A006A0556E8AC520B00", "the skill-point path: STATS_GetUnitBaseStat(unit, 5, 0)"),
    (0x00570107, "3BC17C47", "newskills < cost: no spend"),
    (0x0057011A, "E8F16F0D00", "then SKILLS_AddSkill"),
    (0x00647245, "8B7E28", "SKILLS_AddSkill: the entry's level +0x28"),
    (0x0064724F, "3BF87C08", "below the maximum: raise"),
    (0x00647256, "833801", "a monster (type 1) is raised at the maximum too"),
    (0x006471EE, "C7462801000000", "a new entry at level 1"),
    (0x0063C6FC, "3BFA", "BeltFreeSlot: column < box count"),
    (0x0063C70C, "83C104", "down the column: box + 4"),
    (0x0063C731, "80B83101000000", "the first-free path: item record +0x131 (autobelt)"),
    (0x0063C74B, "83F804", "boxes 0..3"),
    (0x00535A1E, "83FE017E78", "PLAYER_DeathExpLoss: level <= 1 returns"),
    (0x00535A53, "B81F85EB51F7E2", "loss: x 0x51EB851F (mul)"),
    (0x00535A5C, "C1EE057439", "shr 5; loss 0 returns"),
    (0x00535A63, "3BFB770B", "new <= T(L-1) (unsigned): the clamp"),
    (0x00535AC8, "833F00", "the gate: a player killer (type 0) skips"),
    (0x0057F816, "81F9000010007E3C", "PLAYER_CorpseCreate: v <= 0x100000"),
    (0x0057FBB6, "6A006A0D57E8C058", "PLAYER_CorpsePickup: the corpse's stat 13"),
]


def rows(excel, name):
    with open(os.path.join(excel, name), encoding="latin1") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def events(path):
    out = []
    for line in open(path, errors="replace"):
        tag, _, rest = line.rstrip("\n").partition(" ")
        if rest.startswith("{"):
            try:
                out.append((tag, json.loads(rest)))
            except ValueError:
                pass
    return out


class Fail(Exception):
    pass


def eq(what, model, logged):
    if model != logged:
        raise Fail("%s: model %r, logged %r" % (what, model, logged))


def bd(entries):
    return {(s, p): v for s, p, v in (entries or [])}


def bget(b, s):
    return b.get((s, 0), 0)


class Tables:
    def __init__(self, excel):
        cs = rows(excel, "charstats.txt")
        self.cs = [r for r in cs if r["class"] != "Expansion"]
        xp = rows(excel, "experience.txt")
        self.maxlvl = int(xp[0]["Sorceress"])
        self.cols = ["Amazon", "Sorceress", "Necromancer", "Paladin", "Barbarian", "Druid", "Assassin"]
        self.T = {int(r["Level"]): [int(r[c]) for c in self.cols] for r in xp if r["Level"].isdigit()}
        self.pen = {r["Name"]: int(r["DeathExpPenalty"]) for r in rows(excel, "difficultylevels.txt")}
        self.pen_by = [self.pen["Normal"], self.pen["Nightmare"], self.pen["Hell"]]
        sk = rows(excel, "skills.txt")
        self.skill_max = [int(r["maxlvl"] or 0) for r in sk]
        self.items = []
        for t in ("weapons.txt", "armor.txt", "misc.txt"):
            self.items += [r for r in rows(excel, t) if r.get("code")]
        self.uniq = rows(excel, "uniqueitems.txt")

    def thr(self, cls, lvl):
        return self.T[lvl][cls if 0 <= cls <= 6 else 0]

    def code(self, icls):
        return self.items[icls]["code"] if icls is not None and 0 <= icls < len(self.items) else None


def unique_prop_max(T, name, prop):
    for r in T.uniq:
        if r.get("index") == name:
            for k in range(1, 13):
                if r.get("prop%d" % k) == prop:
                    return int(r["max%d" % k])
    return None


def check(excel, exe, logs):
    import player
    T = Tables(excel)
    S = collections.Counter()
    fails = []
    # 1. tools/player.py check on the same logs
    class NS:
        pass
    ns = NS()
    ns.excel, ns.logs, ns.verbose = excel, logs, False
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = player.cmd_check(ns)
    print(buf.getvalue().rstrip())
    print("tools/player.py check exit %d" % rc)
    if rc:
        fails.append("tools/player.py check exit %d" % rc)
    s85_max = unique_prop_max(T, "Annihilus", "addxp")
    for path in logs:
        name = os.path.basename(path)
        ev = events(path)
        cls_of = {}
        nc0 = {}
        xk = None
        open_sp = {}
        skc = {}
        as0 = {}
        bf = {}
        expect = {}
        death = {}
        kept_last = None
        share_last = None
        pick = None
        eg = None
        for i, (t, d) in enumerate(ev):
            th = d.get("th")
            try:
                if t == "NC0":
                    nc0[d["client"]] = d["c3d4"]
                elif t == "C3W":
                    S["C3W %s before bit0=%d" % (hex(d["site"]), d["before"] & 1)] += 1
                elif t == "NCF":
                    if d["client"] in nc0:
                        eq("client +0x3D4 after sub_00537970", nc0[d["client"]] | 1, d["c3d4"])
                        S["ncf: +0x3D4 = NC0 | 1 (bit 0 already set at NC0: %d)" % (nc0[d["client"]] & 1)] += 1
                elif t == "XA0":
                    cls_of[d["unit"]] = d["cls"]
                elif t == "XK0":
                    xk = d
                elif t == "XKE":
                    if xk is None:
                        raise Fail("XKE without XK0")
                    eq("the monster's stat 13 read = its base entry at XK0", bget(bd(xk.get("mb")), 13), d["v"])
                    S["kill: monster base stat 13 read = its XK0 entry"] += 1
                    xk = dict(xk, xke=d["v"], need_xc=d["v"] > 0 and xk.get("ktype") == 0)
                    if d["v"] <= 0:
                        S["kill: value <= 0"] += 1
                elif t == "XC0":
                    if xk is not None and xk.get("need_xc"):
                        eq("XP_Compute's input = the monster's stat 13", xk["xke"], d["exp"])
                        S["kill: XP_Compute input = the monster's stat 13 (player killer)"] += 1
                        xk["need_xc"] = False
                        if d["clvl"] >= T.maxlvl:
                            S["cap: XP_Compute at clvl %d (>= MaxLvl)" % d["clvl"]] += 1
                        xk["clvl"] = d["clvl"]
                elif t == "XC85":
                    if d["v"]:
                        eq("stat 85 = Annihilus addxp max (uniqueitems.txt)", s85_max, d["v"])
                        S["xp85: XC85 = uniqueitems Annihilus addxp max %d" % s85_max] += 1
                        xk = dict(xk or {}, s85=d["v"])
                elif t == "XCR":
                    if xk is not None:
                        xk["xcr"] = d["v"]
                elif t == "XCX":
                    if xk is not None and xk.get("s85") and "xcr" in xk:
                        bonus = d["v"] - xk["xcr"]
                        if bonus:
                            S["xp85: kills with a non-zero stat-85 term"] += 1
                    if xk is not None and xk.get("clvl", 0) >= T.maxlvl:
                        eq("XP_Compute at clvl >= MaxLvl", 0, d["v"])
                        S["cap: XP_Compute returned 0 at clvl >= MaxLvl"] += 1
                elif t == "XAX":
                    pass
                # ---- attribute points
                elif t == "SP0":
                    open_sp[th] = d
                elif t == "SPX":
                    a = open_sp.pop(th)
                    b = bd(a["b"])
                    w = a["which"]
                    cs = T.cs[1]  # the batch's characters are Sorceresses (class read below)
                    cs = T.cs[cls_of.get(a["unit"], 1)] if a["unit"] in cls_of else cs
                    if bget(b, 4) == 0 or w > 3:
                        site = "refused"
                    else:
                        site = {0: "str", 1: "energy", 2: "dex", 3: "vit"}[w]
                        b[(4, 0)] = bget(b, 4) - 1
                        if w == 0:
                            b[(0, 0)] = bget(b, 0) + 1
                        elif w == 2:
                            b[(2, 0)] = bget(b, 2) + 1
                        elif w == 1:
                            b[(1, 0)] = bget(b, 1) + 1
                            m = int(cs["ManaPerMagic"]) * 64
                            b[(9, 0)] = bget(b, 9) + m
                            b[(8, 0)] = min(bget(b, 8) + m, b[(9, 0)])
                        else:
                            b[(3, 0)] = bget(b, 3) + 1
                            hp, st = int(cs["LifePerVitality"]) * 64, int(cs["StaminaPerVitality"]) * 64
                            b[(7, 0)] = bget(b, 7) + hp
                            b[(6, 0)] = min(bget(b, 6) + hp, b[(7, 0)])
                            b[(11, 0)] = bget(b, 11) + st
                            b[(10, 0)] = min(bget(b, 10) + st, b[(11, 0)])
                    eq("PLAYER_SpendStatPoint return site (which %d)" % w, site, d["site"])
                    got = bd(d["b"])
                    model = {k: v for k, v in b.items() if v != 0}
                    eq("base entries 0..11 after PLAYER_SpendStatPoint(%s)" % site, model,
                       {k: v for k, v in got.items() if v != 0})
                    S["stat: PLAYER_SpendStatPoint %s reproduced" % site] += 1
                # ---- skill points
                elif t == "SKC":
                    skc[th] = d
                    S["skill: newskills %d >= cost %d (skill %d)" % (d["newskills"], d["cost"], d["skill"])] += 1
                elif t == "AS0":
                    as0[th] = d
                elif t == "ASX":
                    a = as0.pop(th)
                    # Skills +0x12C is an i16 (SKILLS_GetMaxLevel: movsx word, 0x004AA8CD); h6g.py r1/r2 read a
                    # dword there, so the low word is taken
                    cell = a["maxlvl"] & 0xFFFF
                    cell = cell - 0x10000 if cell & 0x8000 else cell
                    mx = cell if cell > 0 else 20
                    eq("Skills maxlvl cell = skills.txt maxlvl (skill %d)" % a["skill"], T.skill_max[a["skill"]], cell)
                    if a["ex"] is None:
                        site, lvl = "append", 1
                    else:
                        site = "existing"
                        lvl = a["ex"]["lvl"] + 1 if a["ex"]["lvl"] < mx else a["ex"]["lvl"]
                    eq("SKILLS_AddSkill (skill %d, entry %s)" % (a["skill"], a["ex"]), (site, lvl), (d["site"], d["lvl"]))
                    if a["ra"] == 0x0057011F:
                        S["skill: SKILLS_AddSkill from the skill-point path, %s%s" % (
                            site, " (raise %d -> %d)" % (a["ex"]["lvl"], lvl) if a["ex"] else "")] += 1
                    else:
                        S["skill: SKILLS_AddSkill from %s, %s" % (hex(a["ra"]), site)] += 1
                elif t == "SKX":
                    c = skc.pop(th)
                    eq("newskills after the spend", c["newskills"] - c["cost"], bget(bd(d["b5"]), 5))
                    S["skill: newskills - cost after the spend"] += 1
                # ---- belt
                elif t == "BF0":
                    bf[th] = {"in": d}
                elif t == "BFG":
                    if th in bf:
                        bf[th]["g"] = d
                    e = expect.pop(th, None)
                    if e is not None:
                        eq("the item in the predicted box at the next lookup", e[1], d["boxes"][e[0]])
                        S["belt: the next lookup shows the item in the predicted box"] += 1
                elif t == "BFX":
                    c = bf.get(th)
                    if not c or "g" not in c:
                        raise Fail("BFX without BF0/BFG")
                    boxes, n, ic = c["g"]["boxes"], c["g"]["n"], c["in"]["icls"]
                    res = None
                    for col in range(4):
                        if boxes[col] == ic and col < n:
                            k = col
                            while k < n:
                                if boxes[k] is None:
                                    res = ("col", k)
                                    break
                                k += 4
                            if res:
                                break
                    if res is None:
                        auto = T.items[ic].get("autobelt") == "1"
                        if auto:
                            for k in range(4):
                                if boxes[k] is None:
                                    res = ("free", k)
                                    break
                    if res is None:
                        res = ("none", None)
                    eq("BeltFreeSlot (item %s, boxes %d)" % (T.code(ic), n), res, (d["path"], d.get("box")))
                    S["belt: BeltFreeSlot %s path reproduced (ra %s)" % (res[0], hex(c["in"]["ra"]))] += 1
                    if res[1] is not None and c["in"]["ra"] == 0x0054D5C4:
                        expect[th] = (res[1], ic)
                # ---- death
                elif t == "DG0":
                    death[th] = {"g": d}
                    S["death: gate, killer type %s" % d.get("ktype")] += 1
                elif t == "DL0":
                    c = death.setdefault(th, {})
                    if "g" in c:
                        eq("the gate calls PLAYER_DeathExpLoss for a monster killer", 1, c["g"].get("ktype"))
                    b = bd(d["b"])
                    lvl, exp = bget(b, 12), bget(b, 13) & M32
                    cls = cls_of.get(d["unit"], 1)
                    m = {"lvl": lvl, "exp": exp, "diff": d["diff"]}
                    if lvl > 1:
                        t0, t1 = T.thr(cls, lvl - 1), T.thr(cls, lvl)
                        m["span"] = (t1 - t0) & M32
                        m["pen"] = T.pen_by[d["diff"]]
                        m["loss"] = ((m["pen"] * m["span"]) & M32) // 100
                        m["t0"] = t0
                        if m["loss"]:
                            new = (exp - m["loss"]) & M32
                            kept = m["loss"]
                            if new <= t0:
                                kept = m["loss"] + ((new - t0) & M32)
                                kept &= M32
                                kept = kept - (1 << 32) if kept & 0x80000000 else kept
                                kept = max(kept, 0)
                                new = t0 + 1
                                m["clamp"] = True
                            m["new"], m["kept"] = new, kept
                        else:
                            m["new"] = exp
                    else:
                        m["new"] = exp
                    c["m"] = m
                elif t == "DLP":
                    m = death[th]["m"]
                    eq("DeathExpPenalty (difficulty %d)" % m["diff"], m["pen"], d["pen"])
                    eq("the level span T(L) - T(L-1)", m["span"], d["span"])
                    eq("stat 13", m["exp"], d["exp"] & M32)
                elif t == "DLL":
                    m = death[th]["m"]
                    eq("loss = penalty x span / 100", m["loss"], d["loss"])
                elif t == "DLC":
                    m = death[th]["m"]
                    eq("the kept amount (client +0x508)", m["kept"], d["kept"])
                    kept_last = d["kept"]
                elif t == "DLW":
                    m = death[th]["m"]
                    eq("the new experience", m["new"], d["new"] & M32)
                elif t == "DLX":
                    c = death.pop(th)
                    m = c["m"]
                    b = bd(d["b"])
                    eq("stat 13 after PLAYER_DeathExpLoss", m["new"], bget(b, 13) & M32)
                    eq("the level unchanged", m["lvl"], bget(b, 12))
                    kind = "level 1" if m["lvl"] <= 1 else ("loss 0" if not m.get("loss") else
                                                            ("clamp" if m.get("clamp") else "loss"))
                    S["death: PLAYER_DeathExpLoss reproduced, difficulty %d, %s" % (m["diff"], kind)] += 1
                    if not m.get("loss"):
                        kept_last = kept_last if kind == "loss 0" and kept_last else 0
                elif t == "EG0":
                    # sub_0058C5C0_ExpGrantCapped (player/0001 § Plan 0038 H6g shortfalls, steps 1-4)
                    b = bd(d["b"])
                    G = (1400000, 20000000, 40000000)[d["diff"]]
                    L, ex, nx = bget(b, 12), bget(b, 13), bget(b, 30)
                    cut = T.thr(0, L + 1) - T.thr(0, L) if L < T.maxlvl else 0
                    G = min(G, cut)
                    passes, lastexp = [], bget(b, 29)
                    while L < T.maxlvl:
                        passes.append(G)
                        if G == 0:
                            break
                        need = nx - ex
                        if G < need:
                            ex += G
                            G = 0
                        else:
                            ex, lastexp, L, G = nx, need, L + 1, G - need
                            nx = T.thr(0, L)
                    eg = {"passes": passes, "end": [L, ex, lastexp, nx], "got": [], "cut": cut,
                          "uncut": (1400000, 20000000, 40000000)[d["diff"]], "L0": bget(b, 12)}
                elif t == "EGS" and eg is not None:
                    eg["got"].append(d["grant"])
                elif t == "EGX" and eg is not None:
                    b = bd(d["b"])
                    eq("EGS values (the grant at each loop pass)", eg["passes"], eg["got"])
                    eq("the base entries after the grant (12, 13, 29, 30)", eg["end"],
                       [bget(b, 12), bget(b, 13), bget(b, 29), bget(b, 30)])
                    S["grant: ExpGrantCapped reproduced (cut %s than the fixed amount, %d level-up(s))" % (
                        "lower" if eg["cut"] < eg["uncut"] else "not lower", eg["end"][0] - eg["L0"])] += 1
                    eg = None
                elif t == "CC0":
                    v = d["v"]
                    if kept_last is not None:
                        eq("CLIENT_GetDeathExpLoss at the corpse = the kept amount", kept_last, v)
                    share = (v * 75) // 100 if v <= 0x100000 else (v // 100) * 75
                    share_last = share
                    S["death: corpse created, v = the kept amount"] += 1
                elif t == "CCX":
                    eq("the corpse's share", share_last, d["share"])
                    S["death: corpse share v*75/100 reproduced (v %s)" % ("0" if not share_last else "> 0")] += 1
                elif t == "CP0":
                    pick = {"d": d}
                    S["death: corpse pickup called"] += 1
                elif t == "CPS":
                    eq("the corpse's stat 13 at the pickup = its share", share_last, d["v"])
                    S["death: corpse stat 13 at the pickup = the share"] += 1
                elif t == "CPA":
                    eq("AddExperienceDirect's value = the share", share_last, d["v"])
                    pick = dict(pick or {}, aed=d["v"])
                elif t == "AED":
                    if pick and "aed" in pick:
                        eq("AddExperienceDirect entry value", pick["aed"], d["v"])
                        pick["xa"] = True
                        S["death: AddExperienceDirect with the share"] += 1
            except (Fail, KeyError, IndexError, TypeError) as e:
                fails.append("%s line %d %s: %s" % (name, i, t, e))
                print("FAIL %s line %d %s: %s" % (name, i, t, e))
    print("== tools/sweep_h6g.py check ==")
    for k in sorted(S):
        print("  %-78s %d" % (k, S[k]))
    print("%d mismatches" % len(fails))
    return 0 if not fails else 1


def static(exe):
    import player
    data = open(exe, "rb").read()
    bad = 0
    for a, hx, what in PINS:
        got = data[a - BASE:a - BASE + len(hx) // 2].hex().upper()
        ok = got == hx
        bad += not ok
        print("%s 0x%08X %-40s %s" % ("ok  " if ok else "FAIL", a, hx, what))
    below = list(struct.unpack_from("<11I", data, 0x006E1668 - BASE))
    above = list(struct.unpack_from("<11I", data, 0x006E1694 - BASE))
    for nm, got, ref in (("g_XpPenaltyBelow", below, player.XP_BELOW), ("g_XpPenaltyAbove", above, player.XP_ABOVE)):
        ok = got == ref
        bad += not ok
        print("%s %s %s (player.py %s)" % ("ok  " if ok else "FAIL", nm, got, ref))
    print("%d pins, %d failing" % (len(PINS) + 2, bad))
    return 0 if not bad else 1


def main(argv):
    if len(argv) >= 4 and argv[0] == "check":
        return check(argv[1], argv[2], argv[3:])
    if len(argv) == 2 and argv[0] == "static":
        return static(argv[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

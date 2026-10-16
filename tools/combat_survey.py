"""Survey of the table columns the combat code is expected to read (plan 0037 Phase 0).

Usage:
  python3 -I tools/combat_survey.py codes      <excel-dir>
  python3 -I tools/combat_survey.py monstats   <excel-dir>
  python3 -I tools/combat_survey.py monstats2  <excel-dir>
  python3 -I tools/combat_survey.py difficulty <excel-dir>
  python3 -I tools/combat_survey.py isc        <excel-dir>
  python3 -I tools/combat_survey.py items      <excel-dir>
  python3 -I tools/combat_survey.py states     <excel-dir>
  python3 -I tools/combat_survey.py skills     <excel-dir>
  python3 -I tools/combat_survey.py summary    <excel-dir>

codes       the ElemTypes, MonMode and PlrMode rows (index, code, token) and how many cells of the other tables name
            each one (MonStats El<e>Type/El<e>Mode/Sk<k>mode/spawnmode, Skills EType/anim/seqtrans/monanim/summode,
            MonStats2 ResurrectMode).
monstats    MonStats § Combat columns: per attack mode (A1, A2, S1) and difficulty, the records with damage or to-hit
            set and how many of them have that mode in their MonStats2 row; the three El groups (mode, type, cells per
            difficulty); Drain, coldeffect, ToBlock, DamageRegen, noRatio, NoShldBlock, Crit, SkillDamage, isMelee,
            rangedtype and the MissA1/MissA2 missiles.
monstats2   MonStats2 § Combat columns: rows per mode bit m<XX>, MeleeRng and HitClass distributions, isAtt.
difficulty  DifficultyLevels § Combat columns: the combat columns per row.
isc         ItemStatCost § Combat stats: one line per stat of the combat list (COMBAT_STATS below) with its id,
            record offset in the .bin, ValShift, Signed, Save Bits, Save Add, Save Param Bits, damagerelated, op.
items       Weapons and Armor § Combat columns: per column the rows with a value and the range.
states      States: the rows the on-hit effects are expected to set (ON_HIT_STATES below), by row id, with stat,
            flags and functions.
skills      Skills: for each damage-feeding column the rows with a value, and the normal attack row (row 0).
summary     the counts of every section only.

Every command ends with `SURVEY combat key=value ...`; tools/gate.py --full compares the summary line with its
baseline. Values come from the .bin records decoded with the layouts of tools/excel_layouts.py (what the game
loads); whether a cell is blank comes from the .txt (a blank integer cell compiles to 0). The stat and state lists
are chosen by name ([L] meanings, docs/tables/ItemStatCost.md § Combat stats). Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402

DIFF = ["", "(N)", "(H)"]
DIFF_NAME = ["normal", "nightmare", "hell"]
DK = ["n", "nm", "h"]   # survey-key suffix per difficulty
MODES = ["DT", "NU", "WL", "GH", "A1", "A2", "BL", "SC", "S1", "S2", "S3", "S4", "DD", "KB", "SQ", "RN"]

# The stats a combat formula is expected to read, by ItemStatCost `Stat` name, grouped as plan 0037 Phase 0 asks.
COMBAT_STATS = [
    ("attacker", ["level", "strength", "dexterity"]),
    ("attack rating", ["tohit", "item_tohit_percent", "item_ignoretargetac", "item_fractionaltargetac",
                       "item_demon_tohit", "item_undead_tohit", "attack_vs_montype"]),
    ("defence", ["armorclass", "armorclass_vs_missile", "armorclass_vs_hth", "item_armor_percent"]),
    ("block", ["toblock"]),
    ("damage", ["mindamage", "maxdamage", "secondary_mindamage", "secondary_maxdamage", "item_throw_mindamage",
                "item_throw_maxdamage", "damagepercent", "item_mindamage_percent", "item_maxdamage_percent",
                "item_normaldamage", "item_demondamage_percent", "item_undeaddamage_percent", "damage_vs_montype",
                "item_kickdamage"]),
    ("fire", ["firemindam", "firemaxdam", "firelength", "burningmin", "burningmax"]),
    ("lightning", ["lightmindam", "lightmaxdam"]),
    ("magic", ["magicmindam", "magicmaxdam"]),
    ("cold", ["coldmindam", "coldmaxdam", "coldlength"]),
    ("poison", ["poisonmindam", "poisonmaxdam", "poisonlength", "poison_count"]),
    ("leech", ["lifedrainmindam", "lifedrainmaxdam", "manadrainmindam", "manadrainmaxdam", "stamdrainmindam",
               "stamdrainmaxdam"]),
    ("other on-hit", ["stunlength", "item_crushingblow", "item_deadlystrike", "item_openwounds", "item_freeze",
                      "item_slow", "item_preventheal", "item_pierce", "item_knockback", "item_damagetomana",
                      "item_halffreezeduration", "item_cannotbefrozen", "item_poisonlengthresist",
                      "passive_critical_strike"]),
    ("resistance", ["damageresist", "magicresist", "fireresist", "lightresist", "coldresist", "poisonresist"]),
    ("max resistance", ["maxmagicresist", "maxfireresist", "maxlightresist", "maxcoldresist", "maxpoisonresist"]),
    ("damage reduction", ["normal_damage_reduction", "magic_damage_reduction"]),
    ("absorb", ["item_absorbfire_percent", "item_absorbfire", "item_absorblight_percent", "item_absorblight",
                "item_absorbmagic_percent", "item_absorbmagic", "item_absorbcold_percent", "item_absorbcold"]),
    ("enemy resistance", ["item_pierce_cold", "item_pierce_fire", "item_pierce_ltng", "item_pierce_pois",
                          "passive_fire_pierce", "passive_ltng_pierce", "passive_cold_pierce",
                          "passive_pois_pierce", "passive_mag_pierce"]),
    ("life", ["hitpoints", "maxhp", "mana", "maxmana", "stamina", "hpregen"]),
    ("avoidance", ["passive_dodge", "passive_avoid", "passive_evade"]),
]

# The states the on-hit effects are expected to set, by States `state` name.
ON_HIT_STATES = ["freeze", "poison", "cold", "stunned", "openwounds", "preventheal", "slowed", "shatter",
                 "burning", "justhit", "uninterruptable"]

# MonStats columns surveyed in § Combat columns.
MON_ONE = ["Drain", "coldeffect", "ToBlock"]
MON_ATTACKS = [("A1", ["A1MinD", "A1MaxD", "A1TH"]), ("A2", ["A2MinD", "A2MaxD", "A2TH"]),
               ("S1", ["S1MinD", "S1MaxD", "S1TH"])]
EL_PER_DIFF = ["Pct", "MinD", "MaxD", "Dur"]

WEAPON_COLS = ["mindam", "maxdam", "1or2handed", "2handed", "2handmindam", "2handmaxdam", "minmisdam", "maxmisdam",
               "rangeadder", "speed", "StrBonus", "DexBonus", "reqstr", "reqdex", "durability", "nodurability",
               "hit class", "missiletype"]
ARMOR_COLS = ["minac", "maxac", "block", "absorbs", "speed", "mindam", "maxdam", "StrBonus", "DexBonus", "reqstr",
              "durability"]

SKILL_COLS = ["ToHit", "LevToHit", "ToHitCalc", "HitShift", "SrcDam", "MinDam", "MaxDam", "MinLevDam1",
              "MaxLevDam1", "DmgSymPerCalc", "EType", "EMin", "EMax", "EMinLev1", "EMaxLev1", "EDmgSymPerCalc", "ELen",
              "ELevLen1", "ELenSymPerCalc", "HitFlags", "HitClass", "Kick", "range", "weapsel", "srvdofunc",
              "srvstfunc"]

DL_COLS = ["ResistPenalty", "MonsterFreezeDivisor", "MonsterColdDivisor", "AiCurseDivisor", "LifeStealDivisor",
           "ManaStealDivisor", "UniqueDamageBonus", "ChampionDamageBonus", "HireableBossDamagePercent",
           "MonsterCEDamagePercent", "StaticFieldMin"]


class Table:
    """One excel table: .txt rows as dicts and .bin records decoded with the layout (dicts by column name)."""

    def __init__(self, excel_dir, name, refs):
        header, rows, recs, size = eb.load_table(excel_dir, name)
        lay = LAYOUTS[name]
        assert size == lay["size"], (name, size)
        self.txt = [dict(zip(header, r)) for r in rows]
        self.rec = [{(f.get("name") or f["col"]): eb.decode_field(b, f, refs) for f in lay["fields"]} for b in recs]
        self.fields = {(f.get("name") or f["col"]): f for f in lay["fields"]}
        assert len(self.txt) == len(self.rec), name

    def blank(self, i, col):
        return self.txt[i].get(col, "") == ""


class Data:
    def __init__(self, excel_dir):
        self.refs = eb.Refs(excel_dir)
        self.t = {}
        for name in ("elemtypes", "monmode", "plrmode", "monstats", "monstats2", "difficultylevels",
                     "itemstatcost", "weapons", "armor", "states", "skills"):
            self.t[name] = Table(excel_dir, name, self.refs)
        self.elem = [r["Code"] for r in self.t["elemtypes"].txt]
        self.mmode = [r["code"] for r in self.t["monmode"].txt]
        self.pmode = [r["Code"] for r in self.t["plrmode"].txt]
        self.skills = [r["skill"] for r in self.t["skills"].txt]
        self.stats = [r["Stat"] for r in self.t["itemstatcost"].txt]


def rng(vals):
    vals = list(vals)
    if not vals:
        return "-"
    lo, hi = min(vals), max(vals)
    return "%d..%d (%d distinct)" % (lo, hi, len(set(vals))) if lo != hi else "always %d" % lo


def hist(vals):
    c = collections.Counter(vals)
    return ", ".join("%s x%d" % (k, n) for k, n in sorted(c.items(), key=lambda kv: (str(kv[0]))))


# ---------------------------------------------------------------- sections: each returns (lines, kv)

def sec_codes(d):
    out, kv = [], collections.OrderedDict()
    ms, sk, m2 = d.t["monstats"], d.t["skills"], d.t["monstats2"]
    kv["elemtypes_rows"] = len(d.t["elemtypes"].rec)
    kv["monmode_rows"] = len(d.t["monmode"].rec)
    kv["plrmode_rows"] = len(d.t["plrmode"].rec)

    use_el = collections.Counter()
    for i, r in enumerate(ms.rec):
        for e in (1, 2, 3):
            if not ms.blank(i, "El%dType" % e):
                use_el[("monstats", r["El%dType" % e])] += 1
    for i, r in enumerate(sk.rec):
        if not sk.blank(i, "EType"):
            use_el[("skills", r["EType"])] += 1
    out.append("ElemTypes: index code token-name | MonStats El<e>Type cells | Skills EType cells")
    for k, row in enumerate(d.t["elemtypes"].txt):
        out.append("  %2d %-4s %-14s | %3d | %3d" % (k, row["Code"] or "(blank)", row["Elemental Type"],
                                                   use_el[("monstats", k)], use_el[("skills", k)]))
    kv["el_cells_monstats"] = sum(n for (t, _), n in use_el.items() if t == "monstats")
    kv["el_cells_skills"] = sum(n for (t, _), n in use_el.items() if t == "skills")
    kv["el_types_used"] = len({k for (_, k) in use_el})

    use_m = collections.Counter()
    for i, r in enumerate(ms.rec):
        for e in (1, 2, 3):
            if not ms.blank(i, "El%dMode" % e):
                use_m[("el", r["El%dMode" % e])] += 1
        for k in range(1, 9):
            c = "Sk%dmode" % k
            if not ms.blank(i, c) and ms.txt[i][c] in d.mmode:
                use_m[("sk", r[c])] += 1
        if not ms.blank(i, "spawnmode"):
            use_m[("spawn", r["spawnmode"])] += 1
    for i, r in enumerate(sk.rec):
        if not sk.blank(i, "monanim"):
            use_m[("monanim", r["monanim"])] += 1
        if not sk.blank(i, "summode"):
            use_m[("summode", r["summode"])] += 1
    for i, r in enumerate(m2.rec):
        if not m2.blank(i, "ResurrectMode"):
            use_m[("resurrect", r["ResurrectMode"])] += 1
    out.append("MonMode: index code token name | El<e>Mode, Sk<k>mode, spawnmode (MonStats) | monanim, summode "
               "(Skills) | ResurrectMode (MonStats2)")
    for k, row in enumerate(d.t["monmode"].txt):
        rec = d.t["monmode"].rec[k]
        out.append("  %2d %-2s %-2s %-10s | %3d %3d %3d | %3d %3d | %3d" % (
            k, row["code"], rec["token"], row["name"], use_m[("el", k)], use_m[("sk", k)], use_m[("spawn", k)],
            use_m[("monanim", k)], use_m[("summode", k)], use_m[("resurrect", k)]))
    kv["monmode_token_ne_code"] = sum(1 for k, row in enumerate(d.t["monmode"].txt)
                                      if row["code"] != d.t["monmode"].rec[k]["token"])
    kv["monmode_cells"] = sum(use_m.values())

    use_p = collections.Counter()
    for i, r in enumerate(sk.rec):
        for c in ("anim", "seqtrans"):
            if not sk.blank(i, c):
                use_p[(c, r[c])] += 1
    out.append("PlrMode: index code token name | Skills anim cells | Skills seqtrans cells")
    for k, row in enumerate(d.t["plrmode"].txt):
        rec = d.t["plrmode"].rec[k]
        out.append("  %2d %-2s %-2s %-12s | %3d | %3d" % (k, row["Code"], rec["Token"], row["Name"],
                                                       use_p[("anim", k)], use_p[("seqtrans", k)]))
    kv["plrmode_token_ne_code"] = sum(1 for k, row in enumerate(d.t["plrmode"].txt)
                                      if row["Code"] != d.t["plrmode"].rec[k]["Token"])
    kv["plrmode_cells"] = sum(use_p.values())
    return out, kv


def sec_monstats(d):
    out, kv = [], collections.OrderedDict()
    ms, m2 = d.t["monstats"], d.t["monstats2"]
    n = len(ms.rec)
    m2rec = [m2.rec[r["MonStatsEx"]] if 0 <= r["MonStatsEx"] < len(m2.rec) else None for r in ms.rec]

    out.append("Attack modes (records of %d): set = any of MinD/MaxD/TH non-blank; with m<mode> = MonStats2 row has "
               "the mode bit" % n)
    for mode, cols in MON_ATTACKS:
        for di, dn in enumerate(DIFF):
            sets = [i for i in range(n) if any(not ms.blank(i, c + dn) for c in cols)]
            withm = [i for i in sets if m2rec[i] is not None and m2rec[i]["m" + mode]]
            th = [ms.rec[i][cols[2] + dn] for i in sets]
            mind = [ms.rec[i][cols[0] + dn] for i in sets]
            maxd = [ms.rec[i][cols[1] + dn] for i in sets]
            zero = sum(1 for i in sets if ms.rec[i][cols[1] + dn] == 0)
            out.append("  %s %-9s set %3d  with m%s %3d  MinD %s  MaxD %s  TH %s  MaxD 0: %d" % (
                mode, DIFF_NAME[di], len(sets), mode, len(withm), rng(mind), rng(maxd), rng(th), zero))
            kv["%s_%s_set" % (mode.lower(), DK[di])] = len(sets)
            kv["%s_%s_mode" % (mode.lower(), DK[di])] = len(withm)
        nomode = [i for i in range(n) if m2rec[i] is not None and m2rec[i]["m" + mode]
                  and all(ms.blank(i, c + dn) for c in cols for dn in DIFF)]
        out.append("  %s: records whose MonStats2 row has m%s but no %s cell in any difficulty: %d" % (
            mode, mode, mode, len(nomode)))
        kv["%s_mode_nocells" % mode.lower()] = len(nomode)
    s1 = [i for i in range(n) if any(not ms.blank(i, c + dn) for c in MON_ATTACKS[2][1] for dn in DIFF)]
    s1seq = [i for i in s1 if ms.txt[i]["Sk1mode"].startswith("seq_") and m2rec[i] is not None and m2rec[i]["mSQ"]]
    out.append("  S1 records whose Sk1mode is a sequence (seq_*) and whose MonStats2 row has mSQ: %d of %d (%s)" % (
        len(s1seq), len(s1), hist(ms.txt[i]["Skill1"] for i in s1)))
    kv["s1_seq"] = len(s1seq)

    out.append("Elemental groups El<e> (one Mode and Type for all difficulties; Pct/MinD/MaxD/Dur per difficulty)")
    for e in (1, 2, 3):
        mode_set = [i for i in range(n) if not ms.blank(i, "El%dMode" % e)]
        type_set = [i for i in range(n) if not ms.blank(i, "El%dType" % e)]
        modes = hist(d.mmode[ms.rec[i]["El%dMode" % e]] for i in mode_set)
        types = hist(d.elem[ms.rec[i]["El%dType" % e]] for i in type_set)
        has_mode = sum(1 for i in mode_set if m2rec[i] is not None
                       and m2rec[i]["m" + d.mmode[ms.rec[i]["El%dMode" % e]]])
        out.append("  El%d Mode set %d (%s); Type set %d (%s); mode present in MonStats2 %d" % (
            e, len(mode_set), modes or "-", len(type_set), types or "-", has_mode))
        kv["el%d_mode_set" % e] = len(mode_set)
        kv["el%d_type_set" % e] = len(type_set)
        kv["el%d_mode_in_m2" % e] = has_mode
        for di, dn in enumerate(DIFF):
            parts = []
            for c in EL_PER_DIFF:
                col = "El%d%s%s" % (e, c, dn)
                vals = [ms.rec[i][col] for i in range(n) if not ms.blank(i, col)]
                parts.append("%s %d %s" % (c, len(vals), rng(vals)))
                kv["el%d_%s_%s" % (e, c.lower(), DK[di])] = len(vals)
            nodmg = sum(1 for i in range(n) if not ms.blank(i, "El%dType" % e)
                        and ms.blank(i, "El%dMinD%s" % (e, dn)) and ms.blank(i, "El%dMaxD%s" % (e, dn)))
            out.append("    %-9s %s; Type set but MinD and MaxD blank: %d" % (DIFF_NAME[di], "; ".join(parts), nodmg))
        orphan = sum(1 for i in range(n) if ms.blank(i, "El%dType" % e)
                     and any(not ms.blank(i, "El%d%s%s" % (e, c, dn)) for c in EL_PER_DIFF for dn in DIFF))
        out.append("    cells set with El%dType blank: %d records" % (e, orphan))
        kv["el%d_orphan" % e] = orphan
    el_dur = collections.Counter()
    for i in range(n):
        for e in (1, 2, 3):
            if not ms.blank(i, "El%dType" % e) and any(not ms.blank(i, "El%dDur%s" % (e, dn)) for dn in DIFF):
                el_dur[d.elem[ms.rec[i]["El%dType" % e]]] += 1
    out.append("  El<e>Dur set, by El<e>Type (record-groups): %s" % (hist(el_dur.elements()) or "-"))

    out.append("One-byte combat columns per difficulty (set = non-blank cell)")
    for c in MON_ONE:
        for di, dn in enumerate(DIFF):
            vals = [ms.rec[i][c + dn] for i in range(n) if not ms.blank(i, c + dn)]
            out.append("  %-10s %-9s set %3d  %s" % (c, DIFF_NAME[di], len(vals), rng(vals)))
            kv["%s_%s" % (c.lower(), DK[di])] = len(vals)
    nsb = [i for i in range(n) if ms.rec[i]["NoShldBlock"]]
    tb_any = [i for i in range(n) if any(ms.rec[i]["ToBlock" + dn] > 0 for dn in DIFF)]
    out.append("  NoShldBlock 1: %d records; ToBlock > 0 in some difficulty: %d; both: %d" % (
        len(nsb), len(tb_any), len(set(nsb) & set(tb_any))))
    kv["noshldblock"] = len(nsb)
    kv["toblock_any"] = len(tb_any)
    kv["noshldblock_and_toblock"] = len(set(nsb) & set(tb_any))
    mbl = sum(1 for i in tb_any if m2rec[i] is not None and m2rec[i]["mBL"])
    out.append("  ToBlock > 0 records whose MonStats2 row has mBL: %d" % mbl)
    kv["toblock_mbl"] = mbl

    flags = collections.OrderedDict((c, [i for i in range(n) if ms.rec[i][c]])
                                    for c in ("noRatio", "isMelee", "rangedtype", "deathDmg"))
    for c, rows in flags.items():
        out.append("  %-10s 1 on %d records" % (c, len(rows)))
        kv[c.lower()] = len(rows)
    crit = [ms.rec[i]["Crit"] for i in range(n) if not ms.blank(i, "Crit")]
    out.append("  Crit set %d %s" % (len(crit), rng(crit)))
    kv["crit"] = len(crit)
    dr = [ms.rec[i]["DamageRegen"] for i in range(n) if not ms.blank(i, "DamageRegen")]
    out.append("  DamageRegen set %d %s; non-zero %d" % (len(dr), rng(dr), sum(1 for v in dr if v)))
    kv["damageregen_set"] = len(dr)
    kv["damageregen_nonzero"] = sum(1 for v in dr if v)
    sd = [i for i in range(n) if not ms.blank(i, "SkillDamage")]
    out.append("  SkillDamage set %d: %s" % (len(sd), hist(ms.txt[i]["SkillDamage"] for i in sd)))
    kv["skilldamage"] = len(sd)
    for c in ("MissA1", "MissA2", "MissS1", "MissC"):
        rows = [i for i in range(n) if not ms.blank(i, c)]
        rt = sum(1 for i in rows if ms.rec[i]["rangedtype"])
        out.append("  %-6s set %3d; of them rangedtype %3d" % (c, len(rows), rt))
        kv[c.lower()] = len(rows)
        kv[c.lower() + "_ranged"] = rt
    rt_nomiss = sum(1 for i in flags["rangedtype"] if ms.blank(i, "MissA1") and ms.blank(i, "MissA2"))
    out.append("  rangedtype with MissA1 and MissA2 blank: %d" % rt_nomiss)
    kv["ranged_nomiss"] = rt_nomiss
    melee_ranged = len(set(flags["isMelee"]) & set(flags["rangedtype"]))
    out.append("  isMelee and rangedtype: %d" % melee_ranged)
    kv["melee_and_ranged"] = melee_ranged
    return out, kv


def sec_monstats2(d):
    out, kv = [], collections.OrderedDict()
    m2 = d.t["monstats2"]
    n = len(m2.rec)
    out.append("MonStats2 mode bits m<XX> at +0x0F0 (bit k = MonMode row k), rows with the bit (of %d)" % n)
    parts = []
    for k, m in enumerate(MODES):
        c = sum(1 for r in m2.rec if r["m" + m])
        parts.append("%s %d" % (m, c))
        kv["m%s" % m.lower()] = c
    out.append("  " + ", ".join(parts))
    out.append("  MeleeRng: %s" % hist(r["MeleeRng"] for r in m2.rec))
    out.append("  HitClass: %s" % hist(r["HitClass"] for r in m2.rec))
    out.append("  BaseW: %s" % hist(r["BaseW"] for r in m2.rec))
    kv["meleerng_distinct"] = len({r["MeleeRng"] for r in m2.rec})
    kv["hitclass_distinct"] = len({r["HitClass"] for r in m2.rec})
    for c in ("isAtt", "small", "large", "soft"):
        kv[c.lower()] = sum(1 for r in m2.rec if r[c])
        out.append("  %-6s 1 on %d rows" % (c, kv[c.lower()]))
    a_nomr = sum(1 for r in m2.rec if (r["mA1"] or r["mA2"]) and r["MeleeRng"] == 0)
    out.append("  mA1 or mA2 with MeleeRng 0: %d" % a_nomr)
    kv["attack_meleerng0"] = a_nomr
    return out, kv


def sec_difficulty(d):
    out, kv = [], collections.OrderedDict()
    dl = d.t["difficultylevels"]
    out.append("%-26s %s" % ("column (.bin offset)", "  ".join("%9s" % r["Name"] for r in dl.txt)))
    for c in DL_COLS:
        f = dl.fields[c]
        out.append("%-26s %s" % ("%s (+0x%03X)" % (c, f["off"]), "  ".join("%9d" % r[c] for r in dl.rec)))
    kv["dl_rows"] = len(dl.rec)
    kv["dl_cols"] = len(DL_COLS)
    return out, kv


def sec_isc(d):
    out, kv = [], collections.OrderedDict()
    isc = d.t["itemstatcost"]
    size = LAYOUTS["itemstatcost"]["size"]
    out.append("group | id Stat | record at file offset | ValShift Signed SaveBits SaveAdd SaveParamBits damagerelated "
               "op")
    n = missing = signed = shifted = saved = dmg = 0
    for group, names in COMBAT_STATS:
        for name in names:
            if name not in d.stats:
                out.append("  %-16s MISSING %s" % (group, name))
                missing += 1
                continue
            i = d.stats.index(name)
            r = isc.rec[i]
            n += 1
            signed += r["Signed"]
            shifted += 1 if r["ValShift"] else 0
            saved += 1 if r["Save Bits"] else 0
            dmg += r["damagerelated"]
            out.append("  %-16s %3d %-26s 0x%05X  %d %d %2d %4d %2d %d %d" % (
                group, i, name, 4 + size * i, r["ValShift"], r["Signed"], r["Save Bits"], r["Save Add"],
                r["Save Param Bits"], r["damagerelated"], r["op"]))
    kv["isc_stats"] = n
    kv["isc_missing"] = missing
    kv["isc_signed"] = signed
    kv["isc_valshift"] = shifted
    kv["isc_saved"] = saved
    kv["isc_damagerelated"] = dmg
    return out, kv


def _item_cols(t, cols, label, out, kv):
    for c in cols:
        if c not in t.fields:
            continue
        rows = [i for i in range(len(t.rec)) if not t.blank(i, c)]
        vals = [t.rec[i][c] for i in rows]
        nz = sum(1 for v in vals if v)
        f = t.fields[c]
        out.append("  %-12s +0x%03X %-4s set %3d non-zero %3d  %s" % (c, f["off"], f["type"], len(rows), nz,
                                                                      rng(vals) if vals else "-"))
        kv["%s_%s" % (label, c.lower().replace(" ", ""))] = nz


def sec_items(d):
    out, kv = [], collections.OrderedDict()
    w, a = d.t["weapons"], d.t["armor"]
    out.append("Weapons (%d records): column offset type | set (non-blank .txt) | non-zero | range" % len(w.rec))
    _item_cols(w, WEAPON_COLS, "w", out, kv)
    both = sum(1 for r in w.rec if r["mindam"] or r["maxdam"])
    two = sum(1 for r in w.rec if r["2handmindam"] or r["2handmaxdam"])
    one_two = sum(1 for r in w.rec if r["1or2handed"])
    mis = sum(1 for r in w.rec if r["minmisdam"] or r["maxmisdam"])
    out.append("  one-hand damage %d, two-hand damage %d, 1or2handed %d, missile damage %d" % (both, two, one_two, mis))
    kv["w_rows"] = len(w.rec)
    kv["w_onehand"] = both
    kv["w_twohand"] = two
    kv["w_both_dmg"] = sum(1 for r in w.rec if (r["mindam"] or r["maxdam"]) and (r["2handmindam"] or r["2handmaxdam"]))
    out.append("  rows with one-hand and two-hand damage: %d" % kv["w_both_dmg"])
    out.append("Armor (%d records)" % len(a.rec))
    _item_cols(a, ARMOR_COLS, "a", out, kv)
    types = d.refs.names("itemtypes:Code")
    out.append("  armor rows with damage, by type: %s" % hist(
        types[r["type"]] for r in a.rec if r["mindam"] or r["maxdam"]))
    out.append("  armor rows with block, by type: %s" % hist(types[r["type"]] for r in a.rec if r["block"]))
    kv["a_rows"] = len(a.rec)
    return out, kv


def sec_states(d):
    out, kv = [], collections.OrderedDict()
    st = d.t["states"]
    names = [r["state"] for r in st.txt]
    out.append("state | id | stat | setfunc remfunc srvactivefunc | flags set")
    flagcols = [f["col"] for f in LAYOUTS["states"]["fields"] if f.get("type") == "bit"]
    found = 0
    for s in ON_HIT_STATES:
        if s not in names:
            out.append("  %-16s MISSING" % s)
            continue
        found += 1
        i = names.index(s)
        r = st.rec[i]
        stat = d.stats[r["stat"]] if r["stat"] < len(d.stats) else "-"
        fl = [c for c in flagcols if r[c]]
        out.append("  %-16s %3d %-22s %3d %3d %3d | %s" % (s, r["id"], stat, r["setfunc"], r["remfunc"],
                                                         r["srvactivefunc"], " ".join(fl) or "-"))
    kv["states_listed"] = len(ON_HIT_STATES)
    kv["states_found"] = found
    kv["states_rows"] = len(st.rec)
    return out, kv


def sec_skills(d):
    out, kv = [], collections.OrderedDict()
    sk = d.t["skills"]
    n = len(sk.rec)
    out.append("Skills (%d rows): column | rows with a non-blank cell | rows with a non-zero value | values" % n)
    for c in SKILL_COLS:
        rows = [i for i in range(n) if not sk.blank(i, c)]
        f = sk.fields[c]
        if f["type"] == "calc":
            nz = len(rows)
            desc = "%d distinct formulas" % len({sk.txt[i][c] for i in rows})
        elif f["type"] == "ref" and c == "EType":
            nz = len(rows)
            desc = hist(d.elem[sk.rec[i][c]] for i in rows)
        elif f["type"] == "enum":
            nz = sum(1 for i in rows if sk.rec[i][c])
            desc = hist(sk.txt[i][c] for i in rows)
        else:
            vals = [sk.rec[i][c] for i in rows]
            nz = sum(1 for v in vals if v)
            desc = rng(vals)
        out.append("  %-15s +0x%03X %3d %3d  %s" % (c, f["off"], len(rows), nz, desc))
        kv["sk_" + c.lower()] = len(rows)
    dmg = [i for i in range(n) if not sk.blank(i, "MinDam") or not sk.blank(i, "EMin") or not sk.blank(i, "SrcDam")]
    kv["sk_any_damage"] = len(dmg)
    out.append("  rows with MinDam, EMin or SrcDam set: %d" % len(dmg))
    srcdam_cls = hist(sk.txt[i]["charclass"] or "(none)" for i in range(n) if not sk.blank(i, "SrcDam"))
    out.append("  SrcDam rows by charclass: %s" % srcdam_cls)
    r0, t0 = sk.rec[0], sk.txt[0]
    out.append("Row 0 (the normal attack): skill %s Id %d charclass %s anim %s monanim %s range %s srvstfunc %d "
               "srvdofunc %d HitShift %d SrcDam %d ToHit %d MinDam %d EType %s" % (
                   t0["skill"], r0["Id"], t0["charclass"] or "(blank)", t0["anim"] or "(blank)",
                   t0["monanim"] or "(blank)", t0["range"], r0["srvstfunc"], r0["srvdofunc"], r0["HitShift"],
                   r0["SrcDam"], r0["ToHit"], r0["MinDam"], t0["EType"] or "(blank)"))
    kv["sk_rows"] = n
    for name in ("Attack", "Kick", "Throw", "Left Hand Swing", "Left Hand Throw"):
        if name in d.skills:
            i = d.skills.index(name)
            out.append("  %-16s row %d anim %-2s srvdofunc %3d HitShift %d SrcDam %3d range %s" % (
                name, i, sk.txt[i]["anim"] or "-", sk.rec[i]["srvdofunc"], sk.rec[i]["HitShift"], sk.rec[i]["SrcDam"],
                sk.txt[i]["range"]))
    return out, kv


SECTIONS = collections.OrderedDict([
    ("codes", sec_codes), ("monstats", sec_monstats), ("monstats2", sec_monstats2), ("difficulty", sec_difficulty),
    ("isc", sec_isc), ("items", sec_items), ("states", sec_states), ("skills", sec_skills)])


def survey_line(kv):
    return "SURVEY combat " + " ".join("%s=%d" % (k, v) for k, v in kv.items())


def main(argv):
    if len(argv) != 3 or (argv[1] not in SECTIONS and argv[1] != "summary"):
        print(__doc__)
        return 2
    d = Data(argv[2])
    if argv[1] == "summary":
        kv = collections.OrderedDict()
        for name, fn in SECTIONS.items():
            kv.update(fn(d)[1])
        print(survey_line(kv))
        return 0
    lines, kv = SECTIONS[argv[1]](d)
    print("\n".join(lines))
    print(survey_line(kv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

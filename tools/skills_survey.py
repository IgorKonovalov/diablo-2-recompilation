"""Survey of the skill and missile dispatch columns (plan 0045 Phase 0).

Usage:
  python3 -I tools/skills_survey.py skills   <excel-dir>
  python3 -I tools/skills_survey.py missiles <excel-dir>
  python3 -I tools/skills_survey.py pettype  <excel-dir>
  python3 -I tools/skills_survey.py families <excel-dir>
  python3 -I tools/skills_survey.py tiera    <excel-dir>
  python3 -I tools/skills_survey.py summary  <excel-dir>

skills    Skills § Dispatch: rows per srvstfunc, srvdofunc and srvprgfunc1..3 number (each number with its rows),
          the progressive, missile, param, animation, cost, requirement and summon columns: rows set and values.
          The client columns (cltstfunc, cltdofunc, cltprgfunc1..3, cltmissile*) are counted only (presentation).
missiles  Missiles: rows per server do, hit and damage function number (each number with its rows), the client
          function columns counted, the motion, collision, damage, link and param columns: rows set and values; the
          sub-missile and explosion links resolved; the missiles the Skills srvmissile* columns name.
pettype   PetType: one line per row, with the skills whose pettype names it and their summon and petmax.
families  the family sizes: per function number (Skills srvstfunc, srvdofunc, srvprgfunc; Missiles pSrvDoFunc,
          pSrvHitFunc, pSrvDmgFunc) the number of stock rows, largest first, and the families of ten rows or more.
tiera     the tier-A candidate rows of plan 0045 (the general rows, the per-class pairs, one row for each function
          family of ten rows or more that no candidate covers): their dispatch columns and their missiles' functions.
summary   the counts of every section only.

Every command ends with `SURVEY skills key=value ...`; tools/gate.py --full compares the summary line with its
baseline. Values come from the .bin records decoded with the layouts of tools/excel_layouts.py (what the game loads);
whether a cell is blank comes from the .txt. Meanings are [L] unless a finding anchors them (docs/tables/Missiles.md,
docs/tables/Skills.md § Dispatch, docs/tables/PetType.md). Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
from combat_survey import Table, hist  # noqa: E402

SK_FUNCS = ("srvstfunc", "srvdofunc", "srvprgfunc1", "srvprgfunc2", "srvprgfunc3")
SK_CLT_FUNCS = ("cltstfunc", "cltdofunc", "cltprgfunc1", "cltprgfunc2", "cltprgfunc3")
SK_MISSILES = ("srvmissile", "srvmissilea", "srvmissileb", "srvmissilec")
SK_CLT_MISSILES = ("cltmissile", "cltmissilea", "cltmissileb", "cltmissilec", "cltmissiled")
MS_SRV_FUNCS = ("pSrvDoFunc", "pSrvHitFunc", "pSrvDmgFunc")
MS_CLT_FUNCS = ("pCltDoFunc", "pCltHitFunc")
MS_LINKS = ("ExplosionMissile", "SubMissile1", "SubMissile2", "SubMissile3", "HitSubMissile1", "HitSubMissile2",
            "HitSubMissile3", "HitSubMissile4")
MS_CLT_LINKS = ("CltSubMissile1", "CltSubMissile2", "CltSubMissile3", "CltHitSubMissile1", "CltHitSubMissile2",
                "CltHitSubMissile3", "CltHitSubMissile4")
MS_PARAMS = ["Param%d" % k for k in range(1, 6)] + ["sHitPar%d" % k for k in range(1, 4)] + \
            ["dParam1", "dParam2"]
MS_CLT_PARAMS = ["CltParam%d" % k for k in range(1, 6)] + ["cHitPar%d" % k for k in range(1, 4)]
MS_CALCS = ("SrvCalc1", "SHitCalc1", "DmgCalc1", "DmgSymPerCalc", "EDmgSymPerCalc")
MS_CLT_CALCS = ("CltCalc1", "CHitCalc1")

# plan 0045 Phase 1 "tier A": the general rows and per class the skills the pilot can cast (self-centred, directional,
# melee or summon). The plan names the first 17; the Druid and Assassin pairs are this phase's proposal (rows by their
# skills.txt names: Fire Trauma is Fire Blast). The review
# of Phase 1 fixes the list.
TIER_A = [
    ("general", ["Attack", "Kick", "Throw", "Left Hand Throw", "Left Hand Swing"]),
    ("sor", ["Nova", "Frost Nova", "Static Field", "Teleport", "Fire Bolt"]),
    ("bar", ["Bash", "Howl"]),
    ("ama", ["Jab", "Multiple Shot"]),
    ("nec", ["Raise Skeleton", "Bone Armor"]),
    ("pal", ["Holy Fire", "Holy Shield"]),
    ("dru", ["Raven", "Firestorm"]),
    ("ass", ["Fire Trauma", "Fists of Fire"]),   # Fire Blast (internal name) and a progressive melee skill
]
FAMILY_MIN = 10


class Data:
    def __init__(self, excel_dir):
        self.refs = eb.Refs(excel_dir)
        self.t = {n: Table(excel_dir, n, self.refs) for n in ("skills", "missiles", "pettype")}
        for t in self.t.values():   # a ref field's not-found value (all bits set) reads as -1 here
            for c, f in t.fields.items():
                if f["type"] == "ref":
                    ones = (1 << (8 * eb.INT_SIZE[f.get("int", "u16")])) - 1
                    for r in t.rec:
                        if r[c] == ones:
                            r[c] = -1
        self.sk = self.t["skills"]
        self.ms = self.t["missiles"]
        self.pt = self.t["pettype"]
        self.skn = [r["skill"] for r in self.sk.txt]
        self.msn = [r["Missile"] for r in self.ms.txt]
        self.ptn = [r["pet type"] for r in self.pt.txt]
        self.monn = self.refs.names("monstats:Id")
        self.pmode = self.refs.names("plrmode:Code")
        self.mmode = self.refs.names("monmode:code")
        self.itn = self.refs.names("itemtypes:Code")


def set_rows(t, col):
    """Rows whose .txt cell is not blank."""
    return [i for i in range(len(t.rec)) if not t.blank(i, col)]


def span(vals):
    vals = list(vals)
    if not vals:
        return "-"
    lo, hi = min(vals), max(vals)
    return "%d..%d (%d distinct)" % (lo, hi, len(set(vals))) if lo != hi else "always %d" % lo


def by_number(t, cols, names):
    """{number: [row, ...]} over the non-blank cells of cols (a row counted once per number)."""
    out = collections.defaultdict(list)
    for c in cols:
        for i in set_rows(t, c):
            v = t.rec[i][c]
            if i not in out[v]:
                out[v].append(i)
    return {k: sorted(v) for k, v in sorted(out.items())}


def rows_str(rows, names, limit=None):
    xs = ["%d %s" % (i, names[i]) for i in rows]
    if limit and len(xs) > limit:
        return ", ".join(xs[:limit]) + ", … (%d)" % len(xs)
    return ", ".join(xs)


def func_section(out, kv, t, cols, names, key, label):
    per = by_number(t, cols, names)
    nrows = len({i for c in cols for i in set_rows(t, c)})
    kv["%s_rows" % key] = nrows
    kv["%s_numbers" % key] = len(per)
    kv["%s_max" % key] = max(per) if per else 0
    out.append("%s: %d rows, %d numbers (%s)" % (label, nrows, len(per), span(per)))
    for n, rows in per.items():
        out.append("  %3d (%d): %s" % (n, len(rows), rows_str(rows, names)))
    return per


# ---------------------------------------------------------------- Skills § Dispatch

def sec_skills(d):
    out, kv = [], collections.OrderedDict()
    t, n = d.sk, d.skn
    R = t.rec
    kv["sk_rows"] = len(R)
    for c in SK_FUNCS[:2]:
        func_section(out, kv, t, [c], n, "sk_" + c, c)
    func_section(out, kv, t, SK_FUNCS[2:], n, "sk_srvprgfunc", "srvprgfunc1..3")
    for c in SK_FUNCS[2:]:
        kv["sk_%s_set" % c] = len(set_rows(t, c))
    st, do = set(set_rows(t, "srvstfunc")), set(set_rows(t, "srvdofunc"))
    kv["sk_st_and_do"] = len(st & do)
    kv["sk_st_only"] = len(st - do)
    kv["sk_neither_st_do"] = len(R) - len(st | do)
    mis = {i for c in SK_MISSILES for i in set_rows(t, c)}
    nodo = sorted(mis - do)
    kv["sk_missile_without_do"] = len(nodo)
    out.append("srvstfunc and srvdofunc: %d rows; srvstfunc only %d; neither %d" % (
        kv["sk_st_and_do"], kv["sk_st_only"], kv["sk_neither_st_do"]))
    out.append("rows with a srvmissile* and no srvdofunc: %d: %s" % (len(nodo), rows_str(nodo, n)))
    for c in ("prgcalc1", "prgcalc2", "prgcalc3", "prgdam"):
        rows = set_rows(t, c)
        kv["sk_%s_set" % c] = len(rows)
        out.append("%s: %d rows: %s" % (c, len(rows), rows_str(rows, n)))
    out.append("prgdam values: %s" % hist(R[i]["prgdam"] for i in set_rows(t, "prgdam")))
    prog = [i for i in range(len(R)) if R[i]["progressive"]]
    kv["sk_progressive_bit"] = len(prog)
    kv["sk_prg_without_bit"] = sum(1 for i in set_rows(t, "srvprgfunc1") if not R[i]["progressive"])
    out.append("progressive bit: %d rows: %s" % (len(prog), rows_str(prog, n)))
    # client function columns: counted only
    for c in SK_CLT_FUNCS:
        kv["sk_%s_set" % c] = len(set_rows(t, c))
    out.append("client functions (presentation, counted only): %s" % ", ".join(
        "%s %d rows / %d numbers" % (c, kv["sk_%s_set" % c], len({R[i][c] for i in set_rows(t, c)}))
        for c in SK_CLT_FUNCS))
    # missiles
    named = set()
    for c in SK_MISSILES:
        rows = set_rows(t, c)
        bad = [i for i in rows if R[i][c] < 0]
        kv["sk_%s_set" % c] = len(rows)
        kv["sk_%s_unresolved" % c] = len(bad)
        vals = {R[i][c] for i in rows}
        named |= vals
        out.append("%s: %d rows, %d distinct missiles, unresolved %d" % (c, len(rows), len(vals), len(bad)))
    kv["sk_srvmissile_any"] = len({i for c in SK_MISSILES for i in set_rows(t, c)})
    kv["sk_srvmissile_distinct"] = len(named)
    out.append("rows with any srvmissile*: %d; distinct missiles named: %d" % (
        kv["sk_srvmissile_any"], kv["sk_srvmissile_distinct"]))
    for c in SK_CLT_MISSILES:
        kv["sk_%s_set" % c] = len(set_rows(t, c))
    out.append("client missiles (presentation, counted only): %s" % ", ".join(
        "%s %d" % (c, kv["sk_%s_set" % c]) for c in SK_CLT_MISSILES))
    # params
    for k in range(1, 9):
        c = "Param%d" % k
        rows = set_rows(t, c)
        kv["sk_param%d_set" % k] = len(rows)
        out.append("%s: %d rows, %s" % (c, len(rows), span(R[i][c] for i in rows)))
    # animation
    for c, names in (("anim", d.pmode), ("seqtrans", d.pmode), ("monanim", d.mmode)):
        rows = set_rows(t, c)
        kv["sk_%s_set" % c] = len(rows)
        kv["sk_%s_distinct" % c] = len({R[i][c] for i in rows})
        out.append("%s: %d rows: %s" % (c, len(rows), hist(names[R[i][c]] for i in rows)))
    rows = set_rows(t, "seqnum")
    kv["sk_seqnum_set"] = len(rows)
    out.append("seqnum: %d rows, %s; seqinput %d rows" % (len(rows), span(R[i]["seqnum"] for i in rows),
                                                          len(set_rows(t, "seqinput"))))
    kv["sk_seq_without_seqtrans"] = sum(1 for i in rows if t.blank(i, "seqtrans"))
    rows = set_rows(t, "delay")
    kv["sk_delay_set"] = len(rows)
    out.append("delay (calc): %d rows: %s" % (len(rows), rows_str(rows, n)))
    rng_names = ["none", "h2h", "rng", "both"]
    out.append("range: %s" % hist(rng_names[r["range"]] for r in R))
    for k, nm in enumerate(rng_names):
        kv["sk_range_%s" % nm] = sum(1 for r in R if r["range"] == k)
    # mana
    for c in ("startmana", "minmana", "manashift", "mana", "lvlmana"):
        rows = set_rows(t, c)
        kv["sk_%s_set" % c] = len(rows)
        out.append("%s: %d rows, %s" % (c, len(rows), span(R[i][c] for i in rows)))
    kv["sk_mana_negative"] = sum(1 for r in R if r["mana"] < 0)
    kv["sk_lvlmana_negative"] = sum(1 for r in R if r["lvlmana"] < 0)
    out.append("manashift values: %s" % hist(R[i]["manashift"] for i in set_rows(t, "manashift")))
    neg = [i for i in range(len(R)) if R[i]["lvlmana"] < 0]
    out.append("lvlmana < 0: %s" % rows_str(neg, n))
    # flags
    for c in ("InTown", "leftskill", "repeat", "TgtPlaceCheck", "AttackNoMana", "usemanaondo", "immediate",
              "interrupt", "InGame"):
        rows = [i for i in range(len(R)) if R[i][c]]
        kv["sk_%s" % c.lower()] = len(rows)
        lim = None if len(rows) <= 40 else 40
        out.append("%s bit: %d rows: %s" % (c, len(rows), rows_str(rows, n, lim)))
    # item-type requirements
    for c in ("itypea1", "itypea2", "itypea3", "itypeb1", "itypeb2", "itypeb3", "etypea1", "etypea2", "etypeb1",
              "etypeb2"):
        rows = set_rows(t, c)
        kv["sk_%s_set" % c] = len(rows)
        out.append("%s: %d rows: %s" % (c, len(rows), hist(d.itn[R[i][c]] for i in rows)))
    rows = set_rows(t, "weapsel")
    kv["sk_weapsel_set"] = len(rows)
    out.append("weapsel: %d rows: %s" % (len(rows), ", ".join("%d %s=%d" % (i, n[i], R[i]["weapsel"]) for i in rows)))
    # summon
    rows = set_rows(t, "summon")
    kv["sk_summon_set"] = len(rows)
    kv["sk_summon_unresolved"] = sum(1 for i in rows if R[i]["summon"] < 0)
    kv["sk_pettype_set"] = len(set_rows(t, "pettype"))
    kv["sk_summode_set"] = len(set_rows(t, "summode"))
    kv["sk_petmax_set"] = len(set_rows(t, "petmax"))
    kv["sk_summon_without_pettype"] = sum(1 for i in rows if t.blank(i, "pettype"))
    kv["sk_pettype_without_summon"] = sum(1 for i in set_rows(t, "pettype") if t.blank(i, "summon"))
    kv["sk_summon_without_petmax"] = sum(1 for i in rows if t.blank(i, "petmax"))
    out.append("summon: %d rows (unresolved %d), pettype %d, summode %d, petmax %d; summon without pettype %d, "
               "pettype without summon %d, summon without petmax %d" % (
                   len(rows), kv["sk_summon_unresolved"], kv["sk_pettype_set"], kv["sk_summode_set"],
                   kv["sk_petmax_set"], kv["sk_summon_without_pettype"], kv["sk_pettype_without_summon"],
                   kv["sk_summon_without_petmax"]))
    for i in sorted(set(rows) | set(set_rows(t, "pettype"))):
        r = R[i]
        sks = ["%s" % n[r["sumskill%d" % k]] for k in range(1, 6) if not t.blank(i, "sumskill%d" % k)]
        out.append("  %d %-24s summon %-16s pettype %-13s summode %-3s petmax %-24s srvdofunc %s sumskills %s" % (
            i, n[i], d.monn[r["summon"]] if r["summon"] >= 0 else "-",
            d.ptn[r["pettype"]] if not t.blank(i, "pettype") else "-",
            d.mmode[r["summode"]] if not t.blank(i, "summode") else "-",
            t.txt[i]["petmax"] or "-", r["srvdofunc"] if not t.blank(i, "srvdofunc") else "-",
            ", ".join(sks) or "-"))
    for k in range(1, 6):
        kv["sk_sumskill%d_set" % k] = len(set_rows(t, "sumskill%d" % k))
        kv["sk_sumsk%dcalc_set" % k] = len(set_rows(t, "sumsk%dcalc" % k))
    kv["sk_sumskill_without_calc"] = sum(1 for k in range(1, 6) for i in set_rows(t, "sumskill%d" % k)
                                         if t.blank(i, "sumsk%dcalc" % k))
    return out, kv


# ---------------------------------------------------------------- Missiles

def sec_missiles(d):
    out, kv = [], collections.OrderedDict()
    t, n = d.ms, d.msn
    R = t.rec
    kv["ms_rows"] = len(R)
    kv["ms_id_is_row"] = sum(1 for i, r in enumerate(R) if r["Id"] == i)
    for c in MS_SRV_FUNCS:
        func_section(out, kv, t, [c], n, "ms_" + c.lower(), c)
    kv["ms_srv_any"] = len({i for c in MS_SRV_FUNCS for i in set_rows(t, c)})
    kv["ms_srv_none"] = len(R) - kv["ms_srv_any"]
    out.append("rows with any server function: %d; with none: %d" % (kv["ms_srv_any"], kv["ms_srv_none"]))
    for c in MS_CLT_FUNCS:
        rows = set_rows(t, c)
        kv["ms_%s_set" % c.lower()] = len(rows)
        kv["ms_%s_numbers" % c.lower()] = len({R[i][c] for i in rows})
    odd = [i for i in set_rows(t, "pCltHitFunc") + set_rows(t, "pSrvHitFunc")
           if not t.txt[i]["pCltHitFunc"].isdigit() and not t.blank(i, "pCltHitFunc")
           or not t.txt[i]["pSrvHitFunc"].isdigit() and not t.blank(i, "pSrvHitFunc")]
    kv["ms_func_nondigit_cells"] = len(set(odd))
    out.append("client functions (presentation, counted only): %s" % ", ".join(
        "%s %d rows / %d numbers" % (c, kv["ms_%s_set" % c.lower()], kv["ms_%s_numbers" % c.lower()])
        for c in MS_CLT_FUNCS))
    for i in sorted(set(odd)):
        out.append("  non-digit function cell: %d %s pCltHitFunc %r -> %d, pSrvHitFunc %r -> %d" % (
            i, n[i], t.txt[i]["pCltHitFunc"], R[i]["pCltHitFunc"], t.txt[i]["pSrvHitFunc"], R[i]["pSrvHitFunc"]))
    # motion
    for c in ("Vel", "MaxVel", "VelLev", "Accel", "Range", "LevRange", "InitSteps", "Activate", "LoopAnim",
              "SubLoop", "SubStart", "SubStop", "RandStart", "NumDirections"):
        rows = set_rows(t, c)
        kv["ms_%s_set" % c.lower()] = len(rows)
        out.append("%s: %d rows, %s" % (c, len(rows), span(R[i][c] for i in rows)))
    kv["ms_range_zero"] = sum(1 for r in R if r["Range"] == 0)
    kv["ms_maxvel_below_vel"] = sum(1 for r in R if r["MaxVel"] < r["Vel"])
    kv["ms_accel_negative"] = sum(1 for r in R if r["Accel"] < 0)
    out.append("Range 0: %d rows; MaxVel < Vel: %d rows; Accel < 0: %d rows" % (
        kv["ms_range_zero"], kv["ms_maxvel_below_vel"], kv["ms_accel_negative"]))
    out.append("Accel: %s" % ", ".join("%d %s=%d (Vel %d MaxVel %d)" % (i, n[i], R[i]["Accel"], R[i]["Vel"],
                                                                     R[i]["MaxVel"]) for i in set_rows(t, "Accel")))
    # collision
    out.append("CollideType: %s" % hist(r["CollideType"] for r in R))
    for k in range(0, 9):
        kv["ms_collidetype_%d" % k] = sum(1 for r in R if r["CollideType"] == k)
    for c in ("Collision", "ClientCol", "CollideKill", "CollideFriend", "LastCollide", "NextHit", "Pierce",
              "CanDestroy", "AlwaysExplode", "Explosion", "ToHit", "Town", "SrcTown", "CanSlow", "ReturnFire",
              "GetHit", "SoftHit", "ClientSend", "NoMultiShot", "NoUniqueMod", "MissileSkill", "ApplyMastery",
              "Half2HSrc", "SpecialSetup", "Qty", "LocalBlood"):
        kv["ms_%s" % c.lower()] = sum(1 for r in R if r[c])
    out.append("flag and byte columns (rows non-zero): %s" % ", ".join(
        "%s %d" % (c, kv["ms_%s" % c.lower()]) for c in (
            "Collision", "ClientCol", "CollideKill", "CollideFriend", "LastCollide", "NextHit", "Pierce",
            "CanDestroy", "AlwaysExplode", "Explosion", "ToHit", "Town", "SrcTown", "CanSlow", "ReturnFire",
            "GetHit", "SoftHit", "ClientSend", "NoMultiShot", "NoUniqueMod", "MissileSkill", "ApplyMastery",
            "Half2HSrc", "SpecialSetup", "Qty", "LocalBlood")))
    kv["ms_collision_type0"] = sum(1 for r in R if r["Collision"] and r["CollideType"] == 0)
    kv["ms_collidekill_type0"] = sum(1 for r in R if r["CollideKill"] and r["CollideType"] == 0)
    out.append("Collision set with CollideType 0: %d; CollideKill with CollideType 0: %d" % (
        kv["ms_collision_type0"], kv["ms_collidekill_type0"]))
    out.append("Collision rows: %s" % rows_str([i for i, r in enumerate(R) if r["Collision"]], n))
    out.append("Pierce rows: %s" % rows_str([i for i, r in enumerate(R) if r["Pierce"]], n))
    for c in ("NextDelay", "Size", "KnockBack", "CltSrcTown", "Holy", "Trans", "DamageRate", "HitShift",
              "SrcDamage", "SrcMissDmg", "HitClass", "HitFlags", "ResultFlags"):
        rows = set_rows(t, c)
        kv["ms_%s_set" % c.lower()] = len(rows)
        out.append("%s: %d rows: %s" % (c, len(rows), hist(R[i][c] for i in rows)))
    kv["ms_size_nonzero"] = sum(1 for r in R if r["Size"])
    # damage
    for c in ("MinDamage", "MaxDamage", "MinLevDam1", "MaxLevDam1", "EMin", "Emax", "MinELev1", "MaxELev1", "ELen",
              "ELevLen1"):
        rows = set_rows(t, c)
        kv["ms_%s_set" % c.lower()] = len(rows)
        out.append("%s: %d rows, %s" % (c, len(rows), span(R[i][c] for i in rows)))
    elem = d.refs.names("elemtypes:Code")
    et = [i for i, r in enumerate(R) if r["EType"]]
    kv["ms_etype_set"] = len(et)
    kv["ms_etype_space"] = sum(1 for i in range(len(R)) if t.txt[i]["EType"] == " ")
    out.append("EType (non-zero): %d rows: %s; cells holding one space: %d (stored 0)" % (
        len(et), hist(elem[R[i]["EType"]] for i in et), kv["ms_etype_space"]))
    kv["ms_emin_without_etype"] = sum(1 for i in set_rows(t, "EMin") if not R[i]["EType"])
    kv["ms_etype_without_emin"] = sum(1 for i in et if t.blank(i, "EMin") and t.blank(i, "Emax"))
    out.append("EMin without EType: %d; EType without EMin/Emax: %d" % (kv["ms_emin_without_etype"],
                                                                        kv["ms_etype_without_emin"]))
    for c in MS_CALCS + MS_CLT_CALCS:
        kv["ms_%s_set" % c.lower()] = len(set_rows(t, c))
    out.append("calcs (rows set): %s" % ", ".join("%s %d" % (c, kv["ms_%s_set" % c.lower()])
                                                  for c in MS_CALCS + MS_CLT_CALCS))
    # params
    for c in MS_PARAMS + MS_CLT_PARAMS:
        rows = set_rows(t, c)
        kv["ms_%s_set" % c.lower()] = len(rows)
        out.append("%s: %d rows, %s" % (c, len(rows), span(R[i][c] for i in rows)))
    # links
    for c in MS_LINKS + MS_CLT_LINKS:
        rows = set_rows(t, c)
        bad = [i for i in rows if R[i][c] < 0]
        selfl = [i for i in rows if R[i][c] == i]
        kv["ms_%s_set" % c.lower()] = len(rows)
        kv["ms_%s_unresolved" % c.lower()] = len(bad)
        kv["ms_%s_self" % c.lower()] = len(selfl)
        out.append("%s: %d rows, %d distinct targets, unresolved %d, self %d" % (
            c, len(rows), len({R[i][c] for i in rows}), len(bad), len(selfl)))
    kv["ms_linked_any"] = len({i for c in MS_LINKS for i in set_rows(t, c)})
    targets = {R[i][c] for c in MS_LINKS for i in set_rows(t, c)}
    kv["ms_link_targets"] = len(targets)
    out.append("rows with any server link: %d; distinct targets: %d" % (kv["ms_linked_any"], len(targets)))
    # depth of the server link graph
    def depth(i, seen):
        if i in seen:
            return 0
        seen = seen | {i}
        kids = [R[i][c] for c in MS_LINKS if not t.blank(i, c) and R[i][c] >= 0]
        return 1 + max((depth(k, seen) for k in kids), default=0)
    deep = max(range(len(R)), key=lambda i: depth(i, frozenset()))
    kv["ms_link_depth_max"] = depth(deep, frozenset())
    out.append("deepest server link chain: %d levels, from %d %s" % (kv["ms_link_depth_max"], deep, n[deep]))
    rows = set_rows(t, "Skill")
    kv["ms_skill_set"] = len(rows)
    kv["ms_skill_unresolved"] = sum(1 for i in rows if R[i]["Skill"] < 0)
    out.append("Skill: %d rows (unresolved %d)" % (len(rows), kv["ms_skill_unresolved"]))
    # missiles named by skills
    sk = d.sk
    named = collections.defaultdict(set)
    for c in SK_MISSILES:
        for i in set_rows(sk, c):
            named[sk.rec[i][c]].add(i)
    kv["ms_named_by_skills"] = len(named)
    kv["ms_named_without_srvdo"] = sum(1 for m in named if t.blank(m, "pSrvDoFunc"))
    out.append("missiles named by Skills srvmissile*: %d; of them without pSrvDoFunc: %d" % (
        len(named), kv["ms_named_without_srvdo"]))
    out.append("  their pSrvDoFunc: %s" % hist(R[m]["pSrvDoFunc"] for m in named))
    return out, kv


# ---------------------------------------------------------------- PetType

def sec_pettype(d):
    out, kv = [], collections.OrderedDict()
    t, R, sk = d.pt, d.pt.rec, d.sk
    kv["pt_rows"] = len(R)
    kv["pt_idx_is_row"] = sum(1 for i, r in enumerate(R) if r["idx"] == i)
    for c in ("warp", "range", "partysend", "unsummon", "automap", "drawhp"):
        kv["pt_%s" % c] = sum(1 for r in R if r[c])
    kv["pt_group_set"] = sum(1 for r in R if r["group"])
    out.append("bits (rows set): %s; group set %d" % (", ".join("%s %d" % (c, kv["pt_%s" % c]) for c in (
        "warp", "range", "partysend", "unsummon", "automap", "drawhp")), kv["pt_group_set"]))
    out.append("basemax: %s" % hist(r["basemax"] for r in R))
    kv["pt_basemax_0"] = sum(1 for r in R if r["basemax"] == 0)
    kv["pt_basemax_1"] = sum(1 for r in R if r["basemax"] == 1)
    kv["pt_mclass_set"] = sum(1 for r in R for k in range(1, 5) if r["mclass%d" % k])
    kv["pt_mclass_bad"] = sum(1 for r in R for k in range(1, 5)
                              if r["mclass%d" % k] and r["mclass%d" % k] >= len(d.monn))
    users = collections.defaultdict(list)
    for i in set_rows(sk, "pettype"):
        users[sk.rec[i]["pettype"]].append(i)
    kv["pt_types_used_by_skills"] = len(users)
    kv["pt_skill_rows"] = sum(len(v) for v in users.values())
    for i, r in enumerate(R):
        mc = ["%d %s" % (r["mclass%d" % k], d.monn[r["mclass%d" % k]]) for k in range(1, 5) if r["mclass%d" % k]]
        out.append("  %2d %-13s group %d basemax %d bits %s%s%s%s%s%s icontype %d mclass %s" % (
            i, d.ptn[i], r["group"], r["basemax"],
            *("W" if r["warp"] else "-", "R" if r["range"] else "-", "P" if r["partysend"] else "-",
              "U" if r["unsummon"] else "-", "A" if r["automap"] else "-", "H" if r["drawhp"] else "-"),
            r["icontype"], ", ".join(mc) or "-"))
        for s in users.get(i, []):
            sr = sk.rec[s]
            out.append("       skill %d %-22s summon %-16s petmax %s" % (
                s, d.skn[s], d.monn[sr["summon"]] if sr["summon"] >= 0 else "-", sk.txt[s]["petmax"] or "-"))
    unused = [d.ptn[i] for i in range(len(R)) if i not in users]
    out.append("pet types no skill names: %s" % ", ".join(unused))
    kv["pt_unused"] = len(unused)
    return out, kv


# ---------------------------------------------------------------- families

FAMILY_COLS = [("skills", "srvstfunc", ("srvstfunc",)), ("skills", "srvdofunc", ("srvdofunc",)),
               ("skills", "srvprgfunc", SK_FUNCS[2:]), ("missiles", "pSrvDoFunc", ("pSrvDoFunc",)),
               ("missiles", "pSrvHitFunc", ("pSrvHitFunc",)), ("missiles", "pSrvDmgFunc", ("pSrvDmgFunc",))]


def families(d):
    """[(table, label, number, rows)] for every function number."""
    res = []
    for tn, label, cols in FAMILY_COLS:
        t = d.t[tn]
        names = d.skn if tn == "skills" else d.msn
        for num, rows in by_number(t, cols, names).items():
            res.append((tn, label, num, rows))
    return res


def sec_families(d):
    out, kv = [], collections.OrderedDict()
    fam = families(d)
    for tn, label, cols in FAMILY_COLS:
        mine = sorted([f for f in fam if f[1] == label], key=lambda f: (-len(f[3]), f[2]))
        big = [f for f in mine if len(f[3]) >= FAMILY_MIN]
        key = label.lower()
        kv["fam_%s_numbers" % key] = len(mine)
        kv["fam_%s_big" % key] = len(big)
        kv["fam_%s_big_rows" % key] = sum(len(f[3]) for f in big)
        kv["fam_%s_single" % key] = sum(1 for f in mine if len(f[3]) == 1)
        out.append("%s.%s: %d numbers, %d with one row, %d with >= %d rows (%d rows): %s" % (
            tn, label, len(mine), kv["fam_%s_single" % key], len(big), FAMILY_MIN, kv["fam_%s_big_rows" % key],
            ", ".join("%d x%d" % (f[2], len(f[3])) for f in big)))
        out.append("  sizes: %s" % ", ".join("%d x%d" % (f[2], len(f[3])) for f in mine))
    return out, kv


# ---------------------------------------------------------------- tier A

def tier_rows(d):
    idx = {}
    for i, nm in enumerate(d.skn):
        idx.setdefault(nm.lower(), i)
    out = []
    for grp, names in TIER_A:
        for nm in names:
            out.append((grp, nm, idx.get(nm.lower(), -1)))
    return out


def skill_missiles(d, i):
    sk = d.sk
    return list(dict.fromkeys(sk.rec[i][c] for c in SK_MISSILES if not sk.blank(i, c) and sk.rec[i][c] >= 0))


def sec_tiera(d):
    out, kv = [], collections.OrderedDict()
    sk, ms = d.sk, d.ms
    tier = tier_rows(d)
    kv["ta_named"] = len(tier)
    kv["ta_unresolved"] = sum(1 for t in tier if t[2] < 0)
    covered = set()   # (label, number)

    def cover(i):
        r = sk.rec[i]
        for lab, cols in (("srvstfunc", ("srvstfunc",)), ("srvdofunc", ("srvdofunc",)),
                          ("srvprgfunc", SK_FUNCS[2:])):
            for c in cols:
                if not sk.blank(i, c):
                    covered.add((lab, r[c]))
        for m in skill_missiles(d, i):
            for c in MS_SRV_FUNCS:
                if not ms.blank(m, c):
                    covered.add((c, ms.rec[m][c]))

    def line(grp, i):
        r = sk.rec[i]
        mis = []
        for m in skill_missiles(d, i):
            mr = ms.rec[m]
            mis.append("%s(do %s hit %s dmg %s)" % (d.msn[m], *(mr[c] if not ms.blank(m, c) else "-"
                                                                 for c in MS_SRV_FUNCS)))
        return "  %-7s %3d %-20s class %-3s st %-3s do %-3s prg %-11s anim %-2s range %-4s mana %d+%d<<%d %s" % (
            grp, i, d.skn[i], sk.txt[i]["charclass"] or "-",
            r["srvstfunc"] if not sk.blank(i, "srvstfunc") else "-",
            r["srvdofunc"] if not sk.blank(i, "srvdofunc") else "-",
            "/".join(str(r[c]) for c in SK_FUNCS[2:] if not sk.blank(i, c)) or "-",
            sk.txt[i]["anim"] or "-", ["none", "h2h", "rng", "both"][r["range"]], r["mana"], r["lvlmana"],
            r["manashift"], "missiles " + ", ".join(mis) if mis else "")

    for grp, nm, i in tier:
        if i < 0:
            out.append("  %-7s  ?  %s: no such row" % (grp, nm))
            continue
        cover(i)
        out.append(line(grp, i))
    kv["ta_rows"] = sum(1 for t in tier if t[2] >= 0)
    big = [f for f in families(d) if len(f[3]) >= FAMILY_MIN]
    kv["ta_big_families"] = len(big)
    miss = [f for f in big if (f[1], f[2]) not in covered]
    kv["ta_big_covered"] = len(big) - len(miss)
    out.append("families of >= %d rows: %d; covered by the named rows: %d" % (FAMILY_MIN, len(big),
                                                                               kv["ta_big_covered"]))
    # one representative per uncovered family: a skills row with a charclass first, else the first row; a missile
    # family by the first skill whose srvmissile* names one of its rows, else the missile row itself
    extra = 0
    for tn, label, num, rows in miss:
        if (label, num) in covered:
            out.append("  %s %d: covered by an added row" % (label, num))
            continue
        if tn == "skills":
            cls = [i for i in rows if sk.txt[i]["charclass"]]
            i = (cls or rows)[0]
            cover(i)
            extra += 1
            out.append("  %s %d (%d rows) ->" % (label, num, len(rows)))
            out.append(line("added", i))
        else:
            users = [i for i in range(len(sk.rec)) if set(skill_missiles(d, i)) & set(rows)]
            if users:
                cls = [i for i in users if sk.txt[i]["charclass"]]
                i = (cls or users)[0]
                cover(i)
                extra += 1
                out.append("  missiles.%s %d (%d rows) ->" % (label, num, len(rows)))
                out.append(line("added", i))
            else:
                out.append("  missiles.%s %d (%d rows): no skill names one of its rows directly; first row %d %s"
                           % (label, num, len(rows), rows[0], d.msn[rows[0]]))
    kv["ta_added"] = extra
    kv["ta_big_uncovered"] = sum(1 for f in big if (f[1], f[2]) not in covered)
    out.append("rows added for the uncovered families: %d; families still uncovered: %d" % (
        extra, kv["ta_big_uncovered"]))
    out.append("monster skills of the combat logs' attackers: not in the excel data; Phase 1.3 adds them from "
               "workspace/logs/combat/.")
    return out, kv


SECTIONS = collections.OrderedDict([
    ("skills", sec_skills), ("missiles", sec_missiles), ("pettype", sec_pettype), ("families", sec_families),
    ("tiera", sec_tiera)])


def survey_line(kv):
    return "SURVEY skills " + " ".join("%s=%d" % (k, v) for k, v in kv.items())


def main(argv):
    if len(argv) != 3 or (argv[1] not in SECTIONS and argv[1] != "summary"):
        print(__doc__)
        return 2
    d = Data(argv[2])
    if argv[1] == "summary":
        kv = collections.OrderedDict()
        for fn in SECTIONS.values():
            kv.update(fn(d)[1])
        print(survey_line(kv))
        return 0
    lines, kv = SECTIONS[argv[1]](d)
    print("\n".join(lines))
    print(survey_line(kv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

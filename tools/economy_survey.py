"""Survey of the price, cost and durability columns the economy code is expected to read (plan 0043 Phase 0).

Usage:
  python3 -I tools/economy_survey.py items    <excel-dir>
  python3 -I tools/economy_survey.py types    <excel-dir>
  python3 -I tools/economy_survey.py stats    <excel-dir>
  python3 -I tools/economy_survey.py affixes  <excel-dir>
  python3 -I tools/economy_survey.py npc      <excel-dir>
  python3 -I tools/economy_survey.py hireling <excel-dir>
  python3 -I tools/economy_survey.py skills   <excel-dir>
  python3 -I tools/economy_survey.py books    <excel-dir>
  python3 -I tools/economy_survey.py summary  <excel-dir>

items     Weapons/Armor/Misc § Economy: per table the ranges of cost, gamble cost, durability, nodurability,
          durwarning, qntwarning, stackable, minstack/maxstack/spawnstack, multibuy and quest; the rows that break
          a pattern (cost 0, gamble cost 0, cost above gamble cost, nodurability with a durability, a maxstack
          without stackable); the Gamble rows' gamble cost.
types     ItemTypes § Repair and throwing columns: the rows with Repair, Throwable, Reload, ReEquip, AutoStack,
          Shoots, Quiver, CostFormula; per item table, the bases whose own `type` row has Repair against their
          nodurability and durability, and the bases whose Equiv closure (Equiv1/Equiv2 to the root) has Repair.
stats     ItemStatCost § Price: Divide, Multiply, Add; every row with a non-zero Multiply or Add.
affixes   MagicPrefix/MagicSuffix/AutoMagic divide/multiply/add, UniqueItems/SetItems cost mult/add, and the
          QualityItems and RareSuffix price cells (.txt only: those columns have no field).
npc       Npc § Multipliers: one line per row.
hireling  Hireling § Costs: Gold and Exp/Lvl per (Version, Id), with the level bands.
skills    Skills § Charge cost columns: cost mult / cost add against reqlevel and charclass.
books     Books: the three rows.
summary   the counts of every section only.

Every command ends with `SURVEY economy key=value ...`; tools/gate.py --full compares the summary line with its
baseline. Values come from the .bin records decoded with the layouts of tools/excel_layouts.py (what the game
loads); whether a cell is blank, and the columns with no field, come from the .txt. Meanings are [L] unless a finding
anchors them (docs/tables/Weapons.md § Economy and the docs it links). Stdlib only. Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
from combat_survey import Table, hist  # noqa: E402

ITEM_TABLES = ("weapons", "armor", "misc")
SHORT = {"weapons": "w", "armor": "a", "misc": "m"}


class Data:
    def __init__(self, excel_dir):
        self.refs = eb.Refs(excel_dir)
        self.t = {}
        for name in ITEM_TABLES + ("itemtypes", "itemstatcost", "magicprefix", "magicsuffix", "automagic",
                                   "uniqueitems", "setitems", "npc", "hireling", "skills", "books", "gamble"):
            self.t[name] = Table(excel_dir, name, self.refs)
        self.dir = excel_dir
        self.monstats = self.refs.names("monstats:Id")
        self.types = [r["Code"] for r in self.t["itemtypes"].txt]

    def code(self, table, i):
        return self.t[table].txt[i]["code"]

    def txt(self, table):
        """.txt rows as dicts (for a table with no layout)."""
        h, rows = eb.read_txt(eb.find_file(self.dir, table, ".txt"))
        return [dict(zip(h, r)) for r in rows]


def span(vals):
    vals = list(vals)
    return (min(vals), max(vals)) if vals else (0, 0)


def codes(xs, limit=60):
    xs = list(xs)
    s = ", ".join(str(x) for x in xs[:limit])
    return s + (" … (%d)" % len(xs) if len(xs) > limit else "")


# ---------------------------------------------------------------- sections: each returns (lines, kv)

ITEM_COLS = ("cost", "gamble cost", "durability", "nodurability", "durwarning", "qntwarning", "stackable",
             "minstack", "maxstack", "spawnstack", "multibuy", "quest")


def sec_items(d):
    out, kv = [], collections.OrderedDict()
    for tn in ITEM_TABLES:
        t, s = d.t[tn], SHORT[tn]
        R = t.rec
        out.append("== %s: %d records" % (tn, len(R)))
        for c in ITEM_COLS:
            vals = [r[c] for r in R]
            lo, hi = span(vals)
            out.append("  %-12s %d..%d, %d distinct, %d non-zero, %d blank" % (
                c, lo, hi, len(set(vals)), sum(1 for v in vals if v), sum(1 for i in range(len(R)) if t.blank(i, c))))
        kv["%s_rows" % s] = len(R)
        kv["%s_cost_min" % s], kv["%s_cost_max" % s] = span(r["cost"] for r in R)
        kv["%s_cost_distinct" % s] = len({r["cost"] for r in R})
        kv["%s_cost_zero" % s] = sum(1 for r in R if r["cost"] == 0)
        kv["%s_gcost_nonzero" % s] = sum(1 for r in R if r["gamble cost"])
        kv["%s_gcost_max" % s] = max(r["gamble cost"] for r in R)
        kv["%s_cost_above_gcost" % s] = sum(1 for r in R if r["gamble cost"] and r["cost"] > r["gamble cost"])
        kv["%s_dur_nonzero" % s] = sum(1 for r in R if r["durability"])
        kv["%s_dur_max" % s] = max(r["durability"] for r in R)
        kv["%s_nodur" % s] = sum(1 for r in R if r["nodurability"])
        kv["%s_nodur_with_dur" % s] = sum(1 for r in R if r["nodurability"] and r["durability"])
        kv["%s_dur_zero_nodur_zero" % s] = sum(1 for r in R if not r["nodurability"] and not r["durability"])
        kv["%s_durwarning_distinct" % s] = len({r["durwarning"] for r in R})
        kv["%s_qntwarning_nonzero" % s] = sum(1 for r in R if r["qntwarning"])
        kv["%s_stackable" % s] = sum(1 for r in R if r["stackable"])
        kv["%s_maxstack_max" % s] = max(r["maxstack"] for r in R)
        kv["%s_maxstack_not_stackable" % s] = sum(1 for r in R if r["maxstack"] and not r["stackable"])
        kv["%s_spawnstack_nonzero" % s] = sum(1 for r in R if r["spawnstack"])
        kv["%s_qnt_without_stackable" % s] = sum(1 for r in R if r["qntwarning"] and not r["stackable"])
        kv["%s_multibuy" % s] = sum(1 for r in R if r["multibuy"])
        kv["%s_multibuy_not_perm" % s] = sum(1 for r in R if r["multibuy"] and not r["PermStoreItem"])
        kv["%s_quest" % s] = sum(1 for r in R if r["quest"])
        kv["%s_quest_cost_zero" % s] = sum(1 for r in R if r["quest"] and r["cost"] == 0)
        out.append("  cost 0: %s" % codes(d.code(tn, i) for i, r in enumerate(R) if r["cost"] == 0))
        out.append("  gamble cost 0: %s" % codes(d.code(tn, i) for i, r in enumerate(R) if r["gamble cost"] == 0))
        out.append("  cost > gamble cost (gamble cost set): %s" % codes(
            "%s %d>%d" % (d.code(tn, i), r["cost"], r["gamble cost"]) for i, r in enumerate(R)
            if r["gamble cost"] and r["cost"] > r["gamble cost"]))
        out.append("  nodurability with durability: %s" % codes(
            "%s %d" % (d.code(tn, i), r["durability"]) for i, r in enumerate(R) if r["nodurability"] and r["durability"]))
        out.append("  nodurability, durability 0 (on a durability table): %s" % codes(
            d.code(tn, i) for i, r in enumerate(R) if tn != "misc" and r["nodurability"] and not r["durability"]))
        out.append("  durwarning: %s; qntwarning: %s" % (hist(r["durwarning"] for r in R),
                                                       hist(r["qntwarning"] for r in R)))
        out.append("  stackable (code min/max/spawn qntwarning): %s" % codes(
            "%s %d/%d/%d q%d" % (d.code(tn, i), r["minstack"], r["maxstack"], r["spawnstack"], r["qntwarning"])
            for i, r in enumerate(R) if r["stackable"] or r["maxstack"]))
        out.append("  multibuy (code cost PermStoreItem): %s" % codes(
            "%s %d p%d" % (d.code(tn, i), r["cost"], r["PermStoreItem"]) for i, r in enumerate(R) if r["multibuy"]))
        out.append("  quest (code quest cost gamble): %s" % codes(
            "%s q%d %d %d" % (d.code(tn, i), r["quest"], r["cost"], r["gamble cost"]) for i, r in enumerate(R)
            if r["quest"]))
        if tn == "misc":
            out.append("  gamble cost set: %s" % codes(
                "%s %d/%d" % (d.code(tn, i), r["cost"], r["gamble cost"]) for i, r in enumerate(R) if r["gamble cost"]))
    # the gamble list against gamble cost
    base = {}
    for tn in ITEM_TABLES:
        for i, r in enumerate(d.t[tn].rec):
            base.setdefault(d.code(tn, i), (tn, r))
    g = [r["code"].strip() for r in d.t["gamble"].rec]
    kv["gamble_rows"] = len(g)
    kv["gamble_gcost_zero"] = sum(1 for c in g if base[c][1]["gamble cost"] == 0)
    kv["gamble_cost_above_gcost"] = sum(1 for c in g if base[c][1]["cost"] > base[c][1]["gamble cost"])
    for tn in ITEM_TABLES:
        kv["gamble_from_%s" % SHORT[tn]] = sum(1 for c in g if base[c][0] == tn)
    out.append("== gamble list: %d rows (%s); gamble cost 0 on %d; cost above gamble cost on %d: %s" % (
        len(g), ", ".join("%s %d" % (tn, kv["gamble_from_%s" % SHORT[tn]]) for tn in ITEM_TABLES),
        kv["gamble_gcost_zero"], kv["gamble_cost_above_gcost"],
        codes(c for c in g if base[c][1]["cost"] > base[c][1]["gamble cost"])))
    return out, kv


TYPE_FLAGS = ("Repair", "Throwable", "Reload", "ReEquip", "AutoStack")


def sec_types(d):
    out, kv = [], collections.OrderedDict()
    it = d.t["itemtypes"]
    kv["types_rows"] = len(it.rec)
    for c in TYPE_FLAGS:
        rows = [d.types[i] for i, r in enumerate(it.rec) if r[c]]
        kv["types_%s" % c.lower()] = len(rows)
        out.append("%-10s %2d: %s" % (c, len(rows), codes(rows)))
    for c in ("Shoots", "Quiver"):
        rows = ["%s->%s" % (d.types[i], d.types[r[c]]) for i, r in enumerate(it.rec) if r[c]]
        kv["types_%s" % c.lower()] = len(rows)
        out.append("%-10s %2d: %s" % (c, len(rows), codes(rows)))
    cf = [(d.types[i], r["CostFormula"]) for i, r in enumerate(it.rec) if r["CostFormula"]]
    for v in sorted({v for _, v in cf}):
        kv["types_costformula%d" % v] = sum(1 for _, x in cf if x == v)
    out.append("CostFormula: %s" % codes("%s=%d" % p for p in cf))
    kv["types_repair_and_throwable"] = sum(1 for r in it.rec if r["Repair"] and r["Throwable"])
    kv["types_throwable_reequip"] = sum(1 for r in it.rec if r["Throwable"] and r["ReEquip"])
    kv["types_reload_not_autostack"] = sum(1 for r in it.rec if r["Reload"] and not r["AutoStack"])
    kv["types_costformula_not_repair"] = sum(1 for r in it.rec if r["CostFormula"] and not r["Repair"])
    out.append("Repair and Throwable: %d; Throwable and ReEquip: %d; Reload without AutoStack: %s; CostFormula "
               "without Repair: %d" % (kv["types_repair_and_throwable"], kv["types_throwable_reequip"],
                                       codes(d.types[i] for i, r in enumerate(it.rec) if r["Reload"] and not r["AutoStack"]),
                                       kv["types_costformula_not_repair"]))
    # bases against their own type's Repair (the type tree, Equiv1/2, is not walked)
    for tn in ("weapons", "armor"):
        R, s = d.t[tn].rec, SHORT[tn]
        rep = [it.rec[r["type"]]["Repair"] for r in R]
        kv["%s_type_repair" % s] = sum(rep)
        kv["%s_type_norepair_nodur0" % s] = sum(1 for r, x in zip(R, rep) if not x and not r["nodurability"])
        kv["%s_type_repair_nodur" % s] = sum(1 for r, x in zip(R, rep) if x and r["nodurability"])
        kv["%s_type_throwable" % s] = sum(1 for r in R if it.rec[r["type"]]["Throwable"])
        out.append("%s: own type has Repair %d of %d; no Repair and nodurability 0: %s; Repair and nodurability 1: %s;"
                   " own type Throwable: %d" % (
                       tn, kv["%s_type_repair" % s], len(R),
                       codes("%s(%s)" % (d.code(tn, i), d.types[r["type"]]) for i, (r, x) in enumerate(zip(R, rep))
                             if not x and not r["nodurability"]),
                       codes("%s(%s)" % (d.code(tn, i), d.types[r["type"]]) for i, (r, x) in enumerate(zip(R, rep))
                             if x and r["nodurability"]),
                       kv["%s_type_throwable" % s]))
    # the same against the Equiv closure (the item's own type and every type reached through Equiv1/Equiv2): the
    # count of bases whose closure holds a Repair type, and of bases where it differs from the own-type answer
    n = len(it.rec)

    def closure(t):
        seen, todo = set(), [t]
        while todo:
            x = todo.pop()
            if 0 <= x < n and x not in seen:
                seen.add(x)
                todo += [it.rec[x]["Equiv1"], it.rec[x]["Equiv2"]]
        return seen
    for tn in ITEM_TABLES:
        R, s = d.t[tn].rec, SHORT[tn]
        own = [bool(it.rec[r["type"]]["Repair"]) if 0 <= r["type"] < n else False for r in R]
        clo = [any(it.rec[x]["Repair"] for x in closure(r["type"])) for r in R]
        kv["%s_closure_repair" % s] = sum(clo)
        kv["%s_closure_repair_differs" % s] = sum(1 for a, b in zip(own, clo) if a != b)
        out.append("%s: Equiv closure has Repair %d of %d; differs from the own type: %s" % (
            tn, kv["%s_closure_repair" % s], len(R),
            codes(d.code(tn, i) for i, (a, b) in enumerate(zip(own, clo)) if a != b) or "none"))
    return out, kv


def sec_stats(d):
    out, kv = [], collections.OrderedDict()
    t = d.t["itemstatcost"]
    R = t.rec
    names = [r["Stat"] for r in t.txt]
    kv["isc_rows"] = len(R)
    kv["isc_divide_1024"] = sum(1 for r in R if r["Divide"] == 1024)
    kv["isc_divide_0"] = sum(1 for r in R if r["Divide"] == 0)
    kv["isc_divide_blank"] = sum(1 for i in range(len(R)) if t.blank(i, "Divide"))
    kv["isc_multiply_nonzero"] = sum(1 for r in R if r["Multiply"])
    kv["isc_multiply_negative"] = sum(1 for r in R if r["Multiply"] < 0)
    kv["isc_multiply_min"], kv["isc_multiply_max"] = span(r["Multiply"] for r in R)
    kv["isc_multiply_distinct"] = len({r["Multiply"] for r in R})
    kv["isc_add_nonzero"] = sum(1 for r in R if r["Add"])
    kv["isc_add_max"] = max(r["Add"] for r in R)
    kv["isc_add_distinct"] = len({r["Add"] for r in R})
    kv["isc_priced"] = sum(1 for r in R if r["Multiply"] or r["Add"])
    kv["isc_multiply_only"] = sum(1 for r in R if r["Multiply"] and not r["Add"])
    kv["isc_add_only"] = sum(1 for r in R if r["Add"] and not r["Multiply"])
    kv["isc_priced_divide0"] = sum(1 for r in R if (r["Multiply"] or r["Add"]) and r["Divide"] == 0)
    kv["isc_priced_saved"] = sum(1 for r in R if (r["Multiply"] or r["Add"]) and r["Saved"])
    out.append("Divide: %s" % hist(r["Divide"] for r in R))
    out.append("Divide 0: %s" % codes("%d %s" % (i, names[i]) for i, r in enumerate(R) if r["Divide"] == 0))
    out.append("Multiply non-zero %d, Add non-zero %d, either %d; Multiply only: %s; Add only: %s" % (
        kv["isc_multiply_nonzero"], kv["isc_add_nonzero"], kv["isc_priced"],
        codes("%d %s" % (i, names[i]) for i, r in enumerate(R) if r["Multiply"] and not r["Add"]),
        codes("%d %s" % (i, names[i]) for i, r in enumerate(R) if r["Add"] and not r["Multiply"])))
    out.append("negative Multiply: %s" % codes("%d %s %d" % (i, names[i], r["Multiply"]) for i, r in enumerate(R)
                                               if r["Multiply"] < 0))
    out.append("id | Stat | Divide Multiply Add | Saved ValShift")
    for i, r in enumerate(R):
        if r["Multiply"] or r["Add"]:
            out.append("  %3d %-30s %4d %5d %6d | %d %d" % (i, names[i], r["Divide"], r["Multiply"], r["Add"],
                                                           r["Saved"], r["ValShift"]))
    # against the stats a used property code writes (tools/prop_survey.py stats; drop = reachable on the drop path)
    import prop_survey
    su = prop_survey.stat_use(prop_survey.Data(d.dir))
    priced = {i for i, r in enumerate(R) if r["Multiply"] or r["Add"]}
    used, drop = set(su), {s for s in su if su[s][0]}
    kv["isc_used"] = len(used)
    kv["isc_used_priced"] = len(used & priced)
    kv["isc_drop_unpriced"] = len(drop - priced)
    kv["isc_priced_unused"] = len(priced - used)
    out.append("written by a used property code: %d, priced %d; on the drop path and unpriced: %s" % (
        len(used), len(used & priced), codes("%d %s" % (i, names[i]) for i in sorted(drop - priced))))
    out.append("priced, written by no used code: %d" % len(priced - used))
    return out, kv


def sec_affixes(d):
    out, kv = [], collections.OrderedDict()
    for tn, s in (("magicprefix", "mp"), ("magicsuffix", "ms"), ("automagic", "am")):
        t = d.t[tn]
        R = t.rec
        kv["%s_rows" % s] = len(R)
        for c in ("divide", "multiply", "add"):
            kv["%s_%s_nonzero" % (s, c)] = sum(1 for r in R if r[c])
        kv["%s_add_max" % s] = max(r["add"] for r in R)
        out.append("%s: %d rows; divide %s; multiply %s; add non-zero %d (max %d)" % (
            tn, len(R), hist(r["divide"] for r in R), hist(r["multiply"] for r in R), kv["%s_add_nonzero" % s],
            kv["%s_add_max" % s]))
        for i, r in enumerate(R):
            if r["multiply"] or r["add"] or r["divide"]:
                out.append("  %3d %-14s %-8s lvl %2d  divide %d multiply %4d add %5d" % (
                    i, t.txt[i]["Name"], t.txt[i]["mod1code"], r["level"], r["divide"], r["multiply"], r["add"]))
        kv["%s_priced_not_resall" % s] = sum(1 for i, r in enumerate(R)
                                             if (r["multiply"] or r["add"]) and t.txt[i]["mod1code"] != "res-all")
    for tn, s, key in (("uniqueitems", "ui", "index"), ("setitems", "si", "index")):
        t = d.t[tn]
        R = t.rec
        kv["%s_rows" % s] = len(R)
        kv["%s_costmult_blank" % s] = sum(1 for i in range(len(R)) if t.blank(i, "cost mult"))
        for v, n in sorted(collections.Counter(r["cost mult"] for r in R).items()):
            kv["%s_costmult_%d" % (s, v)] = n
        for v, n in sorted(collections.Counter(r["cost add"] for r in R).items()):
            kv["%s_costadd_%d" % (s, v)] = n
        out.append("%s: %d rows; cost mult %s; cost add %s; blank cost mult on: %s" % (
            tn, len(R), hist(r["cost mult"] for r in R), hist(r["cost add"] for r in R),
            codes("%d %s" % (i, t.txt[i][key]) for i in range(len(R)) if t.blank(i, "cost mult"))))
        pairs = collections.Counter((r["cost mult"], r["cost add"]) for r in R)
        out.append("  (cost mult, cost add): %s" % ", ".join("%s x%d" % kvp for kvp in sorted(pairs.items())))
    si = d.t["setitems"]
    sets = collections.OrderedDict()
    for i, r in enumerate(si.rec):
        sets.setdefault(si.txt[i]["set"], set()).add(r["cost add"])
    kv["si_sets_mixed_costadd"] = sum(1 for v in sets.values() if len(v) > 1)
    setver = {r["index"]: r["version"] for r in d.txt("sets")}
    kv["si_costadd_2500_classic_set"] = sum(1 for i, r in enumerate(si.rec)
                                            if r["cost add"] == 2500 and setver[si.txt[i]["set"]] == "0")
    kv["si_costadd_5000_expansion_set"] = sum(1 for i, r in enumerate(si.rec)
                                              if r["cost add"] == 5000 and setver[si.txt[i]["set"]] == "100")
    ui = d.t["uniqueitems"]
    kv["ui_costmult_3_version100"] = sum(1 for r in ui.rec if r["cost mult"] == 3 and r["version"] == 100)
    kv["ui_costmult_5_version0"] = sum(1 for r in ui.rec if r["cost mult"] == 5 and r["version"] == 0)
    kv["ui_costmult_5_version100"] = sum(1 for r in ui.rec if r["cost mult"] == 5 and r["version"] == 100)
    out.append("  setitems cost add 2500 on a classic set (version 0): %d; 5000 on an expansion set: %d" % (
        kv["si_costadd_2500_classic_set"], kv["si_costadd_5000_expansion_set"]))
    out.append("  uniqueitems cost mult 3 with version 100: %d; cost mult 5 with version 0 / 100: %d / %d; cost mult 3"
               " records %s" % (kv["ui_costmult_3_version100"], kv["ui_costmult_5_version0"],
                                kv["ui_costmult_5_version100"],
                                codes(i for i, r in enumerate(ui.rec) if r["cost mult"] == 3)))
    out.append("  sets whose members differ in cost add: %d of %d; cost add 2500 sets: %s" % (
        kv["si_sets_mixed_costadd"], len(sets), codes(k for k, v in sets.items() if v == {2500})))
    # price cells with no .bin field (txt only)
    q = d.txt("qualityitems")
    kv["qi_rows"] = len(q)
    kv["qi_multiply_distinct"] = len({r["multiply"] for r in q})
    kv["qi_add_distinct"] = len({r["add"] for r in q})
    out.append("qualityitems (.txt only, no field): %s" % "; ".join(
        "%s %s..%s mult %s add %s" % (r["effect1"], r["mod1min"], r["mod1max"], r["multiply"], r["add"]) for r in q))
    rs = d.txt("raresuffix")
    rp = d.txt("rareprefix")
    for nm, rows, s in (("rareprefix", rp, "rp"), ("raresuffix", rs, "rs")):
        nz = [r["name"] for r in rows if any(r.get(c, "") not in ("", "0") for c in ("add", "multiply", "divide"))]
        kv["%s_price_nonzero" % s] = len(nz)
        out.append("%s (.txt only, no field): add/multiply/divide set on %d rows: %s" % (nm, len(nz), codes(nz)))
    return out, kv


def sec_npc(d):
    out, kv = [], collections.OrderedDict()
    t = d.t["npc"]
    R = t.rec
    kv["npc_rows"] = len(R)
    for c in ("sell mult", "buy mult", "rep mult"):
        kv["npc_%s_distinct" % c.split()[0]] = len({r[c] for r in R})
    kv["npc_questb"] = sum(1 for r in R if r["questflag B"])
    kv["npc_questc"] = sum(1 for r in R if r["questflag C"])
    kv["npc_questsella_922"] = sum(1 for r in R if r["questsellmult A"] == 922)
    kv["npc_questbuyrep_not1024"] = sum(1 for r in R for g in "AB" if r["questflag " + g]
                                        and (r["questbuymult " + g] != 1024 or r["questrepmult " + g] != 1024))
    kv["npc_maxbuy_distinct"] = len({r["max buy"] for r in R})
    kv["npc_maxbuyn_distinct"] = len({r["max buy (N)"] for r in R})
    kv["npc_maxbuyh_distinct"] = len({r["max buy (H)"] for r in R})
    out.append("row npc (class) | sell buy rep | flagA sellA buyA repA | flagB sellB buyB repB | max buy N/NM/H")
    for i, r in enumerate(R):
        out.append("  %2d %-9s %3d | %4d %3d %3d | %2d %4d %4d %4d | %2d %4d %4d %4d | %5d %5d %5d" % (
            i, d.monstats[r["npc"]], r["npc"], r["sell mult"], r["buy mult"], r["rep mult"],
            r["questflag A"], r["questsellmult A"], r["questbuymult A"], r["questrepmult A"],
            r["questflag B"], r["questsellmult B"], r["questbuymult B"], r["questrepmult B"],
            r["max buy"], r["max buy (N)"], r["max buy (H)"]))
    return out, kv


def sec_hireling(d):
    out, kv = [], collections.OrderedDict()
    t = d.t["hireling"]
    R = t.rec
    groups = collections.OrderedDict()
    for r in R:
        groups.setdefault((r["Version"], r["Id"]), []).append(r)
    kv["hire_rows"] = len(R)
    kv["hire_groups"] = len(groups)
    kv["hire_gold_min"], kv["hire_gold_max"] = span(r["Gold"] for r in R)
    kv["hire_gold_distinct"] = len({r["Gold"] for r in R})
    kv["hire_gold_const_per_group"] = sum(1 for g in groups.values() if len({r["Gold"] for r in g}) == 1)
    kv["hire_explvl_const_per_group"] = sum(1 for g in groups.values() if len({r["Exp/Lvl"] for r in g}) == 1)
    kv["hire_gold_same_classic_exp"] = sum(1 for (v, i), g in groups.items() if v == 100 and (0, i) in groups
                                           and g[0]["Gold"] == groups[(0, i)][0]["Gold"])
    kv["hire_gold_rises_with_diff"] = int(all(
        max(r["Gold"] for r in R if r["Act"] == a and r["Difficulty"] == df and r["Version"] == v)
        < min(r["Gold"] for r in R if r["Act"] == a and r["Difficulty"] == df + 1 and r["Version"] == v)
        for v in (0, 100) for a in (1, 2, 3, 5) for df in (1, 2)))
    out.append("Version Id | Act Diff | Gold Exp/Lvl | Level bands")
    for (v, i), g in groups.items():
        out.append("  %3d %2d | %d %d | %5d %3d | %s" % (v, i, g[0]["Act"], g[0]["Difficulty"], g[0]["Gold"],
                                                       g[0]["Exp/Lvl"], ", ".join(str(r["Level"]) for r in g)))
    return out, kv


def sec_skills(d):
    out, kv = [], collections.OrderedDict()
    t = d.t["skills"]
    R = t.rec
    names = [r["skill"] for r in t.txt]
    priced = [i for i, r in enumerate(R) if r["cost mult"] or r["cost add"]]
    kv["sk_rows"] = len(R)
    kv["sk_cost_rows"] = len(priced)
    kv["sk_cost_rows_class"] = sum(1 for i in priced if t.txt[i]["charclass"])
    kv["sk_class_rows"] = sum(1 for r in t.txt if r["charclass"])
    kv["sk_costadd_without_mult"] = sum(1 for r in R if r["cost add"] and not r["cost mult"])
    kv["sk_costmult_blank"] = sum(1 for i in range(len(R)) if t.blank(i, "cost mult"))
    kv["sk_costadd_blank"] = sum(1 for i in range(len(R)) if t.blank(i, "cost add"))
    tri = collections.Counter((R[i]["reqlevel"], R[i]["cost mult"], R[i]["cost add"]) for i in priced)
    kv["sk_cost_triples"] = len(tri)
    # mult is a function of reqlevel: 256 + 128·k for the k-th of reqlevel 1, 6, 12, 18, 24, 30
    lv = sorted({R[i]["reqlevel"] for i in priced})
    kv["sk_cost_reqlevels"] = len(lv)
    kv["sk_mult_by_reqlevel"] = int(all(R[i]["cost mult"] == 256 + 128 * lv.index(R[i]["reqlevel"]) for i in priced))
    usual = {}
    for (l, m, a), n in tri.items():
        if n > usual.get(l, (0, 0))[1]:
            usual[l] = (a, n)
    odd = [i for i in priced if R[i]["cost add"] != usual[R[i]["reqlevel"]][0]]
    kv["sk_add_off_tier"] = len(odd)
    # the skills a `charged` property names (.txt params: a skill id or name), per source table
    low = {n.lower(): i for i, n in enumerate(names)}
    named = collections.Counter()
    for tn, pairs in (("magicprefix", [("mod%dcode" % k, "mod%dparam" % k) for k in (1, 2, 3)]),
                      ("magicsuffix", [("mod%dcode" % k, "mod%dparam" % k) for k in (1, 2, 3)]),
                      ("uniqueitems", [("prop%d" % k, "par%d" % k) for k in range(1, 13)]),
                      ("setitems", [("prop%d" % k, "par%d" % k) for k in range(1, 10)]),
                      ("runes", [("T1Code%d" % k, "T1Param%d" % k) for k in range(1, 8)])):
        for r in d.txt(tn):
            for c, p in pairs:
                par = r.get(p, "")
                if r.get(c, "").lower() == "charged" and par:
                    named[(tn, int(par) if par.lstrip("-").isdigit() else low.get(par.lower(), -1))] += 1
    sk_named = {i for _, i in named}
    kv["sk_charged_named"] = len(sk_named)
    kv["sk_charged_unresolved"] = sum(1 for i in sk_named if not 0 <= i < len(R))
    kv["sk_charged_unpriced"] = sum(1 for i in sk_named if 0 <= i < len(R) and not R[i]["cost mult"])
    for tn in ("magicsuffix", "uniqueitems", "setitems", "runes"):
        kv["sk_charged_cells_%s" % tn] = sum(n for (t, _), n in named.items() if t == tn)
    out.append("skills named by a `charged` property: %d (unresolved %d, without cost mult %d); cells per table: %s" % (
        len(sk_named), kv["sk_charged_unresolved"], kv["sk_charged_unpriced"],
        ", ".join("%s %d" % (tn, kv["sk_charged_cells_%s" % tn]) for tn in ("magicsuffix", "uniqueitems", "setitems",
                                                                              "runes"))))
    out.append("rows with cost mult/add: %d (all with a charclass: %d of %d class rows); reqlevels %s" % (
        len(priced), kv["sk_cost_rows_class"], kv["sk_class_rows"], lv))
    out.append("(reqlevel, cost mult, cost add): %s" % ", ".join("%s x%d" % p for p in sorted(tri.items())))
    out.append("cost add off its reqlevel's usual value (%s): %s" % (
        ", ".join("%d->%d" % (l, usual[l][0]) for l in lv),
        codes("%d %s (lvl %d, add %d)" % (i, names[i], R[i]["reqlevel"], R[i]["cost add"]) for i in odd)))
    return out, kv


def sec_books(d):
    out, kv = [], collections.OrderedDict()
    t = d.t["books"]
    R = t.rec
    kv["books_rows"] = len(R)
    kv["books_cost_per_charge_is_fifth"] = sum(1 for r in R if 5 * r["CostPerCharge"] == r["BaseCost"])
    skills = d.refs.names("skills:skill")
    for i, r in enumerate(R):
        out.append("  %d %-14s pSpell %d SpellIcon %2d scroll %-4s %-22s book %-4s %-22s BaseCost %d CostPerCharge %d"
                   % (i, t.txt[i]["Namco"], r["pSpell"], r["SpellIcon"], r["ScrollSpellCode"].strip() or "-",
                      skills[r["ScrollSkill"]] if r["ScrollSkill"] >= 0 else "-", r["BookSpellCode"].strip() or "-",
                      skills[r["BookSkill"]] if r["BookSkill"] >= 0 else "-", r["BaseCost"], r["CostPerCharge"]))
    misc = d.t["misc"]
    for i, r in enumerate(misc.rec):
        if misc.txt[i]["code"] in {x["ScrollSpellCode"].strip() for x in R} | {x["BookSpellCode"].strip() for x in R}:
            out.append("  misc %s cost %d stackable %d minstack %d maxstack %d spawnstack %d" % (
                misc.txt[i]["code"], r["cost"], r["stackable"], r["minstack"], r["maxstack"], r["spawnstack"]))
    return out, kv


SECTIONS = collections.OrderedDict([
    ("items", sec_items), ("types", sec_types), ("stats", sec_stats), ("affixes", sec_affixes), ("npc", sec_npc),
    ("hireling", sec_hireling), ("skills", sec_skills), ("books", sec_books)])


def survey_line(kv):
    return "SURVEY economy " + " ".join("%s=%d" % (k, v) for k, v in kv.items())


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

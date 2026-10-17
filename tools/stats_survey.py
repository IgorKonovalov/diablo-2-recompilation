"""Survey of the table columns the stat-list and state code is expected to read (plan 0041 Phase 0).

Usage:
  python3 -I tools/stats_survey.py isc      <excel-dir>
  python3 -I tools/stats_survey.py states   <excel-dir>
  python3 -I tools/stats_survey.py skills   <excel-dir>
  python3 -I tools/stats_survey.py sets     <excel-dir>
  python3 -I tools/stats_survey.py shrines  <excel-dir>
  python3 -I tools/stats_survey.py summary  <excel-dir>

isc      ItemStatCost § Aggregation: every row with an `op` (id, Stat, op, op param, op base, op stat1..3); the
         histogram of op and op param; the inverse lists (for each target stat, the rows whose op stat1..3 name it,
         the shape of the run-time table at +0x0DE); the rows with direct (and their maxstat), itemspecific,
         keepzero, fCallback, fMin (with MinAccr), UpdateAnimRate, and the damagerelated count.
states   States: for each flag bit the rows that set it; group, stat, setfunc, remfunc, cltactivefunc,
         srvactivefunc, skill and missile by row; and, per row, which data names it: Skills aurastate,
         auratargetstate, passivestate, State1..3; Weapons/Armor/Misc state, cstate1, cstate2; a Sets bonus
         block with the property `state` (its param); and the rows named `shrine_*`.
skills   Skills § Passive and aura columns: rows with the `passive` and `aura` flag bits, rows with
         passivestate / passivestat1 / aurastate / auratargetstate / aurastat1 / auralencalc / aurarangecalc /
         aurafilter, their cross counts, and one line per row that has any of them.
sets     Sets § Bonus blocks: per set, the partial blocks (PCode2a..5b) and full blocks (FCode1..8) used, the
         property codes, the params that hold a name; SetItems `add func` against the aprop blocks.
shrines  Shrines § Effects: the 23 rows (Code, Arg0, Arg1, duration, reset, effectclass, LevelMin).
summary  the counts of every section only.

Every command ends with `SURVEY stats key=value ...`; tools/gate.py --full compares the summary line with its
baseline. Values come from the .bin records decoded with the layouts of tools/excel_layouts.py (what the game
loads); whether a cell is blank comes from the .txt. Meanings are [L] (docs/tables/ItemStatCost.md § Aggregation,
States.md, Skills.md § Passive and aura columns, Sets.md § Bonus blocks, Shrines.md § Effects). Stdlib only.
Read-only.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import excel_bin as eb  # noqa: E402
from combat_survey import Table, hist  # noqa: E402
from excel_layouts import LAYOUTS  # noqa: E402

NONE16 = 0xFFFF
ISC_FLAGS = ["direct", "itemspecific", "keepzero", "fCallback", "fMin", "UpdateAnimRate", "damagerelated"]
SKILL_PA_COLS = ["passivestate", "passiveitype", "passivestat1", "aurastate", "auratargetstate", "aurastat1",
                 "auralencalc", "aurarangecalc", "aurafilter", "auraevent1"]


class Data:
    def __init__(self, excel_dir):
        self.refs = eb.Refs(excel_dir)
        self.t = {}
        for name in ("itemstatcost", "states", "skills", "sets", "setitems", "shrines", "properties", "weapons",
                     "armor", "misc"):
            self.t[name] = Table(excel_dir, name, self.refs)
        self.stats = [r["Stat"] for r in self.t["itemstatcost"].txt]
        self.states = [r["state"] for r in self.t["states"].txt]
        self.skills = [r["skill"] for r in self.t["skills"].txt]
        self.props = [r["code"] for r in self.t["properties"].txt]

    def stat(self, i):
        return self.stats[i] if 0 <= i < len(self.stats) else "-"

    def state(self, i):
        return self.states[i] if 0 <= i < len(self.states) else "-"


def ids(rows):
    """Compact id list: 3, 5-8, 12."""
    rows = sorted(rows)
    out, k = [], 0
    while k < len(rows):
        j = k
        while j + 1 < len(rows) and rows[j + 1] == rows[j] + 1:
            j += 1
        out.append(str(rows[k]) if j == k else "%d-%d" % (rows[k], rows[j]))
        k = j + 1
    return ", ".join(out) or "-"


# ---------------------------------------------------------------- sections: each returns (lines, kv)

def sec_isc(d):
    out, kv = [], collections.OrderedDict()
    isc = d.t["itemstatcost"]
    n = len(isc.rec)
    kv["isc_rows"] = n
    tcols = ("op stat1", "op stat2", "op stat3")
    oprows = [i for i in range(n) if isc.rec[i]["op"]]
    out.append("Rows with an op (%d of %d): id Stat | op | op param | op base | op stat1 op stat2 op stat3" % (
        len(oprows), n))
    inverse = collections.defaultdict(list)
    no_target = 0
    for i in oprows:
        r = isc.rec[i]
        tg = [r[c] for c in tcols if r[c] != NONE16]
        for t in tg:
            inverse[t].append(i)
        if not tg:
            no_target += 1
        out.append("  %3d %-32s op %2d  param %d  base %-6s | %s" % (
            i, d.stats[i], r["op"], r["op param"], d.stat(r["op base"]) if r["op base"] != NONE16 else "-",
            " ".join(d.stat(t) for t in tg) or "-"))
    kv["op_rows"] = len(oprows)
    ops = collections.Counter(isc.rec[i]["op"] for i in oprows)
    for k in sorted(ops):
        kv["op%d" % k] = ops[k]
    out.append("  op: %s" % hist(isc.rec[i]["op"] for i in oprows))
    out.append("  op param (rows with an op): %s" % hist(isc.rec[i]["op param"] for i in oprows))
    out.append("  op param by op: %s" % hist("%d/%d" % (isc.rec[i]["op"], isc.rec[i]["op param"]) for i in oprows))
    kv["op_param_rows"] = sum(1 for i in range(n) if isc.rec[i]["op param"])
    kv["op_param_without_op"] = sum(1 for i in range(n) if isc.rec[i]["op param"] and not isc.rec[i]["op"])
    kv["op_base_rows"] = sum(1 for i in range(n) if isc.rec[i]["op base"] != NONE16)
    kv["op_base_without_op"] = sum(1 for i in range(n) if isc.rec[i]["op base"] != NONE16 and not isc.rec[i]["op"])
    kv["op_target_cells"] = sum(len(v) for v in inverse.values())
    kv["op_targets_distinct"] = len(inverse)
    kv["op_rows_no_target"] = no_target
    kv["op_target_without_op"] = sum(1 for i in range(n) if not isc.rec[i]["op"]
                                     and any(isc.rec[i][c] != NONE16 for c in tcols))
    kv["op_self_target"] = sum(1 for t, src in inverse.items() if t in src)
    kv["op_target_has_op"] = sum(1 for t in inverse if isc.rec[t]["op"])
    fan = max((len(v) for v in inverse.values()), default=0)
    kv["op_fanin_max"] = fan
    out.append("Inverse (+0x0DE run-time table shape): target <- sources (op)")
    for t in sorted(inverse):
        out.append("  %3d %-24s <- %s" % (t, d.stat(t), ", ".join("%d %s (op %d)" % (s, d.stats[s], isc.rec[s]["op"])
                                                                    for s in inverse[t])))
    out.append("  targets %d, target cells %d, most sources on one target %d (capacity 16)" % (
        len(inverse), kv["op_target_cells"], fan))
    out.append("Flag and cap columns: rows")
    for c in ISC_FLAGS:
        rows = [i for i in range(n) if isc.rec[i][c]]
        kv["isc_" + c.lower()] = len(rows)
        if len(rows) <= 40:
            out.append("  %-14s %3d: %s" % (c, len(rows), ", ".join("%d %s" % (i, d.stats[i]) for i in rows)))
        else:
            out.append("  %-14s %3d: ids %s" % (c, len(rows), ids(rows)))
    ms = [i for i in range(n) if isc.rec[i]["maxstat"] != NONE16]
    kv["isc_maxstat"] = len(ms)
    kv["isc_maxstat_and_direct"] = sum(1 for i in ms if isc.rec[i]["direct"])
    out.append("  maxstat        %3d: %s" % (len(ms), ", ".join("%d %s -> %s" % (i, d.stats[i],
                                                                               d.stat(isc.rec[i]["maxstat"]))
                                                                for i in ms)))
    fm = [i for i in range(n) if isc.rec[i]["fMin"]]
    out.append("  fMin with MinAccr: %s" % ", ".join("%d %s MinAccr %d" % (i, d.stats[i], isc.rec[i]["MinAccr"])
                                                     for i in fm))
    kv["isc_minaccr"] = sum(1 for i in range(n) if isc.rec[i]["MinAccr"])
    kv["isc_minaccr_without_fmin"] = sum(1 for i in range(n) if isc.rec[i]["MinAccr"] and not isc.rec[i]["fMin"])
    cb_ev = sum(1 for i in range(n) if isc.rec[i]["fCallback"] and isc.rec[i]["itemevent1"] != NONE16)
    kv["isc_fcallback_with_event"] = cb_ev
    out.append("  fCallback rows with an itemevent1: %d" % cb_ev)
    return out, kv


def _state_sources(d):
    """state row -> list of 'source' strings, from every data column that names a state."""
    src = collections.defaultdict(list)
    sk = d.t["skills"]
    for i, r in enumerate(sk.rec):
        for c in ("aurastate", "auratargetstate", "passivestate", "State1", "State2", "State3"):
            if not sk.blank(i, c):
                src[r[c]].append(("skills." + c, d.skills[i]))
    for t in ("weapons", "armor", "misc"):
        tb = d.t[t]
        for i, r in enumerate(tb.rec):
            for c in ("state", "cstate1", "cstate2"):
                if not tb.blank(i, c):
                    src[r[c]].append(("%s.%s" % (t, c), tb.txt[i]["code"]))
    st = d.t["sets"]
    blocks = [("P", "%d%s" % (k // 2 + 2, "ab"[k % 2])) for k in range(8)] + [("F", "%d" % (k + 1)) for k in range(8)]
    for i, r in enumerate(st.rec):
        for c, nm in blocks:
            code = r["%sCode%s" % (c, nm)]
            if code >= 0 and d.props[code].lower() == "state":
                src[r["%sParam%s" % (c, nm)]].append(("sets.%sParam%s" % (c, nm), st.txt[i]["index"]))
    return src


def sec_states(d):
    out, kv = [], collections.OrderedDict()
    st = d.t["states"]
    n = len(st.rec)
    kv["states_rows"] = n
    flagcols = [(f["col"], (f["off"] - 0x010) * 8 + f["bit"]) for f in LAYOUTS["states"]["fields"]
                if f.get("type") == "bit"]
    out.append("Flag bits (bit column: rows)")
    for c, bit in sorted(flagcols, key=lambda x: x[1]):
        rows = [i for i in range(n) if st.rec[i][c]]
        kv["flag_" + c.replace("-", "_")] = len(rows)
        out.append("  %2d %-13s %3d: %s" % (bit, c, len(rows), ids(rows)))
    out.append("Value columns (value: rows)")
    for c in ("group", "setfunc", "remfunc", "cltactivefunc", "srvactivefunc", "clteventfunc"):
        by = collections.defaultdict(list)
        for i in range(n):
            if st.rec[i][c]:
                by[st.rec[i][c]].append(i)
        kv["col_" + c] = sum(len(v) for v in by.values())
        out.append("  %-13s %3d rows: %s" % (c, kv["col_" + c], "; ".join(
            "%d: %s" % (v, ids(by[v])) for v in sorted(by))))
    srows = [i for i in range(n) if not st.blank(i, "stat")]
    kv["col_stat"] = len(srows)
    out.append("  stat %d rows: %s" % (len(srows), ", ".join("%d %s -> %d %s" % (
        i, d.states[i], st.rec[i]["stat"], d.stat(st.rec[i]["stat"])) for i in srows)))
    for c, names in (("skill", d.skills), ("missile", None), ("itemtype", None)):
        rows = [i for i in range(n) if not st.blank(i, c)]
        kv["col_" + c] = len(rows)
        out.append("  %s %d rows: %s" % (c, len(rows), ", ".join("%d %s -> %s" % (i, d.states[i], st.txt[i][c])
                                                                 for i in rows)))
    imm = [i for i in range(n) if not st.blank(i, "immed")]
    kv["col_immed"] = len(imm)
    out.append("  immed (not compiled) %d rows: %s" % (len(imm), ids(imm)))

    src = _state_sources(d)
    out.append("Rows named by data: id state | flags | sources")
    kinds = collections.Counter()
    for i in range(n):
        s = src.get(i, [])
        for k, _ in s:
            kinds[k] += 1
        fl = [c for c, _ in flagcols if st.rec[i][c]]
        tags = sorted({k for k, _ in s})
        out.append("  %3d %-24s | %-40s | %s" % (i, d.states[i], " ".join(fl) or "-", "; ".join(
            "%s: %s" % (k, ", ".join(sorted({v for kk, v in s if kk == k}))) for k in tags) or "-"))
    for k in sorted(kinds):
        kv["src_" + k.replace(".", "_").lower()] = kinds[k]
    named = [i for i in range(n) if src.get(i)]
    kv["rows_named"] = len(named)
    kv["rows_named_skills"] = sum(1 for i in named if any(k.startswith("skills.") for k, _ in src[i]))
    kv["rows_named_items"] = sum(1 for i in named if any(k.split(".")[0] in ("weapons", "armor", "misc")
                                                         for k, _ in src[i]))
    kv["rows_named_sets"] = sum(1 for i in named if any(k.startswith("sets.") for k, _ in src[i]))
    shr = [i for i in range(n) if d.states[i].startswith("shrine_")]
    kv["rows_shrine_named"] = len(shr)
    out.append("  named by some data column: %d of %d (skills %d, items %d, sets %d); rows named shrine_*: %s" % (
        len(named), n, kv["rows_named_skills"], kv["rows_named_items"], kv["rows_named_sets"],
        ", ".join("%d %s" % (i, d.states[i]) for i in shr)))
    return out, kv


def sec_skills(d):
    out, kv = [], collections.OrderedDict()
    sk = d.t["skills"]
    n = len(sk.rec)
    passive = {i for i in range(n) if sk.rec[i]["passive"]}
    aura = {i for i in range(n) if sk.rec[i]["aura"]}
    kv["sk_passive"] = len(passive)
    kv["sk_aura"] = len(aura)
    kv["sk_passive_and_aura"] = len(passive & aura)
    out.append("passive flag (+0x004 bit 4) %d rows: %s" % (len(passive), ids(passive)))
    out.append("aura flag (+0x004 bit 5) %d rows: %s" % (len(aura), ids(aura)))
    has = {c: {i for i in range(n) if not sk.blank(i, c)} for c in SKILL_PA_COLS}
    for c in SKILL_PA_COLS:
        kv["sk_" + c] = len(has[c])
        out.append("  %-15s %3d rows; with passive flag %3d, with aura flag %3d" % (
            c, len(has[c]), len(has[c] & passive), len(has[c] & aura)))
        kv["sk_%s_passive" % c] = len(has[c] & passive)
        kv["sk_%s_aura" % c] = len(has[c] & aura)
    kv["sk_passive_no_state_no_stat"] = len(passive - has["passivestate"] - has["passivestat1"])
    kv["sk_passivestat_no_flag"] = len(has["passivestat1"] - passive)
    kv["sk_aurastate_no_flag"] = len(has["aurastate"] - aura)
    kv["sk_aurastat_no_aurastate"] = len(has["aurastat1"] - has["aurastate"])
    pstat_cells = sum(1 for i in range(n) for k in range(1, 6) if not sk.blank(i, "passivestat%d" % k))
    pcalc_cells = sum(1 for i in range(n) for k in range(1, 6) if not sk.blank(i, "passivecalc%d" % k))
    astat_cells = sum(1 for i in range(n) for k in range(1, 7) if not sk.blank(i, "aurastat%d" % k))
    acalc_cells = sum(1 for i in range(n) for k in range(1, 7) if not sk.blank(i, "aurastatcalc%d" % k))
    kv["sk_passivestat_cells"] = pstat_cells
    kv["sk_passivecalc_cells"] = pcalc_cells
    kv["sk_aurastat_cells"] = astat_cells
    kv["sk_auracalc_cells"] = acalc_cells
    kv["sk_passivestat_without_calc"] = sum(1 for i in range(n) for k in range(1, 6)
                                            if not sk.blank(i, "passivestat%d" % k)
                                            and sk.blank(i, "passivecalc%d" % k))
    kv["sk_aurastat_without_calc"] = sum(1 for i in range(n) for k in range(1, 7)
                                         if not sk.blank(i, "aurastat%d" % k) and sk.blank(i, "aurastatcalc%d" % k))
    kv["sk_auracalc_without_stat"] = sum(1 for i in range(n) for k in range(1, 7)
                                         if sk.blank(i, "aurastat%d" % k) and not sk.blank(i, "aurastatcalc%d" % k))
    out.append("  passivestat cells %d, passivecalc cells %d; aurastat cells %d, aurastatcalc cells %d" % (
        pstat_cells, pcalc_cells, astat_cells, acalc_cells))
    out.append("  aurafilter values: %s" % hist("0x%X" % sk.rec[i]["aurafilter"] for i in has["aurafilter"]))
    out.append("  passiveitype values: %s" % hist(sk.txt[i]["passiveitype"] for i in has["passiveitype"]))
    out.append("Rows (id skill [class] flags | passive: state itype stat=calc | aura: state tgtstate len range filter "
               "stat=calc | events)")
    anyrows = sorted(passive | aura | set().union(*has.values()))
    kv["sk_rows_listed"] = len(anyrows)
    for i in anyrows:
        t = sk.txt[i]
        fl = "".join(c for c, s in (("P", passive), ("A", aura)) if i in s) or "-"
        ps = ["%s=%s" % (t["passivestat%d" % k], t["passivecalc%d" % k]) for k in range(1, 6)
              if t["passivestat%d" % k] or t["passivecalc%d" % k]]
        au = ["%s=%s" % (t["aurastat%d" % k], t["aurastatcalc%d" % k]) for k in range(1, 7)
              if t["aurastat%d" % k] or t["aurastatcalc%d" % k]]
        ev = ["%s/%s" % (t["auraevent%d" % k], t["auraeventfunc%d" % k]) for k in range(1, 4) if t["auraevent%d" % k]]
        out.append("  %3d %-22s [%s] %-2s | P: %s %s %s | A: %s %s len=%s range=%s filter=%s %s | %s" % (
            i, t["skill"], t["charclass"] or "-", fl, t["passivestate"] or "-", t["passiveitype"] or "-",
            " ".join(ps) or "-", t["aurastate"] or "-", t["auratargetstate"] or "-", t["auralencalc"] or "-",
            t["aurarangecalc"] or "-", ("0x%X" % sk.rec[i]["aurafilter"]) if t["aurafilter"] else "-",
            " ".join(au) or "-", " ".join(ev) or "-"))
    return out, kv


def sec_sets(d):
    out, kv = [], collections.OrderedDict()
    st, si = d.t["sets"], d.t["setitems"]
    pblocks = ["%d%s" % (k // 2 + 2, "ab"[k % 2]) for k in range(8)]
    fblocks = ["%d" % (k + 1) for k in range(8)]
    members = collections.Counter(r["set"] for r in si.rec)
    codes = collections.Counter()
    pcells = fcells = beyond = named_par = 0
    out.append("Sets: index | members | partial blocks used | full blocks used")
    for i, r in enumerate(st.rec):
        pu = [b for b in pblocks if r["PCode" + b] >= 0]
        fu = [b for b in fblocks if r["FCode" + b] >= 0]
        for b in pu:
            codes[d.props[r["PCode" + b]]] += 1
            if int(b[0]) > members[i]:
                beyond += 1
            if not st.txt[i]["PParam" + b].lstrip("-").isdigit() and st.txt[i]["PParam" + b]:
                named_par += 1
        for b in fu:
            codes[d.props[r["FCode" + b]]] += 1
            if not st.txt[i]["FParam" + b].lstrip("-").isdigit() and st.txt[i]["FParam" + b]:
                named_par += 1
        pcells += len(pu)
        fcells += len(fu)
        out.append("  %2d %-28s %d | %-22s | %s" % (i, st.txt[i]["index"], members[i], " ".join(pu) or "-",
                                                    " ".join(fu) or "-"))
    kv["sets_rows"] = len(st.rec)
    kv["sets_partial_blocks"] = pcells
    kv["sets_full_blocks"] = fcells
    kv["sets_partial_beyond_members"] = beyond
    kv["sets_params_named"] = named_par
    kv["sets_codes_distinct"] = len(codes)
    # Gaps: a used block after an unused one in the same run (the a blocks, the b blocks, the full blocks).
    gaps = 0
    for r in st.rec:
        for run in ([r["PCode" + b] for b in pblocks if b[1] == "a"], [r["PCode" + b] for b in pblocks if b[1] == "b"],
                    [r["FCode" + b] for b in fblocks]):
            seen_blank = False
            for c in run:
                if c < 0:
                    seen_blank = True
                elif seen_blank:
                    gaps += 1
    kv["sets_block_gaps"] = gaps
    out.append("  partial blocks %d, full blocks %d, partial blocks k > members %d, used after a blank in its run %d" % (
        pcells, fcells, beyond, gaps))
    out.append("  property codes: %s" % hist(codes.elements()))
    by_k = collections.Counter(b for r in st.rec for b in pblocks if r["PCode" + b] >= 0)
    out.append("  partial blocks by name: %s" % ", ".join("%s %d" % (b, by_k[b]) for b in pblocks))
    out.append("SetItems add func and aprop blocks (aprop k a/b = partial bonus at k+1 worn items, [L])")
    af = collections.Counter()
    beyond_items = 0
    for i, r in enumerate(si.rec):
        used = [k for k in range(10) if r["aprop%d%s" % (k // 2 + 1, "ab"[k % 2])] >= 0]
        af[(r["add func"], bool(used))] += 1
        if used and max(k // 2 + 2 for k in used) > members[r["set"]]:
            beyond_items += 1
    for (a, u), c in sorted(af.items()):
        out.append("  add func %d, has aprop %-5s: %3d rows" % (a, u, c))
        kv["si_addfunc%d_%s" % (a, "aprop" if u else "noaprop")] = c
    kv["si_aprop_beyond_members"] = beyond_items
    out.append("  rows with an aprop pair k whose k+1 exceeds the set's members: %d" % beyond_items)
    return out, kv


def sec_shrines(d):
    out, kv = [], collections.OrderedDict()
    sh = d.t["shrines"]
    out.append("Code | Shrine name | Arg0 Arg1 | Duration | reset | effectclass | LevelMin")
    for i, r in enumerate(sh.rec):
        out.append("  %2d %-22s %4d %5d | %4d | %d | %d | %2d" % (
            r["Code"], sh.txt[i]["Shrine name"], r["Arg0"], r["Arg1"], r["Duration in frames"],
            r["reset time in minutes"], r["effectclass"], r["LevelMin"]))
    kv["shrine_rows"] = len(sh.rec)
    kv["shrine_timed"] = sum(1 for r in sh.rec if r["Duration in frames"])
    kv["shrine_arg0_nonzero"] = sum(1 for r in sh.rec if r["Arg0"])
    kv["shrine_arg1_nonzero"] = sum(1 for r in sh.rec if r["Arg1"])
    shr = [i for i, s in enumerate(d.states) if s.startswith("shrine_")]
    timed = [r["Code"] for r in sh.rec if r["Duration in frames"]]
    out.append("  timed rows %d (codes %s); States rows named shrine_*: %d (%s)" % (
        len(timed), ids(timed), len(shr), ", ".join("%d %s" % (i, d.states[i]) for i in shr)))
    # Pair each timed code with the shrine_* state whose name shares its key word (a name reading, [L]).
    words = {"armor": "armor", "combat": "combat", "fire": "resist_fire", "cold": "resist_cold",
             "lightning": "resist_lightning", "poison": "resist_poison", "skill": "skill", "recharge": "mana_regen",
             "stamina": "stamina", "experience": "experience"}
    pairs = []
    for i, r in enumerate(sh.rec):
        if not r["Duration in frames"]:
            continue
        nm = sh.txt[i]["Shrine name"].lower()
        hit = [w for w in words if w in nm.split()]
        st_i = d.states.index("shrine_" + words[hit[0]]) if len(hit) == 1 else -1
        pairs.append((r["Code"], st_i))
    kv["shrine_states"] = len(shr)
    kv["shrine_pairs"] = sum(1 for _, st_i in pairs if st_i >= 0)
    kv["shrine_pairs_code_plus_122"] = sum(1 for c, st_i in pairs if st_i == c + 122)
    out.append("  timed code -> shrine_* state by name: %s" % ", ".join(
        "%d -> %s" % (c, ("%d %s" % (st_i, d.states[st_i])) if st_i >= 0 else "-") for c, st_i in pairs))
    out.append("  pairs %d, of them state = code + 122: %d" % (kv["shrine_pairs"], kv["shrine_pairs_code_plus_122"]))
    return out, kv


SECTIONS = collections.OrderedDict([
    ("isc", sec_isc), ("states", sec_states), ("skills", sec_skills), ("sets", sec_sets), ("shrines", sec_shrines)])


def survey_line(kv):
    return "SURVEY stats " + " ".join("%s=%d" % (k, v) for k, v in kv.items())


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

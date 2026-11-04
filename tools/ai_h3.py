#!/usr/bin/env python3
"""Plan 0052 Phase 2, H3: the Raven class's MonAttackStats calls with the owner pair, from the kept skills logs.

    python3 -I tools/ai_h3.py check LOG [LOG ...] [--excel DIR] [--out FILE]
    python3 -I tools/ai_h3.py selftest

`sub_005A4F50_MonAttackStats` (ECX unit, EDX mode) adds the block of `sub_0056E050_MonOwnerSkillDamage` to the mode's
MonLvlStats values (0x005A505D..0x005A5103) before it writes 21, 22 and 19 to list 1 (0x005A51A9..0x005A51C5). The block is
`SkillDamagePair(s, O)` (0x0056E000): for the owner O, lvl = SkillLevelClamped(O, s), PhysMin(O, s, lvl, 1) >> 8,
PhysMax(O, s, lvl, 1) >> 8, ToHit(O, s, lvl). This tool takes MonAttackStats' other inputs from tools/skills.py's `mas_model` and
adds the block computed from Skills.bin with the owner's level from the caster's logged SST0 line (id 221, a[1]).

The logs (skills logger rev 2 for these two sessions) give the unit's *full* stats, the sum of its lists, not list 1's. So a
call is compared in two steps, neither with a learned value: a unit's first call with a list has no 21 or 22 before it, and its
19 before the call is the other lists' sum, which the call must raise by the model's value (`first_call`); every later call
must leave the full stats where the first put them (`later`). The readings the run must tell apart are printed with the
differences each leaves (`OFFSET`): the owner's level, the owner's level one off, the summon's own level, level 0 (the summon has no entry for the skill), no pair at all.
Stdlib only, and the tools the checker imports.
"""
import json
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

RAVEN_CLASS, RAVEN_SKILL = 419, 221


def level_bands(lvl, b):
    """SKILLS_LevelBands 0x00644B70: lvl <= 1 -> 0; bands 2-8, 9-16, 17-22, 23-28, 29+."""
    if lvl <= 1:
        return 0
    if lvl > 28:
        return (lvl - 28) * b[4] + 6 * b[3] + 6 * b[2] + 8 * b[1] + 7 * b[0]
    if lvl > 22:
        return (lvl - 22) * b[3] + 6 * b[2] + 8 * b[1] + 7 * b[0]
    if lvl > 16:
        return (lvl - 16) * b[2] + 8 * b[1] + 7 * b[0]
    if lvl > 8:
        return (lvl - 8) * b[1] + 7 * b[0]
    return (lvl - 1) * b[0]


def skill_cells(rec):
    i = lambda o: struct.unpack_from("<i", rec, o)[0]  # noqa: E731
    return {"b05": rec[5], "shift": rec[0x1A4], "src": rec[0x1A5], "min": i(0x1A8), "max": i(0x1AC),
            "bmin": [i(0x1B0 + 4 * k) for k in range(5)], "bmax": [i(0x1C4 + 4 * k) for k in range(5)], "sym": i(0x1D8),
            "tohit": i(0x198), "levtohit": i(0x19C), "thcalc": i(0x1A0)}


def owner_pair(c, lvl):
    """SkillDamagePair's block for a row with no Kick bit, no SrcDam, no DmgSymPerCalc and no ToHitCalc; a row that has one
    raises rather than guess (GetPhysMin 0x00647BF9, 0x00647C4D, 0x00647CC2; GetToHit 0x00644A3C)."""
    if c["b05"] & 2 or c["src"] or c["sym"] != -1 or c["thcalc"] != -1:
        raise ValueError("row needs a term this model does not take: %r" % (c,))
    mn = (level_bands(lvl, c["bmin"]) + c["min"]) << c["shift"]
    mx = (level_bands(lvl, c["bmax"]) + c["max"]) << c["shift"]
    th = (lvl - 1) * c["levtohit"] + c["tohit"] if lvl > 0 else 0
    return mn >> 8, mx >> 8, th


def mas_stats(ck, call):
    """MonAttackStats' own (19, 21, 22) with no pair, by tools/skills.py's model."""
    import skills as K
    w, _t, _d, _n = ck.mas_model(RAVEN_CLASS, call[1], call[6], 0, call[0], K.sd_parse(call[4]))
    return w[19], w[21], w[22]


def read_log(path):
    """-> (calls [(mode, level before, stats before, stats after, seed before, seed after, diff, n, unit, id)], owner levels)"""
    calls, pend, own = [], {}, Counter()
    with open(path, errors="replace") as fh:
        for ln in fh:
            t = ln.split(" ", 1)
            if t[0] == "MAS0":
                d = json.loads(t[1])
                if d["u"]["c"] == RAVEN_CLASS:
                    pend[d["n"]] = d
            elif t[0] == "MAS1":
                d = json.loads(t[1])
                p = pend.pop(d["k"], None)
                if p:
                    st0 = p["u"]["st"]
                    calls.append((p["mode"], st0.get("12"), st0, d["st"], p["u"]["s"], d["s"], p.get("diff") or 0, p["n"], p["u"]["u"], p["u"]["id"]))
            elif t[0] == "SST0":
                d = json.loads(t[1])
                if d["a"][0] == RAVEN_SKILL and d["u"]["t"] == 0:
                    own[d["a"][1]] += 1
    return calls, own


def compare(calls, written):
    """Per unit, in log order: `written(call)` -> (19, 21, 22) the call writes to list 1. -> counts of the two steps."""
    seen, r = {}, Counter()
    for c in calls:
        st0, st1 = c[2], c[3]
        if not st0 and not st1:
            continue
        w = written(c)
        got = (st1.get("19", 0), st1.get("21", 0), st1.get("22", 0))
        key = (c[8], c[9])
        if key not in seen:
            r["units"] += 1
            base = st0.get("19", 0)
            ok = not st0.get("21") and not st0.get("22") and got == (base + w[0], w[1], w[2])
            r["first_call_ok" if ok else "first_call_bad"] += 1
            seen[key] = got
        else:
            ok = got == seen[key]
            r["later_ok" if ok else "later_bad"] += 1
    return r


def check(paths, excel=None):
    import skills as K
    T = K.Tables(excel) if excel else K.Tables()
    ck = K.Checker.__new__(K.Checker)
    ck.T = T
    c = skill_cells(T.sk[RAVEN_SKILL])
    sdmg = struct.unpack_from("<H", T.ms[RAVEN_CLASS], 0xA8)[0]
    L = ["H3 class=%d SkillDamage=%d cells=%s" % (RAVEN_CLASS, sdmg, json.dumps(c, sort_keys=True))]
    total = {"calls": 0, "list": 0, "nolist": 0, "seed_bad": 0}
    for p in paths:
        calls, own = read_log(p)
        L.append("LOG %s calls=%d owner_levels=%s" % (os.path.basename(p), len(calls), dict(own)))
        lv = own.most_common(1)[0][0]
        if len(own) != 1:
            L.append("  owner level not unique in this log: %s" % dict(own))
        modes, after = Counter(), Counter()
        def written(call, lv2=lv):
            return tuple(a + b for a, b in zip(mas_stats(ck, call), (lambda m: (m[2], m[0], m[1]))(owner_pair(c, lv2) if lv2 is not None else (0, 0, 0))))
        for name, f in (("owner", written), ("owner-1", lambda x: written(x, lv - 1)), ("owner+1", lambda x: written(x, lv + 1)),
                        ("summon_own_level", lambda x: written(x, x[1])), ("no_skill_entry_lvl0", lambda x: written(x, 0)),
                        ("no_pair", lambda x: written(x, None))):
            r = compare(calls, f)
            L.append("  COMPARE %-19s %s" % (name, " ".join("%s=%d" % kv for kv in sorted(r.items()))))
            if name == "owner":
                for k2 in r:
                    total[k2] = total.get(k2, 0) + r[k2]
        for mode, lvl, st0, st1, s0, s1, d, n, _u, _id in calls:
            total["calls"] += 1
            if not st0 and not st1:
                total["nolist"] += 1
                if s0 != s1:
                    total["seed_bad"] += 1
                continue
            total["list"] += 1
            modes[mode] += 1
            w, t, draws, notes = ck.mas_model(RAVEN_CLASS, lvl, d, 0, mode, K.sd_parse(s0))
            if K.sd_fmt(t) != s1:
                total["seed_bad"] += 1
            after[(lvl, st1.get("19", 0), st1.get("21", 0), st1.get("22", 0), w[19], w[21], w[22])] += 1
        L.append("  modes=%s" % dict(sorted(modes.items())))
        readings = [("owner", lv)] + [("owner%+d" % k, lv + k) for k in (-1, 1)] + [("summon_own_level", -1), ("no_skill_entry_lvl0", 0), ("no_pair", None)]
        for key, k in after.most_common():
            lvl, s19, s21, s22, m19, m21, m22 = key
            L.append("  VALUES n=%d level=%d logged 19=%d 21=%d 22=%d, MonLvl only 19=%d 21=%d 22=%d" % (k, lvl, s19, s21, s22, m19, m21, m22))
            for name, l2 in readings:
                l2 = lvl if l2 == -1 else l2
                mn, mx, th = owner_pair(c, l2) if l2 is not None else (0, 0, 0)
                o19, o21, o22 = s19 - (m19 + th), s21 - (m21 + mn), s22 - (m22 + mx)
                L.append("    OFFSET %-19s level=%s pair=(%d,%d,%d) logged-model: 19 %+d, 21 %+d, 22 %+d" % (
                    name, l2, mn, mx, th, o19, o21, o22))
    L.append("H3TOTAL " + " ".join("%s=%d" % (k, total[k]) for k in sorted(total)))
    return "\n".join(L) + "\n"


def selftest():
    assert level_bands(1, [9] * 5) == 0
    assert level_bands(8, [1, 2, 3, 4, 5]) == 7
    assert level_bands(20, [1, 2, 3, 4, 5]) == 7 + 16 + 12
    assert level_bands(29, [1, 2, 3, 4, 5]) == 7 + 16 + 18 + 24 + 5
    c = {"b05": 0, "shift": 8, "src": 0, "min": 2, "max": 4, "bmin": [1, 1, 1, 1, 1], "bmax": [2, 2, 2, 2, 2], "sym": -1,
         "tohit": 10, "levtohit": 5, "thcalc": -1}
    assert owner_pair(c, 3) == (4, 8, 20)
    assert owner_pair(c, 0) == (2, 4, 0)
    mk = lambda st0, st1, u=1: (2, 104, st0, st1, "0:0", "0:0", 0, 1, u, 1)  # noqa: E731
    calls = [mk({}, {}), mk({"12": 104, "19": 100}, {"19": 120, "21": 3, "22": 4}), mk({"19": 120, "21": 3, "22": 4}, {"19": 120, "21": 3, "22": 4})]
    r = compare(calls, lambda c: (20, 3, 4))
    assert dict(r) == {"units": 1, "first_call_ok": 1, "later_ok": 1}, r
    assert compare(calls, lambda c: (21, 3, 4))["first_call_bad"] == 1
    assert compare(calls + [mk({"19": 120}, {"19": 121, "21": 3, "22": 4})], lambda c: (20, 3, 4))["later_bad"] == 1
    print("selftest ok")
    return 0


def main(argv):
    if argv and argv[0] == "selftest":
        return selftest()
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    paths, out, excel = [], None, None
    a, k = argv[1:], 0
    while k < len(a):
        if a[k] == "--out":
            out = a[k + 1]
            k += 2
        elif a[k] == "--excel":
            excel = a[k + 1]
            k += 2
        else:
            paths.append(a[k])
            k += 1
    text = check(paths, excel)
    if out:
        open(out, "w").write(text)
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

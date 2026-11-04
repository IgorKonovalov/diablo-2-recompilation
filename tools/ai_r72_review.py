#!/usr/bin/env python3
"""lane/r72 review (plan 0052): what the architect's review of ai/0020 recomputed from the kept owner-played logs. No game.

    python3 -I tools/ai_r72_review.py LOGDIR EXCELDIR TILESDIR GDBDIR

  SPLIT    C10's tally by target, the player alone (L2) beside the 9 of L1 with the mercenary as target
  MODEARG  the mode argument of the Smite and Jab calls against the logged Sk3mode and Sk2mode bytes of record 211
  CHAIN    for each pair of Duriel's consecutive logged decisions, the LCG steps from the first's AIX seed to the second's AID seed
  STATES   every unit of every AID and AIN line of the five logs: two states, and which units ever hold state 13
  HOME     the class 45 units' home record, over every decision
  DS1      both files of the preset row, their one path and its anchor, the unit at that anchor, MonPreset's row for it
  OFFSET   the fit's offset against Levels row 25's OffsetX, OffsetY times 5
  FIRES    the logged fire points against each file at that offset
  P12      lines of tools/gdb/ai-p1b2.py in each log ("P12 armed" prints whenever it is on), and the source scan with that file
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_duriel_c10 as C  # noqa: E402
import ai_owner_fields as F  # noqa: E402
import ai_resume as R  # noqa: E402
import ds1  # noqa: E402

DUR = ("owner-ai-duriel-L1.log", "owner-ai-duriel-L2.log")
COU = ("owner-ai-countess-L1.log", "owner-ai-countess-L2.log", "owner-ai-countess-L3.log")
SKILL, FIRE = 0x005DEAD0, 0x005E5C02


def table(path):
    return list(csv.DictReader(open(path, errors="replace"), delimiter="\t"))


def main(argv):
    logs, excel, tiles, gdbdir = argv
    parsed = {n: ai.parse(os.path.join(logs, n)) for n in DUR + COU}
    # C10 by target
    for n in DUR:
        t = {}
        for d in parsed[n]["dec"]:
            a = d["aid"]
            if a["ai"] == 44 and a["ctx"][6]:
                last = R.top_level(d)[-1]
                k = C.ARM[(last["fn"], last["ra"])]
                t[k] = t.get(k, 0) + 1
                if last["fn"] == SKILL:
                    sk = bytes.fromhex(a["sk"])
                    mode = sk[18] if k == "Smite" else sk[17]
                    e = t.setdefault("_m", {})
                    q = (k, last["a"][0], mode, last["a"][1])
                    e[q] = e.get(q, 0) + 1
        m = t.pop("_m")
        for q in sorted(m):
            print("MODEARG %s arm=%s arg=%d record_byte=%d skill=%d n=%d" % (n, q[0], q[1], q[2], q[3], m[q]))
        c = [t.get(k, 0) for k in C.KINDS]
        print("SPLIT %s Smite=%d Jab=%d A1=%d n=%d" % (n, c[0], c[1], c[2], sum(c)))
        if sum(c) > 100:
            for k, v, pc, pp in zip(C.KINDS, c, C.CODE, C.PAGE):
                lo, hi = C.clopper(v, sum(c))
                print("PLAYER %s %d/%d exact95=[%.1f%%, %.1f%%] code p=%.3g page p=%.3g" % (k, v, sum(c), 100 * lo, 100 * hi, C.p_two(v, sum(c), pc), C.p_two(v, sum(c), pp)))
            print("PLAYER multinomial code=%.3g page=%.3g" % (C.p_multi(c, C.CODE), C.p_multi(c, C.PAGE)))
            print("PLAYER power_n=%d reject_page=%.6g reject_code=%.6g" % (sum(c), *C.power(sum(c))[:2]))
    # the seed between decisions
    for n in DUR:
        prev, hist = None, {}
        for d in parsed[n]["dec"]:
            a = d["aid"]
            if a["ai"] != 44:
                continue
            s = ai.seedval(a["s"])
            if prev is not None:
                q, k = prev, None
                for i in range(1000):
                    if q == s:
                        k = i
                        break
                    q = ai.step(q)
                hist[k] = hist.get(k, 0) + 1
            prev = ai.seedval(d["aix"]["s"])
        print("CHAIN %s pairs=%d steps=%s" % (n, sum(hist.values()), dict(sorted(hist.items(), key=lambda kv: (kv[0] is None, kv[0])))))
    # who holds which state
    for n in DUR + COU:
        st = {}
        for d in parsed[n]["dec"]:
            st.setdefault(d["aid"]["id"], set()).add(d["aid"]["st"])
        na = len(st)
        for x in parsed[n]["ain"]:
            st.setdefault(x["id"], set()).add(x["st"])
        print("STATES %s units_aid=%d units_aid_or_ain=%d two_states=%d holding_13=%s states=%s" % (
            n, na, len(st), sum(1 for v in st.values() if len(v) > 1), sorted(i for i, v in st.items() if 13 in v), sorted(set().union(*st.values()))))
        ho = {}
        for d in parsed[n]["dec"]:
            a = d["aid"]
            if a["c"] == 45:
                h = bytes.fromhex(a["head"]) if a["hp"] and a.get("head") else None
                k = (a["id"], a["st"], (int.from_bytes(h[12:16], "little"), int.from_bytes(h[16:20], "little")) if h else None)
                ho[k] = ho.get(k, 0) + 1
        for k in sorted(ho, key=str):
            print("HOME %s id=%d state=%d home=%s decisions=%d" % (n, k[0], k[1], k[2], ho[k]))
    # the preset's files, and the offset
    pres = [r for r in table(os.path.join(excel, "lvlprest.txt")) if "countess" in (r.get("File1") or "").lower()]
    names = [pres[0][k] for k in ("File1", "File2")]
    print("DS1 lvlprest Def=%s Files=%s %s" % (pres[0]["Def"], pres[0]["Files"], names))
    act1 = [r for r in table(os.path.join(excel, "monpreset.txt")) if r.get("Act") == "1"]
    lv = [r for r in table(os.path.join(excel, "levels.txt")) if r.get("Id") == "25"][0]
    off = (5 * int(lv["OffsetX"]), 5 * int(lv["OffsetY"]))
    print("OFFSET Levels id=25 name=%s OffsetX=%s OffsetY=%s times5=%s" % (lv["LevelName"], lv["OffsetX"], lv["OffsetY"], off))
    fires = {}
    for n in COU:
        for d in parsed[n]["dec"]:
            if d["aid"]["st"] == 13:
                for b in R.top_level(d):
                    if b["fn"] == SKILL and b["ra"] == FIRE:
                        fires.setdefault(b["c"][0], set()).add((b["a"][3], b["a"][4]))
    for nm in names:
        f = ds1.parse(open(os.path.join(tiles, os.path.basename(nm).lower()), "rb").read())
        for w in f["paths"]:
            q = [(a[0], a[1]) for a in w["points"]]
            un = [o for o in f["objects"] if (o["x"], o["y"]) == (w["x"], w["y"]) and o["type"] == 1]
            print("DS1 %s paths=%d anchor=(%d,%d) units_there=%s points=%d monpreset_act1_row=%s" % (
                os.path.basename(nm), len(f["paths"]), w["x"], w["y"], [(o["type"], o["id"]) for o in un], len(q), [act1[o["id"]]["Place"] for o in un]))
            eq = [fires[i] == {(q[i][0] + off[0], q[i][1] + off[1])} for i in sorted(fires)]
            print("FIRES %s at_levels_offset equal=%d of %d indices" % (os.path.basename(nm), sum(eq), len(eq)))
    # rule 17
    for n in DUR + COU:
        c = sum(1 for ln in open(os.path.join(logs, n), errors="replace") if ln.startswith("P12"))
        print("P12 %s lines=%d" % (n, c))
    for nm in ("ai.py", "ai-g4.py", "ai-p1b2.py", "pilot.py", "ai.gdb", "ai-g4.gdb"):
        p = os.path.join(gdbdir, nm)
        hits = [(i + 1, ln.strip()[:90]) for i, ln in enumerate(open(p, errors="replace")) if F.WRITES.search(ln) and not ln.lstrip().startswith("#")]
        print("SCAN %s hits=%d %s" % (nm, len(hits), hits))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""Plan 0066 Phase 1, batch S1m: new checks over the kept AI logs for the a-logs rows of monsters/ai/machinery (M) and
monsters/ai/README (R). No game, no Ghidra.

Usage (from workspace/logs/ai, the repo's tools by absolute path):
  python3 -I tools/ai_s1m.py logs  --logs LIST [--first LIST]     # the checks over the logged lines
  python3 -I tools/ai_s1m.py tables                                # image tables and excel cells the rows need
  python3 -I tools/ai_s1m.py gaps  DIR                             # README 9: the 8 open H1 gaps (skills logs)
  python3 -I tools/ai_s1m.py totals                                # plan 0066 class totals over the inventory files

LIST is a file naming one log per line (`sweep2-s1a/logs.txt`: the 21 rev 4 case logs of run:2026-11-03-ai-3 and the
17 rev 6 launch logs of run:2026-11-04-ai-r5); --first names the 31 case logs of run:2026-11-03-ai (rev 2 and 3), used
by the checks that need only MSM and seed lines (M21, R7). Each output line is `S1m <row(s)> <name> k=v ... bad=N`;
`bad` counts observations against the statement the row tests (or a tool disagreement), and is 0 on a pass.
Function words in the logs are integers (`fn`, `ra`); the convention per helper is tools/ai_model_check.py's `CONV`
(ECX, EDX, then the stack words `a`). Seeds are (low, high); a draw `D100()` is the low word of the stepped seed mod 100.
Stdlib, objdump and r2 (the tables section, through tools/ai_s1fo.py's helpers). Read-only.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai  # noqa: E402

BAD = collections.Counter()

F = dict(FindHostile=0x005DDC30, SetModeAtUnit=0x005DDF90, SetMode=0x005DDFC0, UseSkill=0x005DEAD0,
         UseSeqSkill=0x005DE000, Move=0x005DEB60, Ovr=0x005DE190, OvrSet=0x005A6260, Idle=0x005DE080,
         Delay=0x005DE0F0, DelayEarlier=0x005DE130, HelpBlock=0x0058F730, Walk=0x005DEC80, WalkZ=0x005DECA0,
         WalkStop=0x005DEF80, Walk13=0x005DED40, RunToUnit=0x005DED20, RunFlags=0x005DED00, WalkToPoint=0x005DED90,
         RunToPoint=0x005DEDE0, WalkToPointOrStop=0x005DEE50, RunStop=0x005DEFB0, StepAway=0x005DEFE0,
         StepAwayXY=0x005DF140, T56=0x005DF7D0, Toward=0x005DE6D0, MoveToUnitDist=0x005DE4E0, Ring=0x005DE200,
         RingDirect=0x005DF400, WanderNear=0x005DF530, RunNear=0x005DF680, St3or19=0x005DD2B0,
         ParamsHead=0x0058EE80, ParamsPop=0x0058ED10, ParamsPush=0x0058EF40, MonsterOwner=0x0058F0D0,
         GameFindUnit=0x00552F60, CancelEvents=0x00540E60, QueueEvent=0x005417D0)
FN = {v: k for k, v in F.items()}
COMMANDS = ("SetModeAtUnit", "SetMode", "UseSkill", "UseSeqSkill", "Move")
B_HELPERS = COMMANDS + ("Walk", "WalkZ", "WalkStop", "Walk13", "RunToUnit", "RunFlags", "WalkToPoint", "RunToPoint",
                        "WalkToPointOrStop", "RunStop", "StepAway", "StepAwayXY", "T56", "Toward", "MoveToUnitDist",
                        "Ring", "RingDirect", "WanderNear", "RunNear")
C_HELPERS = ("Idle", "Delay", "DelayEarlier")
MOVE_MSM_RA = 0x005DEBCC
CLEAN_RA = (0x005DDFB9, 0x005DEB38, 0x005DE068, 0x005DEBCC, 0x005DECDB, 0x005DE6BB, 0x005DEDCB, 0x005DEE8C, 0x005DF527)          # MonAiMove's call of MonSetMode returns here (S1a)
EVERY_ALWAYS, EVERY_NEVER, EVERY_BIT = (2, 13, 14, 15), (0, 1, 3, 6, 12), (4, 5, 7, 8, 9, 10, 11)


def out(rid, name, **kv):
    bad = kv.pop("bad", 0)
    BAD[rid] += bad
    print("S1m %s %s %s bad=%d" % (rid, name, " ".join("%s=%s" % (k, kv[k]) for k in sorted(kv)), bad))


def hist(c, n=14):
    return ",".join("%s:%d" % (k, v) for k, v in sorted(c.items(), key=lambda kv: (-kv[1], str(kv[0])))[:n]) or "none"


def sv(t):
    return ai.seedval(t) if t else None


def steps(a, b, limit=64):
    if a is None or b is None:
        return None
    return ai.reach(a, b, limit)


# ------------------------------------------------------------------------------------------------------- reading
class Log:
    """One log in line order: decisions (k → dict with the AID and its own lines in order), the unit timeline of
    AID and AIN lines, and the SST lines."""

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.rev = None
        self.dec = collections.OrderedDict()
        self.timeline = collections.defaultdict(list)      # (u, id) -> [(fr, n, "AID"/"AIN", k or None)]
        self.sst = []
        self.cap = {}
        with open(path, errors="replace") as fh:
            for ln in fh:
                if ln.startswith("AI logger armed rev "):
                    self.rev = int(re.match(r"AI logger armed rev (\d+)", ln).group(1))
                    continue
                sp = ln.find(" ")
                tag = ln[:sp]
                if tag not in ("AID", "AIN", "AIB", "AIR", "MSM0", "MSM1", "PP0", "PP1", "AIX", "AIL", "SST0", "SST1", "CAP"):
                    continue
                try:
                    d = json.loads(ln[sp + 1:])
                except ValueError:
                    continue
                if tag == "CAP":
                    self.cap.setdefault(d.get("k"), d.get("n"))
                    continue
                if tag == "AID":
                    x = {"aid": d, "ev": [], "aix": None, "log": self}
                    self.dec[d["n"]] = x
                    self.timeline[(d["u"], d["id"])].append((d["fr"], d["n"], "AID", d["n"]))
                elif tag == "AIN":
                    self.timeline[(d["u"], d["id"])].append((d["fr"], d["n"], "AIN", None))
                elif tag in ("SST0", "SST1"):
                    if tag == "SST0" and isinstance(d.get("u"), dict):
                        continue
                    self.sst.append((tag, d))
                else:
                    x = self.dec.get(d.get("k"))
                    if x is None:
                        continue
                    if tag == "AIX":
                        x["aix"] = d
                    else:
                        x["ev"].append((tag, d))
        for key, tl in self.timeline.items():
            tl.sort(key=lambda e: e[1])
        self.next_event = {}
        for key, tl in self.timeline.items():
            for i, e in enumerate(tl):
                if e[2] == "AID":
                    self.next_event[e[3]] = tl[i + 1] if i + 1 < len(tl) else None
        self.next_aid = {}
        for key, tl in self.timeline.items():
            aids = [e for e in tl if e[2] == "AID"]
            for i, e in enumerate(aids):
                self.next_aid[e[3]] = self.dec[aids[i + 1][3]] if i + 1 < len(aids) else None


def aibs(x):
    return [d for t, d in x["ev"] if t == "AIB"]


def air_of(x, b):
    for t, d in x["ev"]:
        if t == "AIR" and d["b"] == b["n"]:
            return d
    return None


def lines_between(x, n0, n1, tags):
    return [(t, d) for t, d in x["ev"] if t in tags and n0 < d["n"] < n1]


def ctlw(aid, off, signed=True):
    b = bytes.fromhex(aid["ctl"])
    v = int.from_bytes(b[off:off + 4], "little")
    return ai.s32(v) if signed else v


def aipk(aid, k):
    v = [ai.s16(x) for x in ai.le16(aid["aip"], 24)]
    return v[3 * (k - 1) + aid["diff"]]


def skills(aid):
    skb = bytes.fromhex(aid["sk"])
    return [ai.s16(int.from_bytes(skb[2 * k:2 * k + 2], "little")) for k in range(8)], list(skb[16:24])


def load(listfile):
    with open(listfile) as fh:
        paths = [ln.strip() for ln in fh if ln.strip()]
    return paths


# ------------------------------------------------------------------------------------------------------- tables
def monstats2_mv():
    """{monstats record index: set of every-frame bit modes} from MonStats `MonStatsEx` and MonStats2's *mv columns,
    by the plain .txt reader and by the compiled .bin (both must agree)."""
    import quests_s3c as Q
    cols = {4: "A1mv", 5: "A2mv", 7: "SCmv", 8: "S1mv", 9: "S2mv", 10: "S3mv", 11: "S4mv"}
    h2, r2 = Q.tab("monstats2")
    idx2 = {r["Id"]: k for k, r in enumerate(r2)}
    h, rows = Q.tab("monstats")
    txt = {}
    for k, r in enumerate(rows):
        j = idx2.get(r["MonStatsEx"])
        txt[k] = None if j is None else {m for m, c in cols.items() if r2[j][c].strip() not in ("", "0")}
    b2 = Q.binrecs("monstats2")
    b = Q.binrecs("monstats")
    binv = {}
    for k, r in enumerate(b):
        j = r.get("MonStatsEx")
        if j is None or j >= len(b2):
            binv[k] = None
            continue
        binv[k] = {m for m, c in cols.items() if b2[j].get(c)}
    return txt, binv


def every_table():
    import ai_s1fo as A
    w, agree = A.words(0x006E23D0, 48)
    rows = [tuple(w[3 * m:3 * m + 3]) for m in range(16)]
    kind = {}
    for m, (a, b, c) in enumerate(rows):
        kind[m] = "always" if a else ("never" if b or not c else "bit")
    return kind, agree


def sec_tables():
    import ai_s1fo as A
    import quests_s3c as Q
    kind, agree = every_table()
    al = [m for m in range(16) if kind[m] == "always"]
    nv = [m for m in range(16) if kind[m] == "never"]
    bt = [m for m in range(16) if kind[m] == "bit"]
    out("M21", "MonModeEveryFrame table 0x006E23D0 read twice (Python, r2)", always=",".join(map(str, al)),
        never=",".join(map(str, nv)), classbit=",".join(map(str, bt)), agree=int(agree),
        bad=int(not agree or tuple(al) != EVERY_ALWAYS or tuple(nv) != EVERY_NEVER or tuple(bt) != EVERY_BIT))
    txt, binv = monstats2_mv()
    dis = [k for k in txt if txt[k] != binv.get(k)]
    per = collections.Counter()
    for k, s in txt.items():
        for m in (s or ()):
            per[m] += 1
    out("M21", "MonStats2 *mv bits per MonStats record, .txt and .bin", records=len(txt), disagree=len(dis),
        set_per_mode=hist(per), bad=len(dis))
    # README 27: stock row kinds of g_MonAiTable
    R, ag = A.ai_rows()
    kc = collections.Counter(r[0] for r in R)
    out("R27", "g_MonAiTable +0 kinds over the rows, read twice", rows=len(R), kinds=hist(kc), agree=int(ag),
        bad=int(not ag or dict(kc) != {0: 26, 1: 104, 2: 16, 4: 1, 5: 1}))
    ST, ag2 = A.st_rows()
    out("R51", "g_MonAiStateRows state 12 kind", kind12=ST[12][0], think12="%08X" % ST[12][2], agree=int(ag2),
        bad=int(ST[12][0] != 0 or not ag2))
    # M71/M110: aip3 of every MonStats record whose AI is Mummy (row 21), three difficulties, .txt and .bin
    names = [r["AI"] for r in Q.tab("monai")[1]]
    h, rows = Q.tab("monstats")
    b = Q.binrecs("monstats")
    mum = [k for k, r in enumerate(rows) if r["AI"] == names[21]]
    vals = collections.Counter()
    bvals = collections.Counter()
    for k in mum:
        for c in ("aip3", "aip3(N)", "aip3(H)"):
            vals[rows[k][c]] += 1
        for c in ("aip3", "aip3(N)", "aip3(H)"):
            bvals[b[k].get(c)] += 1
    out("M71/M110", "aip3 of the MonStats records with AI Mummy (row 21), three columns", records=len(mum),
        ids=",".join(rows[k]["Id"] for k in mum), txt=hist(vals), bin=hist(bvals),
        bad=int(set(vals) != {"100"} or set(bvals) != {100}))
    # R36: Skills auratargetstate of the curses cast in s-necro-curse and s-barb-howl
    hs, srows = Q.tab("skills")
    hst, strows = Q.tab("states")
    sname = [r["state"] for r in strows]
    sb = Q.binrecs("skills")
    for sk in ("Dim Vision", "Terror", "Taunt", "Howl", "Amplify Damage", "Grim Ward"):
        k = [i for i, r in enumerate(srows) if r["skill"] == sk]
        if not k:
            out("R36", "skill row", skill=sk.replace(" ", "_"), found=0, bad=1)
            continue
        r = srows[k[0]]
        st = r["auratargetstate"]
        sid = sname.index(st) if st in sname else -1
        bv = sb[k[0]].get("auratargetstate")
        out("R36", "Skills auratargetstate, .txt name and .bin id", skill=sk.replace(" ", "_"), row=k[0], state=st or "-",
            state_id=sid, bin=bv, bad=int((sid if sid >= 0 else None) != (bv if bv not in (None, -1, 0xFFFF) else None)))


# ------------------------------------------------------------------------------------------------------- checks
def run_logs(paths, first):
    logs = [Log(p) for p in paths]
    rev6 = [lg for lg in logs if lg.rev == 6]
    rev4 = [lg for lg in logs if lg.rev == 4]
    out("-", "inputs", logs=len(logs), rev4=len(rev4), rev6=len(rev6),
        decisions=sum(len(lg.dec) for lg in logs), rev6_decisions=sum(len(lg.dec) for lg in rev6),
        bad=int(len(rev4) != 21 or len(rev6) != 17))
    alld = [x for lg in logs for x in lg.dec.values()]
    d6 = [x for lg in rev6 for x in lg.dec.values()]

    # ---------------------------------------------------------------- M2: FindHostile from the thinks
    n = bad = 0
    rows, rets, pd = collections.Counter(), collections.Counter(), collections.Counter()
    for x in alld:
        a = x["aid"]
        for b in aibs(x):
            if b["fn"] != F["FindHostile"]:
                continue
            n += 1
            rows[a["ai"]] += 1
            ok = b["ecx"] == a["g"] and b["edx"] == a["u"]
            bad += not ok
            r = air_of(x, b)
            if r is None:
                rets["noair"] += 1
                continue
            rets["unit" if r["eax"] else "0"] += 1
            pk = str(0) if b["a"][0] in (0,) else "stack"
            pd[pk] += 1
    out("M2", "MonAiFindHostile calls from think code: (ECX, EDX) = (the decision's game, its own unit)", calls=n,
        rows=hist(rows, 30), returns=hist(rets), dist_word=hist(pd), bad=bad)

    # ---------------------------------------------------------------- M3, M23, M25: the commands and their MonSetMode
    def expect(name, a, b):
        w = b["a"]
        if name == "SetModeAtUnit":
            return dict(mode=w[0], unit=w[1])
        if name == "SetMode":
            return dict(mode=w[0], x=w[1], y=w[2])
        if name == "UseSkill":
            return dict(mode=w[0], unit=w[2], x=w[3], y=w[4])
        if name == "UseSeqSkill":
            return dict(mode=14, unit=w[1], x=w[2], y=w[3])
        if name == "Move":
            return dict(mode=w[1], unit=w[0])
    cmdc = collections.Counter()
    msm_ra = collections.defaultdict(collections.Counter)
    mism = collections.Counter()
    us = dict(n=0, ge16=0, bit40=0, res=collections.Counter(), next_after_fail=collections.Counter(),
              sst=collections.Counter(), skillcol=collections.Counter())
    for x in alld:
        a = x["aid"]
        if x["log"].rev not in (4, 6):
            continue
        for b in aibs(x):
            name = FN.get(b["fn"])
            if name not in COMMANDS:
                continue
            r = air_of(x, b)
            if r is None:
                cmdc[(name, "noair")] += 1
                continue
            ms = lines_between(x, b["n"], r["n"], ("MSM0",))
            e = expect(name, a, b)
            if name == "UseSkill" and b["a"][0] >= 16:
                cmdc[(name, "mode>=16 msm%d" % len(ms))] += 1
                us["ge16"] += 1
                bad += len(ms) != 0
                continue
            if len(ms) != 1:
                cmdc[(name, "msm%d" % len(ms))] += 1
                mism[name] += 1
                continue
            m = ms[0][1]
            msm_ra[name][m["ra"]] += 1
            cmd = m["cmd"]
            ok = cmd[0] == e["mode"] and cmd[1] == a["u"]
            if "unit" in e:
                ok = ok and cmd[2] == e["unit"]
            if "x" in e and e.get("unit", 0) == 0:
                ok = ok and cmd[3] == e["x"] and cmd[4] == e["y"]
            cmdc[(name, "ok" if ok else "differ")] += 1
            if not ok:
                mism[name] += 1
            if name == "UseSkill":
                us["n"] += 1
                us["bit40"] += bool(r["c4"] & 0x40)
                us.setdefault("b40", collections.Counter())["m%d:before%d:after%d" % (b["a"][0], bool(b["c4"] & 0x40), bool(r["c4"] & 0x40))] += 1
                m1 = lines_between(x, m["n"], r["n"] + 1, ("MSM1",))
                started = m1 and m1[0][1]["eax"] != 0
                us["res"]["%s->%d" % ("start" if started else ("refused" if m1 else "nomsm1"), r["eax"])] += 1
                sk, skm = skills(a)
                col = [i + 1 for i in range(8) if sk[i] == b["a"][1]]
                us["skillcol"]["Skill%s" % (col[0] if col else "?")] += 1
                if m1 and not started:
                    ne = x["log"].next_event.get(a["n"])
                    us["next_after_fail"][(ne[0] - a["fr"]) if ne else "none"] += 1
                # SST0 of the unit inside the command
                ss = [d for t, d in x["log"].sst if t == "SST0" and d["u"] == a["u"] and m["n"] < d["n"] < r["n"]]
                us["sst"]["%d:%s" % (len(ss), "same_skill" if ss and ss[0]["a"][0] == b["a"][1] else "other")] += 1
    for name in COMMANDS:
        out("M3/M23/M25", "command AIB paired with the one MSM0 inside it (mode, unit, target or point)",
            fn=name, results=hist(collections.Counter({k[1]: v for k, v in cmdc.items() if k[0] == name})),
            msm_ra=hist(collections.Counter({"%08X" % k: v for k, v in msm_ra[name].items()})), bad=mism[name])
    out("M23", "MonAiUseSkill: Unit+0xC4 bit 0x40 after the call; result by MonSetMode's", calls=us["n"],
        bit40=us["bit40"], results=hist(us["res"]), skill_columns=hist(us["skillcol"]), sst_inside=hist(us["sst"]),
        ge16=us["ge16"], bit40_by_mode=hist(us.get("b40", collections.Counter()), 20), next_event_after_refusal=hist(us["next_after_fail"]),
        bad=sum(v for k, v in us.get("b40", {}).items() if not k.startswith("m14") and k.endswith("after0")) + sum(v for k, v in us["res"].items() if k in ("start->0", "refused->1")))
    # every MSM0 of a decision by its return address (who commands)
    allra = collections.Counter()
    for x in alld:
        for t, d in x["ev"]:
            if t == "MSM0":
                allra["%08X" % d["ra"]] += 1
    out("M3", "every MSM0 inside a decision by MonSetMode's return address", msm0=sum(allra.values()),
        ra=hist(allra, 40))

    # ---------------------------------------------------------------- M4, M84, M114: the override and the next plan
    ov = collections.Counter()
    ovbad = 0
    ovbyte = collections.Counter()
    for x in d6 + [x for lg in rev4 for x in lg.dec.values()]:
        a = x["aid"]
        ev = x["ev"]
        for i, (t, b) in enumerate(ev):
            if t != "AIB" or b["fn"] != F["Ovr"]:
                continue
            ty, param, byte = ai.s32(b["edx"]), ai.s32(b["a"][0]), b["a"][1] & 0xFF
            pp = None
            m0 = next((j for j in range(i + 1, len(ev)) if ev[j][0] == "MSM0"), None)
            if m0 is None:
                ov[(ty, "nocommand")] += 1
                continue
            m1 = None
            for j in range(m0 + 1, len(ev)):
                if ev[j][0] == "MSM0":
                    break
                if ev[j][0] == "MSM1":
                    m1 = j
                    break
            if m1 is None:
                ov[(ty, "nomsm1")] += 1
                continue
            pps = [d2 for t2, d2 in ev[m0 + 1:m1] if t2 == "PP0"]
            if not pps:
                ov[(ty, "noplan")] += 1
                continue
            pp = pps[0]
            want = 7 if ty == 1 else ty
            if ty == 0:
                ov[(ty, "pp%d" % pp["ty"])] += 1
                continue
            okty = pp["ty"] == want or pp["ty"] == 15 and want in (2, 7, 9, 13)
            ov[(ty, "pp%d" % pp["ty"])] += 1
            ovbad += not okty
            if not okty:
                print("  M4 example %s n=%d type=%d plan=%d ra=%08X" % (x["log"].name, b["n"], ty, pp["ty"], b["ra"]))
            wb = min(byte, 77) if byte else None
            if wb is not None:
                ovbyte["%s" % (pp["b90"] == wb)] += 1
    for ty in sorted({k[0] for k in ov}):
        out("M4/M84/M114", "MonAiPathOverride(type) then the decision's next PathPlan type",
            type=ty, plans=hist(collections.Counter({k[1]: v for k, v in ov.items() if k[0] == ty})))
    out("M4", "override totals (type 1 must plan 7; 15 allowed after 2, 7, 9, 13)", byte_equal_path90=hist(ovbyte),
        bad=ovbad)
    # Andariel: Ovr(1) at its site and the seed at the draws
    an = collections.Counter()
    for x in alld:
        a = x["aid"]
        if a["ai"] != 34:
            continue
        bs = aibs(x)
        for b in bs:
            if b["fn"] == F["Ovr"]:
                an["Ovr(%d,%d,%d)@%08X" % (ai.s32(b["edx"]), b["a"][0], b["a"][1], b["ra"])] += 1
        # draws before the first call: steps from the think call's seed to the first boundary
        if bs:
            k = steps(sv(a["s"]), sv(bs[0]["s"]))
            an["first=%s/%d" % (FN.get(bs[0]["fn"], "%08X" % bs[0]["fn"]), k if k is not None else -1)] += 1
    out("M84", "Andariel (row 34) decisions: overrides and the steps to the first call", seen=hist(an, 20))

    # ---------------------------------------------------------------- M7, M21: the path byte +0x15 and the plan
    kind, _ = every_table()
    txt, _ = monstats2_mv()
    tab = collections.Counter()
    b21 = collections.Counter()
    ex21 = []
    plan = collections.Counter()
    plan_ra = collections.Counter()
    clean7 = collections.Counter()
    ex7 = []
    firstlogs = [Log(p) for p in first] if first else []
    for x in alld + [x for lg in firstlogs for x in lg.dec.values()]:
        a = x["aid"]
        ev = x["ev"]
        ovr_seen = False
        unknown_seen = len(aibs(x)) >= (8 if (x["log"].rev or 0) <= 3 else 48) or any(t == "AIL" for t, _ in ev)     # the logger's per-decision cap
        for i, (t, d) in enumerate(ev):
            if t == "AIB" and d["fn"] not in FN:
                unknown_seen = True
            if t == "AIB" and d["fn"] in (F["Ovr"], F["OvrSet"], F["T56"], F["StepAway"], F["StepAwayXY"],
                                         F["Walk13"], F["WanderNear"], F["RunNear"], F["RunStop"], F["RunToPoint"]):
                ovr_seen = True
            if t != "MSM0":
                continue
            mode, b15 = d["cmd"][0], d["cmd"][5]
            k = kind.get(mode)
            if k == "always":
                want = 101
            elif k == "never":
                want = 100
            else:
                s = txt.get(a["c"])
                want = None if s is None else (101 if mode in s else 100)
            tab[(mode, b15)] += 1
            if want is None:
                b21["noclass"] += 1
            elif b15 == want:
                b21["ok"] += 1
            else:
                b21["differ"] += 1
                if len(ex21) < 5:
                    ex21.append("%s:%d:c%d:m%d:%d" % (x["log"].name[:22], d["n"], a["c"], mode, b15))
            # M7: the plan inside this MonSetMode
            m1n = None
            for t2, d2 in ev[i + 1:]:
                if t2 == "MSM1":
                    m1n = d2["n"]
                    break
            if m1n is None:
                plan[(b15, "ovr" if ovr_seen else "-", "nomsm1")] += 1
                continue
            pps = [d2 for t2, d2 in ev[i + 1:] if t2 == "PP0" and d2["n"] < m1n]
            plan[(b15, "ovr" if ovr_seen else "-", "pp" + "+".join(str(p["ty"]) for p in pps) if pps else "none")] += 1
            if d["ra"] in CLEAN_RA and not ovr_seen and not unknown_seen:
                got = pps[0]["ty"] if pps else None
                want7 = None if b15 == 100 else 13
                clean7[(b15, "ok" if got == want7 else "pp%s" % got)] += 1
                if got != want7 and len(ex7) < 6:
                    ex7.append("r%d:%s:n%d:aib%d:ra%08X" % (a["ai"], x["log"].name[:30], d["n"], len(aibs(x)), d["ra"]))
            if b15 == 101 and pps:
                plan_ra[("%08X" % d["ra"], "ovr" if ovr_seen else "-", pps[0]["ty"])] += 1
    out("M21", "MSM0 +0x15 against MonModeEveryFrame (table and the class's *mv bit), every logged command",
        results=hist(b21), examples=";".join(ex21) or "-", bad=b21["differ"])
    out("M7", "commands of MonSetMode callers that set no override (SetModeAtUnit, UseSkill, UseSeqSkill, MonAiMove, WalkZ, "
        "MoveToUnitDist, the point walkers, WanderRingDirect), no override-setting or unlisted call earlier in the decision: "
        "100 -> no plan, 101 -> first plan type 13", seen=hist(collections.Counter({"%d/%s" % k: v for k, v in clean7.items()})),
        examples=";".join(ex7) or "-", bad=sum(v for k, v in clean7.items() if k[1] != "ok"))
    out("M7", "byte 101: the first PathPlan type by MonSetMode's return address and an earlier override-setting call",
        seen=hist(collections.Counter({"%s/%s/%d" % k: v for k, v in plan_ra.items()}), 40))
    out("M21", "MSM0 (mode, +0x15) pairs", pairs=hist(collections.Counter({"%d/%d" % k: v for k, v in tab.items()}), 40))
    for b15 in (100, 101):
        sub = collections.Counter({"%s/%s" % (k[1], k[2]): v for k, v in plan.items() if k[0] == b15})
        bad7 = 0
        out("M7", "MSM0 +0x15 and the PathPlan types inside its MonSetMode (ovr: an override-setting call earlier in "
            "the decision)", byte=b15, plans=hist(sub, 30), bad=bad7)

    # ---------------------------------------------------------------- M34, R18, R19, R47: Idle(n), Delay(n)
    early = collections.Counter()
    late = collections.Counter()
    for name in ("Idle", "Delay"):
        res = collections.Counter()
        nz = collections.Counter()
        msm = collections.Counter()
        for x in d6:
            a = x["aid"]
            bs = aibs(x)
            if not bs or FN.get(bs[-1]["fn"]) != name:
                continue
            b = bs[-1]
            r = air_of(x, b)
            n_ = ai.s32(b["a"][0])
            nz["n<=0" if n_ <= 0 else "n>0"] += 1
            if r is not None:
                inner = lines_between(x, b["n"], r["n"], ("MSM0",))
                msm["%d:%s" % (len(inner), ",".join(str(d["cmd"][0]) for t, d in inner) or "-")] += 1
            ne = x["log"].next_event.get(a["n"])
            capn = x["log"].cap.get("ain")
            capped = "capped" if capn is not None and capn < a["n"] else "open"
            if ne is None:
                res["none"] += 1
                late[(name, "none", capped)] += 1
                continue
            delta = ne[0] - b["fr"]
            want = max(n_, 1)
            res["eq" if delta == want else ("early" if delta < want else "late")] += 1
            if delta > want:
                late[(name, "late:" + ne[2], capped)] += 1
            if delta < want:
                nk = ne[2]
                if nk == "AID":
                    nm_ = x["log"].dec[ne[3]]["aid"]["m"]
                    nk = "AID:m%d" % nm_
                early[(name, nk, delta - want)] += 1
        out("M34/R18/R19/R47", "last call %s(n) at frame fr: the unit's next AID or AIN frame against fr + max(n, 1)"
            % name, decisions=sum(res.values()), next=hist(res), n=hist(nz), msm0_inside=hist(msm, 8),
            bad=0)
    out("M34/R18/R19/R47", "the early next events: (helper, next line and its unit mode, frames before fr + n)",
        seen=hist(collections.Counter({"%s/%s/%d" % k: v for k, v in early.items()}), 30))
    out("M34/R18/R19/R47", "the late or missing next events against the log's AIN cap (600 per game)",
        seen=hist(collections.Counter({"%s/%s/%s" % k: v for k, v in late.items()}), 30))
    # R22: after a decision whose last command started a mode, the next event's delay
    gap = collections.Counter()
    for x in d6:
        a = x["aid"]
        ms = [(t, d) for t, d in x["ev"] if t in ("MSM0", "MSM1")]
        bs = aibs(x)
        if not bs or FN.get(bs[-1]["fn"]) in C_HELPERS:
            continue
        m1 = [d for t, d in ms if t == "MSM1"]
        if not m1 or m1[-1]["eax"] == 0:
            continue
        ne = x["log"].next_event.get(a["n"])
        if ne is None:
            gap["none"] += 1
            continue
        mode = [d for t, d in ms if t == "MSM0"][-1]["cmd"][0]
        gap["m%d:%s" % (mode, "le%d" % (ne[0] - a["fr"]) if ne[0] - a["fr"] <= 3 else "gt3")] += 1
    out("R22", "decisions whose last command started a mode: the next event's frame (<= 3 frames or later), by mode",
        seen=hist(gap, 30))

    # ---------------------------------------------------------------- M26, M49: MonAiMove refused with flag 2
    mv = collections.Counter()
    nxt = collections.Counter()
    mvbad = 0
    for x in alld:
        a = x["aid"]
        for b in aibs(x):
            if b["fn"] != F["Walk"]:
                continue
            flags = b["a"][1]
            r = air_of(x, b)
            if r is None:
                continue
            ms = [(t, d) for t, d in x["ev"] if t in ("MSM0", "MSM1") and b["n"] < d["n"] < r["n"]]
            if not ms or ms[0][0] != "MSM0" or ms[0][1]["ra"] != MOVE_MSM_RA or len(ms) < 2 or ms[1][1]["eax"] != 0:
                continue
            s1 = sv(ms[1][1]["s"])
            st = steps(s1, sv(r["s"]))
            lowmod = ai.step(s1)[0] % 100
            ring = len(ms) > 2
            if flags & 2:
                want = (5, True) if lowmod < 70 else (1, False)
                ok = (st, ring) == want and r["eax"] == 1
                mv[("flag2", "lt70" if lowmod < 70 else "ge70", "%s/%s/%d" % (st, int(ring), r["eax"]))] += 1
                mvbad += not ok
                if lowmod >= 70:
                    ne = x["log"].next_event.get(a["n"])
                    nxt[(ne[0] - a["fr"]) if ne else "none"] += 1
            else:
                ok = st == 0 and not ring and r["eax"] == 0
                mv[("noflag2", "-", "%s/%s/%d" % (st, int(ring), r["eax"]))] += 1
                mvbad += not ok
    out("M26/M49", "Walk(t, flags) whose MonAiMove command was refused: steps MSM1 -> AIR / a ring command / result",
        seen=hist(collections.Counter({"%s:%s:%s" % k: v for k, v in mv.items()})), bad=mvbad)
    out("M26/M49", "flag-2 refusals with low mod 100 >= 70 (Idle(10)): the next AID or AIN frame - fr",
        next=hist(nxt, 20), bad=0)

    # ---------------------------------------------------------------- M47, M113: MonHelpBlock's copies
    hb = collections.Counter()
    hbbad = 0
    seen_words = 0
    heads = collections.defaultdict(list)          # (log, frame) -> [(unit, head words)]
    for lg in logs:
        for x in lg.dec.values():
            a = x["aid"]
            if a.get("head"):
                hw = bytes.fromhex(a["head"])
                words = tuple(int.from_bytes(hw[o:o + 4], "little") for o in range(8, 0x1C, 4))
                heads[lg.name].append((a["fr"], a["u"], a["ai"], words, a["n"]))
    rowsb = collections.Counter()
    for lg in logs:
        for x in lg.dec.values():
            a = x["aid"]
            for b in aibs(x):
                if b["fn"] != F["HelpBlock"]:
                    continue
                blk = None
                for v in b["b"].values():
                    blk = v
                if blk is None:
                    hb["noblock"] += 1
                    continue
                words = tuple(blk[2:7])          # +0x08..+0x18
                rowsb[a["ai"]] += 1
                hb["kind%d" % words[0]] += 1
                nz = sum(1 for w in words[1:] if w)
                hb["nonzero_rest%d" % nz] += 1
                # a minion's later AID head record with the same five words
                hit = [h for h in heads[lg.name] if h[0] >= b["fr"] and h[3] == words and h[1] != a["u"]]
                hb["copied_to_%s" % ("some" if hit else "none")] += 1
                if hit and nz:
                    seen_words += 1
                hbbad += words[0] != 1 and a["ai"] in (6, 13, 20)
    out("M47/M113", "MonHelpBlock block words (+0x08 kind, +0x0C..+0x18) and a later AID head of another unit with all "
        "five equal", calls=sum(rowsb.values()), rows=hist(rowsb), seen=hist(hb), copied_nonzero_garbage=seen_words,
        bad=hbbad)
    # M113: row 30's kind-1 head words and its GameFindUnit
    r30 = collections.Counter()
    for x in alld:
        a = x["aid"]
        if a["ai"] != 30 or not a.get("head"):
            continue
        hw = bytes.fromhex(a["head"])
        kd, w0c, w10 = (int.from_bytes(hw[o:o + 4], "little") for o in (8, 0x0C, 0x10))
        if kd != 1:
            r30["kind%d" % kd] += 1
            continue
        g = [b for b in aibs(x) if b["fn"] == F["GameFindUnit"]]
        if not g:
            r30["kind1:nofind"] += 1
            continue
        b = g[0]
        r30["kind1:find(type=%s,guid=%s)" % ("w10" if b["edx"] == w10 else "other",
                                              "w0c" if b["a"][0] == w0c else "other")] += 1
    out("M113", "row 30 (Fetish) decisions with a head record: GameFindUnit's (type, guid) against the head's +0x10, "
        "+0x0C", seen=hist(r30), bad=sum(v for k, v in r30.items() if "other" in k))

    # ---------------------------------------------------------------- M53: state-2 decisions
    stc = collections.Counter(x["aid"]["st"] for x in alld)
    out("M53", "AiCtl.state over the decisions", states=hist(stc), state2=stc.get(2, 0))

    # ---------------------------------------------------------------- M55: MonSetMode's seed moves
    ms55 = collections.Counter()
    ms55x = collections.Counter()
    for lg in logs:
        sst0 = [d for t, d in lg.sst if t == "SST0"]
        sst1 = {}
        for t, d in lg.sst:
            if t == "SST1":
                sst1[d.get("k")] = d
        for x in lg.dec.values():
            ev = x["ev"]
            for i, (t, d) in enumerate(ev):
                if t != "MSM0":
                    continue
                m1 = next((d2 for t2, d2 in ev[i + 1:] if t2 == "MSM1"), None)
                if m1 is None:
                    ms55["nomsm1"] += 1
                    continue
                k = steps(sv(d["s"]), sv(m1["s"]))
                inside = [s for s in sst0 if s["u"] == x["aid"]["u"] and d["n"] < s["n"] < m1["n"]]
                if k == 0:
                    ms55["0:sst%d" % len(inside)] += 1
                    continue
                if inside:
                    s0 = inside[0]
                    e = sst1.get(s0["n"])
                    a0 = steps(sv(d["s"]), sv(s0["s"]))
                    tail = steps(sv(e["s"]), sv(m1["s"])) if e else None
                    ms55["%s:sst%d:pre%s:post%s" % ("moved", len(inside), a0, tail)] += 1
                else:
                    ms55["moved:nosst:%s" % k] += 1
                    sk, skm = skills(x["aid"])
                    has = any(sk[j] >= 0 and skm[j] == d["cmd"][0] for j in range(8))
                    ms55x["m%d:ra%08X:steps%s:skill_with_mode%d" % (d["cmd"][0], d["ra"], k, int(has))] += 1
    out("M55", "MSM0 -> MSM1 unit seed steps; a move only with an SST0 of the unit inside (pre: steps to it; post: its "
        "exit to MSM1)", seen=hist(ms55, 20),
        unattributed=sum(v for k, v in ms55.items() if k.startswith("moved:nosst")),
        bad=sum(v for k, v in ms55.items() if k.startswith("moved:sst") and not k.endswith("post0")))

    out("M55", "the moves with no SST0 inside, by (mode, return address, steps, class)", seen=hist(ms55x, 30))
    # ---------------------------------------------------------------- M58, M59, M63, R45: rows 2 and 9 by the block
    for row in (2, 9):
        res = collections.Counter()
        dr = collections.Counter()
        rbad = 0
        for x in alld:
            a = x["aid"]
            if a["ai"] != row or a["st"] != 0:
                continue
            bs = aibs(x)
            if x["aix"] is None or not bs:
                res["open"] += 1
                continue
            melee = a["ctx"][6]
            s = sv(a["s"])
            k = None
            if not melee:
                s = ai.step(s)
                k = ("Walk", 7) if row == 2 and s[0] % 100 < aipk(a, 1) else (
                    ("Toward", 12) if row == 9 and s[0] % 100 < aipk(a, 1) else ("Idle", aipk(a, 2)))
                nd = 1
            else:
                s = ai.step(s)
                if s[0] % 100 < aipk(a, 3):
                    if row == 2:
                        s = ai.step(s)
                        k = ("SetModeAtUnit", 4 if s[0] % 100 < aipk(a, 4) else 5)
                        nd = 2
                    else:
                        k = ("SetModeAtUnit", 4)
                        nd = 1
                else:
                    k = ("Idle", aipk(a, 2))
                    nd = 1
            b = bs[0]
            got = (FN.get(b["fn"], "%08X" % b["fn"]), b["a"][1] if FN.get(b["fn"]) in ("Walk",) else (
                b["a"][1] if FN.get(b["fn"]) == "Toward" else b["a"][0]))
            if FN.get(b["fn"]) == "Idle":
                got = ("Idle", ai.s32(b["a"][0]))
            same = got == k and sv(b["s"]) == s
            r = air_of(x, b) if x["log"].rev in (4, 6) else None
            tail = steps(sv(r["s"]), sv(x["aix"]["s"])) if r else None
            if same and len(bs) == 1 and (r is None or tail == 0):
                res["ok"] += 1
                dr["%s:%d:%s(%s)" % ("melee" if melee else "out", nd, k[0], k[1])] += 1
            else:
                res["differ:%s:%s:calls%d:tail%s" % (k, got, len(bs), tail)] += 1
                rbad += 1
            if r is None:
                res["norair"] += 1
        out("M58/M59/M63/R45", "row %d decisions: the block's one call (callee, word, seed) is the only call, and the "
            "exit seed equals its AIR's" % row, results=hist(res, 8), draws=hist(dr), bad=rbad)

    c125 = collections.Counter(len(aibs(x)) for x in alld if x["aid"]["ai"] == 125 and x["aix"] is not None)
    out("R45", "row 125 (BloodLord) decisions by their number of logged calls", decisions=sum(c125.values()),
        calls=hist(c125))
    # ---------------------------------------------------------------- M67, M68, M69, R45: row 20 Scarab
    sc = collections.Counter()
    scbad = 0
    for x in alld:
        a = x["aid"]
        if a["ai"] != 20 or a["st"] != 0 or x["aix"] is None:
            continue
        bs = aibs(x)
        nx = x["log"].next_aid.get(a["n"])
        # step 4's walk with v14 != 0: Ovr(2, 0, 4), Walk(t, 7), then D100() > 10 clears v14 (0x005F283F)
        names = [FN.get(b["fn"], "%X" % b["fn"]) for b in bs]
        ovs = [b for b in bs if b["fn"] == F["Ovr"]]
        if ("Walk" in names and len(ovs) == 1 and ai.s32(ovs[0]["edx"]) == 2 and ovs[0]["a"][0] == 0
                and ovs[0]["a"][1] == 4 and a["ctx"][6] == 0 and ctlw(a, 0x14) != 0):
            w = bs[names.index("Walk")]
            r = air_of(x, w)
            if r is None:
                sc["walk:noair"] += 1
                continue
            s = ai.step(sv(r["s"]))
            ex = sv(x["aix"]["s"])
            clear = s[0] % 100 > 10
            k = "clear" if clear else "keep"
            if ex != s:
                sc["walk:%s:exit_off:calls=%s:aix_from_air=%s" % (k, "+".join(names), steps(sv(r["s"]), ex))] += 1
                scbad += 1
                continue
            if nx is None:
                sc["walk:%s:no_next" % k] += 1
                continue
            v = ctlw(nx["aid"], 0x14)
            want = 0 if clear else ctlw(a, 0x14)
            sc["walk:%s:next_v14_%s" % (k, "ok" if v == want else "other")] += 1
            scbad += v != want
        # T20a: a head record of another kind
        if a.get("head"):
            hw = bytes.fromhex(a["head"])
            kd = int.from_bytes(hw[8:12], "little")
            if kd != 1:
                pop = any(n_ == "ParamsPop" for n_ in names)
                same = nx is not None and nx["aid"].get("head") == a["head"] and nx["aid"]["hp"] == a["hp"]
                sc["head_kind%d:pop%d:next_same%d" % (kd, int(pop), int(same))] += 1
            else:
                sc["head_kind1"] += 1
        else:
            sc["nohead"] += 1
    out("M67/M68/M69/R45", "row 20: step 4's draw after the walk (0x005F283F's v14 clear) at the unit's next AID, and "
        "head records of another kind", seen=hist(sc, 20), bad=scbad)

    # ---------------------------------------------------------------- M71, M110: row 21 Mummy
    mu = collections.Counter()
    mubad = 0
    for x in alld:
        a = x["aid"]
        if a["ai"] != 21 or a["st"] != 0 or x["aix"] is None:
            continue
        bs = aibs(x)
        names = [FN.get(b["fn"], "%X" % b["fn"]) for b in bs]
        if not names or names[0] != "St3or19":
            mu["first:%s" % (names[0] if names else "-")] += 1
            continue
        r0 = air_of(x, bs[0])
        if r0 is None:
            continue
        dist, melee, a1 = ai.s32(a["ctx"][5]), a["ctx"][6], aipk(a, 1)
        if r0["eax"] and not melee:
            mu["st3or19"] += 1
            continue
        if dist == a1 or dist == a1 + 1:
            mu["edge:dist%s:%s" % ("=aip1" if dist == a1 else "=aip1+1", names[1] if len(names) > 1 else "-")] += 1
            if dist == a1 and names[1:2] == ["Ring"]:
                mubad += 1
            if dist == a1 + 1 and melee == 0 and names[1:2] == ["Walk"]:
                mubad += 1
        if dist <= a1 and melee:
            s = ai.step(sv(a["s"]))
            mu["melee:aip3=%d:draw%s" % (aipk(a, 3), "pass" if s[0] % 100 < aipk(a, 3) else "fail")] += 1
            if not s[0] % 100 < aipk(a, 3):
                mubad += 1
    out("M71/M110", "row 21: the dist <= aip(1) range test at its edges, and the aip3 draw in melee range",
        seen=hist(mu, 20), bad=mubad)

    # ---------------------------------------------------------------- M107: each decision's last call
    last = collections.Counter()
    lastq = collections.Counter()
    for x in d6:
        bs = aibs(x)
        if x["aix"] is None:
            continue
        if not bs:
            last["none"] += 1
            continue
        nm = FN.get(bs[-1]["fn"], "%08X" % bs[-1]["fn"])
        cat = "B" if nm in B_HELPERS else ("C" if nm in C_HELPERS else "other")
        last[cat] += 1
        if cat == "other":
            lastq[nm] += 1
    out("M107", "rev 6 decisions by their last logged call: a § B command or move helper, a § C helper, none, other",
        decisions=sum(last.values()), seen=hist(last), other_fns=hist(lastq, 20))

    # ---------------------------------------------------------------- R7: decision pairs on one seed by commanded mode
    pairs = collections.Counter()
    for lg in firstlogs + logs:
        for x in lg.dec.values():
            a = x["aid"]
            nx = lg.next_aid.get(a["n"])
            if nx is None or x["aix"] is None:
                continue
            ne = lg.next_event.get(a["n"])
            if ne is None or ne[2] != "AID":
                continue                          # an AIN between: its own draws
            m1 = [d for t, d in x["ev"] if t == "MSM1"]
            m0 = [d for t, d in x["ev"] if t == "MSM0"]
            if not m1 or m1[-1]["eax"] == 0:
                mode = "none"
            else:
                mode = m0[-1]["cmd"][0]
            k = steps(sv(x["aix"]["s"]), sv(nx["aid"]["s0"]), 4096)
            sstb = [s for t, s in lg.sst if t == "SST0" and s["u"] == a["u"] and x["aix"]["n"] < s["n"] < nx["aid"]["n"]]
            pairs[(mode, "0" if k == 0 else ("sst" if sstb else ("n%s" % ("off" if k is None else "moved"))))] += 1
    for mode in sorted({k[0] for k in pairs}, key=str):
        out("R7", "decision pairs of one unit with no AIN between, by the decision's started mode: exit seed = next "
            "entry (0), moved with an SST0 of the unit between (sst), moved without (nmoved)", mode=mode,
            pairs=hist(collections.Counter({k[1]: v for k, v in pairs.items() if k[0] == mode})))

    # ---------------------------------------------------------------- R13: the AiCtx words
    cx = collections.Counter()
    for x in alld:
        a = x["aid"]
        c = a["ctx"]
        cx["ctl"] += c[0] == a["ctlp"]
        cx["ms"] += c[7] == a["ms"]
        cx["z04_0c_10"] += c[1] == 0 and c[3] == 0 and c[4] == 0
        cx["n"] += 1
    out("R13", "AID ctx words: +0x00 the AiCtl, +0x1C the MonStats record, +0x04, +0x0C, +0x10 zero", **{k: v for k, v in cx.items()},
        bad=3 * cx["n"] - cx["ctl"] - cx["ms"] - cx["z04_0c_10"])
    ain = sum(1 for lg in logs for tl in lg.timeline.values() for e in tl if e[2] == "AIN")
    out("R13", "AIN and AID lines", aid=len(alld), ain=ain)

    # ---------------------------------------------------------------- R27, R51: the row kind and the target
    import ai_s1fo as A
    R, _ = A.ai_rows()
    ST, _ = A.st_rows()
    rk = collections.Counter()
    rkbad = 0
    for x in alld:
        a = x["aid"]
        st = a["st"]
        kd = (R[a["ai"]][0] if st == 0 else ST[st][0]) if a["ai"] < len(R) else -1
        has = a["ctx"][2] != 0
        rk[(kd, st, has)] += 1
        if kd == 1 and not has:
            rkbad += 1
    out("R27/R51", "decisions by (row kind of the stored state, state, a target in ctx+0x08)",
        seen=hist(collections.Counter({"k%d/s%d/%s" % (k[0], k[1], "t" if k[2] else "no_t"): v for k, v in rk.items()}), 20),
        bad=rkbad)
    s12 = collections.Counter()
    for x in alld:
        a = x["aid"]
        if a["st"] != 12:
            continue
        c = a["ctx"]
        s12["classkind%d:ctx(t,dist,melee)=%s" % (R[a["ai"]][0], "zero" if c[2] == 0 and c[5] == 0 and c[6] == 0 else "set")] += 1
    out("R51", "state-12 decisions: the class's row kind and the search words", seen=hist(s12),
        bad=sum(v for k, v in s12.items() if k.endswith("set")))

    # ---------------------------------------------------------------- R32: the first logged decision's AiCtl words
    first_ctl = collections.Counter()
    first_ctl2 = collections.Counter()
    seen = set()
    for lg in logs:
        for x in lg.dec.values():
            a = x["aid"]
            key = (lg.name, a["u"], a["id"])
            if key in seen:
                continue
            seen.add(key)
            w = (ctlw(a, 0x0C), ctlw(a, 0x10), ctlw(a, 0x2C), ctlw(a, 0x30))
            first_ctl["eq" if w == (-1, 1, -1, 1) else "%d,%d,%d,%d:r%d" % (w + (a["ai"],))] += 1
            first_ctl2["0C,10=%s" % ("-1,1" if w[:2] == (-1, 1) else "other")] += 1
            if w[2:] != (-1, 1):
                first_ctl2["2C,30_other_row%d" % a["ai"]] += 1
    out("R32", "each unit's first logged AID: AiCtl +0x0C, +0x10, +0x2C, +0x30 against (-1, 1, -1, 1)", units=len(seen),
        seen=hist(first_ctl, 12), split=hist(first_ctl2, 20), bad=0)

    # ---------------------------------------------------------------- R36: the states per case log
    stl = collections.Counter()
    for lg in logs:
        for x in lg.dec.values():
            st = x["aid"]["st"]
            if st:
                case = lg.name.split(":")[-1].replace(".log", "") if ":" in lg.name else lg.name[:30]
                stl["%s:s%d" % (case, st)] += 1
    out("R36", "non-zero AiCtl.state decisions by case log", seen=hist(stl, 20))


def sec_gaps(d):
    """README 9: the open monster gaps of run:2026-11-04-h1 in the review's gap walks, each first disagreement an AD0
    whose attacker is the gap's unit."""
    res = collections.Counter()
    bad = 0
    stepsc = collections.Counter()
    for f in sorted(os.listdir(d)):
        if not f.startswith("gaps-"):
            continue
        for ln in open(os.path.join(d, f)):
            m = re.match(r"(\S+) n=(\d+) monster unit (\d+) \[.*?\]: (\d+) steps; (.*?); first disagreement (\S+) n=(\d+)", ln)
            if not m:
                continue
            log, n, u, st, how, tag, dn = m.groups()
            if "stopped" not in how:
                res["closed"] += 1
                continue
            path = os.path.join(d, "..", log)
            line = None
            with open(path, errors="replace") as fh:
                for l2 in fh:
                    if l2.startswith(tag + " ") and ('"n":%s}' % dn) in l2:
                        line = json.loads(l2[len(tag) + 1:])
                        break
            att = line is not None and line.get("a") == int(u)
            res["%s:attacker_is_unit=%d" % (tag, att)] += 1
            stepsc[int(st)] += 1
            bad += not (tag == "AD0" and att and 1 <= int(st) <= 4)
    out("R9", "open monster gaps of the h1 logs: first disagreement and its attacker", seen=hist(res),
        steps=hist(stepsc), bad=bad)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    sec = argv[1]
    print("== %s" % sec)
    if sec == "logs":
        lst = argv[argv.index("--logs") + 1]
        first = load(argv[argv.index("--first") + 1]) if "--first" in argv else []
        run_logs(load(lst), first)
    elif sec == "tables":
        sec_tables()
    elif sec == "gaps":
        sec_gaps(argv[2])
    elif sec == "totals":
        import quests_s3c as Q
        Q.sec_totals()
    bad = sum(BAD.values())
    print("S1m total bad=%d %s" % (bad, " ".join("%s=%d" % kv for kv in sorted(BAD.items()) if kv[1])))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

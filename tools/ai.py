#!/usr/bin/env python3
"""Plan 0052 Phase 2: the monster AI decision model and checker for the logs of tools/gdb/ai.gdb.

    python3 -I tools/ai.py check LOG [LOG ...] [--controls] [--out FILE] [--json FILE]   # compare every decision with its model;
                                                                             # --controls: the outcome mix is always printed, this adds
                                                                             # the negative controls (wrong maps that must fail)
    python3 -I tools/ai.py counts LOG [LOG ...]                              # decisions per AI row, nothing compared
    python3 -I tools/ai.py selftest                                          # the model against its own inputs

One AI decision is one call of the think function of sub_005B1740_MonAiEvent (docs/findings/ai/0001 § 1), logged
as an AID line with its AIB boundary calls, MSM/PP command and plan lines and an AIX exit (tools/gdb/ai.py). The
models are the first-boundary maps of the Ghidra-emulated think functions in tools/ai_cat_emu*.py (ADR-0015, ADR-0021;
`FNS`: think address to family, `MODELS`, `OBSERVE`: the functions each emulation treats as boundaries); this tool
imports them, builds each model's input from the logged AID line, runs it, and compares what the model says the
think function reaches first (the boundary function, its call site, the registers and stack words, the unit seed, the
AI control words, and the block a pointer argument addresses) with the first logged boundary call of the module's
`OBSERVE` set. Five tier AIs have no emulation (Fallen 6, FallenShaman 13, Vampire 28, BatDemon 29, CorruptArcher 35,
the first callee of each is a function whose read set is not declarable, ai/0002 § 3, 0003, 0004): `HAND` holds their
first-boundary maps read from the findings and objdump of the pinned game.exe (`[I]`), checked the same way.

Every decision, modelled or not, also takes the draw accounting: the unit seed at the event entry, at the think call, at
each logged boundary, command and plan line and at the exit must follow each other by whole LCG steps (at most 64),
and the chaining counts (ADR-0014): a decision whose exit seed is the next decision's entry seed for the same unit, and
a skill start (SST0) whose entry seed is a decision's exit seed.

Not covered: every call at or after the first boundary (the boundary's result decides the rest, ADR-0021), the
state-146 candidate-seed draw and the search's own draws, which fall between the entry seed and the think call.
Stdlib only.
"""
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

MUL = 0x6AC690C5
M32 = 0xFFFFFFFF
MODS = ["ai_cat_emu", "ai_cat_emu2", "ai_cat_emu3", "ai_cat_emu4", "ai_cat_emu5", "ai_cat_emu6", "ai_cat_emu8",
        "ai_cat_emu9"]
# the 18 tier AIs (plan 0052 P1.1 review ruling 1): MonStats AI row -> name
TIER = {2: "Skeleton", 6: "Fallen", 9: "Wraith", 13: "FallenShaman", 20: "Scarab", 21: "Mummy", 22: "GreaterMummy",
        28: "Vampire", 29: "BatDemon", 30: "Fetish", 34: "Andariel", 35: "CorruptArcher", 37: "SkeletonBow",
        61: "Hireable", 64: "SkeletonMage", 67: "NecroPet", 89: "Megademon", 125: "BloodLord"}
TAGS = ("AGM", "AIN", "AID", "AIB", "AIR", "MSM0", "MSM1", "PP0", "PP1", "SST0", "SST1", "AIX", "CAP")
# the controls after the seed in each module's Hit tuple (before the block, where it has one): which AiCtl words
CTRL = {"ai_cat_emu": ("c14",), "ai_cat_emu2": ("c14", "c18"), "ai_cat_emu3": ("c14", "c18", "c1c", "c4"),
        "ai_cat_emu4": ("c14", "c18", "c1c", "c4", None), "ai_cat_emu5": ("c14", "c18", "c1c"),
        "ai_cat_emu6": ("c14", "c18", "c1c"), "ai_cat_emu8": ("c14", "c18", "c1c", "c4"),
        "ai_cat_emu9": ("c14", "c18", "c1c", "c4")}
HAS_BLOCK = {"ai_cat_emu": False, "ai_cat_emu2": True, "ai_cat_emu3": True, "ai_cat_emu4": True, "ai_cat_emu5": False,
             "ai_cat_emu6": True, "ai_cat_emu8": True, "ai_cat_emu9": True}

# Call sites outside the logger's return-address window for revisions up to 2 (0x005B14E0..0x005B1650 and
# 0x005E0000..0x005FFFFF): the call of GameFindUnit inside MonsterOwner (0x0058F0D0) and two helpers' calls. A model
# whose first boundary is at one of them cannot be compared with such a log (counted as "unlogged", not a match).
UNLOGGED_SITES = (0x0058F0FF, 0x005DE864, 0x005DF97B)

# AI row (MonStats AI, +0x1E) of each think address: docs/tables/MonAI.md; the rows the models cover
THINK_ROW = {}


def u32(v):
    return v & M32


def s32(v):
    v &= M32
    return v - (1 << 32) if v & 0x80000000 else v


def s16(v):
    v &= 0xFFFF
    return v - (1 << 16) if v & 0x8000 else v


def step(s):
    t = s[0] * MUL + s[1]
    return (t & M32, (t >> 32) & M32)


def seedval(txt):
    a, b = txt.split(":")
    return (int(a, 16), int(b, 16))


def reach(a, b, limit=64):
    """The number of LCG steps from seed a to seed b (0..limit), or None."""
    s = a
    for n in range(limit + 1):
        if s == b:
            return n
        s = step(s)
    return None


_loaded = {}


def load_mods():
    if _loaded:
        return _loaded
    reg = {}
    for mn in MODS:
        m = importlib.import_module(mn)
        for fam, addr in m.FNS.items():
            reg.setdefault(addr, (mn, fam))
        _loaded[mn] = m
    _loaded["_reg"] = reg
    return _loaded


# ------------------------------------------------------------------------------------------------ the hand models
def hand_fallen(i):
    """Row 6 (0x005F02C0, ai/0002 § 2.5): a unit in mode 0 or 12 returns; else UNIT_CancelEvents(G, U, 2, 0) first."""
    if i["m"] in (0, 12):
        return None
    return (0x00540E60, 0x005F02FD, None, None, [2, 0], i["seed"], None)


def hand_shaman(i):
    """Row 13 (0x005F1440, ai/0002 § 2.11): a melee unit draws once against aip3 (signed s16) and attacks (mode 4 at the
    target); else MonTypeFlag(U, 8) is the first callee."""
    seed = i["seed"]
    if i["melee"]:
        seed = step(seed)
        if seed[0] % 100 < s16(i["aip"][2][i["diff"]]):
            return (0x005DDF90, 0x005F14B3, "G", "U", [4, "T"], seed, None)
    return (0x005A0180, 0x005F14E1, "U", 8, [], seed, None)


def hand_vampire(i):
    """Row 28 (0x005F4A70, ai/0003 § 2.12): a positive AiCtl+0x1C is decremented, then FindHostile(&hd, 0)."""
    return (0x005DDC30, 0x005F4AD5, "G", "U", ["B", 0], i["seed"], None)


def hand_batdemon(i):
    """Row 29's think (0x005F5040, ai/0003 § 2.13): UnitLifePct(U) first."""
    return (0x00621F20, 0x005F5070, None, None, ["U"], i["seed"], None)


def hand_archer(i):
    """Row 35 (0x005F5A20, ai/0004 § 2.2): FindHostile(&dist, 0) first (the block's first word is the event's distance)."""
    return (0x005DDC30, 0x005F5A56, "G", "U", ["B", 0], i["seed"], i["dist"])


HAND = {0x005F02C0: ("Fallen", hand_fallen), 0x005F1440: ("FallenShaman", hand_shaman),
        0x005F4A70: ("Vampire", hand_vampire), 0x005F5040: ("BatDemon", hand_batdemon),
        0x005F5A20: ("CorruptArcher", hand_archer)}
HAND_OBS = {0x005F02C0: (0x00540E60,), 0x005F1440: (0x005DDF90, 0x005A0180), 0x005F4A70: (0x005DDC30,),
            0x005F5040: (0x00621F20,), 0x005F5A20: (0x005DDC30,)}


# ----------------------------------------------------------------------------------------------------- the log
def parse(path):
    """The AI lines of a log: {"dec": [decision], "ain": [..], "sst": [..], "cap": [..], "lines": n}."""
    dec, byk, ain, sst, sstk, cap = [], {}, [], [], {}, []
    n_lines = 0
    rev = None
    bmax = 8
    with open(path, errors="replace") as fh:
        for ln in fh:
            n_lines += 1
            if ln.startswith("AI logger armed rev "):
                mr = re.match(r"AI logger armed rev (\d+)(?: bmax (\d+))?", ln)
                rev = int(mr.group(1))
                bmax = int(mr.group(2)) if mr.group(2) else (8 if rev <= 3 else 16)
                continue
            sp = ln.find(" ")
            tag = ln[:sp] if sp > 0 else ln.strip()
            if tag not in TAGS:
                continue
            try:
                d = json.loads(ln[sp + 1:])
            except ValueError:
                continue
            if tag == "AID":
                x = {"aid": d, "aib": [], "air": {}, "msm": [], "pp": [], "aix": None, "log": path}
                dec.append(x)
                byk[d["n"]] = x
            elif tag == "AIB" and d["k"] in byk:
                byk[d["k"]]["aib"].append(d)
            elif tag == "AIR" and d["k"] in byk:
                byk[d["k"]]["air"][d["b"]] = d
            elif tag in ("MSM0", "PP0") and d["k"] in byk:
                byk[d["k"]]["msm" if tag == "MSM0" else "pp"].append([d, None])
            elif tag in ("MSM1", "PP1") and d["k"] in byk:
                lst = byk[d["k"]]["msm" if tag == "MSM1" else "pp"]
                for pair in reversed(lst):
                    if pair[1] is None:
                        pair[1] = d
                        break
            elif tag == "AIX" and d["k"] in byk:
                byk[d["k"]]["aix"] = d
            elif tag == "AIN":
                ain.append(d)
            elif tag == "SST0":
                sst.append(d)
                sstk[d["n"]] = d
            elif tag == "SST1" and d["k"] in sstk:
                sstk[d["k"]]["exit"] = d
            elif tag == "CAP":
                cap.append(d)
    for d in dec:
        d["rev"] = rev
        d["bmax"] = bmax
    return {"dec": dec, "ain": ain, "sst": sst, "cap": cap, "lines": n_lines, "rev": rev}


# ----------------------------------------------------------------------------------------------------- inputs
def le16(hexs, count):
    b = bytes.fromhex(hexs)
    return [int.from_bytes(b[2 * k:2 * k + 2], "little") for k in range(count)]


def inputs(aid):
    """The model input dict (the union of the keys the emulation case writers use) from an AID line."""
    ctl = bytes.fromhex(aid["ctl"])
    w = lambda off: int.from_bytes(ctl[off:off + 4], "little")
    aipv = [s16(v) for v in le16(aid["aip"], 24)]
    skb = bytes.fromhex(aid["sk"])
    skill = [s16(int.from_bytes(skb[2 * k:2 * k + 2], "little")) for k in range(8)]
    skmode = list(skb[16:24])
    ctx = aid["ctx"]
    head = bytes.fromhex(aid["head"]) if aid.get("head") else None
    hw = (lambda off: int.from_bytes(head[off:off + 4], "little")) if head else (lambda off: 0)
    return {
        "seed": seedval(aid["s"]), "diff": aid["diff"], "aip": [[aipv[3 * k + d] for d in range(3)] for k in range(8)],
        "melee": ctx[6], "dist": s32(ctx[5]), "target": ctx[2], "m54": aid["md"], "m": aid["m"],
        "ctl14": s32(w(0x14)), "ctl18": s32(w(0x18)), "ctl1c": s32(w(0x1C)), "c4": aid["c4"], "rk": -1,
        "head": head is not None, "rec_kind": hw(8), "rec_0c": hw(0x0C), "rec_10": hw(0x10),
        "own28": w(0x28), "own2c": w(0x2C), "own30": w(0x30), "skill": skill, "skmode": skmode,
        "skill1": skill[0], "sk1mode": skmode[0], "cls": aid["c"], "mscount": aid["ms2"], "umode": aid["m"],
        "state": aid["st"], "frame": aid["fr"], "ux": aid["x"], "uy": aid["y"],
        "tx": aid["t"][4] if aid.get("t") and aid["t"][4] is not None else 0,
        "ty": aid["t"][5] if aid.get("t") and aid["t"][5] is not None else 0,
    }


def live_map(mod, aid):
    """The model image's symbolic addresses (GAME, UNIT, ...) as the live pointers of the logged decision."""
    m = {}
    for name, val in (("GAME", aid["g"]), ("UNIT", aid["u"]), ("TARGET", aid["ctx"][2]), ("CTL", aid["ctlp"]),
                      ("MDATA", aid["mdp"]), ("MREC", aid["ms"]), ("CTX", aid["cx"]), ("REC", aid["hp"])):
        k = getattr(mod, name, None)
        if k is not None:
            m[k] = val
    return m


def lv(x, lm):
    """A model value translated to the live image; None for a value that has no live counterpart (a stack address)."""
    if x is None:
        return None
    x = u32(x)
    if x in lm:
        return lm[x]
    if x >= 0x7FE00000 or 0x12000000 <= x < 0x13000000:
        return None
    return x


def first_aib(dec, obs):
    for b in dec["aib"]:
        if b["fn"] in obs:
            return b
    return None


def compare(res, b, mod, aid):
    """The differences between a model's boundary tuple and a logged AIB line (an empty list: match)."""
    lm = live_map(mod, aid)
    mn = mod.__name__
    fn, site, ecx, edx, args, seed = res[:6]
    diff = []
    if fn != b["fn"]:
        diff.append("fn %08x != %08x" % (fn, b["fn"]))
    if site != b["ra"]:
        diff.append("site %08x != %08x" % (site, b["ra"]))
    for nm, exp, got in (("ecx", ecx, b["ecx"]), ("edx", edx, b["edx"])):
        e = lv(exp, lm)
        if exp is not None and e is not None and e != got:
            diff.append("%s %08x != %08x" % (nm, e, got))
    for k, a in enumerate(args):
        e = lv(a, lm)
        if e is not None and e != b["a"][k]:
            diff.append("arg%d %08x != %08x" % (k, e, b["a"][k]))
    if "%08x:%08x" % tuple(seed) != b["s"]:
        diff.append("seed %08x:%08x != %s" % (seed[0], seed[1], b["s"]))
    ctrl = CTRL.get(mn, ())
    live = {"c14": b["c"][0], "c18": b["c"][1], "c1c": b["c"][2], "c4": b["c4"]}
    for k, name in enumerate(ctrl):
        if name and u32(res[6 + k]) != live[name]:
            diff.append("%s %08x != %08x" % (name, u32(res[6 + k]), live[name]))
    if HAS_BLOCK.get(mn) and res[-1]:
        addr, words = res[-1]
        idx = [k for k, a in enumerate(args) if u32(a) == u32(addr)]
        got = b["b"].get(str(idx[0])) if idx else None
        if got is None:
            diff.append("block missing")
        else:
            for k, wv in enumerate(words):
                if u32(wv) != got[k]:
                    diff.append("block[%d] %08x != %08x" % (k, u32(wv), got[k]))
    return diff


def check_hand(dec, i, entry):
    name, fn = entry
    aid = dec["aid"]
    res = fn(i)
    obs = HAND_OBS[aid["th"]]
    b = first_aib(dec, obs)
    if res is None:
        return [] if b is None else ["boundary %08x logged, none predicted" % b["fn"]]
    if b is None:
        return ["no boundary logged, %08x predicted" % res[0]]
    diff = []
    if res[0] != b["fn"]:
        diff.append("fn %08x != %08x" % (res[0], b["fn"]))
    if res[1] != b["ra"]:
        diff.append("site %08x != %08x" % (res[1], b["ra"]))
    sym = {"G": aid["g"], "U": aid["u"], "T": aid["ctx"][2]}
    for nm, exp, got in (("ecx", res[2], b["ecx"]), ("edx", res[3], b["edx"])):
        if exp is not None:
            e = sym.get(exp, exp) if isinstance(exp, str) else exp
            if e != got:
                diff.append("%s %x != %x" % (nm, e, got))
    for k, a in enumerate(res[4]):
        if a == "B":
            continue
        e = sym.get(a, a) if isinstance(a, str) else a
        if u32(e) != b["a"][k]:
            diff.append("arg%d %x != %x" % (k, u32(e), b["a"][k]))
    if res[5] and "%08x:%08x" % tuple(res[5]) != b["s"]:
        diff.append("seed %08x:%08x != %s" % (res[5][0], res[5][1], b["s"]))
    if res[6] is not None:
        got = b["b"].get("0")
        if got is None or got[0] != u32(res[6]):
            diff.append("block0 %x != %s" % (u32(res[6]), got and "%x" % got[0]))
    return diff


def hand_fallen_inverted(i):
    """The deliberately wrong Fallen map of the negative control: the mode test inverted (CancelEvents in modes 0 and
    12, a return in every other mode)."""
    if i["m"] not in (0, 12):
        return None
    return (0x00540E60, 0x005F02FD, None, None, [2, 0], i["seed"], None)


def check_decision(dec, mut=None):
    """-> (kind, name, diffs, outcome): kind in model, hand, none, unlogged; outcome = the (function, call site) the map
    predicts first, ("return", None) for a hand map that returns, None for no map.

    `mut` is the negative control (check --controls): "site" shifts the predicted call site by one byte (every compared
    decision must fail), "melee" flips the melee flag of the model input (fails where the flag chooses the outcome),
    "fallen" runs the inverted Fallen map (row 6 only)."""
    mods = load_mods()
    aid = dec["aid"]
    th = aid["th"]
    i = inputs(aid)
    ent = mods["_reg"].get(th)
    if ent:
        mn, fam = ent
        mod = mods[mn]
        i = dict(i, fam=fam)
        for k in ("TARGET",):
            if getattr(mod, k, None) is not None and aid["ctx"][2]:
                i["target"] = getattr(mod, k)
        if mut == "melee":
            i["melee"] = 0 if i["melee"] else 1
        try:
            res = mod.run_model(i)
        except KeyError as e:        # an input the logger does not carry (the trap rows' level and region words)
            return "none", mn + ":" + fam, [], None
        if mut == "site":
            res = (res[0], res[1] + 1) + tuple(res[2:])
        if res[1] in UNLOGGED_SITES and (dec.get("rev") or 0) <= 2:
            return "unlogged", mn + ":" + fam, [], (res[0], res[1])
        b = first_aib(dec, set(mod.OBSERVE))
        if b is None:
            return "model", mn + ":" + fam, ["no boundary logged, %08x predicted" % res[0]], (res[0], res[1])
        return "model", mn + ":" + fam, compare(res, b, mod, aid), (res[0], res[1])
    if th in HAND:
        name, fn = HAND[th]
        if mut == "fallen" and th != 0x005F02C0:
            return "hand", name, [], None
        if mut == "fallen":
            fn = hand_fallen_inverted
        elif mut == "melee":
            i = dict(i, melee=0 if i["melee"] else 1)
        if mut == "site":
            inner = fn
            fn = lambda x, inner=inner: (lambda r: None if r is None else (r[0], r[1] + 1) + tuple(r[2:]))(inner(x))
        res = fn(i)
        return "hand", name, check_hand(dec, i, (name, fn)), ((res[0], res[1]) if res else ("return", None))
    return "none", "%08x" % (th or 0), [], None


def accounting(dec):
    """The unit-seed steps between the logged points of one decision: ([steps], [violations])."""
    aid = dec["aid"]
    pts = [(0, "s0", aid["s0"]), (aid["n"], "s", aid["s"])]
    for b in dec["aib"]:
        pts.append((b["n"], "AIB", b["s"]))
    for m0, m1 in dec["msm"]:
        if m0["cmd"][1] == aid["u"] and m0["s"]:
            pts.append((m0["n"], "MSM0", m0["s"]))
            if m1 and m1["s"]:
                pts.append((m1["n"], "MSM1", m1["s"]))
    for p0, p1 in dec["pp"]:
        if p0["u"] == aid["u"] and p0["s"]:
            pts.append((p0["n"], "PP0", p0["s"]))
            if p1 and p1["s"]:
                pts.append((p1["n"], "PP1", p1["s"]))
    for t in dec.get("sst", []):
        pts.append((t["n"], "SST0", t["s"]))
        if t.get("exit"):
            pts.append((t["exit"]["n"], "SST1", t["exit"]["s"]))
    if dec["aix"]:
        pts.append((dec["aix"]["n"], "AIX", dec["aix"]["s"]))
    pts.sort(key=lambda p: (p[0], 0))
    steps, bad = [], []
    for (n0, t0, a), (n1, t1, b) in zip(pts, pts[1:]):
        k = reach(seedval(a), seedval(b))
        if k is None:
            bad.append("%s(%d) -> %s(%d): %s -> %s unreachable" % (t0, n0, t1, n1, a, b))
        else:
            steps.append(k)
    return steps, bad


def chains(decs, ssts):
    """ADR-0014 chaining counts: (decision pairs on one seed, drawing pairs, per row; decision -> skill start)."""
    by_unit = {}
    for d in decs:
        by_unit.setdefault((d["log"], d["aid"]["u"], d["aid"]["id"]), []).append(d)
    pairs = {}
    for k, lst in by_unit.items():
        lst.sort(key=lambda d: d["aid"]["n"])
        for a, b in zip(lst, lst[1:]):
            if a["aix"] and a["aix"]["s"] == b["aid"]["s0"]:
                row = a["aid"]["ai"]
                drew = a["aid"]["s"] != a["aix"]["s"]
                r = pairs.setdefault(row, [0, 0])
                r[0] += 1
                r[1] += int(drew)
    # decision -> SrvStart (ADR-0014): SKILLS_SrvStart of the decision's own unit runs inside the event (between the AID
    # and the AIX line); the chain is "the unit seed at the skill start is the decision's last logged seed advanced n
    # steps, and the exit of the skill start is the event's exit seed"
    skill = {}
    for d in decs:
        for t in d.get("sst", []):
            row = d["aid"]["ai"]
            r = skill.setdefault(row, [0, 0, 0, {}])
            r[2] += 1                                  # a skill start inside the decision
            prev = [d["aid"]["s"]] + [b["s"] for b in d["aib"] if b["n"] < t["n"]] + \
                [m0["s"] for m0, m1 in d["msm"] if m0["n"] < t["n"] and m0["s"] and m0["cmd"][1] == d["aid"]["u"]]
            last = max([(d["aid"]["n"], d["aid"]["s"])] + [(b["n"], b["s"]) for b in d["aib"] if b["n"] < t["n"]] +
                       [(m0["n"], m0["s"]) for m0, m1 in d["msm"] if m0["n"] < t["n"] and m0["s"] and
                        m0["cmd"][1] == d["aid"]["u"]])[1]
            n = reach(seedval(last), seedval(t["s"]), 12)
            ex_ok = bool(t.get("exit")) and d["aix"] is not None and t["exit"]["s"] == d["aix"]["s"]
            if n is not None:
                r[1] += 1
                r[3][n] = r[3].get(n, 0) + 1
            if ex_ok:
                r[0] += 1
    return pairs, skill


def run_check(paths, out=None, controls=False):
    decs, ssts, ains, caps, rows = [], [], [], [], {}
    for p in paths:
        r = parse(p)
        for d in r["dec"]:
            decs.append(d)
        for s in r["sst"]:
            s["log"] = p
            ssts.append(s)
        ains += r["ain"]
        caps += r["cap"]
    sst_by = {}
    for t in ssts:
        sst_by.setdefault((t["log"], t["u"]), []).append(t)
    for d in decs:
        a = d["aid"]
        x = d["aix"]["n"] if d["aix"] else a["n"]
        d["sst"] = [t for t in sst_by.get((d["log"], a["u"]), []) if a["n"] < t["n"] < x]
    per = {}
    mism = []
    acc_bad = []
    hist = {}
    mix = {}
    for d in decs:
        aid = d["aid"]
        row = aid["ai"]
        kind, name, diffs, outc = check_decision(d)
        if outc is not None:
            mix.setdefault((row, aid["th"]), {}).setdefault(outc, 0)
            mix[(row, aid["th"])][outc] += 1
        e = per.setdefault(row, {"n": 0, "model": 0, "hand": 0, "none": 0, "unlogged": 0, "bad": 0, "name": name, "th": aid["th"],
                                 "logs": set()})
        e["n"] += 1
        e[kind] += 1
        e["logs"].add(os.path.basename(d["log"]))
        if kind != "none":
            e["name"] = name
        if diffs:
            e["bad"] += 1
            mism.append((d["log"], aid["n"], row, name, diffs))
        steps, bad = accounting(d)
        for k in steps:
            hist[k] = hist.get(k, 0) + 1
        if bad:
            acc_bad.append((d["log"], aid["n"], row, bad))
    pairs, skill = chains(decs, ssts)
    pp_n = pp_bad = 0
    pp_ex = []
    for d in decs:
        for p0, p1 in d["pp"]:
            if p1 is not None and p0["s"] and p1["s"]:
                pp_n += 1
                if p0["s"] != p1["s"]:
                    pp_bad += 1
                    pp_ex.append((d["log"], d["aid"]["n"], d["aid"]["ai"], p0["ty"], p0["s"], p1["s"]))
    msm_n = sum(1 for d in decs for m0, m1 in d["msm"] if m1 is not None)
    ptypes, cmodes = {}, {}
    for d in decs:
        for p0, p1 in d["pp"]:
            ptypes[p0["ty"]] = ptypes.get(p0["ty"], 0) + 1
        for m0, m1 in d["msm"]:
            key = "%d/%d" % (m0["cmd"][0], m0["cmd"][5])
            cmodes[key] = cmodes.get(key, 0) + 1
    perlog = {}
    for d in decs:
        e = perlog.setdefault(os.path.basename(d["log"]), {})
        e[d["aid"]["ai"]] = e.get(d["aid"]["ai"], 0) + 1
    lines = []
    lines.append("CHECK logs=%d decisions=%d ain=%d sst=%d caps=%d" % (len(paths), len(decs), len(ains), len(ssts),
                                                                      len(caps)))
    tot = {"model": 0, "hand": 0, "none": 0, "unlogged": 0}
    for row in sorted(per, key=lambda r: (r is None, r)):
        e = per[row]
        for k in tot:
            tot[k] += e[k]
        lines.append("ROW %s %-28s th=%08x decisions=%d model=%d hand=%d unmodelled=%d unlogged=%d mismatches=%d logs=%d"
                     % (row, e["name"], e["th"] or 0, e["n"], e["model"], e["hand"], e["none"], e["unlogged"], e["bad"],
                        len(e["logs"])))
    lines.append("TOTAL decisions=%d model=%d hand=%d unmodelled=%d unlogged=%d mismatches=%d" % (
        len(decs), tot["model"], tot["hand"], tot["none"], tot["unlogged"], len(mism)))
    lines.append("PLAN pp_pairs=%d seed_changed=%d msm_pairs=%d" % (pp_n, pp_bad, msm_n))
    lines.append("PLANTYPES %s" % json.dumps({str(k): ptypes[k] for k in sorted(ptypes)}))
    lines.append("CMDS mode/pathtype=%s" % json.dumps({k: cmodes[k] for k in sorted(cmodes, key=lambda x: -cmodes[x])}))
    for lg in sorted(perlog):
        lines.append("LOG %s decisions=%d rows=%s" % (lg, sum(perlog[lg].values()), json.dumps(
            {str(k): perlog[lg][k] for k in sorted(perlog[lg], key=lambda x: -perlog[lg][x])[:6]})))
    for t in TIER:
        e = per.get(t)
        lines.append("TIER %d %-14s decisions=%d checked=%d floor50=%s" % (
            t, TIER[t], e["n"] if e else 0, (e["model"] + e["hand"]) if e else 0,
            "met" if e and e["n"] >= 50 else "SHORT"))
    one = []
    main_th = {}
    for (row, th), v in mix.items():
        if sum(v.values()) > main_th.get(row, (0, None))[0]:
            main_th[row] = (sum(v.values()), th)
    for key in sorted(mix, key=lambda k: (k[0] is None, k[0] or 0, k[1] or 0)):
        row, th = key
        outs = sorted(mix[key].items(), key=lambda kv: (-kv[1], str(kv[0])))
        nm = (per.get(row) or {}).get("name", "?")
        flag = "ONE-OUTCOME" if len(outs) == 1 else "outcomes=%d" % len(outs)
        if len(outs) == 1 and row in TIER and main_th[row][1] == th:
            one.append(row)
        lines.append("MIX %s th=%08x %-20s predicted=%d %s: %s" % (row, th or 0, nm, sum(mix[key].values()), flag, "; ".join(
            "%s@%s=%d" % (("%08x" % o[0]) if isinstance(o[0], int) else o[0], ("%08x" % o[1]) if o[1] else "-", n)
            for o, n in outs)))
    lines.append("MIXSUM tier_ais_with_one_outcome=%d rows=%s tier_ais_with_more=%d (per tier AI's main think; an alt or "
                 "state think of the same row is its own MIX line)" % (
        len(one), ",".join(str(r) for r in sorted(one)), sum(1 for r in TIER if r in main_th and r not in one)))
    ctl_fail = None
    if controls:
        ctl_fail = []
        for mut, what in (("site", "predicted call site shifted by one byte: every compared decision must fail"),
                          ("fallen", "row 6 (Fallen) mode test inverted: must fail where mode is 0 or 12 or not"),
                          ("melee", "melee flag of the model input flipped: fails where the flag decides the outcome")):
            tot = {}
            for d in decs:
                kind, name, diffs, outc = check_decision(d, mut)
                if kind in ("model", "hand") and not (mut == "fallen" and d["aid"]["ai"] != 6):
                    t = tot.setdefault(d["aid"]["ai"], [name, 0, 0])
                    t[1] += 1
                    t[2] += 1 if diffs else 0
            n = sum(v[1] for v in tot.values())
            f = sum(v[2] for v in tot.values())
            rows_unsep = [r for r in sorted(tot) if tot[r][2] == 0]
            lines.append("CONTROL %s compared=%d failed=%d rows=%d rows_not_separated=%s : %s" % (
                mut, n, f, len(tot), ",".join(str(r) for r in rows_unsep) or "-", what))
            for r in sorted(tot):
                if r in TIER or mut == "fallen":
                    lines.append("CONTROL-ROW %s %s %-14s compared=%d failed=%d" % (mut, r, tot[r][0].split(":")[-1],
                                                                                 tot[r][1], tot[r][2]))
            if mut == "site":
                ok = n > 0 and f == n
            elif mut == "fallen":
                ok = n > 0 and f > 0
            else:
                ok = True                       # informative: the rows it does not separate are the weak ones
            ctl_fail.append((mut, ok))
        lines.append("CONTROLS " + " ".join("%s=%s" % (m, "FAILS-AS-REQUIRED" if ok else "PASSED-WRONGLY")
                                            for m, ok in ctl_fail))
    lines.append("ACCOUNT steps_histogram=%s violations=%d" % (
        json.dumps({str(k): hist[k] for k in sorted(hist)}), len(acc_bad)))
    ct = sum(v[0] for v in pairs.values())
    cd = sum(v[1] for v in pairs.values())
    lines.append("CHAIN decision_pairs=%d drawing=%d rows=%s" % (ct, cd, json.dumps({str(k): v for k, v in
                                                                                    sorted(pairs.items())})))
    lines.append("CHAIN decision_to_skillstart inside=%d entry_within_12_steps=%d exit_seed_is_event_exit=%d" % (
        sum(v[2] for v in skill.values()), sum(v[1] for v in skill.values()), sum(v[0] for v in skill.values())))
    for row in sorted(skill):
        v = skill[row]
        lines.append("SKCHAIN %s %-14s inside=%d entry_within12=%d exit_is_event_exit=%d steps=%s" % (
            row, (per.get(row) or {}).get("name", "?"), v[2], v[1], v[0],
            json.dumps({str(k): v[3][k] for k in sorted(v[3])})))
    for row in sorted(pairs):
        v = pairs[row]
        lines.append("DCHAIN %s %-14s pairs=%d drawing=%d floor20=%s" % (
            row, (per.get(row) or {}).get("name", "?"), v[0], v[1], "met" if v[1] >= 20 else
            ("n/a (no draw)" if v[1] == 0 else "SHORT")))
    for m in mism[:60]:
        lines.append("MISMATCH %s n=%d row=%s %s: %s" % (os.path.basename(m[0]), m[1], m[2], m[3], "; ".join(m[4])))
    for m in pp_ex[:20]:
        lines.append("PP-SEED-CHANGED %s n=%d row=%s type=%s %s -> %s" % (os.path.basename(m[0]), m[1], m[2], m[3], m[4], m[5]))
    for m in acc_bad[:30]:
        lines.append("ACCOUNT-BAD %s n=%d row=%s %s" % (os.path.basename(m[0]), m[1], m[2], "; ".join(m[3])))
    text = "\n".join(lines) + "\n"
    if out:
        with open(out, "w") as fh:
            fh.write(text)
    return text, {"decisions": len(decs), "mismatches": len(mism), "acc": len(acc_bad), "per": per, "pairs": pairs,
                  "skill": skill, "pp_bad": pp_bad, "mix": mix, "controls": ctl_fail}


# ---------------------------------------------------------------------------------------------------- selftest
def synth_log(path, rows, rev=3):
    """A fake log built from the emulation case writers' inputs: for every tier family, the model's own first boundary
    as the logged AIB line. Used by selftest and tools/test_ai.py (no game)."""
    import random
    mods = load_mods()
    out = ["AI logger armed rev %d" % rev]
    n = 0
    for mn, fam in rows:
        mod = mods[mn]
        gen = mod.gen_family(fam, random.Random("ai-selftest-" + fam))
        meta = gen[1]
        for inp in meta[:60]:
            inp = dict(inp, target=mod.TARGET) if inp.get("target") else inp
            res = mod.run_model(inp)
            fn, site, ecx, edx, args, seed = res[:6]
            lm = {mod.GAME: 0x1000, mod.UNIT: 0x2000, mod.TARGET: 0x3000}
            for nm, val in (("CTL", 0x4000), ("MDATA", 0x5000), ("MREC", 0x6000), ("CTX", 0x7000), ("REC", 0x8000)):
                if getattr(mod, nm, None) is not None:
                    lm[getattr(mod, nm)] = val
            aipf = b"".join((v & 0xFFFF).to_bytes(2, "little") for col in inp["aip"] for v in col) \
                if "aip" in inp else bytes(48)
            skl = inp.get("skill", [inp.get("skill1", -1), -1, -1, -1, -1, -1, -1, -1])
            skm = inp.get("skmode", [inp.get("sk1mode", 0)] + [0] * 7)
            skl = (list(skl) + [-1] * 8)[:8]
            skm = (list(skm) + [0] * 8)[:8]
            skb = b"".join((v & 0xFFFF).to_bytes(2, "little") for v in skl) + bytes(skm)
            ctl = bytearray(0x40)
            ctl[0x14:0x18] = u32(inp["ctl14"]).to_bytes(4, "little")
            ctl[0x18:0x1C] = u32(inp.get("ctl18", 0)).to_bytes(4, "little")
            ctl[0x1C:0x20] = u32(inp.get("ctl1c", 0)).to_bytes(4, "little")
            for nm, off in (("own28", 0x28), ("own2c", 0x2C), ("own30", 0x30)):
                ctl[off:off + 4] = u32(inp.get(nm, 0)).to_bytes(4, "little")
            head = None
            if inp.get("head"):
                hd = bytearray(0x1C)
                hd[8:12] = u32(inp.get("rec_kind", 0)).to_bytes(4, "little")
                hd[12:16] = u32(inp.get("rec_0c", 0)).to_bytes(4, "little")
                hd[16:20] = u32(inp.get("rec_10", 0)).to_bytes(4, "little")
                head = bytes(hd).hex()
            tgt = 0x3000 if inp.get("target", 1) else 0
            n += 1
            aid = {"u": 0x2000, "id": n, "c": inp.get("cls", 7), "ai": 99, "st": inp.get("state", 0),
                   "th": mod.FNS[fam], "cx": 0x7000, "g": 0x1000, "mdp": 0x5000, "ctlp": 0x4000, "hp": 0x8000,
                   "md": inp.get("m54", 0) & M32, "m": inp.get("umode", 1), "c4": u32(inp.get("c4", 0)),
                   "x": 1, "y": 1, "s0": "%08x:%08x" % tuple(inp["seed"]), "s": "%08x:%08x" % tuple(inp["seed"]),
                   "fr": 100, "diff": inp.get("diff", 0), "ms": 0x6000, "ms2": inp.get("mscount", 0x2E0),
                   "ctx": [0x4000, 0, tgt, 0, 0, u32(inp.get("dist", 0)), inp.get("melee", 0), 0x6000, 0],
                   "ctl": bytes(ctl).hex(), "head": head, "aip": aipf.hex(), "sk": skb.hex(), "ad": [15, 0],
                   "t": None, "pl": [0, 0], "n": 10 * n}
            b = {}
            blk = res[-1] if HAS_BLOCK.get(mn) else None
            a = [0] * 6
            for k, v in enumerate(args):
                x = lv(v, lm)
                a[k] = x if x is not None else 0x0012F000
            if blk:
                idx = [k for k, v in enumerate(args) if u32(v) == u32(blk[0])]
                if idx:
                    b[str(idx[0])] = [u32(w) for w in blk[1]] + [0] * (8 - len(blk[1]))
            cl = CTRL.get(mn, ())
            ctrl = {name: u32(res[6 + k]) for k, name in enumerate(cl) if name}
            e = lv(ecx, lm)
            d_ = lv(edx, lm)
            aib = {"k": aid["n"], "fn": fn, "ra": site, "ecx": e if e is not None else 0x0012F000,
                   "edx": d_ if d_ is not None else 0x0012F000, "a": a, "b": b, "s": "%08x:%08x" % tuple(seed),
                   "c": [ctrl.get("c14", u32(inp["ctl14"])), ctrl.get("c18", u32(inp.get("ctl18", 0))),
                         ctrl.get("c1c", u32(inp.get("ctl1c", 0)))], "c4": ctrl.get("c4", u32(inp.get("c4", 0))),
                   "fr": 100, "n": aid["n"] + 1}
            aix = {"k": aid["n"], "s": aib["s"], "nb": 1, "fr": 100, "n": aid["n"] + 2}
            out.append("AID " + json.dumps(aid))
            out.append("AIB " + json.dumps(aib))
            out.append("AIX " + json.dumps(aix))
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")
    return n


TIER_MODELS = [("ai_cat_emu", "skeleton"), ("ai_cat_emu", "wraith"), ("ai_cat_emu2", "scarab"),
               ("ai_cat_emu2", "mummy"), ("ai_cat_emu2", "gmummy"), ("ai_cat_emu2", "fetish"),
               ("ai_cat_emu3", "skelbow"), ("ai_cat_emu4", "skmage"), ("ai_cat_emu5", "necropet"),
               ("ai_cat_emu6", "hire"), ("ai_cat_emu6", "hirealt"), ("ai_cat_emu6", "andariel"),
               ("ai_cat_emu8", "mega"), ("ai_cat_emu9", "blood")]


def selftest(tmp):
    path = os.path.join(tmp, "synth.log")
    n = synth_log(path, TIER_MODELS)
    text, r = run_check([path])
    return n, r, text


def main(argv):
    if not argv or argv[0] not in ("check", "counts", "selftest"):
        print(__doc__)
        return 2
    if argv[0] == "selftest":
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            n, r, text = selftest(tmp)
        print(text)
        return 0 if r["mismatches"] == 0 and r["decisions"] == n else 1
    out = js = None
    controls = False
    paths = []
    a = argv[1:]
    k = 0
    while k < len(a):
        if a[k] == "--controls":
            controls = True
            k += 1
        elif a[k] == "--out":
            out = a[k + 1]
            k += 2
        elif a[k] == "--json":
            js = a[k + 1]
            k += 2
        else:
            paths.append(a[k])
            k += 1
    if argv[0] == "counts":
        per = {}
        for p in paths:
            for d in parse(p)["dec"]:
                per[d["aid"]["ai"]] = per.get(d["aid"]["ai"], 0) + 1
        for row in sorted(per):
            print("ROW", row, per[row])
        print("TOTAL", sum(per.values()))
        return 0
    text, r = run_check(paths, out, controls)
    print(text, end="")
    if js:
        with open(js, "w") as fh:
            json.dump({"decisions": r["decisions"], "mismatches": r["mismatches"], "accounting_violations": r["acc"]},
                      fh)
    bad_ctl = controls and any(not ok for m, ok in r["controls"] if m in ("site", "fallen"))
    return 0 if r["mismatches"] == 0 and r["acc"] == 0 and r["pp_bad"] == 0 and not bad_ctl else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

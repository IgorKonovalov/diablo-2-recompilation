#!/usr/bin/env python3
"""lane/r71: row 106's think (0x005EB970) as written in docs/findings/ai/0019-row-tables-and-scoring.md, against the code.

    python3 -I tools/ai_sm_check.py check [--exe PATH] [--cases N] [--seed S] [--out FILE]

The think function runs from its entry as code, in the x86 interpreter of tools/ai_resume.py, over the pinned image.
Every callee except RNG_Range (executed) is a stub that logs its words and returns a value the case declares: the
callees are the boundary, as in ADR-0021, and nothing here reads what they do. `model()` below is the finding's
pseudocode as written, and it never reads the interpreter. Compared per case, in order: every callee's words (a draw's
range and the seed after it included), the outcome (the callee that ended the think, or its return), the score list's
words in the frame, the accumulated aura value, `v14` and `v18`, the seed.

The `K` table names every constant and branch of the model; a control changes one of them alone and must fail at least
one case, so each line `CTL <name> differs=<n>` says how many cases separate that one term (`p_hi` cannot: a chance of 100 and of
101 against Range(100) are the same, so its 0 is expected and it is the one zero allowed). Each conditional branch in
the think's range is listed if the cases took it one way only (`BR` lines). Cases come from random.Random(seed), the
values drawn around each threshold, the skill records synthetic (ADR-0015 condition 4).

What it shows: the finding's model and the instructions are the same map from those inputs. It is an interpreter of
ours, not a Ghidra run: ADR-0015's conditions are not claimed, the reading stays [I]. It does not show what the stubs
return in play, nor that the offsets hold the columns their names say. Stdlib and objdump only.
"""
import argparse
import hashlib
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai_resume as R  # noqa: E402

ROOT = os.path.dirname(HERE)
EXE = os.path.join(ROOT, "workspace", "install", "app", "game.exe")
TEXT_LO, TEXT_HI = 0x005EB970, 0x005EC634
RNG = 0x0045C390

U, T, O, N, P, W, CTL, CTX, G, REC, SKT, LIST, DT, MIS = (0x10000000, 0x11000000, 0x12000000, 0x13000000, 0x14000000,
                                                         0x15000000, 0x16000000, 0x17000000, 0x18000000, 0x19000000,
                                                         0x20000000, 0x1A000000, 0x1B000000, 0x1C000000)
NODE = 0x1D000000
SLIST = 0x1E000000
MONREC = 0x1F000000
SKILL_MUL = 0x23C

# name -> callee, as the trace spells it
F = {0x0058F0D0: "MonsterOwner", 0x00540E60: "CancelEvents", 0x005B0BD0: "DistSq", 0x005E45D0: "AiPetGuard",
     0x00553540: "GetTarget", 0x005EB8B0: "Use", 0x00643910: "ListFirst", 0x006438F0: "ListNext",
     0x00643CE0: "NodeId", 0x00620190: "LeftSkill", 0x00643BC0: "SetLeft", 0x00639DF0: "HasState",
     0x005EB7F0: "GroupHeld", 0x006439B0: "FindSkill", 0x00645460: "RangeType", 0x005DED00: "RunToFlags",
     0x00644360: "SkillMode", 0x005DEAD0: "UseSkill", 0x005541B0: "Dead", 0x00554200: "Hostile", 0x005DE080: "Idle",
     0x005DD0B0: "Search", 0x005EB650: "Priority", 0x00621F20: "LifePct", 0x0063A2B0: "MaskState",
     0x00622AA0: "LineBlocked", 0x005DED20: "RunToUnit", 0x005DF140: "StepAway", 0x006442A0: "SkillLevel",
     0x00625480: "GetStat", 0x006256B0: "FindList", 0x00625D00: "BaseStat", 0x0046ACE0: "MissileRec",
     0x0045ADF0: "SubX", 0x0045AE20: "SubY", 0x0044BE50: "UnitType", 0x0055B7E0: "MonRec", 0x00622C40: "InMelee",
     0x0045C4B0: "SkillRec"}
# stack words a stub takes (ret imm of the callee, read from the code at load time); registers: fastcall ones log ecx/edx
REGS = {"MonsterOwner": "c", "CancelEvents": "cd", "DistSq": "cd", "AiPetGuard": "cd", "Use": "cd", "GroupHeld": "cd",
        "FindSkill": "cd", "RunToFlags": "cd", "UseSkill": "cd", "Dead": "c", "Hostile": "cd", "Idle": "cd", "Search": "cd",
        "Priority": "cd", "RunToUnit": "cd", "StepAway": "cd", "MissileRec": "c", "SubX": "c", "SubY": "c", "UnitType": "c",
        "MonRec": "c", "SkillRec": "c"}


def s16w(v):
    return v & 0xFFFF


def step_seed(lo, hi):
    t = lo * R.MUL + hi
    return t & R.M32, (t >> 32) & R.M32


class Seed:
    def __init__(self, lo, hi):
        self.lo, self.hi = lo, hi

    def step(self):
        self.lo, self.hi = step_seed(self.lo, self.hi)
        return self.lo

    def range(self, n):
        """RNG_Range (0x0045C390): n <= 0 is 0 and no step; a power of two masks; else the unsigned remainder."""
        if n <= 0:
            return 0
        v = self.step()
        return v & (n - 1) if n & (n - 1) == 0 else v % n


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


# ------------------------------------------------------------------------------------------------- the finding's model
K = {
    # the think, before the score
    "own_far_sq": 1, "pet_gate": 144, "use1_held": 4, "use1_chance": 60, "left_chance": 20, "p_mul": 2, "p_lo": 5, "p_hi": 100,
    "prio_dist": 1024, "own_prio_dist": 1024, "crowd_n": 3, "crowd_range": 32, "crowd_mul": 2, "crowd_run": 36, "away": 8,
    "pending_len": 25, "pending_kind": 19, "pick_mask": 3, "last_idle": 15, "none_idle": 25, "noskill_idle": 100,
    # the score base
    "req_div": 4, "res_div": -10,
    # terms, by aitype
    "a1_near": 25, "a1_near_pen": 6, "a1_held": 10, "a1_free": 10,
    "a2_near": 25, "a2_near_pen": 10,
    "a3_ally": 5, "a3_ally_mul": 2, "a3_near": 25, "a3_near_pen": 7, "a3_few": 3, "a3_few_pen": 10, "a3_mul": 3, "a3_sub": 9,
    "a4_far_pen": 10, "a4_near": 25, "a4_close": 10, "a4_stop": 3, "a4_nomask": 10, "a4_acc": 4, "a4_add": 3,
    "a5_near": 25, "a5_near_pen": 5, "a5_d": 25, "a5_d_pen": 5, "a5_mask_pen": 5,
    "a6_none": 20, "a6_some": 6, "a6_range": 100,
    "a7_life": 66, "a7_low": 45, "a7_add": 10, "a7_low_add": 10, "a7_range": 40,
    "a8_life": 66, "a8_low": 45, "a8_mul": 2, "a8_low_mul": 2,
    "a11_near": 25, "a11_near_pen": 5, "a11_d": 25, "a11_d_pen": 5, "a11_mask_pen": 5, "a11_mul": 3,
    "a12_min": 25, "a12_near": 25, "a12_far_pen": 10, "a12_close": 10, "a12_l1": 75, "a12_add1": 8, "a12_l2": 50, "a12_add2": 12,
    "a13_mask_pen": 5, "a13_life": 50, "a13_n": 3, "a13_o": 4, "a13_far": 25, "a13_add": 20, "a13_min": 25, "a13_max": 324, "a13_max_add": 10,
    "tie": 0,
}
# boolean controls: a branch reversed alone
BOOLS = ["a1_state_need", "a2_state_u", "a2_state_t", "a4_flag", "a12_type", "a7_target_zero", "a8_target_self",
         "a1_target_self", "a13_target_near", "res_map_12", "a13_acc", "a4_list_acc", "res_target_u",
         "a7_owner_draws", "keep_ge"]


class Trace(list):
    def add(self, name, *words):
        self.append((name,) + tuple(w & R.M32 for w in words))


RES_STAT = {0: 36, 1: 39, 2: 41, 3: 37, 4: 43, 5: 45, 12: 43}


def model(c, k=None, flip=()):
    """The think, as the finding writes it. Returns (trace, outcome, list, acc, v14, v18, seed)."""
    k = dict(K, **(k or {}))
    tr = Trace()
    s = Seed(c["seed"][0], c["seed"][1])
    v14, v18 = c["v14"], c["v18"]
    if c["nohead"]:
        tr.add("Idle", G, U, k["noskill_idle"])
        return (tr, ("Idle", k["noskill_idle"]), None, None, v14, v18, (s.lo, s.hi))
    a1n, a1m, a1h = c["aip1"]
    a2n, a2m, a2h = c["aip2"]
    t = c["t"]
    m = c["melee"]
    dist_ev = c["dist"]
    own = c["O"]
    res = lambda o: (tr, o, None, None, v14, v18, (s.lo, s.hi))

    def dsq(a, b):
        v = c["d"][(a, b)]
        tr.add("DistSq", a, b)
        return v

    def use(id_, mm, x, a=0, b=0):
        tr.add("Use", G, own, U, id_, mm, x, a, b, CTX)
        return c["use"].get((id_, x), 0)

    def melee_of(x):
        tr.add("InMelee", U, x, 0)
        return c["inmelee"].get(x, 0)

    tr.add("MonsterOwner", U)
    tr.add("CancelEvents", G, U, 2, 0)
    if own != 0:
        if dsq(U, own) > a2h * a2h * k["own_far_sq"]:
            tr.add("AiPetGuard", G, U, 0, own, m, CTX, 0, 6)
            if c["pet"].get(0, 0):
                return res(("AiPetGuard", 0))
    # pending
    if v14 > 0:
        tr.add("GetTarget", G, U)
        g = c["cur_target"]
        if g != 0:
            t = g
        if t == 0:
            v14 = v18 = 0
        else:
            v14 -= 1
            if use(v18, m, t):
                return res(("Use", "pending"))
    if dist_ev > a2m:
        t = 0
    if t == 0:
        tr.add("ListFirst", LIST)
        for i, sk in enumerate(c["skills"]):
            node = NODE + 0x40 * i
            tr.add("NodeId", node, 0x6E3500, 0xD73)
            sid = sk["id"]
            rec = sk.get("rec")
            if rec is not None:
                ai = rec["aitype"]
                if ai == 6:
                    tr.add("LeftSkill", U)
                    if not c["left"]:
                        if (s.step() % 100) < k["left_chance"]:
                            tr.add("SetLeft", U, sid, -1)
                elif ai == 1 and rec["state"] > 0:
                    tr.add("HasState", U, rec["state"])
                    if not c["ustates"].get(rec["state"], 0):
                        tr.add("GroupHeld", U, rec["state"])
                        go = True
                        if c["group"].get(rec["state"], 0):
                            draw = s.range(100)
                            tr.add("draw", 100, s.lo)
                            if draw >= k["use1_held"]:
                                go = False
                        if go and (s.step() % 100) < k["use1_chance"]:
                            tr.add("FindSkill", U, sid, -1)
                            if sk.get("found", 1):
                                x = 0
                                tr.add("RangeType", U, node + 1)
                                if sk.get("rangetype", 0) == 1 and not m:
                                    tr.add("RunToFlags", G, U, 0, 4)
                                    x = c["run"]
                                    if x:
                                        return res(("RunToFlags", sid))
                                else:
                                    tr.add("SkillMode", node + 1)
                                    tr.add("UseSkill", G, U, 0x77, sid, 0, 0, 0)
                                    x = c["useskill"]
                                    if x:
                                        return res(("UseSkill", sid))
            tr.add("ListNext", node)
    o = 0
    if own != 0:
        tr.add("GetTarget", G, own)
        g = c["own_target"]
        if g != 0:
            o = g
            tr.add("Dead", g)
            if c["dead"].get(g, 0):
                o = 0
            else:
                tr.add("Hostile", G, U, g)
                if c["hostile"].get(g, 0):
                    t = g
                else:
                    o = 0
        if dsq(U, own) <= k["pet_gate"]:
            tr.add("AiPetGuard", G, U, t, own, m, CTX, 0, 6)
            if c["pet"].get(1, 0):
                return res(("AiPetGuard", 1))
    if t == 0:
        tr.add("Idle", G, U, k["none_idle"])
        return res(("Idle", k["none_idle"]))
    p = c["aip3"] - k["p_mul"] * max(c["v1C"], 1)
    if p <= k["p_lo"]:
        p = k["p_lo"]
    elif p >= k["p_hi"]:
        p = k["p_hi"]
    if m:
        draw = s.range(100)
        tr.add("draw", 100, s.lo)
        if draw < p:
            if use(0, m, t):
                return res(("Use", "plain"))
    tr.add("Search", G, U, 0x74, 0x5EB6D0, 1)
    if not m:
        moved = 0
        if o != 0:
            t = o
        elif c["nearO"] != 0:
            t = c["nearO"]
        elif c["prio"] != 0:
            if dsq(U, c["prio"]) < k["prio_dist"]:
                t = c["prio"]
        tr.add("Priority", U, t)
        if not c["isprio"].get(t, 0):
            tr.add("MonsterOwner", t)
            w = c["owner_of"].get(t, 0)
            if w != 0:
                tr.add("Dead", w)
                if not c["dead"].get(w, 0):
                    if dsq(U, w) < k["own_prio_dist"]:
                        t = w
    # the locals
    tr.add("LifePct", U)
    life = c["life"]
    d = dsq(U, t)
    tr_mask = 0
    if a1h > 0:
        tr.add("MaskState", U)
        tr_mask = 1 if c["mask"] else 0
    tr.add("LineBlocked", U, t, 4)
    clear = 0 if c["blocked"] else 1
    n10, near, n32, allies, nearO, nO = c["n10"], c["near"], c["n32"], c["allies"], c["nearO"], c["nO"]
    if n10 > k["crowd_n"]:
        draw = s.range(k["crowd_range"])
        tr.add("draw", k["crowd_range"], s.lo)
        if draw < k["crowd_mul"] * n10:
            if own != 0 and dsq(U, own) > k["crowd_run"]:
                tr.add("RunToUnit", G, U, own)
                return res(("RunToUnit", own))
            tr.add("StepAway", G, U, t, k["away"], 1)
            if c["away"]:
                return res(("StepAway", t))
    L = [(t, 0, 0, 0, 0)]
    acc = 0
    tr.add("ListFirst", LIST)

    def draw_n():
        v = s.range(a2n)
        if a2n > 0:
            tr.add("draw", a2n, s.lo)
        return v

    def aura(sk, node, sid):
        """Terms 4 and 12's stat read: returns True when the record is dropped."""
        nonlocal acc
        rec = sk["rec"]
        st = rec["state"]
        if st > 0:
            tr.add("HasState", U, st)
            if c["ustates"].get(st, 0):
                tr.add("FindList", U, st)
                if c["statlist"].get(st, 0):
                    tr.add("BaseStat", SLIST + st, rec["stat"], 0)
                    v = c["statval"].get(st, 0)
                    if "a4_list_acc" not in flip:
                        acc += v
                    return v >= k["a4_stop"]
        return False

    def missile_gate(rec):
        """Terms 5 and 11: True when the target is beyond the missile's reach."""
        if rec["sm0"] < 0 and rec["sm1"] >= 0:
            tr.add("MissileRec", rec["sm1"])
            if c["mis"].get(rec["sm1"]) is not None:
                r = c["mis"][rec["sm1"]] - 1
                if d >= r * r:
                    return True
        return False

    for i, sk in enumerate(c["skills"]):
        node = NODE + 0x40 * i
        tr.add("NodeId", node, 0x6E3500, 0xE3D)
        tr.add("SkillLevel", U, node, 1)
        sid = sk["id"]
        rec = sk.get("rec")
        if rec is not None:
            tgt = t
            score = rec["aibonus"] + tdiv(rec["reqlevel"], k["req_div"]) + sk["level"]
            e = rec["etype"]
            stat = RES_STAT.get(e)
            if e == 12 and "res_map_12" in flip:
                stat = None
            if stat is not None:
                who = U if "res_target_u" in flip else t
                tr.add("GetStat", who, stat, 0)
                score += tdiv(c["res"].get(stat, 0), k["res_div"])
            ai = rec["aitype"]
            sc = 0
            if ai == 1:
                st = rec["state"]
                skip = False
                if st > 0:
                    tr.add("HasState", U, st)
                    h = c["ustates"].get(st, 0)
                    if "a1_state_need" in flip:
                        skip = bool(h)
                    else:
                        skip = not h
                if not skip:
                    if near <= k["a1_near"]:
                        score -= k["a1_near_pen"]
                    tr.add("GroupHeld", U, st)
                    if c["group"].get(st, 0):
                        score -= k["a1_held"]
                    else:
                        score += k["a1_free"]
                    sc = draw_n() + score
                    tgt = t if "a1_target_self" in flip else U
            elif ai == 2:
                skip = False
                if rec["state"] > 0:
                    tr.add("HasState", U, rec["state"])
                    h = c["ustates"].get(rec["state"], 0)
                    skip = (not h) if "a2_state_u" in flip else bool(h)
                if not skip and rec["tstate"] > 0:
                    tr.add("HasState", t, rec["tstate"])
                    h = c["tstates"].get(rec["tstate"], 0)
                    skip = (not h) if "a2_state_t" in flip else bool(h)
                if not skip:
                    if near <= k["a2_near"]:
                        score -= k["a2_near_pen"]
                    sc = draw_n() + score
            elif ai == 3:
                if allies > k["a3_ally"]:
                    score -= k["a3_ally_mul"] * allies
                if near <= k["a3_near"]:
                    score -= k["a3_near_pen"]
                if n32 < k["a3_few"]:
                    score -= k["a3_few_pen"]
                sc = draw_n() + score + k["a3_mul"] * n32 - k["a3_sub"]
            elif ai == 4:
                if d > a1n * a1n:
                    score -= k["a4_far_pen"]
                score += a1m
                if m or d <= k["a4_near"]:
                    score += k["a4_close"]
                flag = rec["flag2"] if "a4_flag" not in flip else not rec["flag2"]
                if flag:
                    if not aura(sk, node, sid):
                        sc = draw_n() + score + a1h
                else:
                    if a1h > 0 and not tr_mask:
                        sc = draw_n() + score - k["a4_nomask"]
                    else:
                        sc = draw_n() + score + k["a4_acc"] * acc + k["a4_add"]
            elif ai in (5, 11):
                pre = "a5" if ai == 5 else "a11"
                if clear and not missile_gate(rec):
                    if near <= k[pre + "_near"]:
                        score -= k[pre + "_near_pen"]
                    if d <= k[pre + "_d"]:
                        score -= k[pre + "_d_pen"]
                    if tr_mask:
                        score -= k[pre + "_mask_pen"]
                    if ai == 5:
                        sc = draw_n() + score
                    else:
                        sc = draw_n() + score + k["a11_mul"] * n32
            elif ai == 6:
                tr.add("LeftSkill", U)
                lim = k["a6_some"] if c["left"] else k["a6_none"]
                v = s.range(k["a6_range"])
                tr.add("draw", k["a6_range"], s.lo)
                if v < lim:
                    tr.add("SetLeft", U, sid, -1)
            elif ai == 7:
                v = draw_n() + score
                if life <= k["a7_life"]:
                    tgt = t if "a7_target_zero" in flip else 0
                    if own == 0:
                        if "a7_owner_draws" not in flip:
                            s.range(k["a7_range"])
                            tr.add("draw", k["a7_range"], s.lo)
                            tr.add("SubX", U)
                            s.range(k["a7_range"])
                            tr.add("draw", k["a7_range"], s.lo)
                            tr.add("SubX", U)
                    else:
                        for who in (own, t, own, t, own):
                            tr.add("SubX", who)
                        tr.add("SubY", own)
                    sc = v + k["a7_add"]
                    if life < k["a7_low"]:
                        sc += k["a7_low_add"]
            elif ai == 8:
                v = draw_n() + score
                if life <= k["a8_life"]:
                    tgt = t if "a8_target_self" in flip else U
                    sc = v * k["a8_mul"]
                    if life < k["a8_low"]:
                        sc *= k["a8_low_mul"]
            elif ai == 12:
                ok = True
                tr.add("UnitType", t)
                ty = c["ttype"]
                if ("a12_type" in flip) != (ty == 1):
                    tr.add("MonRec", t)
                    if not c["tmon"] or c["drain"] < k["a12_min"]:
                        ok = False
                if ok:
                    if d > a1n * a1n:
                        score -= k["a12_far_pen"]
                    score += a1m
                    if m or d <= k["a12_near"]:
                        score += k["a12_close"]
                    drop = False
                    if rec["flag2"]:
                        drop = aura(sk, node, sid)
                    if not drop:
                        sc = draw_n() + score
                        if life < k["a12_l1"]:
                            sc += k["a12_add1"]
                        if life < k["a12_l2"]:
                            sc += k["a12_add2"]
            elif ai == 13:
                score += a1m
                if a1h > 0 and not tr_mask:
                    score -= k["a13_mask_pen"]
                elif "a13_acc" not in flip:
                    score += acc
                chosen = False
                if life < k["a13_life"] or n10 > k["a13_n"]:
                    if nearO != 0 and nO < k["a13_o"]:
                        if dsq(U, nearO) > k["a13_far"]:
                            score += k["a13_add"]
                            tgt = t if "a13_target_near" in flip else nearO
                            chosen = True
                if chosen:
                    sc = draw_n() + score
                elif d >= k["a13_min"]:
                    if d > k["a13_max"]:
                        score += k["a13_max_add"]
                    sc = draw_n() + score
            if ("keep_ge" in flip and sc >= L[-1][2]) or sc > L[-1][2]:
                L.append((tgt, sid, sc, 0, 0))
        tr.add("ListNext", node)
    final = list(L)
    while L:
        ent = L.pop()
        low = s.step()
        if low & k["pick_mask"]:
            mm = melee_of(ent[0])
            if use(ent[1], mm, ent[0], ent[3], ent[4]):
                tr.add("SkillRec", ent[1])
                kind = c["srv"].get(ent[1])
                if kind == k["pending_kind"]:
                    v18 = ent[1]
                    v14 = k["pending_len"]
                return (tr, ("Use", "pick", ent[1]), final, acc, v14, v18, (s.lo, s.hi))
    if t != 0:
        mm = melee_of(t)
        if use(0, mm, t):
            return (tr, ("Use", "last"), final, acc, v14, v18, (s.lo, s.hi))
    tr.add("Idle", G, U, k["last_idle"])
    return (tr, ("Idle", k["last_idle"]), final, acc, v14, v18, (s.lo, s.hi))


# --------------------------------------------------------------------------------------------- the code, in the interpreter
class Done(Exception):
    def __init__(self, st, outcome):
        self.st, self.outcome = st, outcome


class SM(R.Machine):
    def __init__(self, code, case):
        super().__init__(code, (), windows=())
        self.c = case
        self.tr = Trace()
        self.n_list = {}
        self.branches = {}

    def step(self, st):
        ins = self.code.at(st.eip)
        if ins and ins[1] == "jmp" and not ins[2][0].startswith("0x"):
            v = self.read(st, R.parse_op(ins[2][0]))
            if v is None:
                raise R.Stop("indirect jmp unknown at %08x" % st.eip)
            st.eip = v
            return [st]
        if ins and ins[1].startswith("j") and ins[1] != "jmp" and TEXT_LO <= st.eip < TEXT_HI:
            a = st.eip
            out = super().step(st)
            for k, v in st.br.items():
                self.branches[k] = self.branches.get(k, 0) | v
            return out
        return super().step(st)

    def do_call(self, st, tgt, ra):
        fn = int(tgt, 16)
        if fn == RNG:
            n = R.s32(st.r["edx"])
            self._draw(st, n)
            st.eip = ra
            return [st]
        name = F.get(fn)
        if name is None:
            raise R.Stop("unstubbed callee %08x at %08x" % (fn, st.eip))
        n = 0xC if name == "BaseStat" else (self.code.ret_imm(fn) or 0)     # 0x00625D00 is a tail jump
        sp = st.r["esp"]
        words = []
        regs = REGS.get(name, "")
        if "c" in regs:
            words.append(st.r["ecx"])
        if "d" in regs:
            words.append(st.r["edx"])
        words += [st.rd(sp + 4 * i, 4) for i in range(n // 4)]
        ret = self.stub(st, name, words)
        st.r["eax"] = ret & R.M32
        st.r["ecx"] = st.r["edx"] = 0xDEAD0000
        st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
        st.r["esp"] = (sp + n) & R.M32
        st.eip = ra
        return [st]

    def _draw(self, st, n):
        a = st.r["ecx"]
        lo, hi = st.rd(a, 4), st.rd(a + 4, 4)
        s = Seed(lo, hi)
        v = s.range(n)
        st.wr(a, 4, s.lo)
        st.wr(a + 4, 4, s.hi)
        st.r["eax"] = v
        st.r["ecx"] = st.r["edx"] = 0xDEAD0000
        st.f.update({"ZF": None, "SF": None, "CF": None, "OF": None})
        if n > 0:
            self.tr.append(("draw", n & R.M32, s.lo))

    def stub(self, st, name, w):
        c = self.c
        w = [0 if v is None else v for v in w]
        tr = self.tr
        if name == "SkillLevel":
            tr.add(name, *w)
            return c["skills"][(w[1] - NODE) // 0x40]["level"]
        if name == "NodeId":
            tr.add(name, *w)
            return c["skills"][(w[0] - NODE) // 0x40]["id"]
        if name in ("ListFirst", "ListNext"):
            tr.add(name, *w)
            i = -1 if name == "ListFirst" else (w[0] - NODE) // 0x40
            return NODE + 0x40 * (i + 1) if i + 1 < len(c["skills"]) else 0
        if name == "Search":
            # the block the callback fills
            base = st.r["ebp"] - 0x74
            tr.add(name, w[0], w[1], 0x74, w[3], w[4])
            for off, v in ((0x4, c["near_unit"]), (0x8, c["near"]), (0xC, c["n10"]), (0x10, c["nearO"]), (0x14, c["nearO_d"]),
                           (0x18, c["nO"]), (0x1C, c["n32"]), (0x20, c["allies"]), (0x24, c["prio"])):
                st.wr(base + off, 4, v & R.M32)
            return 0
        tr.add(name, *w)
        if name == "MonsterOwner":
            return c["O"] if w[0] == U else c["owner_of"].get(w[0], 0)
        if name == "DistSq":
            return c["d"][(w[0], w[1])] & R.M32
        if name == "AiPetGuard":
            return c["pet"].get(0 if w[2] == 0 and self.pet_first(st) else 1, 0)
        if name == "GetTarget":
            return c["cur_target"] if w[1] == U else c["own_target"]
        if name == "Use":
            r = c["use"].get((R.s32(w[3]), w[5]), 0)
            if r:
                self.last_use = R.s32(w[3])
            return r
        if name == "LeftSkill":
            return c["left"]
        if name == "HasState":
            return (c["ustates"] if w[0] == U else c["tstates"]).get(R.s32(w[1]), 0)
        if name == "GroupHeld":
            return c["group"].get(R.s32(w[1]), 0)
        if name == "FindSkill":
            for i, sk in enumerate(c["skills"]):
                if sk["id"] == R.s32(w[1]):
                    return (NODE + 0x40 * i + 1) if sk.get("found", 1) else 0
            return 0
        if name == "RangeType":
            return c["skills"][(w[1] - 1 - NODE) // 0x40].get("rangetype", 0)
        if name == "RunToFlags":
            return c["run"]
        if name == "SkillMode":
            return 0x77
        if name == "UseSkill":
            return c["useskill"]
        if name == "Dead":
            return c["dead"].get(w[0], 0)
        if name == "Hostile":
            return c["hostile"].get(w[2], 0)
        if name == "Idle":
            raise Done(st, ("Idle", R.s32(w[2])))
        if name == "Priority":
            return c["isprio"].get(w[1], 0)
        if name == "LifePct":
            return c["life"]
        if name == "MaskState":
            return c["mask"]
        if name == "LineBlocked":
            return c["blocked"]
        if name == "RunToUnit":
            raise Done(st, ("RunToUnit", w[2]))
        if name == "StepAway":
            return c["away"]
        if name == "GetStat":
            return c["res"].get(R.s32(w[1]), 0) & R.M32
        if name == "FindList":
            return (SLIST + R.s32(w[1])) if c["statlist"].get(R.s32(w[1]), 0) else 0
        if name == "BaseStat":
            return c["statval"].get(R.s32(w[0] - SLIST), 0) & R.M32
        if name == "MissileRec":
            r = c["mis"].get(R.s32(w[0]))
            if r is None:
                return 0
            st.wr(MIS + 0x96, 2, r & 0xFFFF)
            return MIS
        if name == "UnitType":
            return c["ttype"]
        if name == "MonRec":
            if not c["tmon"]:
                return 0
            st.wr(MONREC + 0xA0 + c["diff"], 1, c["drain"])
            return MONREC
        if name == "InMelee":
            return c["inmelee"].get(w[1], 0)
        if name == "SkillRec":
            kind = c["srv"].get(R.s32(w[0]))
            st.wr(REC + 0x2E, 2, 0xFFFF if kind is None else kind)
            return REC
        if name in ("SubX", "SubY"):
            return 0xBAD0BAD0
        return 0

    def pet_first(self, st):
        return st.eip < 0x5EBA1F


def build_state(c):
    st = R.State()
    F0 = R.STK_TOP - 0x1000
    st.r.update({"esp": F0 + 0x10, "ebp": 0x7EADBEEF, "ecx": G, "edx": U, "eax": 0, "ebx": 0, "esi": 0, "edi": 0})
    # the entry: [esp] = return, [esp+4] = ctx
    st.wr(F0 + 0x10, 4, R.RET_SENTINEL)
    st.wr(F0 + 0x14, 4, CTX)
    st.eip = 0x005EB970
    w = st.wr
    w(G + 0x6D, 1, c["diff"])
    w(G + 0xA8, 4, 1000)
    w(U + 0x00, 4, 1)
    w(U + 0x20, 4, c["seed"][0])
    w(U + 0x24, 4, c["seed"][1])
    w(U + 0xA8, 4, 0 if c["nohead"] else LIST)
    w(CTX + 0x00, 4, CTL)
    w(CTX + 0x08, 4, c["t"])
    w(CTX + 0x14, 4, c["dist"] & R.M32)
    w(CTX + 0x18, 4, c["melee"])
    w(CTX + 0x1C, 4, REC + 0x10000)
    aip = REC + 0x10000
    for off, v in zip((0x56, 0x58, 0x5A), c["aip1"]):
        w(aip + off, 2, v & 0xFFFF)
    for off, v in zip((0x5C, 0x5E, 0x60), c["aip2"]):
        w(aip + off, 2, v & 0xFFFF)
    w(aip + 0x62 + 2 * c["diff"], 2, c["aip3"] & 0xFFFF)
    w(CTL + 0x14, 4, c["v14"] & R.M32)
    w(CTL + 0x18, 4, c["v18"] & R.M32)
    w(CTL + 0x1C, 4, c["v1C"] & R.M32)
    w(R.G_DATATABLES, 4, DT)
    w(DT + 0xBA0, 4, c["nskills"])
    w(DT + 0xB98, 4, SKT)
    for sk in c["skills"]:
        rec = sk.get("rec")
        if rec is None:
            continue
        b = SKT + sk["id"] * SKILL_MUL
        w(b + 0x04, 1, 4 if rec["flag2"] else 0)
        w(b + 0x46, 2, rec["sm0"] & 0xFFFF)
        w(b + 0x48, 2, rec["sm1"] & 0xFFFF)
        w(b + 0x54, 2, rec["stat"] & 0xFFFF)
        w(b + 0x80, 2, rec["state"] & 0xFFFF)
        w(b + 0x82, 2, rec["tstate"] & 0xFFFF)
        w(b + 0x174, 2, rec["reqlevel"] & 0xFFFF)
        w(b + 0x1DC, 1, rec["etype"])
        w(b + 0x230, 1, rec["aitype"])
        w(b + 0x232, 2, rec["aibonus"] & 0xFFFF)
    return st


def load_image_words(st, exe):
    """The two jump tables, the byte map and the mask: image constants the think reads."""
    d = open(exe, "rb").read()
    for lo, hi, base in ((0x005EC634, 0x005EC694, 0x1000 + (0x005EC634 - 0x00401000)), (0x006CE270, 0x006CE274, 0x2CC000 + (0x006CE270 - 0x006CC000))):
        for i in range(hi - lo):
            st.m[lo + i] = d[base + i]


def run_code(code, c, exe):
    st = build_state(c)
    load_image_words(st, exe)
    m = SM(code, c)
    outcome = None
    try:
        for _ in range(200000):
            if st.eip == R.RET_SENTINEL:
                outcome = ("return",)
                break
            r = m.step(st)
            if len(r) != 1:
                raise R.Stop("fork at %08x" % st.eip)
            st = r[0]
    except Done as e:
        st, outcome = e.st, e.outcome
    return m, st, outcome


# ---------------------------------------------------------------------------------------------------------- the cases
def gen_case(r):
    near_vals = lambda *v: r.choice(list(v) + [r.randint(0, 400)])
    diff = r.randrange(3)
    pts = [T, O, N, P, W]
    states = list(range(1, 7))
    nskills = 400
    ids = r.sample(range(1, 390), 12)
    skills = []
    aitypes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 14]
    for i in range(r.randint(0, 9)):
        sid = ids[i]
        ai = r.choice(aitypes)
        rec = {"aitype": ai, "aibonus": r.choice([0, 0, -3, 3, r.randint(-40, 40)]), "reqlevel": r.choice([1, 2, 3, 4, 6, 12, 18, 24, 30, -5, -9]),
               "etype": r.choice([0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 255]), "state": r.choice([0, -1] + states), "tstate": r.choice([0, -1] + states),
               "stat": r.randint(0, 50), "flag2": r.randint(0, 1), "sm0": r.choice([-1, -1, 5]), "sm1": r.choice([-1, 7, 8, 9])}
        sk = {"id": sid, "level": r.randint(0, 30), "rec": rec, "found": r.choice([1, 1, 0]), "rangetype": r.randint(0, 2)}
        if r.random() < 0.06:
            sk = {"id": r.choice([-1, 400, 500]), "level": 1, "rec": None}
        skills.append(sk)
    O_ = r.choice([0, O, O])
    t0 = r.choice([T, T, T, 0])
    nearO = r.choice([0, N, N])
    prio = r.choice([0, P])
    aip2n = r.choice([20, 20, 16, 0, 7])
    c = {"seed": (r.getrandbits(32), r.getrandbits(32)), "nohead": r.random() < 0.01, "diff": diff, "melee": r.randint(0, 1), "t": t0, "O": O_,
         "dist": r.choice([3, 9, 50]), "v14": r.choice([0, 0, 0, 1, 25]), "v18": r.choice([0, ids[0]]), "v1C": r.choice([0, 1, 5, 12, 60]),
         "aip1": (r.choice([0, 3, 12]), r.randint(-3, 9), r.choice([0, 0, 5])), "aip2": (aip2n, r.choice([5, 20]), r.choice([6, 40])),
         "aip3": r.choice([0, 30, 60, 110, 300]), "nskills": nskills, "skills": skills, "left": r.choice([0, 1]),
         "ustates": {s: r.randint(0, 1) for s in states}, "tstates": {s: r.randint(0, 1) for s in states},
         "group": {s: r.randint(0, 1) for s in states}, "statlist": {s: r.randint(0, 1) for s in states},
         "statval": {s: r.choice([0, 1, 2, 3, 4]) for s in states}, "mis": {7: None, 8: r.choice([1, 5, 20, 30]), 9: r.choice([3, 8, 40])},
         "res": {s: r.choice([0, 5, 9, 10, 19, 20, 25, 75, -1, -9, -10, -11, -25, -100, 100, 99999]) for s in (36, 37, 39, 41, 43, 45)},
         "use": {}, "inmelee": {}, "pet": {0: r.choice([0, 0, 1]) if r.random() < .2 else 0, 1: 1 if r.random() < .1 else 0},
         "cur_target": r.choice([0, T]), "own_target": r.choice([0, W, W]), "dead": {W: r.choice([0, 0, 1]), P: 0},
         "hostile": {W: r.choice([1, 1, 0])}, "run": r.choice([0, 0, 1]), "useskill": r.choice([0, 0, 1]),
         "near_unit": N, "near": near_vals(0, 9, 24, 25, 26, 100), "n10": r.choice([0, 1, 3, 3, 4, 6, 9]), "nearO": nearO,
         "nearO_d": r.randint(0, 99), "nO": r.choice([0, 3, 4, 5]), "n32": r.choice([0, 1, 2, 3, 4, 8]), "allies": r.choice([0, 3, 5, 6, 8]),
         "prio": prio, "isprio": {}, "owner_of": {}, "life": r.choice([10, 44, 45, 49, 50, 66, 67, 74, 75, 100]), "mask": r.randint(0, 1),
         "blocked": r.choice([0, 0, 1]), "away": r.choice([0, 0, 1]), "ttype": r.choice([0, 0, 1, 2]), "tmon": r.choice([0, 1, 1]), "drain": r.choice([0, 24, 25, 26, 100]),
         "srv": {}, "d": {}}
    dv = lambda: r.choice([0, 9, 24, 25, 26, 36, 37, 99, 100, 143, 144, 145, 323, 324, 325, 900, 1023, 1024, 1025, 5000])
    units = [T, O, N, P, W]
    for a in units:
        c["d"][(U, a)] = dv()
    for x in (T, O, N, P, W):
        c["isprio"][x] = r.choice([0, 1])
        c["owner_of"][x] = r.choice([0, 0, W])
        c["inmelee"][x] = r.randint(0, 1)
        c["hostile"].setdefault(x, r.randint(0, 1))
    c["inmelee"][0] = r.randint(0, 1)
    c["dead"].setdefault(W, 0)
    allids = [0] + [s["id"] for s in skills]
    tg = [T, O, N, P, W, 0, U]
    if r.random() < 0.7:
        for sid in allids:
            for x in tg:
                if r.random() < 0.2:
                    c["use"][(sid, x)] = 1
    for sid in allids:
        if r.random() < 0.5:
            c["srv"][sid] = r.choice([19, 19, 18, 20])
    return c


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("--exe", default=EXE)
    ap.add_argument("--cases", type=int, default=4000)
    ap.add_argument("--seed", default="r71-sm")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    r = random.Random(a.seed)
    code = R.Code(exe=a.exe)
    cases = [gen_case(r) for _ in range(a.cases)]
    out = []
    bad = stopped = 0
    outcomes = {}
    branches = {}
    pick_seen = {}
    h = hashlib.sha256()
    code_res = []
    for i, c in enumerate(cases):
        try:
            m, st, oc = run_code(code, c, a.exe)
        except R.Stop as e:
            stopped += 1
            out.append("STOP case %d: %s" % (i, e))
            code_res.append(None)
            continue
        for k_, v in m.branches.items():
            branches[k_] = branches.get(k_, 0) | v
        ebp = st.r["ebp"]
        ctl = (R.s32(st.rd(CTL + 0x14, 4)), R.s32(st.rd(CTL + 0x18, 4)))
        seed = (st.rd(U + 0x20, 4), st.rd(U + 0x24, 4))
        cr = {"trace": tuple(m.tr), "outcome": oc, "ctl": ctl, "seed": seed, "st": st}
        code_res.append(cr)
        ok, why = same(c, cr, model(c))
        key = oc[0]
        outcomes[key] = outcomes.get(key, 0) + 1
        h.update(repr((i, cr["trace"], oc, ctl, seed)).encode())
        if not ok:
            bad += 1
            if bad <= 6:
                out.append("DIFF case %d: %s" % (i, why))
    out.append("CASES %d mismatches=%d stopped=%d trace_sha256=%s" % (a.cases, bad, stopped, h.hexdigest()[:16]))
    out.append("OUTCOMES " + " ".join("%s=%d" % kv for kv in sorted(outcomes.items())))
    # controls: one term at a time
    ctl_zero = []
    for name, val in K.items():
        if name == "tie":
            continue
        n = 0
        kk = {name: (val + 1) if not name.endswith("_mask") else 1}
        for c, cr in zip(cases, code_res):
            if cr is None:
                continue
            try:
                res = model(c, kk)
            except KeyError:
                n += 1
                continue
            if not same(c, cr, res)[0]:
                n += 1
        out.append("CTL %s+1 differs=%d" % (name, n))
        if n == 0:
            ctl_zero.append(name)
    for name in BOOLS:
        n = 0
        for c, cr in zip(cases, code_res):
            if cr is None:
                continue
            try:
                res = model(c, None, (name,))
            except KeyError:
                n += 1
                continue
            if not same(c, cr, res)[0]:
                n += 1
        out.append("CTL %s differs=%d" % (name, n))
        if n == 0:
            ctl_zero.append(name)
    out.append("CTL zero: " + (" ".join(ctl_zero) if ctl_zero else "none"))
    # branch coverage, over the conditional jumps of the think
    jcc = []
    for addr in sorted(code_addrs(code)):
        ins = code.at(addr)
        if ins[1].startswith("j") and ins[1] != "jmp":
            jcc.append(addr)
    one = [x for x in jcc if branches.get(x, 0) != 3]
    out.append("BR total=%d both=%d one_or_none=%d" % (len(jcc), len(jcc) - len(one), len(one)))
    for x in one:
        out.append("BR %08x %s" % (x, {0: "never", 1: "taken only", 2: "not taken only"}[branches.get(x, 0)]))
    text = "\n".join(out) + "\n"
    if a.out:
        open(a.out, "w").write(text)
    print("\n".join(out[:12]))
    print("SUMMARY cases=%d mismatches=%d stopped=%d zero_controls=%d jcc=%d one_way=%d" % (a.cases, bad, stopped, len(ctl_zero), len(jcc), len(one)))
    return 1 if bad or stopped else 0


def code_addrs(code):
    a = TEXT_LO
    while a < TEXT_HI:
        ins = code.at(a)
        if ins is None:
            break
        yield a
        a += ins[0]


def same(c, cr, res):
    tr, oc, lst, acc, v14, v18, seed = res
    want, got = list(tr), list(cr["trace"])
    if want != got:
        for i in range(min(len(want), len(got))):
            if want[i] != got[i]:
                return False, "call %d: model %r code %r" % (i, want[i], got[i])
        return False, "length: model %d code %d; next %r" % (len(want), len(got), (want + got)[min(len(want), len(got))])
    if (v14, v18) != cr["ctl"]:
        return False, "ctl: model %r code %r" % ((v14, v18), cr["ctl"])
    if seed != cr["seed"]:
        return False, "seed"
    st = cr["st"]
    if lst is not None:
        ebp = st.r["ebp"]
        if ebp is None or not (R.STK_TOP - 0x2000 < ebp < R.STK_TOP):
            ebp = R.STK_TOP - 0x1000 + 0x10 - 4
        for i, e in enumerate(lst):
            b = ebp - 0x444 + 20 * i
            words = tuple(R.s32(st.rd(b + 4 * j, 4)) for j in range(5))
            if tuple(R.s32(x & R.M32) for x in e) != words:
                return False, "L[%d]: model %r code %r" % (i, e, words)
        if acc is not None and R.s32(st.rd(ebp - 0x30, 4)) != acc:
            return False, "acc: model %r code %r" % (acc, R.s32(st.rd(ebp - 0x30, 4)))
    return True, ""


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Row 44 `Duriel`, plan 0052 P1b-1 (ai/0014 C10): the melee choice against the kept owner-played logs. No game.

Two separate questions, kept apart in the output:

  TALLY / FREQ   the logged first command of each melee decision (MSM0's mode, the skill from the AIB line and SST0), and an
                 exact test of the two distributions: the code's Smite 33 : Jab 33.5 : A1 33.5 against the community page's
                 33 : 50 : 17. A frequency cannot tell how the draws are made.
  REPLAY         from the AID line's unit seed, the block's draws (low word of a step, mod 100) give the arm, and the number
                 of steps gives the seed at the logged call and at AIX. Each READING is one way of making the choice; every
                 reading but `code` must fail decisions. arm = wrong call; seed = right call, wrong seed.

Readings: code       three fresh draws, aip2 Skill3, aip3 Skill2, aip4 A2, else A1 (fn:sub_005F67B0_AiDuriel@0x005F67B0)
          page-one   one draw: < 33 Smite, < 83 Jab, else A1 (the page's percentages as a single roll)
          page-fresh fresh draws with the page's percentages: < 33 Smite, then < 75 Jab, no third draw kept in the arm
          reused     one draw tested against aip2, aip3, aip4 in turn (33 : 17 : 50)
          two-draws  the block with the A2 test's draw left out (aip4 is 0: only the seed can tell)
          swapped    Skill2's test before Skill3's
          one-cum    one draw: < 33 Smite, < 67 Jab, else A1: the code's frequencies from a single roll, so no frequency can
                     tell it from `code`, and only the replay can

    python3 -I tools/ai_duriel_c10.py LOG...
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ai  # noqa: E402
import ai_resume  # noqa: E402

RIGHT, SKILL, MODE = 0x006201D0, 0x005DEAD0, 0x005DDF90
ARM = {(SKILL, 0x005F6884): "Smite", (SKILL, 0x005F68F7): "Jab", (MODE, 0x005F6964): "A1", (MODE, 0x005F694E): "A2"}
CODE = (0.33, 0.335, 0.335)
PAGE = (0.33, 0.50, 0.17)
KINDS = ("Smite", "Jab", "A1")


def s16(v):
    return v - (1 << 16) if v >= (1 << 15) else v


def draws(seed, n):
    out = []
    for _ in range(n):
        seed = ai.step(seed)
        out.append(seed[0] % 100)
    return out, seed


def steps(seed, n):
    for _ in range(n):
        seed = ai.step(seed)
    return seed


def reading(name, seed, a2, a3, a4):
    """-> (arm, the seed after the reading's draws)."""
    d, _ = draws(seed, 3)
    if name == "code":
        if d[0] < a2:
            return "Smite", steps(seed, 1)
        if d[1] < a3:
            return "Jab", steps(seed, 2)
        return ("A2" if d[2] < a4 else "A1"), steps(seed, 3)
    if name == "page-one":
        return ("Smite" if d[0] < 33 else "Jab" if d[0] < 83 else "A1"), steps(seed, 1)
    if name == "page-fresh":
        if d[0] < 33:
            return "Smite", steps(seed, 1)
        return ("Jab" if d[1] < 75 else "A1"), steps(seed, 2)
    if name == "reused":
        return ("Smite" if d[0] < a2 else "Jab" if d[0] < a3 else "A2" if d[0] < a4 else "A1"), steps(seed, 1)
    if name == "two-draws":
        if d[0] < a2:
            return "Smite", steps(seed, 1)
        return ("Jab" if d[1] < a3 else "A1"), steps(seed, 2)
    if name == "swapped":
        if d[0] < a3:
            return "Jab", steps(seed, 1)
        if d[1] < a2:
            return "Smite", steps(seed, 2)
        return ("A2" if d[2] < a4 else "A1"), steps(seed, 3)
    if name == "one-cum":
        return ("Smite" if d[0] < 33 else "Jab" if d[0] < 67 else "A1"), steps(seed, 1)
    raise ValueError(name)


# --- exact statistics ---------------------------------------------------------------------------------------------
def lpmf(k, n, p):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log(1 - p)


def pmf(k, n, p):
    return math.exp(lpmf(k, n, p))


def cdf(k, n, p):
    return sum(pmf(i, n, p) for i in range(0, k + 1)) if k >= 0 else 0.0


def clopper(k, n, alpha=0.05):
    """The exact interval, by bisection on the binomial tails."""
    def solve(f):
        lo, hi = 1e-12, 1 - 1e-12
        for _ in range(200):
            m = (lo + hi) / 2
            if f(m):
                lo = m
            else:
                hi = m
        return lo
    low = 0.0 if k == 0 else solve(lambda p: 1 - cdf(k - 1, n, p) < alpha / 2)
    high = 1.0 if k == n else solve(lambda p: cdf(k, n, p) > alpha / 2)
    return low, high


def p_two(k, n, p):
    """Exact two-sided test, the sum of the outcomes no more likely than the one seen."""
    t = pmf(k, n, p) * (1 + 1e-9)
    return sum(q for q in (pmf(i, n, p) for i in range(n + 1)) if q <= t)


def p_multi(c, ps):
    """Exact multinomial test over the (N+1)(N+2)/2 cells."""
    n = sum(c)

    def lp(a, b):
        z = n - a - b
        return math.lgamma(n + 1) - math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(z + 1) + a * math.log(ps[0]) + b * math.log(ps[1]) + z * math.log(ps[2])
    t = lp(c[0], c[1]) + 1e-9
    s = 0.0
    for a in range(n + 1):
        for b in range(n - a + 1):
            v = lp(a, b)
            if v <= t:
                s += math.exp(v)
    return s


def power(n):
    """For an A1 count: reject the page where its exact test gives p < 0.05, and the other way round; and the one cut that
    splits the two with the two errors stated."""
    rej_page = [k for k in range(n + 1) if p_two(k, n, PAGE[2]) < 0.05]
    rej_code = [k for k in range(n + 1) if p_two(k, n, CODE[2]) < 0.05]
    pw_page = sum(pmf(k, n, CODE[2]) for k in rej_page)
    pw_code = sum(pmf(k, n, PAGE[2]) for k in rej_code)
    cut = min(range(n + 1), key=lambda c: abs((1 - cdf(c - 1, n, PAGE[2])) - cdf(c - 1, n, CODE[2])))
    return pw_page, pw_code, cut, 1 - cdf(cut - 1, n, PAGE[2]), cdf(cut - 1, n, CODE[2])


def main(argv):
    decs = []
    for p in argv:
        for d in ai.parse(p)["dec"]:
            if d["aid"]["ai"] == 44:
                decs.append((os.path.basename(p), d))
    melee = [(p, d) for p, d in decs if d["aid"]["ctx"][6]]
    other = [(p, d) for p, d in decs if not d["aid"]["ctx"][6]]
    print("DURIEL decisions=%d melee=%d not_melee=%d" % (len(decs), len(melee), len(other)))
    per = {}
    for p, d in decs:
        e = per.setdefault(p, [0, 0, set(), set()])
        e[0] += 1
        e[1] += bool(d["aid"]["ctx"][6])
        e[2].add(d["aid"]["c"])
        e[3].add(d["aid"]["diff"])
    for p, e in per.items():
        print("LOG %s decisions=%d melee=%d classes=%s diff=%s" % (p, e[0], e[1], sorted(e[2]), sorted(e[3])))
    tgt = {}
    for p, d in melee:
        t = d["aid"]["t"]
        k = (p, t[0], t[1])
        tgt[k] = tgt.get(k, 0) + 1
    for k in sorted(tgt):
        print("TARGET %s type=%d class=%d melee_decisions=%d" % (k[0], k[1], k[2], tgt[k]))
    # the tally: logged calls only, no draw
    tally, modes, cross = {}, {}, {}
    rs = {}
    for p, d in melee:
        tl = ai_resume.top_level(d)
        g = tl[0]
        if g["fn"] != RIGHT or g["ra"] != 0x005F67DF:
            print("ODD first call %s n=%d" % (p, d["aid"]["n"]))
        rs[bool(d["air"][g["n"]]["eax"])] = rs.get(bool(d["air"][g["n"]]["eax"]), 0) + 1
        last = tl[-1]
        arm = ARM.get((last["fn"], last["ra"]), "?%x@%x" % (last["fn"], last["ra"]))
        tally[arm] = tally.get(arm, 0) + 1
        ms = d["msm"][0][0]["cmd"][0] if d["msm"] else None
        sk = last["a"][1] if last["fn"] == SKILL else None
        k = (arm, ms, sk)
        modes[k] = modes.get(k, 0) + 1
    print("RIGHTSKILL nonzero=%d zero=%d (the aura's grant arm, reached only with zero)" % (rs.get(True, 0), rs.get(False, 0)))
    for k in sorted(modes, key=str):
        print("CMD arm=%s msm0_mode=%s skill=%s n=%d" % (k[0], k[1], k[2], modes[k]))
    c = [tally.get(k, 0) for k in KINDS]
    n = sum(c)
    print("TALLY n=%d Smite=%d Jab=%d A1=%d other=%d" % (n, c[0], c[1], c[2], len(melee) - n))
    for k, v, pc, pp in zip(KINDS, c, CODE, PAGE):
        lo, hi = clopper(v, n)
        print("FREQ %s %d/%d=%.1f%% exact95=[%.1f%%, %.1f%%] code=%.1f%% p=%.3g page=%.1f%% p=%.3g" % (
            k, v, n, 100 * v / n, 100 * lo, 100 * hi, 100 * pc, p_two(v, n, pc), 100 * pp, p_two(v, n, pp)))
    print("MULTI exact multinomial p: code=%.3g page=%.3g" % (p_multi(c, CODE), p_multi(c, PAGE)))
    nn = c[1] + c[2]
    lo, hi = clopper(c[1], nn)
    print("SPLIT Jab among not-Smite %d/%d=%.1f%% exact95=[%.1f%%, %.1f%%] code=50.0%% page=%.1f%%" % (c[1], nn, 100 * c[1] / nn, 100 * lo, 100 * hi, 100 * PAGE[1] / (PAGE[1] + PAGE[2])))
    llr = sum(v * math.log(a / b) for v, a, b in zip(c, CODE, PAGE))
    print("LLR ln(L_code/L_page)=%.1f" % llr)
    for size in (300, n):
        pw, pc, cut, ea, eb = power(size)
        print("POWER n=%d A1 count: reject page at 5%% when the code holds=%.6g, reject code at 5%% when the page holds=%.6g; cut A1>=%d: P(page reaches it)=%.3g, P(code misses it)=%.3g" % (size, pw, pc, cut, ea, eb))
    # the replay
    for name in ("code", "page-one", "page-fresh", "reused", "two-draws", "swapped", "one-cum"):
        ok = arm_bad = seed_bad = exit_bad = 0
        pred = {}
        for p, d in melee:
            a = d["aid"]
            raw = bytes.fromhex(a["aip"])
            aips = [s16(int.from_bytes(raw[i:i + 2], "little")) for i in range(0, len(raw), 2)]
            a2, a3, a4 = (aips[3 * (k - 1) + a["diff"]] for k in (2, 3, 4))
            s0 = ai.seedval(a["s"])
            arm, after = reading(name, s0, a2, a3, a4)
            pred[arm] = pred.get(arm, 0) + 1
            last = ai_resume.top_level(d)[-1]
            logged = ARM.get((last["fn"], last["ra"]))
            if arm != logged:
                arm_bad += 1
            elif ai.seedval(last["s"]) != after:
                seed_bad += 1
            elif d["aix"] and ai.seedval(d["aix"]["s"]) != after:
                exit_bad += 1
            else:
                ok += 1
        print("REPLAY reading=%s melee=%d ok=%d arm_wrong=%d seed_wrong=%d exit_wrong=%d predicted=%s" % (
            name, len(melee), ok, arm_bad, seed_bad, exit_bad, {k: pred[k] for k in sorted(pred)}))
    # equality points, and how close the draws come to the tests
    eq = {"d1=33": 0, "d2=50": 0, "d3=0": 0}
    for p, d in melee:
        ds, _ = draws(ai.seedval(d["aid"]["s"]), 3)
        eq["d1=33"] += ds[0] == 33
        if ds[0] >= 33:
            eq["d2=50"] += ds[1] == 50
            if ds[1] >= 50:
                eq["d3=0"] += ds[2] == 0
    print("EQUALITY %s" % " ".join("%s:%d" % kv for kv in eq.items()))
    for p, d in other:
        tl = ai_resume.top_level(d)
        print("NOTMELEE %s fr=%d dist=%d calls=%s msm=%s" % (p, d["aid"]["fr"], ai.s32(d["aid"]["ctx"][5]), ["%x@%x" % (b["fn"], b["ra"]) for b in tl], [m[0]["cmd"][0] for m in d["msm"]]))
    fr = [d["aid"]["fr"] for p, d in decs]
    print("WINDOW frames=%d..%d (per process)" % (min(fr), max(fr)))


if __name__ == "__main__":
    main(sys.argv[1:])

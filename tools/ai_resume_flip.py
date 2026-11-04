#!/usr/bin/env python3
"""Plan 0052 Phase 2, `lane/p52c` review: which single branches can the resume model's comparison fail on?

    python3 -I tools/ai_resume_flip.py check LOG [LOG ...] [--rows 6,13] [--cap 60] [--per-path 4] [--out FILE]

`tools/ai_resume.py --controls` reverses every known branch at once, which says nothing about any one branch. Here each
known-value branch site that a decision's return-reaching states carry (`Result.br`, the tier table's `branches` column)
is reversed alone, at every occurrence in that decision, and the decision is compared again. Outcomes: `fail` (a mismatch:
the logged calls could tell), `same` (the decision still resumes: this comparison cannot tell, for this decision), `stop`
(the reversed path left the model; says nothing). A site's verdict over the row: `sep` when it fails at least one decision,
else `nosep`. `FREE`: the same over the decisions with no unknown-value branch step only. The sample is fixed: per row, up to --per-path decisions of each distinct path past the first boundary,
then evenly spaced decisions up to --cap, in log order. Also printed per row: known-value and unknown-value branch steps
and the calls with one offered (function, call site), over every resumed decision, and the words the model knew at the matched
calls (`slots` counts the six argument places of every call, used or not).
Stdlib, tools/ai.py and tools/ai_resume.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai_resume as R  # noqa: E402

PROPOSED = (6, 13, 21, 30, 37, 61, 64, 67, 89)
WEAK = (2, 9, 125)


class FlipMachine(R.Machine):
    """The model with the branch at one address reversed where its value is known (`Machine.invert`, for that site only).
    `known` and `unknown` count the branch steps run, by site."""

    def __init__(self, code, bnd, site=None, windows=R.THINK_WINDOWS):
        super().__init__(code, bnd, windows=windows)
        self.site, self.known, self.unknown = site, {}, {}

    def step(self, st):
        a = st.eip
        self.invert = a == self.site
        ins = self.code.at(a)
        out = super().step(st)
        if ins and ins[1].startswith("j") and ins[1] != "jmp":
            d = self.unknown if len(out) == 2 else self.known
            d[a] = d.get(a, 0) + 1
        return out


def path_of(res):
    return tuple((b["fn"], b["ra"]) for b in res.log[1:])


def sample(items, per_path, cap):
    """items: [(decision, base result)] in log order, resumed only."""
    seen, pick = {}, []
    for k, (d, r) in enumerate(items):
        p = path_of(r)
        if seen.get(p, 0) < per_path and len(pick) < cap:
            seen[p] = seen.get(p, 0) + 1
            pick.append(k)
    rest = [k for k in range(len(items)) if k not in set(pick)]
    n = cap - len(pick)
    if n > 0 and rest:
        step = max(1, len(rest) // n)
        pick += rest[::step][:n]
    return [items[k] for k in sorted(pick)]


def flip_decision(code, bnd, dec, base, windows=R.THINK_WINDOWS):
    """-> {site: 'fail' | 'same' | 'stop'} for the sites of base.br."""
    out = {}
    for site in sorted(base.br):
        r = R.check_decision(FlipMachine(code, bnd, site, windows), dec)
        out[site] = {"mismatch": "fail", "stop": "stop"}.get(r.status, "same")
    return out


class Words:
    """Wraps ai_resume.match: of the words of every offer that matched a logged call, how many the model knew and could fail
    on (`match` skips None and synthetic pointers), and how many calls had more than one (fn, ra) offered."""

    def __init__(self):
        self.known, self.slots, self.orig = 0, 0, R.match

    def __enter__(self):
        def wrapped(off, b):
            d = self.orig(off, b)
            if not d:
                ws = [off["ecx"], off["edx"]] + list(off["a"])
                self.slots += len(ws) + 2 + len(off["c"]) + 1
                self.known += sum(1 for v in ws if v is not None and not R.synthetic(v))
                self.known += sum(2 for v in off["s"][:1] if off["s"][0] is not None and off["s"][1] is not None)
                self.known += sum(1 for v in off["c"] if v is not None) + (off["c4"] is not None)
            return d
        R.match = wrapped
        return self

    def __exit__(self, *a):
        R.match = self.orig


def row_report(code, bnd, row, items, per_path, cap):
    L = []
    pick = sample(items, per_path, cap)
    sites = {}
    kn, un, nofork, calls, single = 0, 0, 0, 0, 0
    unk, amb = {}, {}
    wd = Words()
    free = set()
    for d, _base in items:                      # the census: every resumed decision
        m = FlipMachine(code, bnd)
        with wd:
            r0 = R.check_decision(m, d)
        kn += sum(m.known.values())
        un += sum(m.unknown.values())
        nofork += not m.unknown
        if not m.unknown:
            free.add(id(d))
        for a, c in m.unknown.items():
            unk[a] = unk.get(a, 0) + c
        for k, b in zip(r0.offers, r0.log):
            calls += 1
            single += k == 1
            if k > 1:
                amb[(b["fn"], b["ra"])] = amb.get((b["fn"], b["ra"]), 0) + 1
    per_dec = []
    for d, base in pick:                        # the flips: the sample
        res = flip_decision(code, bnd, d, base)
        nf = 0
        for a, v in res.items():
            e = sites.setdefault(a, {"fail": 0, "same": 0, "stop": 0, "bits": 0, "free_fail": 0, "free_n": 0})
            e[v] += 1
            if id(d) in free:
                e["free_n"] += 1
                e["free_fail"] += v == "fail"
            e["bits"] |= base.br[a]
            nf += v == "fail"
        per_dec.append((nf, len(res)))
    allbits = {}
    for _d, r in items:
        for a, b in r.br.items():
            allbits[a] = allbits.get(a, 0) | b
    sep = [a for a, e in sites.items() if e["fail"]]
    nosep = [a for a, e in sites.items() if not e["fail"]]
    two = [a for a in sites if allbits.get(a) == 3]
    L.append("FLIP %d decisions_resumed=%d sampled=%d paths_sampled=%d sites_in_row=%d sites_sampled=%d sep=%d nosep=%d two_way=%d two_way_sep=%d "
             "known_steps=%d unknown_steps=%d decisions_no_unknown_branch=%d calls=%d calls_one_offer=%d words_known=%d/%d sampled_with_a_failing_flip=%d" % (
                 row, len(items), len(pick), len({path_of(r) for _d, r in pick}), len(allbits), len(sites), len(sep), len(nosep), len(two),
                 sum(1 for a in two if sites[a]["fail"]), kn, un, nofork, calls, single, wd.known, wd.slots, sum(1 for nf, _n in per_dec if nf)))
    fs = [a for a, e in sites.items() if e["free_n"]]
    L.append("FREE %d decisions=%d sampled=%d sites=%d sep=%d nosep=%d two_way=%d two_way_sep=%d" % (
        row, len(free), sum(1 for d, _r in pick if id(d) in free), len(fs), sum(1 for a in fs if sites[a]["free_fail"]),
        sum(1 for a in fs if not sites[a]["free_fail"]), sum(1 for a in fs if allbits.get(a) == 3),
        sum(1 for a in fs if allbits.get(a) == 3 and sites[a]["free_fail"])))
    for a in sorted(sites):
        e = sites[a]
        L.append("FSITE %d %08x %s %s fail=%d same=%d stop=%d" % (
            row, a, "two-way" if allbits.get(a) == 3 else "one-way", "sep" if e["fail"] else "nosep", e["fail"], e["same"], e["stop"]))
    for a, c in sorted(unk.items(), key=lambda kv: -kv[1])[:12]:
        L.append("FUNK %d %08x unknown_steps=%d" % (row, a, c))
    for (f, ra), c in sorted(amb.items(), key=lambda kv: -kv[1])[:12]:
        L.append("FAMB %d %08x@%08x calls_with_several_offers=%d" % (row, f, ra, c))
    return L


def run(paths, rows, per_path, cap, code=None):
    import ai
    code = code or R.Code()
    bnd = R.bnd_set()
    base_m = R.Machine(code, bnd)
    by = {}
    for p in paths:
        for d in ai.parse(p)["dec"]:
            row = d["aid"]["ai"]
            if row in rows:
                r = R.check_decision(base_m, d)
                if r.status == "ok":
                    by.setdefault(row, []).append((d, r))
    L = ["FLIPRUN rows=%s per_path=%d cap=%d logs=%d" % (",".join(map(str, sorted(rows))), per_path, cap, len(paths))]
    for row in sorted(rows):
        if row in by:
            L += row_report(code, bnd, row, by[row], per_path, cap)
    return "\n".join(L) + "\n"


def main(argv):
    if not argv or argv[0] != "check":
        print(__doc__)
        return 2
    paths, out, rows, cap, per_path = [], None, set(PROPOSED + WEAK), 60, 4
    a, k = argv[1:], 0
    while k < len(a):
        if a[k] == "--out":
            out = a[k + 1]; k += 2
        elif a[k] == "--rows":
            rows = {int(x) for x in a[k + 1].split(",")}; k += 2
        elif a[k] == "--cap":
            cap = int(a[k + 1]); k += 2
        elif a[k] == "--per-path":
            per_path = int(a[k + 1]); k += 2
        else:
            paths.append(a[k]); k += 1
    text = run(paths, rows, per_path, cap)
    if out:
        open(out, "w").write(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

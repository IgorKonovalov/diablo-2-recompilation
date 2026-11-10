#!/usr/bin/env python3
"""Plan 0066 S1a, `lane/n66a`: what the kept AI logs show after a refused `MonAiMove` (catalogue reimplementation note
"A refused move can queue nothing", machinery B6).

    python3 -I tools/ai_move_refusal.py LOG [LOG ...] [--out FILE]

`MonAiMove` (0x005DEB60) is not a boundary of the AI logger; its command is: the logger writes `MSM0` at the entry of
`MonSetMode` (0x005A7C20) with the return address, and `MSM1` with its `EAX`, while a decision is open. A `MSM0` whose
`ra` is 0x005DEBCC is `MonAiMove`'s own command call. Each such call is attributed to the innermost boundary call open
in its decision (`AIB` without its `AIR`): the helper that reached `MonAiMove`, with its stack words `a`. A second
`MonAiMove` command inside the same helper call after a refused one (the ring's own move, 0x005DEC50) is printed apart as
`inner-of-<helper>`; its seed steps and return are the outer call's, not its own. For a refusal
(`MSM1` `eax` 0) the scan prints, per helper and flags word:

- the helper's own return (`AIR` `eax`);
- the LCG steps of the unit's seed from `MSM1` to the helper's `AIR` (`ai.reach`; the code after the command draws only
  under flag 2, at 0x005DEC15);
- the `MSM0` lines between that `MSM1` and the `AIR` (a nested command: the ring or the idle, 0x005DEC50 / 0x005DEC62);
- the unit's `AiCtl+0x08` flag `0x40` (the `ctl` bytes of `AID`) in this decision and at the unit's next decision;
- the low word of one LCG step from the `MSM1` seed, mod 100, against 70 (what 0x005DEC3F compares if the draw is
  taken), beside the steps counted;
- the frames from this decision to the unit's next `AID`.

The flags word is the helper's stack word read as `MonAiMove`'s `flags` only for helpers whose call passes it through
(`HELPER_FLAGS`: `MonAiWalkToUnit` 0x005DEC80 pushes its second stack word, `MonAiStepAway` 0x005DEFE0 pushes 4 when
its third word is non-zero and 0 otherwise, `MonAiWanderRing` 0x005DE200 pushes 0); any other helper is printed by
address with `flags=?`. Lines whose `MSM1` was never logged (the 600-call limit) are counted
apart. Stdlib and tools/ai.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import ai  # noqa: E402

RA_MOVE_CMD = 0x005DEBCC          # return address of MonAiMove's MonSetMode call (0x005DEBC7)
# helper -> the flags it passes to MonAiMove, from its stack words `a` (read from the code at the addresses named)
HELPER_FLAGS = {
    0x005DEC80: lambda a: a[1],                  # MonAiWalkToUnit: its second word pushed as the flags, 0x005DEC83
    0x005DEFE0: lambda a: 4 if a[2] else 0,      # MonAiStepAway: neg/sbb/and 4 of its third word, 0x005DF105..0x005DF112
    0x005DE200: lambda a: 0,                     # MonAiWanderRing: push 0, 0x005DE2F8
}


def ctl_flags(aid):
    c = aid.get("ctl")
    if not c or len(c) < 20:
        return None
    return int(c[18:20] + c[16:18], 16)       # u16 at +0x08, little endian


def scan(path):
    """-> list of refusal and acceptance records."""
    recs = []
    cur = {}                 # k -> {"aid": .., "open": [AIB], "pending": rec or None}
    units = {}               # u -> list of (line no, aid) in log order
    lines = []
    with open(path, errors="replace") as fh:
        for n, ln in enumerate(fh):
            tag, _, rest = ln.partition(" ")
            if tag not in ("AID", "AIB", "AIR", "MSM0", "MSM1", "AIX"):
                continue
            try:
                j = json.loads(rest)
            except ValueError:
                continue
            lines.append((n, tag, j))
    for n, tag, j in lines:
        if tag == "AID":
            k = j.get("n")
            cur_k = {"aid": j, "open": [], "msm": [], "n": n}
            # decisions are keyed by the AID line's own counter `n`; AIB/AIR/MSM carry it as `k`
            cur[k] = cur_k
            units.setdefault(j["u"], []).append((n, j))
        elif tag == "AIB":
            d = cur.get(j.get("k"))
            if d is not None:
                d["open"].append(j)
        elif tag == "MSM0":
            d = cur.get(j.get("k"))
            if d is None:
                continue
            for r in d["msm"]:
                if r["await_air"]:
                    r["nested"].append(j.get("ra"))
            if j.get("ra") == RA_MOVE_CMD:
                h = d["open"][-1] if d["open"] else None
                outer = [r for r in d["msm"] if r["await_air"] and h is not None and r["helper_n"] == h["n"] and not r["inner"]]
                d["msm"].append({"log": path, "line": n, "u": d["aid"]["u"], "row": d["aid"]["ai"], "th": d["aid"]["th"],
                                 "inner": bool(outer), "fr": d["aid"].get("fr"),
                                 "aid_n": d["n"], "ctl0": ctl_flags(d["aid"]), "helper": h["fn"] if h else None,
                                 "helper_ra": h["ra"] if h else None, "a": h["a"] if h else None,
                                 "helper_n": h["n"] if h else None, "eax": None, "s1": None, "air": None,
                                 "nested": [], "await_msm1": True, "await_air": False})
        elif tag == "MSM1":
            d = cur.get(j.get("k"))
            if d is None or not d["msm"]:
                continue
            r = d["msm"][-1]
            if r["await_msm1"]:
                r["await_msm1"] = False
                r["eax"], r["s1"] = j.get("eax"), j.get("s")
                r["await_air"] = True
        elif tag == "AIR":
            d = cur.get(j.get("k"))
            if d is None:
                continue
            if d["open"] and d["open"][-1]["n"] == j.get("b"):
                d["open"].pop()
            elif any(b["n"] == j.get("b") for b in d["open"]):
                d["open"] = [b for b in d["open"] if b["n"] != j.get("b")]
            for r in d["msm"]:
                if r["helper_n"] == j.get("b") and r["air"] is None:
                    r["air"] = {"eax": j.get("eax"), "s": j.get("s")}
                    r["await_air"] = False
        elif tag == "AIX":
            d = cur.pop(j.get("k"), None)
            if d is not None:
                recs += d["msm"]
    for d in cur.values():
        recs += d["msm"]
    for r in recs:                                    # the unit's next decision after this one
        nxt = [a for (ln, a) in units.get(r["u"], []) if ln > r["aid_n"]]
        r["ctl_next"] = ctl_flags(nxt[0]) if nxt else None
        r["dfr"] = (nxt[0]["fr"] - r["fr"]) if nxt and r.get("fr") is not None else None
    return recs


def flags_of(r):
    if r["inner"]:
        return None
    f = HELPER_FLAGS.get(r["helper"])
    if f is None or r["a"] is None:
        return None
    return f(r["a"])


def report(paths):
    allr = []
    for p in paths:
        allr += scan(p)
    L = ["MOVESCAN logs=%d move_commands=%d" % (len(paths), len(allr))]
    groups = {}
    for r in allr:
        f = flags_of(r)
        hk = "%08x" % r["helper"] if r["helper"] else "direct"
        if r["inner"]:
            hk = "inner-of-" + hk
        key = (hk, "?" if f is None else str(f),
               "nomsm1" if r["eax"] is None else ("refused" if r["eax"] == 0 else "accepted"))
        g = groups.setdefault(key, {"n": 0, "ret": {}, "steps": {}, "nested": {}, "c40_now": {}, "c40_next": {}, "rows": set(),
                                    "split70": {}, "dfr": {}})
        g["n"] += 1
        g["rows"].add(r["row"])
        if r["eax"] == 0:
            ret = r["air"]["eax"] if r["air"] else "noAIR"
            g["ret"][ret] = g["ret"].get(ret, 0) + 1
            st = "noAIR"
            if r["air"] and r["s1"] and r["air"]["s"]:
                st = ai.reach(ai.seedval(r["s1"]), ai.seedval(r["air"]["s"]), 16)
            g["steps"][st] = g["steps"].get(st, 0) + 1
            if r["s1"] and not r["inner"]:
                lo = ai.step(ai.seedval(r["s1"]))[0] % 100        # the draw at 0x005DEC15 if it is taken
                kk = "%s/%s" % ("lt70" if lo < 70 else "ge70", st)
                g["split70"][kk] = g["split70"].get(kk, 0) + 1
            dk = "%s/%s" % (st, "none" if r["dfr"] is None else str(r["dfr"]))
            g["dfr"][dk] = g["dfr"].get(dk, 0) + 1
            nk = ",".join("%08x" % x for x in r["nested"]) or "none"
            g["nested"][nk] = g["nested"].get(nk, 0) + 1
            for name, v in (("c40_now", r["ctl0"]), ("c40_next", r["ctl_next"])):
                kk = "none" if v is None else ("set" if v & 0x40 else "clear")
                g[name][kk] = g[name].get(kk, 0) + 1
    fmt = lambda d: ",".join("%s:%d" % (k, v) for k, v in sorted(d.items(), key=lambda kv: str(kv[0])))
    for key in sorted(groups):
        g = groups[key]
        L.append("MOVE helper=%s flags=%s %s n=%d rows=%s" % (key[0], key[1], key[2], g["n"], ",".join(map(str, sorted(g["rows"])))))
        if key[2] == "refused":
            L.append("  ret=%s seed_steps_msm1_to_air=%s nested_msm0=%s ctl40_this_decision=%s ctl40_next_decision=%s" % (
                fmt(g["ret"]), fmt(g["steps"]), fmt(g["nested"]), fmt(g["c40_now"]), fmt(g["c40_next"])))
            L.append("  draw_if_taken_low_mod_100/steps=%s steps/frames_to_next_decision=%s" % (fmt(g["split70"]), fmt(g["dfr"])))
    return "\n".join(L) + "\n"


def main(argv):
    out, paths, k = None, [], 0
    while k < len(argv):
        if argv[k] == "--out":
            out = argv[k + 1]; k += 2
        else:
            paths.append(argv[k]); k += 1
    if not paths:
        print(__doc__)
        return 2
    text = report(paths)
    if out:
        open(out, "w").write(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

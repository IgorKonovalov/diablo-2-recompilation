#!/usr/bin/env python3
"""Plan 0066 Phase 1, batch S5e part 3 (`lane/n66t`): combat README row 35's remainder, the `Align` = 1 exception of
sub_005A4F50_MonAttackStats' classic factors, as a recount of the kept S5a part 2 check (tools/sweep2_s5a2.py,
unchanged; its output workspace/logs/n66j/check-combat-p2.txt). No game, no emulator.

    python3 -I tools/combat_s5e3_mas.py <lists> --no-shield-log <names>     the same arguments as sweep2_s5a2.py

Runs sweep2_s5a2.py's whole check (every line it prints is printed again, so its totals must come out as before) and
adds, for each checked classic Nightmare/Hell call whose MonStats Align (+0x4C) is 1, the call's stats 19, 21, 22
under the reading without the exception (the same call's model with Align read as 0, so the ×10/12 and ×10/15
factors apply), and whether that reading gives other stats than the logged ones:
    COUNT s5e3 align1 call | <cls> d<d> mode <m> logged {19, 21, 22} | without-exception {19, 21, 22}
    COUNT s5e3 align1 separates (the factors would change a logged stat) | True/False | n
and the same separation count for the Align != 1 calls (the factors' own control, which must all be True or be
named). Stdlib only. Read-only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import sweep2_s5a2 as P2  # noqa: E402


class S5e3(P2.S5b):
    def mas2(self, ev):
        before = self.chk2.get("mas-stats", (0, 0))[0]
        super().mas2(ev)
        if self.chk2.get("mas-stats", (0, 0))[0] == before:
            return                                   # not a checked-and-matched call
        u, mode, g = ev.head["u"], ev.head["mode"], ev.head["g"] or {"diff": 0, "exp": 1}
        cls = u["c"]
        d, exp = g.get("diff", 0), g.get("exp", 1)
        if exp or not d or cls in P2.HIRE:
            return
        st0 = u.get("st") or {}
        st1 = ev.lines[-1][1].get("st") or {}
        lvl, n = st0.get("12", 0), st0.get("100", 0)
        seed = P2.C.sd_parse(u["s"])
        al = self.T.ms[cls][0x4C]
        got = tuple(st1.get(str(s), 0) for s in (19, 21, 22))
        orig = self.T.ms[cls]
        flip = bytearray(orig)
        flip[0x4C] = 0 if al == 1 else 1
        self.T.ms[cls] = bytes(flip) if isinstance(orig, bytes) else flip
        try:
            alt, _, _ = self.mas_model(cls, lvl, d, 1, mode, seed, exp, n, align0=True)
        finally:
            self.T.ms[cls] = orig
        altv = tuple(alt[s] for s in (19, 21, 22))
        if al == 1:
            self.c2("s5e3 align1 call", "%d d%d mode %d logged %s | without-exception %s" % (cls, d, mode, got, altv))
            self.c2("s5e3 align1 separates (the factors would change a logged stat)", altv != got)
        else:
            self.c2("s5e3 align!=1 separates (the exception would change a logged stat)", altv != got)


if __name__ == "__main__":
    P2.S5b = S5e3
    sys.exit(P2.main(sys.argv[1:]))

"""Backlog 2026-11-15 s5a-result-bit-0x4000 (lane/fur): which missile rows deliver result bit 0x4000.

Usage:
  python3 -I tools/fur_bit4000.py <list> [...] [--no-shield-log N,...]   # as tools/sweep2_s5a.py combat

Reruns tools/sweep2_s5a.py's S5 checker (itself tools/combat.py's Checker, unchanged) over the same run lists, and for
every missile (md) event with an AD0 line counts the AD0 result word by the event's missile row (`mrec`), with the
row's Missiles record byte +0x04 bits 6 (GetHit) and 7 (SoftHit) and its KnockBack byte (+0xAE). One line per key:
  BIT4000 <result> row=<mrec> gethit=<0|1> softhit=<0|1> kb=<n> | <count>
Ends with `BIT4000 total events=<n> with_4000=<n> mismatches=<n>`.
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import sweep2_s5a as S5A  # noqa: E402
import combat as C  # noqa: E402


class B(S5A.S5):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.b4 = collections.Counter()

    def post(self, ev, missile):
        super().post(ev, missile)
        if not missile:
            return
        ad0 = [x for t, x in ev.lines if t == "AD0"]
        if not ad0:
            return
        res = S5A.s32b(bytes.fromhex(ad0[0]["p"]), 4) & 0xFFFF
        m = ev.head["mrec"]
        rec = self.T.mi[m] if 0 <= m < len(self.T.mi) else None
        gh = (rec[4] >> 6) & 1 if rec else -1
        sh = (rec[4] >> 7) & 1 if rec else -1
        kb = rec[0xAE] if rec else -1
        self.b4[(res, m, gh, sh, kb)] += 1


def main(argv):
    lists, nsl = [], ()
    k = 0
    while k < len(argv):
        if argv[k] == "--no-shield-log":
            nsl, k = nsl + tuple(argv[k + 1].split(",")), k + 2
        else:
            lists.append(argv[k])
            k += 1
    paths = []
    for lst in lists:
        for ln in open(lst):
            ln = ln.strip()
            if ln:
                paths.append(os.path.join(S5A.ROOT, ln) if not os.path.isabs(ln) else ln)
    X = B(C.Tables(), no_shield_logs=nsl)
    for p in paths:
        X.run(p)
    tot = with4 = 0
    for (res, m, gh, sh, kb), n in sorted(X.b4.items()):
        tot += n
        if res & 0x4000:
            with4 += n
        print("BIT4000 0x%04x row=%d gethit=%d softhit=%d kb=%d | %d" % (res, m, gh, sh, kb, n))
    print("BIT4000 total logs=%d events=%d with_4000=%d mismatches=%d" % (len(paths), tot, with4, len(X.mism)))
    return 0 if not X.mism else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

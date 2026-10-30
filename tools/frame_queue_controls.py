#!/usr/bin/env python3
"""Extra negative controls for run:2026-10-30-frame-emu-2's `cancel` family (plan 0055 P1.2 review).

The kept run's own control for `cancel` (kind only) separates 3 of its 150 cases. This script scores four wrong
readings of the cancel functions against the KEPT emulator output (workspace/logs/r55b/emu/cancel.out, nothing is
re-run): for each, how many cases it separates from the model of frame/0002 § 2.3 and how many of those the kept output
still matches (a wrong reading must match none).

  cancel-kindonly   UNIT_CancelEvents ignores `a` (the kept run's control)
  always-a          UNIT_CancelEvents compares `a` even when the argument is 0 (no zero shortcut)
  cb-zero           UnitCancelEventsByCb treats a callback argument of 0 as "any callback"
  reverse           the chain is walked oldest first instead of from Unit+0xDC (newest first)

Not separable by any memory dump, so not scored: "the chain's next is read before the free" (EventFree leaves +0x24).

Usage: python3 -I tools/frame_queue_controls.py [--dir workspace/logs/r55b/emu] [--tag r55b]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import frame_queue_emu as F  # noqa: E402

READINGS = ("cancel-kindonly", "always-a", "cb-zero", "reverse")
_orig_cancel = F.Model.cancel


def _cancel(self, unit, kind, a, by_cb=False):
    if self.neg in (None, "cancel-kindonly"):
        return _orig_cancel(self, unit, kind, a, by_cb)
    m = self.m
    recs, rec = [], (m.r32(unit + 0xDC) if unit else 0)
    while rec:
        recs.append(rec)
        rec = m.r32(rec + 0x24)
    if self.neg == "reverse":
        recs.reverse()
    for rec in recs:
        if m.r8(rec) != kind & F.M32:
            continue
        if by_cb:
            match = a == m.r32(rec + 0x2C) or (self.neg == "cb-zero" and a == 0)
        elif self.neg == "always-a":
            match = m.r32(rec + 0x14) == a
        else:
            match = a == 0 or m.r32(rec + 0x14) == a
        if match:
            self.free(rec)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=F.DEFAULT_DIR)
    ap.add_argument("--tag", default="r55b")
    a = ap.parse_args(argv)
    F.Model.cancel = _cancel
    cases = F.GEN["cancel"](random.Random("%s-cancel" % a.tag))
    outs, _ = F.read_out(os.path.join(a.dir, "cancel.out"))
    if len(outs) != len(cases):
        print("FR55BC cancel case count %d != %d" % (len(outs), len(cases)))
        return 1
    allok = True
    for neg in READINGS:
        sep, passed, byop = 0, 0, {}
        for c, o in zip(cases, outs):
            mw, ow, _ = F.apply_model(c)
            mn, on, _ = F.apply_model(c, neg)
            if any(mw.region(x, n) != mn.region(x, n) for x, n in F.REGIONS) or ow != on:
                sep += 1
                byop[c["op"][0]] = byop.get(c["op"][0], 0) + 1
                ok, _ = F.compare(c, o, neg)
                passed += ok
        allok &= passed == 0
        print("FR55BC cancel neg=%s separating=%d passed=%d by_op=%s"
              % (neg, sep, passed, ",".join("%s:%d" % kv for kv in sorted(byop.items()))))
    print("FR55BC result=%s" % ("ok" if allok else "FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

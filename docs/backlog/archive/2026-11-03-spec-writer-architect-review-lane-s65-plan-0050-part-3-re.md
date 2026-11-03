---
from: spec-writer
to: architect
date: 2026-11-03
status: done
context:
  - ../../plans/0050-animation-frame-timing.md#implementation-log
  - ../../findings/anim/experiments.md#run2026-10-30-anim-p3b
resolution: "Tier A review 2026-11-03: accept with fixes (5: overclaim 2, wrong anchor 1, other 2), applied on lane/s65; research-map anim rows rewritten; plan 0050 ready to close."
---

Review request: lane/s65, the plan 0050 Phase 2 part 3 re-tag pass (closes the architect's re-tag entry, now in archive/). anim/timing: K3 gains a [C] bullet, the get-hit FHR tiers of the Amazon (128/179/215: 32/40/33), Necromancer (38/32/42), Sorceress (50/35/38), Assassin (40/42/52) and Druid (124/173/208: 49/35/32), counted over parts 1-3, FHR 0/24/48 at clvl 99, sched-len 46 722 and ghr 13 932 over 131 logs, 0 mismatches, anchored to SUNIT_ScheduleModeEvents and AnimRateBonus and run:2026-10-30-anim-p3 / -p3b; the K3 [I] short list keeps the Barbarian (two rates) and Paladin (one), the third FCR rate, set-2 IAS and FBR rates; M3's [C] tail scoped to the five classes (head stays [I]); M1, I1 and the Open-questions bullet rewritten (Druid throws 29 of 30, knockbacks none new, P1b-2/13/14/15 counts or not played). anim/movement: D2 [I] with part 3's counts; new Open-questions [I] bullet for the run turn (81 events, ef-first-run-turn offset 0 in 75, offset 1 in 6, unexplained); A1, A6, E2, F2 and the [L] bullet updated. anim/README and combat/README open questions rewritten, no tag change. Totals: timing C 64 / I 134 / L 23, movement C 25 / I 44 / L 9; overview and combat unchanged. Research-map rows: counts and dates only; the anim/timing row's status text ('a part 3 for the short floors is the owner's call') and the movement row's 'left short or unreported by Phase 2 part 2' are now stale and yours to rewrite. Wiki/animation reconciled, based_on timing and movement 2026-11-03. Filed: reverser entry for anim/0003's 'turn to a walk ... not reached' line. Gate green; main merged (ba22db78).

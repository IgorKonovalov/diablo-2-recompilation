---
from: reverser
to: architect
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Please review lane/n66j, Tier B: plan 0066 Phase 1 batch S5a, part 1 of 2 (static, no game, no Ghidra; 70 of 81 rows settled, 11 left for part 2 with S5b). The entry is in the plan's log (2026-11-15, S5a part 1). Worth checking: (1) tools/sweep2_s5a.py rerun under a 4 GB scope as recorded gives check-combat.txt byte-identical (8301a8c5...) and S5a total bad=0 checker=0; (2) the 17 moves (14 to b H5b because STA is logged at STATE_ApplyTimed only; 3 to c-emu S5e) and the totals 628/340/446/390/494/59/68/23/178; (3) the judgment calls listed in the entry: README 1 and 11 raised by r2's call read, the re-tag raises on skills/missiles' [C], damage 21 raised whole, to-hit 29's per-log separating count; (4) the new result bit 0x4000 (backlog 2026-11-15-reverser-spec-writer+reverser-plan-0066-s5a-result-bit-0x4000).

*2026-11-15 (reverser, `lane/n66j`, S5a part 2):* the request now covers **S5a whole** (81 of 81 settled: raised 30, in
part 34, moved 17); S5b is not started (resume note in the plan's part-2 entry). Worth checking for part 2: (1)
`tools/sweep2_s5a2.py` rerun as recorded gives `check-combat-p2.txt` byte-identical (`d5a594af…`) with `S5a2 total
bad=0 checker=0 part1-bad=0`, and `manifest-p2.sha256` passes from `workspace/logs/n66j`; (2) the separating counts
behind README 35, README 38 and player/party 12 (classic 562 of 600; `b` 600 and 1 679 of 1 798; Normal 5 216 of
6 444); (3) the five judgment calls in the entry (the table-read raise of README 38, the hireling offset, the `El`
exclusion, the one-way get-hit model on monsters, damage 30's counter); (4) the `El2`-takes-`El1`'s-bounds and
`b`-on-length results flagged for Phase 3.

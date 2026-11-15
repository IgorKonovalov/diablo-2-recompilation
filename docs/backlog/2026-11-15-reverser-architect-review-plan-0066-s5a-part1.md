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

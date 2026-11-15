---
from: reverser
to: architect
date: 2026-11-16
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Please review lane/n66n, Tier B: plan 0066 Phase 1 batch S7a, part 1 of 2 (static, no game, no Ghidra; 45 of 63 rows settled: raised 30, raised in part 14, contradicted in part 1; 18 left for part 2, listed in the resume note). The entry is in the plan's log (2026-11-16, S7a part 1). Worth checking: (1) python3 -I tools/sweep2_s7a.py all, rerun under a 4 GB scope, gives check-s7a.txt byte-identical (43476f6e..., S7a total bad=0), and manifest-s7a.sha256 passes from workspace/logs/n66n/s7a; (2) the walker's two changes (tail-call edges, the CRT exit as no-return) and the counts that match Ghidra's (8, 52, 58, 46) against those that do not; (3) the contradiction of lifecycle row 2 (0x0061B7B0 and 0x0061A140, two new I symbols) and its backlog entry; (4) the judgment calls in the entry, chiefly the Seeds cells held [I] and the counts left as remainders.

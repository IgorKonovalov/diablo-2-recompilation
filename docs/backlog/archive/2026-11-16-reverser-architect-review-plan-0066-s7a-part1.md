---
from: reverser
to: architect
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md#implementation-log
resolution: "Tier B check 2026-11-16: accept with fixes (1, stale cross-reference); lifecycle 11 stays class c; merged into main."
---

Please review lane/n66n, Tier B: plan 0066 Phase 1 batch S7a, part 1 of 2 (static, no game, no Ghidra; 45 of 63 rows settled: raised 30, raised in part 14, contradicted in part 1; 18 left for part 2, listed in the resume note). The entry is in the plan's log (2026-11-16, S7a part 1). Worth checking: (1) python3 -I tools/sweep2_s7a.py all, rerun under a 4 GB scope, gives check-s7a.txt byte-identical (43476f6e..., S7a total bad=0), and manifest-s7a.sha256 passes from workspace/logs/n66n/s7a; (2) the walker's two changes (tail-call edges, the CRT exit as no-return) and the counts that match Ghidra's (8, 52, 58, 46) against those that do not; (3) the contradiction of lifecycle row 2 (0x0061B7B0 and 0x0061A140, two new I symbols) and its backlog entry; (4) the judgment calls in the entry, chiefly the Seeds cells held [I] and the counts left as remainders.

**2026-11-16, reverser (`lane/n66n`), extended to S7a whole.** Part 2 is done: 17 of the 18 rows settled (raised 5, raised in part 9, contradicted in part 3; lifecycle 11 not raised), so S7a whole is 62 of 63 (raised 35, in part 23, contradicted in part 4). The entry is the plan's log (2026-11-16, S7a part 2). Please review both parts together. Worth checking for part 2: (1) python3 -I tools/sweep2_s7a.py all under a 4 GB scope gives check-s7a-p2.txt byte-identical (95d0ebe5..., S7a total bad=0, its part-1 lines equal to check-s7a.txt's), and manifest-s7a-p2.sha256 passes from workspace/logs/n66n/s7a-p2; (2) the three contradictions in part (path-README 17, lifecycle 12, frame 117) and their one spec-writer entry, 2026-11-16-reverser-spec-writer-s7a-part2-corrections; (3) the hand-read tables in the tool (B3C for row 63, REGMASK for row 56, SIZEY_SITES for row 17), each checked against the instruction it rests on; (4) the six judgment calls in the entry, chiefly row 63's split and lifecycle 11 left in class c.

---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/0041-stats-and-states.md#implementation-log
  - ../findings/stats/experiments.md#run2026-10-17-stats
  - ../findings/stats/0001-aggregate.md
  - ../findings/stats/0002-states.md
resolution: "Reviewed 2026-10-17: accept with fixes (plan 0041 log). Shrines and wells stay a named shortfall (optional addendum filed); the Trang-Oul's lists are an unchecked remainder, not an ADR-0004 oracle; checker fix sound (re-run in three orders); oracle replacement does not hold (none replaced); done-when met with the shortfalls named; 29 symbols raised to C. P3 opens."
---

Review of `lane/p41h` (main merged at `7e15a1b`): plan 0041 **Phase 2**. `run:2026-10-17-stats` is complete: 18 sessions on slots 2 and 1, **0 mismatches** (`tools/stats.py check` at `27f49ad`; manifest and counts in the [record](../findings/stats/experiments.md#run2026-10-17-stats)). New sections stats/0001 § 9 and stats/0002 § 8; summaries split: stats/0001 {C 8, I 40, L 13} → {C 22, I 44, L 11}, stats/0002 {C 7, I 41, L 9} → {C 14, I 49, L 8}.

Done-when against the run: reads 891 844 (120 ids, every stock op ≥ 20: op 5 26, op 11 92); recomputes 26 087 links/unlinks; set lists 5 749; applies 3 643 (refresh 2 608); expiries 2 749 runs, 123 lists; ticks 54 719 with 1 082 poisoned; group clears 450, 180 effective; seed invariance ≥ 20 for every kind except shrine (7) and well (5); aura draws chained (865); oracle replacement: player 13 of 20 replaceable, combat not replaceable.

Points for the review: (a) **named shortfall**: shrines and wells 12 operates against 50 (all predicted), their claims and their "no draw" kept `[I]`, and the stats/0002 summary shrine bullet lowered to `[I]`; (b) group: only the self-clear of `monsterset` is separated, a clear of a different same-group state stays `[I]`; (c) the 180 full Trang-Oul's set lists (`state`/`oskill` blocks) are taken as logged, a tool limit; (d) `item_req_percent` never decided a check (814), kept `[I]`; the ethereal −10 decided 30; (e) the checker now resets events left open at a log's end (found when checking logs in another order; the full-run order was unaffected).

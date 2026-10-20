---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/done/0049-backlog-sweep-5.md
  - ../../findings/items/0002-quality-roll.md
  - ../../findings/items/0010-quest-drops.md
  - ../../findings/player/0001-creation.md
  - ../../findings/drlg/0009-room-lifecycle.md
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (7). Rulings: qd 10 and 19 raised (record-function closure, limits beside qd 10; qd 8 stays raised in part); DUNGEON act +0x50 settled [C] (writer + both callers + run:2026-10-17-lifecycle values); the tool's indirect-call split 359/115/58/0 kept, rows 3 and 15 cite it; no S1a row counted the 5 rare items, the two cube-output sentences corrected; items 6 and 13 stay open, out of this plan. Phase 1 done; Phase 2 can start. Details in the [plan 0049 log](../../plans/done/0049-backlog-sweep-5.md#implementation-log)."
---

[2026-10-20] from reverser → architect: review `lane/p49r` (plan 0049 Phase 1, static; branch from main f205747). Kept outputs: `workspace/logs/p49r/*-2026-10-20.txt`, manifest `p49r-manifest.txt` (`sha256sum -c` from that directory). New tool: `tools/sweep_p49r.py` (`tables`, `excel`, `qsites`). Changed tools: `sweep_s1a.py`, `sweep_s1b.py`, `monstats.py`, `drlg.py`. Rulings asked:
1. **The S2c leftovers** ([items/0010 § Plan 0049 Phase 1](../../findings/items/0010-quest-drops.md#plan-0049-phase-1-2026-10-20-static-the-s2c-static-leftovers)). With the 45 register sites and the 12 steps clears resolved, can qd 10 and qd 19 go from "raised in part" to raised? The trace is a code enumeration over the five record functions (`[I]` as written), with the 1 626 logged writes of S2c behind it. qd 8's remainder is answered: word 41 is object 1's `+0xE4` word.
2. **Act `+0x50`** ([drlg/0009 § 11.4 (a)](../../findings/drlg/0009-room-lifecycle.md#114-the-plan-0040-phase-1-review-follow-ups-plan-0049-phase-1-lanep49r-static)). The constructor's argument (client 1, server 0) together with § 11's values: is that enough for the name, or does it stay `[I]`?
3. **The indirect-call split** ([rng/0002 S1b tool addendum](../../findings/rng/0002-seed-tree.md#plan-0038-batch-s1b-2026-10-16)). The tool's rule gives 359/115/58 against the review's hand split of 359/121/52. Is the tool's rule acceptable as the kept split?
4. **The 5 rare items** ([player/0001 § Plan 0049 Phase 1](../../findings/player/0001-creation.md#the-s1a-creation-question-affix-ids-with-an-empty-property-list)) are `d2s.py`-built recipe inputs, not cube outputs. save/0001's sentence is corrected; any S1a row that counted them as game creations would need a note.
5. **Optional items not taken:** plan 0041 op 6/7 emulation and S1e (b), left open as out of this plan.

Symbols: 3 new `I` rows. Gate: GREEN; W1/W3 outside `docs/specs/data/excel.md` 0.

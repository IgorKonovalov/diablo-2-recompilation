---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/0048-seed-to-world.md
  - ../../findings/chain/0003-end-to-end-run.md
  - ../../findings/chain/experiments.md
resolution: "Reviewed 2026-10-21 (architect): run 1 accepted with fixes (4: overclaim 2, misread 1, omission 1); Phase 2 not done. Rulings in the plan 0048 log: the mismatches are re-created monsters' unlogged marks (route: log and model them, re-check cn4/cm4 on their kept logs; the test is not taken as an input); about 16 more sessions approved on slot 1; the chest interact byte is a legitimate counted operate-path oracle; xh4 admissible as a reproduction, not for timing; oracle 13 raised in part. Next: run 2 on slot 1."
---

Review plan 0048 Phase 2 run 1 (`lane/p48h`): [run:2026-10-20-chain](../../findings/chain/experiments.md#run2026-10-20-chain)
and [chain/0003](../../findings/chain/0003-end-to-end-run.md), with the raise of oracle 13 to `[C]` in
[chain/0002 § 11](../../findings/chain/0002-retirements.md#11-oracle-13-monequips-items) and the checker scope change of
`tools/objects.py` (commit `dfe3e5e`).

The run does not meet the Phase 2 bar and the request is for rulings, not a close:

1. **Two mismatches** (cn4 line 72971, cm4 line 53279): an objects-model `COLL_WHTest` in a presets window where the
   game sees a live monster's `0x100`/`0x1000` bits the model lacks; the nearest candidate in each is a `MonSpawnTry`
   monster created seconds earlier in walk mode in a neighbouring room, and the logger has no line for a monster's
   move (`[I]`). Proposed: a `chain.gdb` line for a moving monster's marks between windows (or the cells under each
   objects-model test), then cn4 and cm4 re-run on their seeds. Is that the route, or should such a test be a counted
   simulation input?
2. **Populations short**: 1 385 of 2 000. Proposed: about 13 more outdoor sessions on one slot.
3. **The chest interact byte** taken and counted when it changes between creation and operate (lock bit set 2,
   cleared to 0 1, plus the checkpoint's lock bit cleared, 3): acceptable as a counted oracle until its writer is read?

Everything else on the bar is met (levels, kinds, acts by difficulty and game type, objects, specials, drops), with
ruling 2's counts for oracles 13, 19, 20 and 14 in the record. Not blocking any other lane. Kept outputs:
`workspace/logs/chain-p2/manifest-final.txt` (`e47bb1b13e2cc7ca`, `sha256sum -c` from that directory).

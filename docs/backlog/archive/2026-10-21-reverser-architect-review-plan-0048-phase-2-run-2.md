---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/0048-seed-to-world.md
  - ../../findings/chain/0003-end-to-end-run.md
  - ../../findings/chain/experiments.md
resolution: "Reviewed 2026-10-21 (architect): accept with fixes (4: omission 2, overclaim 1, misread 1); Phase 2 closed on 37 logs, 0 mismatches, 2 189 populations; Phase 3 released to the spec-writer. Plan 0048 log."
---

Review plan 0048 Phase 2 run 2 (`lane/p48r2`): [run:2026-10-21-chain2](../../findings/chain/experiments.md#run2026-10-21-chain2)
and [chain/0003](../../findings/chain/0003-end-to-end-run.md) as updated, with the re-creation marks of commit `53ffb95`
(`tools/gdb/collision.py` `CMR0`..`CMRX` scopes, `tools/objects.py` `recreation`, `--cf recreation-off`), and rule on
the Phase 2 close.

What the run claims, for the review to check:

1. **0 mismatches**: `tools/chain.py check --o20` over run 1's 28 logs and run 2's 9, `chain: 37 logs, 0 sub-checks
   failed`, each log alone the same; the Phase 1 world logs, 62, 0 failed, summary equal to run 1's but four
   re-creation lines. cn4 and cm4 pass on their kept logs; `--cf recreation-off` restores exactly their run-1 mismatches.
2. **The bar's counts** from the 37 passing logs: 2 189 populations, 176 levels with every kind and every act of each
   game type in each difficulty, 13 056 objects, 63 + 162 special packs (217 mods rolls), 1 314 drops with an item.
3. **Re-creation marks `[C]`** for the sequences compared line for line (1 903: 1 729 alive, 166 `deadCol` 0, 8
   `deadCol` 1); the call path stays `[I]` (chain/0003 § 2). The dead sequence was corrected from r2-xn1's log; the
   other eight logs' 140 dead cases were not its evidence.
4. **Open**: the chest interact-byte writer (ruling 3) not read, left for Phase 3's *Open questions*.

Not blocking any other lane. Kept outputs: `workspace/logs/chain-p2/manifest-r2-final.txt` (`e1d9e622a85995f5`,
`sha256sum -c` from that directory).

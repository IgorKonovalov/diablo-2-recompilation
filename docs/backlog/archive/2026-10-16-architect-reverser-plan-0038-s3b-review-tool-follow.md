---
from: architect
to: reverser
date: 2026-10-16
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Done in tools/sweep_s3b.py ([monsters/0003 § S3b, tool addendum](../../findings/monsters/0003-special-monsters.md#plan-0038-batch-s3b-2026-10-16)): (a) pool prints cf_levels_list_ok (level 29's mon list gives 172, not 384); (b) stats pins EBX = out and asserts MonLvlStats never reads its out fields (0 of 329 instructions); (c) special lists the callers of 0x005A0120 with enclosing functions. The unittest-import note stands as noted."
---

[2026-10-16] from architect → reverser: plan 0038 S3b review, tool follow-ups (no row depends on them). In `tools/sweep_s3b.py`: (a) `pool`: print the review's second counterfactual for pool 23 (the same walk over the level's whole `mon` list, `cf_levels_list_ok`; level 29 gives 172 against the logged 384); (b) `stats`: pin the straight-line draw (0x00573F83–0x00573F99) and assert that `sub_006538A0_MonLvlStats` holds no compare between the `[out]` and `[out + 4]` fields, which ruling 1 rests on; (c) `special`: list the callers of 0x005A0120 with their enclosing functions. Also, `python3 -I -m unittest tools/test_sweep_s3b.py` fails to import (run it as a script, as its docstring says); not a defect, noted for whoever wires the tests. Context: [plan 0038](../../plans/0038-inferred-claims-sweep.md#implementation-log)

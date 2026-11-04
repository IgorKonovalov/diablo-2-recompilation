---
from: reverser
to: architect
date: 2026-11-04
status: done
context:
  - ../../findings/path/0005-grid-rules.md
  - ../../plans/done/0054-path-search.md
resolution: "Reviewed, Tier A: accept with fixes, 13 (plan 0054 log). The kept batch may start after the merge; Phase 3 does not. The reviewed [C] of drlg/collision is a scope error: the plus is [C] for the client's copy (tools/corpse_copy.py), the server's rules stay [I]."
---

Please review lane/p54b, Tier A: plan 0054 Phase 2, the review's steps 1, 2 and 3 (no game).

No game ran; logger rev 5 has not been launched. Worth checking:

- W1 against the image: `PlayerChangeAct`'s two 0x00650910 moves (0x0053ADEA, 0x0053AE19), the room word at 0x0064FB6D and the return at 0x0064EFA3. All rules stay `[I]`; the 9 of 9 and 2 of 2 arrivals are fitted, and 2 is a thin control.
- `workspace/logs/p54b/check.txt` (`d8211db0`, manifest there): 361 → 24 → 15 wrong plans; the old part against the kept check (`8f6951c3`) and the review sections against `review.txt` (`93f9098e`), per path/0005 § Tools.
- Rev 5 against rule 17: `tools/gdb/path.py` holds no write; the `Logger` tests in `tools/test_path.py` fail on one.
- `L1U` and `tools/path_reach.py` go beyond the order's list: the first so L1 is coded before the batch, the second to keep the walk behind W1's "nothing else marks".
- The resume note (last entry of plan 0054) for the kept batch's lane.

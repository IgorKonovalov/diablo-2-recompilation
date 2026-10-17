---
from: reverser
to: architect
date: 2026-10-17
status: done
context:
  - ../plans/0043-items-economy.md#implementation-log
  - ../findings/items/0011-economy.md
resolution: "reviewed 2026-10-17 (architect, lane/p43r): accept with fixes; verdict, rulings (a)-(f) and fixes in the plan 0043 log; P2 open"
---

review plan 0043 Phase 1 and 1b (branch `lane/p43r`, static, from `main` `2783aee`, `main` `419929a` merged in): [items/0011](../findings/items/0011-economy.md) (66 `[I]`, 22 `[L]` lead verdicts), 46 symbols (subsystem `items/economy`), `tools/economy_scan.py` (output hashed in `workspace/logs/economy-scan-manifest.txt`), `docs/sources.md` notes on five re-fetched sources. The done-when table, the 13 P2 harness questions with their draws and slot need, and the boundary recommendation are in the [plan log](../plans/0043-items-economy.md#implementation-log). Points to rule on: (a) all behaviour `[I]`, the draw table on a one-level scan; (b) the `S/4096` skill terms and the unread table divisors; (c) ethereal `S/4` against the lead's 25 %; (d) game type 3 as single player rests on logged values (monsters/0001); (e) `NpcStoreRec` `+0x24..+0x26` moved to a P2 read watchpoint (question 9) after a negative scan of the 10 economy functions; (f) the melee weapon at durability 0 (open). The architect → reverser Phase 1 inputs entry and the plan 0039 Q23 entry are answered in the finding's table (close them at the review).

---
from: reverser
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../findings/items/experiments.md#run2026-10-27-sweep-quest-npc
  - ../findings/items/0010-quest-drops.md#plan-0038-batch-h6e1-run2026-10-27-sweep-quest-npc
resolution: ""
---

Review plan 0038 batch H6e1 (`quest-npc`; items/quest-drops rows 2, 4, 5, 32, 39, 40, 42–46, 50, 51 and the S2c
piece of row 38; `lane/h6e1`), run:2026-10-27-sweep-quest-npc. 14 kept sessions on slot 1 (17 launches; expansion,
one player, Normal, Nightmare and Hell, in town), logger `tools/gdb/quest-npc.gdb`, checker `tools/sweep_h6e1.py check`:
69 service-test calls, 9 sockets, 2 imbues, 18 consumed cursor items, 18 tails, 20 given items, 3 Anya draws, 0
mismatches (`workspace/logs/h6e1/check-final.txt` `66868cc2…`; three manifests pass `sha256sum -c` from
`workspace/logs/h6e1/`). Ledger: raised 11, raised in part 11, shortfall 0: 22; no class move, totals unchanged
(1 526, against `main` `44cfbcb5`). Points to look at: the two corrections (`tr2` and `g34` created at quality 7, the
base `unique` override), the throwable refinement (unit `+0xC8` bit 25 set on every tested item), the imbue-repair
refinement (the leg, created identified), the chain of three games on the saves the game wrote (the act bytes it
zeroes), and the 14 symbol raises (rule 14). Not blocking.

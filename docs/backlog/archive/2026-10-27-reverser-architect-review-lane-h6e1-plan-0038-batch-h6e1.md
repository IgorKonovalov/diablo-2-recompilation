---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../../findings/items/experiments.md#run2026-10-27-sweep-quest-npc
  - ../../findings/items/0010-quest-drops.md#plan-0038-batch-h6e1-run2026-10-27-sweep-quest-npc
resolution: "Reviewed 2026-10-27: accept with fixes (7: overclaim 1, under-claim 2, miscount 1, omission 2, stale cross-reference 1). The imbue-repair [C] was re-anchored (the leg plus economy2's cap; ItemCanRepair's ethereal half is [I]). ITEMS_CheckFlags and ItemGetFlags were raised, 17 I to C in all. qd 38 is raised under S2c. Rulings, fixes and totals (unchanged, 1 526) are in the plan 0038 log. The spec-writer entry is released, and items/quest-drops is ready for Phase 3."
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

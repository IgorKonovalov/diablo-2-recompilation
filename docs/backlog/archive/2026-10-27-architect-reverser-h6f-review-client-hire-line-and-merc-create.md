---
from: architect
to: reverser
date: 2026-10-27
status: done
context:
  - ../../findings/hirelings/0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings
  - ../../plans/done/0038-inferred-claims-sweep.md#implementation-log
resolution: "Read (plan 0063 P2a, lane/n63r): (1) the client's menu (sub_004B66B0_ClientNpcMenuOpen, gate table g_ClientNpcMenuQuestGates, reset per interaction) offers the hire line exactly when HIRE_Hire's gates pass, for every value of the inputs both read (stat 12 >= 8 or word 2 bit 0 for Kashya; word 36 bit 0 for Qual-Kehk); (2) PlayerPlaceInAct's list is the inventory's corpse list, whose three writers add flag 1 and word 0, so the MERC_Create branch (flag 0, word non-zero) is reached by no stock writer. Ruling inputs for rows 17, 18, 21 and 29 in [hirelings/0001](../../findings/hirelings/0001-hirelings.md#plan-0063-phase-2a-static-lanen63r-2026-11-10); the rulings are the architect's."
---

From the `lane/h6f` review (plan 0038 batch H6f, hirelings). Two static reads (objdump or Ghidra, no harness), each the reach behind a ruling: (1) **the client test that drops the hire line** from Kashya's menu below level 8 with Act I quest word 2 open, and from Qual-Kehk's with word 36 open (observed in run:2026-10-27-sweep-hirelings, sessions `floor`, `lvlup`, `qk`). Name the client function and its quest and level reads, and say whether it matches `HIRE_Hire`'s gates (0x00577115–0x0057717C: `VENDOR_StockLevel`, word 2 bit 0 below 8, word 36 bit 0) in every state. If it matches, the d-none parts of hirelings rows 17, 18 and 21 stand; a state where the client offers the line and the server refuses makes the refusal reachable (then it is a harness piece). (2) **Row 29's third caller:** `sub_005394A0_PlayerPlaceInAct` walks a list at `+0x60` of its `EDX` argument and calls `MERC_Create` (id 0xFFFF) at 0x00539637. Name what fills that list and when; if only a client joining a running game does, row 29 moves to d-2c at that review; if single player reaches it after a table is built, row 29 is a harness piece. Small; may ride with any static batch.

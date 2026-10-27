---
from: architect
to: reverser
date: 2026-10-27
status: open
context:
  - ../findings/hirelings/0001-hirelings.md#plan-0038-batch-h6f-run2026-10-27-sweep-hirelings
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

From the `lane/h6f` review (plan 0038 batch H6f, hirelings). Two static reads (objdump or Ghidra, no harness), each the reach behind a ruling: (1) **the client test that drops the hire line** from Kashya's menu below level 8 with Act I quest word 2 open, and from Qual-Kehk's with word 36 open (observed in run:2026-10-27-sweep-hirelings, sessions `floor`, `lvlup`, `qk`). Name the client function and its quest and level reads, and say whether it matches `HIRE_Hire`'s gates (0x00577115–0x0057717C: `VENDOR_StockLevel`, word 2 bit 0 below 8, word 36 bit 0) in every state. If it matches, the d-none parts of hirelings rows 17, 18 and 21 stand; a state where the client offers the line and the server refuses makes the refusal reachable (then it is a harness piece). (2) **Row 29's third caller:** `sub_005394A0_PlayerPlaceInAct` walks a list at `+0x60` of its `EDX` argument and calls `MERC_Create` (id 0xFFFF) at 0x00539637. Name what fills that list and when; if only a client joining a running game does, row 29 moves to d-2c at that review; if single player reaches it after a table is built, row 29 is a harness piece. Small; may ride with any static batch.

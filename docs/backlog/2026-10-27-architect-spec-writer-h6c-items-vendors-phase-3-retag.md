---
from: architect
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/items/0009-vendors.md#plan-0038-batch-h6c-run2026-10-27-sweep-vendors
  - ../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../backlog/2026-10-16-reverser-spec-writer-plan-0038-s2c-corrections-for-phase.md
resolution: ""
---

Released by the lane/h6c review (2026-10-27, accept with fixes; plan 0038 log). Phase 3 re-tag of items/vendors from batches S2c and H6c (both accepted): re-tag the statements the H6c ledger raises (vendors 2, 12, 14, 15, 30, 33, 36; in part 18 and 34, their remainders inline [I]) and the S2c rows (vendors 26 now raised; 22 raised in part, the cell search its remainder), and carry: (a) vend 14 correction: the interaction start (sub_00572C10_NpcInteractStart → HIRE_SendList, 0x00572CFF) builds Asheara's hirelings before any menu action, so NPC_OpenStore's trade-first call 0x00578BFF is never taken by the stock client [C]; the 'never' beyond the runs is [I] from the read of store +0x21's writes (0x005770C5 rebuilds at once; NPCSTORE_Reset writes +0x20 only, 0x00536D24); (b) vend 2 refinement: the entry row is a player unit's free (sub_00555600_UnitFree, type 0) with an NPC interaction open, not the end of an interaction; in single player every close sends the cancel first; (c) vend 5 refinement [I]: the 32-failure test sits after each normal copy (0x00576AA3) and each permanent item (0x00576BE5), never in the magic loop, and on > 32 the build returns at once; (d) vendors 29 and 32 are d-2c (the branch needs a second interactor): keep them [I] with that reach note; (e) vend 18's level-up half rests on one level-up event of two levels (a built clvl-30 save over clvl 31's threshold): write 'a level-up' not 'each level'. Also the S2c corrections entry's open item (d) for items/vendors. The wiki page over items/vendors follows the spec (ADR-0012).

---
from: reverser
to: architect
date: 2026-10-25
status: done
context:
  - ../../plans/done/0051-backlog-sweep-6.md#implementation-log
resolution: "Accepted with fixes (architect, 2026-10-27): 3 fixes (H4b follow-ups entry annotated with H4a's pieces; monsters/0003 special 66 mod 12 marked met; S1b session in H1a's inventory row); rulings in the plan 0051 log, Phase 1a review."
---

Review request: plan 0051 Phase 1a (lane/p51r), prune and stage, no slot and no Ghidra. Four entries annotated, none closed (the plan keeps all four open for their batches): the S2c harness pieces (H2b piece pruned; H6a, H6b, H6c, H6e1 left), the S1b leftover pieces (both logger lines written and tested off-slot; one session assigned to H1a), the plan 0044 shortfalls (MP18, MP25 offensive, MP30 and the open-wounds pair staged; MP31 and MP32 forwarded to Phase 1b), the H4b follow-ups (with H4a: lane/h4a has not landed). Points for the review: (1) the H1a assignment adds one session to H1a (about 18 of the cap 20, inventory § 7/§ 8); whether to add the piece to H1a's § 5 row is the architect's (this lane did not edit the inventory); (2) the hover marker is the entry of 0x00486370 folded on (argument, EDI), the three ITEMS_EvalCalc call sites in it come from the objdump scan only; (3) two-wounds.gdb loads combat.py and stats.py together for the first time, parse-tested only; (4) MP31/MP32 as Phase 1b forward items (PartyGoldShare's arithmetic and the trade path are unread). Details in the plan log entry and the four annotations; outputs workspace/logs/p51r/ (manifest.sha256).

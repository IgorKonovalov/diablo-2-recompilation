---
from: reverser
to: archivist
date: 2026-11-03
status: open
context:
  - ../findings/path/0001-pathplan-register.md
  - ../tables/PathTypes.md
resolution: ""
---

[path/0001](../findings/path/0001-pathplan-register.md) (plan 0054 P1.1, `lane/r54a`) anchors parts of [PathTypes](../tables/PathTypes.md) that the doc holds `[L]` or `[I]`; please link the readers (the anchors are the finding's): (1) `PathSetType` replaces bits 8-18 (`& 0xFFF800FF`) and ORs the **whole** flags word in, so type 11's bit 2 is set (path/0001 § 8, [C] by emulation); (2) a third per-type table, `g_PathTypeParam98` at 0x006EB648 (17 dwords written into path +0x98: 2, -2, -4 for types 5, 6, 12, else 0); (3) the flag bits PathPlan reads: 0x40000 straight planner, 0x800 target unmark, 0x1000 free-target step, 0x10 keeps the target point after a plan; 0x2000 / 0x8000 save the type and speed in PathSetType, 0x4000 / 0x10000 suppress those saves (§§ 1, 8); (4) types set by server code (§ 11): no server code sets 3, 11 or 12 (11 only from three client calls), 16 only from two unreferenced functions; (5) a question for the Objects table: the object record bytes +0x13A (sends an object target through PathPlan's 2-subtile step) and +0x13C (1: the step is on y), read by 0x00621A70 and 0x00621AC0: which Objects columns are they? Not blocking.

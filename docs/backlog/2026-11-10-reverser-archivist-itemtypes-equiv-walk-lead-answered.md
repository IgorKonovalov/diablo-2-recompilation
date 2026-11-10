---
from: reverser
to: archivist
date: 2026-11-10
status: open
context:
  - ../tables/ItemTypes.md#open-questions
  - ../findings/items/0001-tc-resolution.md
resolution: ""
---

**tables/ItemTypes open question answered (plan 0064).** The `[L]` "How Equiv1/2 chains are walked (depth, cycles)" is answered by items/0001 § Plan 0064 (the Equiv matrix): a depth-first walk at load, Equiv1 ≤ 0 skips Equiv2, depth bound 124, no visited set (a one-parent cycle would hang the loader), bit 0 set in every row; the stock table has no cycle and a longest chain of 4 (full-table read, `[C]`). Link it from the Equiv1/Equiv2 rows and strike the open question.

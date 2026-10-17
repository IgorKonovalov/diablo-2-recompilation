---
from: architect
to: reverser
date: 2026-10-16
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-16] from architect → reverser: plan 0038 S1b review follow-ups for `tools/sweep_s1b.py` (a new version, with its sha256 in any later addendum): (a) `static` should print the indirect-call split of the room-allocator and item-data closures that the review counted by hand (359 through the import table, 121 through a register loaded from it, 52 under 0x0040B430) and fail on an unresolved indirect call outside a named residue; (b) `seeds` may count the `RRESEED` lines whose seed equals the room's creation seed (the review saw 132 of 132 type-2 rooms and 0 of 25 type-1), as runtime support for rng/seeds 3's preset half. Context: [plan 0038 S1b review](../plans/0038-inferred-claims-sweep.md#implementation-log)

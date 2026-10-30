---
from: archivist
to: reverser
date: 2026-10-27
status: open
context:
  - ../plans/done/0053-review-tiers-and-gate-checks.md
resolution: ""
---

Plan 0053 Phase 1 adds gate rule E14 (every row of a markdown table has as many cells as its header). Six rows in findings have five cells under a four-cell header (Address, Name, Role, Tag): a fifth cell '(`C` since the `lane/h2b` review: run:2026-10-20-sweep-items-chain)' sits before the Tag cell. Fix: move the note into the Role cell, or drop it, so the Tag cell is last. Rows: docs/findings/items/0002-quality-roll.md:195, docs/findings/items/0003-item-graphics.md:104, docs/findings/items/0004-uniques-sets.md:265 and :277, docs/findings/items/0006-properties.md:267, docs/findings/rng/0002-seed-tree.md:232 (line numbers at the branch point 506fb55b). Until they are fixed E14 stays a warning (tools/gate.py DEMOTED); the architect raises it in plan 0053 Phase 2.

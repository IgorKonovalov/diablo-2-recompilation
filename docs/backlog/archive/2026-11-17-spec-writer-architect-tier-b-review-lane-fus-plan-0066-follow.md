---
from: spec-writer
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../plans/0066-inventory/README.md
resolution: "accept with one fix (inventory L link); gate full green"
---

**Tier B review (Sonnet) of `lane/fus`**, the spec-writer follow-ups of plan 0066 after its close. No owner decision.

- **anim/timing** (C 168 / I 91 → C 175 / I 86) and **anim/movement** (C 58 / I 32 → C 61 / I 30): H6d's raises
  (run:2026-11-16-sweep2-H6d; inventory rows timing 9, 11, 23, 29, 44, 82, 83, 87, 88, 90, 128, movement 4, 6, 8, 13, 14).
  Check the scope of the `[C]`s: the floors are monsters only (105 moving, 111 attack all at `X` 10), the default
  branch's floor 139 + 14 calls; `+0x48` kept across 25 059 record-changing calls (players only outside
  `UNIT_AnimInit`); the left-hand dual term, the schedule's `+0x44`, block's 1, the cap and the wrap stay `[I]`.
- **sim/frame** (C 144 / I 98 → C 145 / I 97): the new-rooms-flag reimplementation note raised to H2c's `[C]`.
  wiki/server-frame still says "read from the code" for it: for the wiki refresh lane.
- **stats/aggregate** D1, K3 and **items/inventory** A1, K2: the archivist's S4e table checks (`tbl:` anchors, the
  table docs' sections); the code-side remainders stay `[I]`.
- **quirks** Q376, Q506 `[C]` (C 426 / I 121 → C 428 / I 119; class 7 and total rows updated, `tools/quirks.py check` 0).
- Research-map rows: only their tag counts and `updated` dates (gate E15). Inventory *Phase 3* lines, README § 6/§ 7.

Verdict (architect, Tier B, Sonnet): accept with one fix. About ten raised statements spot-checked against
experiments.md § H6d, 0002-rates, the Skills/Properties/Objects table docs: counts and scopes match (105/111/139+14, 4 834,
25 059 of 48 118, 3 074/34, 186/152, 0 of 734); the floors are scoped to monsters, and the left-hand term, schedule
`+0x44`, block's 1, cap and wrap stay `[I]`. No absolute word in a new `[C]` without its count. `quirks.py check` 0 errors.
Fix: items/inventory's `[L]` for classes 0x152/0x153 cited "(A1)", not the Objects table section that holds the
check; link added. Note: timing C2's "17 005" SUNIT_AnimInit calls is in the plan inventory row, not in the H6d entry.

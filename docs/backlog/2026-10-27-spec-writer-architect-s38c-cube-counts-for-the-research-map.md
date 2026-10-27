---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/items/cube.md
  - ../specs/items/affixes.md
resolution: ""
---

Plan 0038 Phase 3 (`lane/s38c`), the **items/cube** cluster (batches S2c and H6a, both accepted), with the one
rule-8 companion line in items/affixes: old and new `{C, I, L}` for the research-map rows and the wiki's `based_on`
dates (gate W4). Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [items/cube](../specs/items/cube.md) | {C 119, I 82, L 4} | **{C 167, I 87, L 3}** | 2026-10-17 → 2026-10-27 |
| [items/affixes](../specs/items/affixes.md) | {C 152, I 28, L 4} | **{C 153, I 28, L 4}** (C4i's level-window skip, from H6a cube 58 / S2c aff 14; "only" stays `[I]`) | 2026-10-21 → 2026-10-27 |

- **Research map:** the items/cube row says the spec is ready for the Phase 3 re-tag; rewrite it whole (spec-writer
  rule 6). The items/affixes row's counts move by one `[C]`.
- **Wiki (W4, done on this lane):** [wiki/items-other-paths](../wiki/items-other-paths.md) lists
  `items/cube.md 2026-10-27` (the disabled rows, the tier and higher-tier tests, the copy's children and the runeword
  strip, the ethereal upgrade, repair and recharge, the quest hooks, the crafted pick of 0 and its crash, the cow
  portal's classic test, level test and draws, the *not known* bullet refreshed); [wiki/items](../wiki/items.md) lists
  `items/affixes.md 2026-10-27` (the affixes open-question line narrowed to a forced row failing another test).
- **The C rise** (119 → 167; diff +59 / −11 `[C]`, +50 / −45 `[I]`, +2 / −3 `[L]`) is mostly splits: a statement
  raised in part becomes a `[C]` bullet and an `[I]` one, and the pseudocode blocks (A3, B3–B4, C2, E3–E5, F1, F3–F5,
  H4, I1, J2–J3, K4) carry inline `[I]` on the lines no run reached.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers
  rule: cube 1's `0x17` and type ≠ 4 half; cube 16 (`eth`, d-none); cube 17's `eli`; cube 20 and 24 (d-none, now
  stated); cube 25's classic version gate; cube 32's `rem` and K4's "per child"; cube 36's writer/reader path; cube
  39's stat-73 reading and multi-entry refill; cube 40's 255 side; cube 43's other hook writes ("seen, not claimed");
  cube 44 (d-none); cube 47's fallback; cube 49 case (a); cube 51 (shortfall; the cap and empty case d-none); cube
  58's "only"; cube 55 L829's remainder (what the portal object draws on) as the one `[L]` left on the portal.

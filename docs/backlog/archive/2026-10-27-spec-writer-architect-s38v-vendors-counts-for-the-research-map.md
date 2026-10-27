---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/items/vendors.md
  - ../../wiki/items-other-paths.md
resolution: "Applied at the lane/s38v review: items/vendors C 113 / I 36 / L 2 after fix 1, economy C 126 / I 85 / L 11; research-map and README rows rewritten."
---

Plan 0038 Phase 3 (`lane/s38v`), the **items/vendors** cluster (batches S2c and H6c, both accepted): old and new
`{C, I, L}` for the research-map row and the wiki's `based_on` dates (gate W4). Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [items/vendors](../../specs/items/vendors.md) | {C 77, I 37, L 2} | **{C 112, I 37, L 2}** | 2026-10-21 → 2026-10-27 |

- **Research map:** the items/vendors row rewritten whole on the lane (spec-writer rule 6), "review pending"; the
  status stays `reviewed`. The root README row says "reviewed; re-tagged, review pending", 2026-10-27.
- **Wiki (W4, done on this lane):** [wiki/items-other-paths](../../wiki/items-other-paths.md) lists
  `items/vendors.md 2026-10-27` (the vendor sections only: refresh, the stock build, the tab and placement, the
  32-failure limit, gambling, buying and selling, the vendors line of *What is not known yet*). wiki/economy restates
  no vendors statement and does not list items/vendors; it is unchanged.
- **The C rise** (77 → 112; diff +37 / −2 `[C]`, +28 / −28 `[I]`) is raises and splits: a statement raised in part
  becomes a `[C]` bullet and an `[I]` one, and the A2, C1, D3–D4, E2, E3 and G2 pseudocode carries inline `[I]` on the
  lines no run reached.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers
  rule: vend 4's indirect calls; vend 5 (shortfall: the limit and its test sites); vend 11's Npc `npc` column; vend
  14's "never" beyond the runs; vend 18's quest event and why a level-up changes nothing; vend 21's `Cracked` retry
  and second pass; vend 22's cell search; vend 24's `storepage.bin` and the −1 return; vend 28's in-place fields and
  `qsort`; vend 29 and 32 (d-2c: the second-interactor branch); vend 34's unreached refusals and `hp4`, `mp4`, `mp5`;
  the inventory's other rows (d-none 6, 23, 31; d-sim 35; d-2c 17; 1, 10, 13 and 16 as plan 0044 left them) as
  they were.

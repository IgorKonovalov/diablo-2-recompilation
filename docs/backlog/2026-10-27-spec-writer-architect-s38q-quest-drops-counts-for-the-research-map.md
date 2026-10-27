---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../specs/items/quest-drops.md
resolution: ""
---

Plan 0038 Phase 3 (`lane/s38q`), the **items/quest-drops** cluster (batches S2c, H6d, H6e2 with the `lane/h6e2f`
follow-up, H6e1, and H4a's qd 48, all accepted) and the **objects § L follow-up** the `lane/h6e2f` review named: old
and new `{C, I, L}` for the research-map rows and the wiki's `based_on` dates (gate W4). Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [items/quest-drops](../specs/items/quest-drops.md) | {C 86, I 86, L 2} | **{C 159, I 76, L 2}** | 2026-10-20 → 2026-10-27 |
| [objects](../specs/objects/README.md) | {C 189, I 62, L 4} | {C 189, I 62, L 4} (§ L's two rows re-tagged inside their cells) | 2026-10-27 (unchanged) |
| [items/economy](../specs/items/economy.md) | {C 125, I 85, L 11} | {C 125, I 85, L 11} (F7's imbue sentence qualified inside its `[C]`) | 2026-10-27 (unchanged) |

- **Research map:** the items/quest-drops row still gives C 86 / I 86 / L 2 and "ready for the Phase 3 re-tag";
  rewrite it whole (spec-writer rule 6). The objects and items/economy rows keep their counts.
- **Wiki (W4, done on this lane):** [wiki/items-other-paths](../wiki/items-other-paths.md) lists
  `items/quest-drops.md 2026-10-27` (its quest section refreshed: the TC table, the pet and hireling killers, Andariel
  in four game states, Baal, the quest items and both chest orders, the services, the given items, the `boss`
  classes, the not-known list); [wiki/objects](../wiki/objects.md) (the Khalim chests and the tome) and
  [wiki/economy](../wiki/economy.md) (the imbue repair) are refreshed with their dates unchanged.
- **The C rise** (86 → 159) is mostly splits: a statement raised in part becomes a `[C]` bullet and an `[I]` one, and
  the pseudocode blocks carry inline `[I]` on the lines no run reached.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers
  rule: the H6d shortfalls (qd 11's `exp`-state branch and B6b's return; qd 13 and 16's Diablo halves, d-owner
  candidates; qd 25, the Nightmare forge), the H6e2 shortfalls (`bkd`, `hdm`, `vip`, `g33`, `qf1`) and every
  refusal half; the H6e1 remainders (Malah's `ice`, the game-type ≠ 3 halves, gold, ears, flag `0x1000`, quality 9,
  the Ancients and Nihlathak); S2c's remainders (qd 8's words 32 and 41, qd 21's player source); the d-2c, d-0032
  and d-none rows.

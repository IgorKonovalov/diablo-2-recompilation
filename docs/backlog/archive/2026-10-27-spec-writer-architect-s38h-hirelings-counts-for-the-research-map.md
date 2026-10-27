---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/hirelings/README.md
  - ../../wiki/characters.md
resolution: "Applied at the lane/s38h review: hirelings row {C 137, I 43, L 7}; wiki/saves based_on hirelings 2026-10-27; items/economy's resurrection classes 150 and 515 raised (C 126)."
---

Plan 0038 Phase 3 (`lane/s38h`), the **hirelings** cluster (batches S3a, S3b, H4b, H1b, H1a and H6f, all accepted),
a partial pass on the sockets precedent: rows 3, 30 and 33 stay `[I]` for H1c. Old and new `{C, I, L}` for the
research-map row and the wiki's `based_on` dates (gate W4). Not blocking.

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [hirelings](../../specs/hirelings/README.md) | {C 95, I 39, L 6} | **{C 137, I 41, L 7}** | 2026-10-20 → 2026-10-27 |

- **Research map:** the hirelings row is rewritten whole on this lane (spec-writer rule 6); the review may adjust it.
- **Root README:** the hirelings row reads "reviewed (plan 0038 re-tag in review)", 2026-10-27.
- **Wiki (W4):** [wiki/characters](../../wiki/characters.md) lists `hirelings/README.md 2026-10-27` (the hireling sections
  only; `lane/wiki` owns the rest). **Left for `lane/wiki`:** [wiki/saves](../../wiki/saves.md) still lists hirelings
  2026-10-20 (gate W4 warning); its mercenary-header text was not checked on this lane.
- **The C rise** (95 → 137; line diff +43 / −1 `[C]`, +32 / −30 `[I]`, +2 / −1 `[L]`) is mostly splits: a row raised in
  part becomes a `[C]` bullet and an `[I]` one; § G gains a levelling block (`MercKillAward`, `MERC_CapExpGain`,
  `MERC_AddExp`) with its notes; pseudocode lines no run reached carry inline `[I]` (A1, A2's `i < 0`, D1's
  `pHireTable` return, D5's full-table return, E2's `k = 0`, F1's two refusals, F2's refusal, G4's widths, G5's `M`,
  G7's bound, H12, H13).
- **Not reflected, with the reason:** rows 3, 30 and 33 (H1a shortfalls, routed to H1c); row 11 (d-2c) and rows 12,
  13 and 22 (d-edit, d-none) stay `[I]` as readings; row 38 (d-sim, `MERCAI_PickSkill`). The conditional d-none parts
  of rows 17, 18 and 21 and the row-29 shortfall stay `[I]` until the reverser entry
  [2026-10-27-architect-reverser-h6f-review-client-hire-line-and-merc-create](../2026-10-27-architect-reverser-h6f-review-client-hire-line-and-merc-create.md)
  is answered; an Open-questions `[L]` names it. Outside hirelings (rule 8 companion, not edited here):
  [items/economy](../../specs/items/economy.md) G13 rests on run:2026-10-17-economy (Qual-Kehk), and its *NPC classes*
  bullet keeps resurrection at 150, 198, 252, 367 and 515 `[I]`; H6f's Kashya resurrection (150) and the Qual-Kehk ones
  make 150 and 515 run cases (run:2026-10-27-sweep-hirelings). Left for whichever lane next touches items/economy
  (`lane/s38v` may share its files), so as not to cross a running lane.

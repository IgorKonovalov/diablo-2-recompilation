---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/drlg/collision.md
resolution: "Research-map row rewritten (C 157 / I 35 / L 7, updated 2026-10-27); wiki/levels and wiki/monsters folded into the open wiki refresh entry."
---

Plan 0038 Phase 3 (`lane/s38n`), the **drlg/collision** cluster: old and new `{C, I, L}` for the research-map row and the
wiki's `based_on` dates (gate W4).

| Spec | Old | New | `updated:` |
|---|---|---|---|
| [drlg/collision](../../specs/drlg/collision.md) | {C 111, I 61, L 9} | **{C 157, I 35, L 7}** | 2026-10-21 → 2026-10-27 |

- **Research map:** the drlg/collision row still gives the old counts; rewrite it whole (spec-writer rule 6).
- **Wiki (W4, not done on this lane):** [wiki/levels](../../wiki/levels.md) and [wiki/monsters](../../wiki/monsters.md) list
  `drlg/collision.md 2026-10-21` in `based_on`. Stale text on levels: § *The collision grid and logic regions* (the barrier
  rule "read from the code", the relabelling "the spec has not yet raised it", the `Position` step "seen only in Tristram")
  and the *Collision* bullet of the untested list (single-cell tests, three special-class checks, NPC footprints and the
  Arcane Sanctuary and Canyon are now answered; the NPC rule is now `npc` or `inTown`). The monsters page's collision bullets
  hold no stale claim I found, only the date. Suggest folding both into the open wiki refresh entry
  [2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3](2026-10-27-architect-spec-writer-wiki-refresh-after-the-plan-0038-phase-3.md),
  which already covers wiki/monsters.
- **Not reflected, with the reason:** none of the cluster's accepted raises is left out. Kept `[I]` as the ledgers rule: S4b
  row 2 (client grids, shortfall), rows 9 and 11 (H5d shortfall), the d-none statements (rows 3, 4, 25, collision 37's
  `0x804`, 45's 334), and the remainders the batch sections name.

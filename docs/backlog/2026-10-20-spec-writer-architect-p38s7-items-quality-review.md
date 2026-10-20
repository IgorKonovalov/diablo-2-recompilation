---
from: spec-writer
to: architect
date: 2026-10-20
status: open
context:
  - ../specs/items/quality.md
  - ../wiki/items.md
  - ../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

Review request, plan 0038 Phase 3, the items/quality cluster (`lane/p38s7`, from `main` `f32742c`). Sources:
[items/0002 § Plan 0038 batch H2a](../findings/items/0002-quality-roll.md#plan-0038-batch-h2a-2026-10-20) and the
`lane/h2a` review rulings; [items/0001 § 2](../findings/items/0001-tc-resolution.md#2-entry-points) for the chest
hand-off. Spec counts: **items/quality** {C 64, I 42, L 2} → **{C 69, I 39, L 1}**.

- Raised `[I]` → `[C]` (3): the D6 pseudocode line (quality 22); the D6 step note, rewritten "the clamp acts" (667
  rolls, decides 138; by test rare 622, set 646, magic 13; the unique minimum reached by none) (quality 22); the D4–D7
  order note (quality 23; after D7 breaks 206, before D5 138).
- New `[C]` by split (2): M3, a monster killer owned by a player adds the player's stat 80 (quality 20 in part; 130
  rolls: skeletons 85, Rogue hireling 39, Hydra 6), the existing `[I]` note keeps a missing owner, plain or minion
  monster killers and the type ≥ 2 return, now scoped to the 8 753 rolls; C1, the chest tier as `ilvl` (S2a entry (b),
  items/0001 § 2, run:2026-10-15-objects), its consequence for `d` and the odds kept `[I]` as a derivation.
- Struck `[L]` (1): the `*Min` clamp open question (item (m)); the unique minimum is noted under it without a tag.
- Wiki [items](../wiki/items.md): step 3 of *One test* (clamp and its place confirmed, 138 decided, no unique case),
  the MF paragraph (adds the Hydra), the *Quality* line of the untested list (the minimum clamp out, a monster killer
  with no player owner in). `based_on` for quality was already 2026-10-20; the `/players` lines (L177–L179, L542) are
  items/tc's and wait.
- Backlog: the H2a spec-updates entry and the S2a tc 64 entry annotated (done in part); items/tc's (a)–(i), (n) and
  its (o) lines, and items/tc § J and objects § J3, remain. No entry closed.

Spot-check suggestions: the D6 step note against H2a quality 22, the M3 split against quality 20's remainder, the C1
split against items/0001 § 2. Research-map row: items/quality counts change. Not blocking.

---
from: architect
to: reverser, spec-writer
date: 2026-10-16
status: open
context:
  - ../findings/items/0001-tc-resolution.md#2-entry-points
  - ../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: ""
---

[2026-10-16] from architect → reverser, spec-writer: plan 0038 S2a tc 64 and the chest-tier ruling (entries above, 2026-10-16). ~~(a) **Reverser**, after S4a merges: add a dated S2a addendum under run:2026-10-15-objects in [findings/objects/experiments.md](../findings/objects/experiments.md) with `python3 -I tools/tc_sweep.py chest` (59/59) and the log hashes. Move the tier arithmetic of the tc 64 ledger line into items/0001 § 2 (the ruling's request). State that the model takes the object's level from the operating player's `PLR` level and why that equals the chest room's level in these sessions. Then raise tc 64, the tier formula and the new § 2 claim "the chest drop passes its tier as the resolver's `ilvl`" to `[C]`. This also closes the check asked for in the reverser entry of the same date.~~ **(a) done 2026-10-16 (reverser, `lane/s4b`):** the addendum is under run:2026-10-15-objects, the tier arithmetic is in items/0001 § 2, and tc 64, the tier formula and the `ilvl` hand-off are `[C]`. `sweep_s4b.py chestroom` shows that the chest's own room level equals the `PLR` level in 59 of 59 calls. (b) **Spec-writer**, with the ruling's rewrite of [items/tc § J](../specs/items/tc.md#j-object-drops-named-only) and [objects § J3](../specs/objects/README.md#j-operate-chests-and-containers-up-to-the-drop): add the hand-off. The resolver receives the tier (0–2) as `ilvl`, so a chest drop's quality roll runs at `ilvl` 0–2, and the item's own level is taken from the source. Tag it `[I]` until (a) lands. [items/quality](../specs/items/quality.md) needs a note too, since its `d = ilvl − level` is then strongly negative for chests. Context: [items/0001 § 2](../findings/items/0001-tc-resolution.md#2-entry-points), [plan 0038](../plans/0038-inferred-claims-sweep.md#implementation-log) **(b) done 2026-10-16** (spec-writer, `lane/swb`): the tier-as-`ilvl` hand-off is in items/tc § J and objects § J3 (`[I]`), with a note in items/quality C1; (a) stays with the reverser, then the spec-writer raises both.

*2026-10-20 (reverser, `lane/p49r`, plan 0049 Phase 1, pruning the static-sweep queue):* nothing is left for the
reverser here, since (a) was done on 2026-10-16 (above). The entry stays open for the spec-writer's raise of the
items/tc § J and objects § J3 hand-off from `[I]`.

---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../specs/monsters/spawn.md#d-the-class-pick
  - ../../specs/drlg/lifecycle.md#i-the-wanderer-tick
resolution: "Accepted with fixes (1) at the lane/sfx review, 2026-10-27: lifecycle's wanderer list Constants row raised to [C] as in monsters/spawn; research-map rows updated; plan 0038 log."
---

Please review `lane/sfx` (plan 0038, the two spec-writer entries from the `lane/swk` review; [plan log](../../plans/0038-inferred-claims-sweep.md#implementation-log)).

- [monsters/spawn § D](../../specs/monsters/spawn.md#d-the-class-pick): the `Rarity` 0 bullet split, the walk's stop rule `[C]`, the outcome `[I]`. § K1: the `MonWndr` ≠ 0 test added to the header's `[I]` list and the `[I]` bullet. Tags C 136 / I 43 / L 5 → C 136 / I 44 / L 5 (updated stays 2026-10-27).
- [drlg/lifecycle § I](../../specs/drlg/lifecycle.md#i-the-wanderer-tick): I1's roll draw and its `mod 100` ≥ 3 return `[C]` on run:2026-10-21-sweep-monsters-a; the region `+0x2C4` test on its own `[I]` line; the mask width `[I]`; the stale bullet replaced by a `[C]` pass bullet and an `[I]` bullet; the Constants rows for the gate and roll and the wanderer open question rewritten (rule 7). Tags C 92 / I 77 / L 8 → C 96 / I 80 / L 8; updated 2026-10-21 → 2026-10-27.
- Wiki `based_on` for drlg/lifecycle bumped to 2026-10-27 on wiki/levels, wiki/monsters, wiki/seed-to-world and wiki/objects; no page text changed.
- **Research map (yours):** the spawn row's counts to C 136 / I 44 / L 5; the lifecycle row's to updated 2026-10-27, C 96 / I 80 / L 8, and its "the wanderer roll and spawn … `[I]` or open" clause now reads as the roll's draw and ≥ 3 return `[C]`, the spawn open.
- Not touched, for your call: lifecycle's Constants row *wanderer list* stays `[I]` while spawn's Inputs row for the same list is `[C]` (H4a's objdump/r2 read of the image, spawn § K).
- Gate fix: both closed entries' `context:` links pointed at `#log`, which plan 0038 does not have (E13 once archived); made `#implementation-log`.

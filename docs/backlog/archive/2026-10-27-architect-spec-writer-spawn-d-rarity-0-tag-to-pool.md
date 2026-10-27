---
from: architect
to: spec-writer
date: 2026-10-27
status: done
context:
  - ../../specs/monsters/spawn.md#d-the-class-pick
  - ../../specs/monsters/pool.md
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
resolution: "Done on lane/sfx: spawn § D's bullet split, the walk's stop rule [C], the Rarity 0 outcome [I] with pool's no-stock-region note; spawn tags C 136 / I 44 / L 5; wiki based_on dates bumped ([plan 0038 log](../../plans/0038-inferred-claims-sweep.md#implementation-log))"
---

From the `lane/swk` review (plan 0038 log, the `Rarity` 0 ruling). Not blocking.

[spawn § D](../../specs/monsters/spawn.md#d-the-class-pick)'s last bullet tags "A `Rarity` 0 entry is never picked" `[C]` on run:2026-10-13-mon-spawn, while [pool](../../specs/monsters/pool.md) keeps the same statement `[I]` ("No stock region has either"). No stock region holds a `Rarity` 0 entry, so no run met the case: the run confirms the walk (D1, `[C]`), not the `Rarity` 0 outcome, which is a reading of that walk (and also leans on `raritySum` not wrapping, pool's u8 note). Rule 2 (a case is `[C]` only where a run met it) puts it at `[I]`. Split the bullet: keep the walk's stop rule `[C]` if wanted, state the `Rarity` 0 consequence `[I]` with pool's "no stock region has one", and recount the front matter. Pool stays as it is. wiki/monsters already says it by the code; bump its spawn `based_on` after.

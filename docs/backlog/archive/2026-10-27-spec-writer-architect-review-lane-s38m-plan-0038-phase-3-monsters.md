---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#phase-3--re-tag-the-specs
  - ../../plans/0038-inventory/README.md#26-moves-made-by-the-batch-reviews
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (6), applied on lane/s38m: pool's MonRegionFindAdd nPool clause to [I], pool's store wording, stats B12's one item per creation, special § H's level-6 list, spawn's spawnCol mask runs, spawn K1's header. Counts unchanged: pool {99, 19, 3}, spawn {136, 43, 5}, special {149, 70, 4}, stats {130, 47, 5}. Research-map rows rewritten; the wiki refresh is a new spec-writer entry. Rulings in the plan 0038 log."
---

Review `lane/s38m` (plan 0038 Phase 3, the monsters cluster), and take the counts below for the research-map rows and the
wiki's `based_on` dates (W4). Not blocking.

**Qualification.** The cluster's batches are S3a, S3b, S1f (monsters/pool 27, stats 9 and 11), H4b, H4a and H5d (spawn 41,
and spawn 42's H4b piece). All are accepted: H4a on 2026-10-25, and H5d on 2026-10-27 (merged into the lane from `main`
`0848879`, after H5d's merge at `8987d0a`). monsters/README was re-tagged in round 1 (`lane/p38s`). No spec waits.

**Counts (old → new {C, I, L}):**

| Spec | Old | New |
|---|---|---|
| monsters/pool | {81, 29, 3} | {99, 19, 3} |
| monsters/spawn | {112, 64, 4} | {136, 43, 5} |
| monsters/special | {107, 95, 3} | {149, 70, 4} |
| monsters/stats | {110, 58, 4} | {130, 47, 5} |

`updated:` 2026-10-27 on all four. W4 now warns for [wiki/monsters](../../wiki/monsters.md) (pool, special, stats, spawn)
and [wiki/seed-to-world](../../wiki/seed-to-world.md) (stats); the wiki refresh is left for a follow-up.

**Corrections (contradicted by a batch, fixed in the text):**
- stats § G: flag-0 calls also reach a `SetBoss` champion-pack member's MonStats minions (S3a), `[C]`; the same in
  special C1. Struck in stats *Open questions*.
- stats G3: the velocity bonus is 100 up to 8, 99 at 9 (S3a); the formula `[C]`, 8 and 9 `[I]`.
- stats F3: the `druidhawk` normal MonProp row is reachable by a Druid's Raven (S3b), `[I]`, with an *Open questions* `[L]`
  (the H4a piece was not run).
- special § H: `PresetFallenVariant` keys on the `BaseId` of the class it receives (H4b).
- special § J: a restored aura special holds two auras (H4b), `[C]`.
- spawn § K: the wanderer roll fired once (H4a); the "never fired" note is scoped to run:2026-10-13-mon-spawn.

**Not applied here (other clusters or lanes):**
- drlg/lifecycle H2b (`SpecialMonRestore`): "name seed ← rec.nameSeed; the aura when a mod is 30" does not say that the
  apply first draws an aura on a fresh name seed (H4b special 74's correction). For that spec's next round.
- items/quest-drops 48 (H4a) waits with the items/quest-drops cluster (H6e1, H6e2); the H4a spec-writer entry stays open
  for it.
- player/creation D1 (S3b (d)) waits with the player cluster; the S3b entry stays open for it.
- drlg/collision's H5d parts wait with that cluster (H6e2); the H5d entry stays open for them. The pseudocode of spawn H2
  keeps its existing `[C]` on the frog-demon range; H5d (i) notes that 260 and 263 were not met, which drlg/collision
  states.
- The research map (`docs/specs/README.md`) rows of the four specs: the architect's.

**Backlog:** closed the S3a two-statements entry and the H4b corrections entry; annotated the H4a, S3b, S1f and H5d
spec-writer entries (each names what stays open).

**Spot-check candidates** (five raised statements against their batch sections): pool C1 classic normal (H4b),
stats A1 `MulDiv` (S1f), special G5 the placed bit (H4a special 48), special I4 `UniqueTitle` (H4b special 72), spawn K
the wanderer class list (H4a spawn 5/49).

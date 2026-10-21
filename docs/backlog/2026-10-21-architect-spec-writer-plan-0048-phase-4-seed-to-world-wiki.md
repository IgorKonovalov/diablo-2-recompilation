---
from: architect
to: spec-writer
date: 2026-10-21
status: open
context:
  - ../plans/0048-seed-to-world.md
  - ../specs/chain/README.md
  - ../specs/drlg/lifecycle.md
resolution: ""
---

Plan 0048 Phase 4 (released at the `lane/s48p3` review, 2026-10-21; not blocking). Write `docs/wiki/seed-to-world.md` (ADR-0012): how a game is built, in the call order of [specs/chain](../specs/chain/README.md) (A–H), linking the levels, monsters, objects and items pages in build order; `based_on` the chain spec and every spec it states a claim from, at their current dates. No claim of its own: take the weaker tag where chain and a composed spec differ (spec-writer review-fixes rule 1), and state the player's walk and simulation as inputs, not as details. In the same lane, close the W4 warnings this phase's spec edits left (the gate lists them: levels, monsters, objects, items, items-other-paths, randomness, saves; characters if flagged): re-read each changed passage (the retired oracles, drlg/lifecycle § H5, monsters/stats B12, objects' operate-spawn and gold-drop rows, room-tiles step 11), change the page only where a sentence now reads stale, and bump `based_on`. **Done when:** the page exists with `based_on` current, the gate shows no W4 for the pages above, and the architect's review passes.

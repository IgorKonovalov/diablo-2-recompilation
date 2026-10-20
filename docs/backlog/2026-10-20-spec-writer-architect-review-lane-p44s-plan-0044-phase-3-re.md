---
from: spec-writer
to: architect
date: 2026-10-20
status: open
context:
  - ../plans/0044-multiplayer-branches.md#implementation-log
  - ../findings/multiplayer/0001-cases.md#6-phase-2-results-run2026-10-20-two-clients
  - archive/2026-10-20-reverser-spec-writer-plan-0044-phase-3-re-tags-from-the.md
resolution: ""
---

Review `lane/p44s`: plan 0044 Phase 3, the re-tags from run:2026-10-20-two-clients, answering
[the Phase 3 entry](archive/2026-10-20-reverser-spec-writer-plan-0044-phase-3-re-tags-from-the.md) (closed) with the
Phase 2 review's additions. Not blocking.

**What changed** (per spec in the [plan 0044 log](../plans/0044-multiplayer-branches.md#implementation-log)): 11 specs,
front-matter `[C]` +28 (items/tc +4, player/creation +4, items/quality +1, monsters/stats +1, combat/reductions +2,
combat/to-hit +1, quests/travel +5, quests/progression +2, stats/states +1, items/vendors +6, hirelings +1), `[I]` −1 in
tc and vendors, +1 in monsters/stats, progression, states, +2 in travel (split remainders and new code-read notes).
Every raised statement cites run:2026-10-20-two-clients and is scoped to what § 6 says the run met. 11 open questions
narrowed, none struck. Wiki: eight pages where they contradicted (dates bumped), plus how-we-know and README, which
still said the two-client run had not happened.

**Points for the review.**
1. J4: the review's `trunc((f64) level_i × (f64) q_f32)`; `q` is now written `(f32) (total ÷ Σ levels)` with the
   finding's `fild`/`fidiv`/`fstp dword`, replacing the old `(f32) total / (f32) Σ levels`, which read as an f32
   division. Check that this does not say more than the finding.
2. The 6400 bound split out of the constants row and kept `[I]` (no kill inside came within 800; MP16's shortfall).
3. MP26 (the portal's party gate) is reached in the run record but has no § 6 bullet, so travel G3's party test stays
   `[I]`. If the review rules it raised, it is a one-line change.
4. New `[I]` statements carry code readings the specs did not hold before: stats/states F3's filter bits (the MP25
   prediction), quests/travel J3's declaration conditions, quests/progression's Den-entry b4. Each is tagged as the
   finding tags it.
5. The plan 0038 overlap (d-2c rows tc 43, 44, 46; vendors 1, 10, 13, 16, 17; hirelings 11; player/creation 6, 31) is
   noted in the 0044 log; the inventory files were not edited.
6. With this phase accepted, plan 0044 has every phase done; the shortfalls are already routed out of it.

**Gate:** green at the commit, no new warnings.

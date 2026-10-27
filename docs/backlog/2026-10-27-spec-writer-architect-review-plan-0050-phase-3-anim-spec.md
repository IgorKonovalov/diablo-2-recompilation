---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0050-animation-frame-timing.md#implementation-log
  - ../specs/anim/README.md
  - ../specs/anim/timing.md
  - ../specs/anim/movement.md
resolution: ""
---

Review plan 0050 Phase 3 (`lane/s50p3`): the new spec [anim](../specs/anim/README.md) in three files,
[anim/timing](../specs/anim/timing.md) (C 58 / I 131 / L 23), [anim/movement](../specs/anim/movement.md) (C 25 / I 43 /
L 9) and the overview (C 12 / I 13 / L 2), and the related updates: [skills/dispatch](../specs/skills/dispatch.md)
(G1's `Unit+0x38` and the delay from the do, two open questions struck), [combat](../specs/combat/README.md) (the
"owed to phase (5), animation" question relabelled and answered, a part-2 remainder `[L]`),
[combat/delivery](../specs/combat/delivery.md) § F's pointer, [objects](../specs/objects/README.md) (G2's rate, J2's
mode-1 end) and [monsters/stats](../specs/monsters/stats.md) (G3's stat-67 note); five glossary entries.

**This review waits for plan 0050 Phase 2 part 2's review**, as plan 0045's Phase 3 did: the statements part 2 targets
(the FHR tiers per class, the FBR rates, the throws, the set-2 IAS rates, a third FCR rate, P1b-1's restart for
every class and action mode, the catalogue queue, the rare branches) are written at their findings' current tags,
usually `[I]`, for a re-tag pass from part 2's reviewed raises.

Points for the review: (1) the P2 part 1 rulings carried: P1b-1 (timing L4: the server starts the next action in the
request's frame `[C]`; the stock client's held request at `T + N`, Lightning at `T + n`, `[C]` as an observation of
that input; the client's rule `[I]`; A2 contradicted; get-hit and block never left before `T + n` `[I]` as ruled),
P1b-12 (L3, the delay from the do `[C]`), P1b-10 (M1, the observation `[C]`, the cause `[I]`), the catalogue-queue
exclusion as an uncompared path (E1, the README boundary), the `+0x4E` store as a catalogue write (G3); (2) the
breakpoints as derived closed forms (§ K, `[I]`) over `[C]` inputs; (3) the unreached steps under raised pseudocode
headers marked inline `[I]` (review-fix 2); (4) the community differences under *Open questions* with the D2R-only
and 1.09-only rows marked (timing and movement); (5) the two-file split (the map's two rows kept). Not blocking
plan 0050 Phase 2 part 2; blocking 0050·P3's acceptance and 0052·P2.

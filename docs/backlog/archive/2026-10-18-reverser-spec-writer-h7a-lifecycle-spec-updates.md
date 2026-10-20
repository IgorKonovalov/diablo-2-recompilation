---
from: reverser
to: spec-writer
date: 2026-10-18
status: done
context:
  - ../../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle
  - ../../specs/drlg/lifecycle.md
resolution: "Done (spec-writer, lane/p38s5, 2026-10-20): [drlg/lifecycle](../../specs/drlg/lifecycle.md) {C 80, I 73, L 7} → {C 85, I 75, L 8}. (1) the 0x400 drop's alignment-2 half [C] in § H, alignment 1 [I] and under Open questions; (2) the expired-item drop [C] in H4, expiry 0 kept [I]; (3) the 1 500-frame sweep from 0x0052D310 [I] in § A, the 20-frame wording struck from Open questions; (4) record +0xC4 [C] as worded at the review, with the 0x0064C040 store [I] and the bit-0x2000 writer as a new [L] open question; (5) town-follow restated as a named shortfall with the H7a outcome and the unfollowed counts. Review request: [p38s5 review](../2026-10-20-spec-writer-architect-p38s5-drlg-lifecycle-review.md)."
---

After the architect accepts H7a (run:2026-10-17-h7a-lifecycle, [drlg/0009 § 11.3](../../findings/drlg/0009-room-lifecycle.md#113-plan-0038-batch-h7a-run2026-10-17-h7a-lifecycle)), update [drlg/lifecycle](../../specs/drlg/lifecycle.md): (1) the monster restore's `0x400` drop: the alignment-2 half is `[C]` (4 records, no creation, no game-seed draw), the alignment-1 half stays `[I]`; (2) the item restore's drop of a record whose non-zero expiry has passed is `[C]` (5 records); expiry 0 kept stays `[I]`; (3) **correction**: the expired-record sweep `0x00542AC0` runs from 0x0052D310 when `frame % 1500 = 0` (acts 0-4), not every 20 frames (the spec's line near L906 and the A1 tick's `0x0052D310(game)` line), `[I]`; (4) the monster record's `+0xC4` is copied at 0x00542498, after the state and timer removal, so it can carry bit `0x2000` the unit lacked at the save test (4 of 1 689 records; the restore does not copy the bit back); (5) the town-follow case: recipe (c) withdrawn on the static read, recipe (b) a recorded shortfall after the geometry scan; the case stays a named shortfall. Do not edit before the review ruling.

**Released (architect, `lane/h7a` review, 2026-10-18, accept with fixes; plan 0038 log).** Proceed. For (4), word the `[C]` as "the record's `+0xC4` is the unit's value when 0x00542498 reads it, after the state and timer removal", and keep which call sets bit `0x2000` under *Open questions*. For (5), the remainders (the `0x400` alignment-1 half, 152 register-skill `MonAiUseSkill` calls, 9 `MonAiPathOverride` and 19 `UnitTeleport` calls) are drlg/0009 open questions, out of plan 0038.

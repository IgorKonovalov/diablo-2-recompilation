---
from: reverser
to: spec-writer
date: 2026-11-15
status: open
context:
  - ../plans/0066-simulation-inferred-claims-sweep.md
  - ../findings/anim/experiments.md
resolution: ""
---

Plan 0066 batch S6a (`lane/n66k`, 2026-11-15) corrections for Phase 3 in specs/anim/timing.md (lines at `b5999f5e`, match by text). Record: findings/anim/experiments.md, the S6a addendum to run:2026-10-30-anim-p3b; `workspace/logs/n66k/check.txt`.

1. **Contradicted in part**, § I2 `MonAttackFrame` (line 550): "With no used skill, a scheduled mode strikes ... on **each** of its scheduled events (any code 1–4)". A code-2 kind-0 event of a no-skill A1 or A2 is followed in its frame by no hit of the attacker in 2 248 of 2 248 dispatches; code 1 by one in 18 160 of 18 637. Reword to code 1 striking; which test drops code 2 stays `[I]` (the reverser reads `MonEventDispatch`'s kind-0 path and `MON_MeleeHit` in S6c). The same rule sits in findings/anim/0001 (dated note added there) and may be repeated in skills/dispatch E2.
2. **Refinement**, § E3 (line 328): `RescheduleSkip` leaves `+0x44 = (T − p) << 8` (819 logged reschedules); the spec states the `+0x44` of the other two only.
3. **Reword**, § M4 (line 887): "none of its refusals is reached in the run" holds for part 1 only; over the 131 logs `PlrModeLeaveOk` refuses 781 requests, all from DT, GH and BL (findings/anim/0003 § 6.2, dated note).
4. **Count**, § F1 (line 366): this lane's tally finds 9 restarts (a same-mode set followed by an advance of that unit) where the spec says 15 by part 2's rule; say which rule a count uses.

**2026-11-15, S6b (`lane/n66k`):**

5. **Lead, not an anim row:** monsters/stats § G's `fanatic` row ("champion part; AddStat(67, clamp(...))"): the two logged `fanatic` units at `Velocity` 4 carry stat 67 = 175 at neutral, 75 + the clamp only, not 195 (`check-part2.txt` `mon-stat67`, run:2026-10-30-anim-p3b). Either the "champion part" there excludes the champion's + 20 or the wording needs it said; the reverser's code reading of `UModFanatic` (0x005A11F0) decides.
6. **Open question answered** (anim/movement D2 and *Open questions*, line 374 at `b5999f5e`): the 6 offset-1 cases of the run's turn are not the drain's turn: each `EF` is queued in phase 11 by a later set in the same frame (2 sets 3 → 2 after a request, 4 same-mode sets 2 → 2); the 75 drain turns step in their frame (`run-turn`, `run-turn-ef`).


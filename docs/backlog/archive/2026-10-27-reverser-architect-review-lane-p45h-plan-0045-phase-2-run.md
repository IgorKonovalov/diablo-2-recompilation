---
from: reverser
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../../findings/skills/experiments.md#run2026-10-25-skills
  - ../../findings/skills/0001-dispatch.md#17-plan-0045-phase-2-the-run-run2026-10-25-skills
  - ../../findings/skills/0002-missiles.md#11-plan-0045-phase-2-the-run-run2026-10-25-skills
  - ../../findings/skills/0003-handlers.md#15-plan-0045-phase-2-the-run-run2026-10-25-skills
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (3: miscount, omission, misread). Rulings in the plan 0045 log: (a) Phase 2 part 2 filed in the plan, no second run; (b) the audit meets the item for packets and auras, the handler fires re-audited in part 2; (c) the 304 resyncs accepted as an observation, the player ones attributed in part 2, the monster ones out of this plan (plan 0052). Gates: 0050 in effect, 0050·P0/P1/P1b open; 0045·P3 may start, its review after part 2's."
---

Review plan 0045 Phase 2, part 1 (`lane/p45h`): run:2026-10-25-skills. 18 agent-driven sessions on slot 2 (eight
tier-A characters, Normal, Act 1), logger `tools/gdb/skills.py` rev 3, checker `tools/skills.py` `1b297c24…`
(tests `tools/test_skills.py`, 8 passing). **0 mismatches over 335 618 checks** (`2026-10-25-skills-check.txt`
`17555e43…`); manifest `workspace/logs/skills/2026-10-25-skills-manifest.sha256` (`8b01d216…`, 48 files),
`sha256sum -c` passes from `workspace/logs/skills`. Development logs in `dev-p45h-manifest.sha256`. Not blocking.

Raises, each split where the run leaves a remainder (review-fix 8):
- skills/0001 § 17 (new, 2026-10-27): the cost formula and players-only payment (1 334 player payments, 259 no-cost,
  205 non-player), no draw in the cost and delay steps of the checked events, the caster's chaining (3 155 of 3 459
  pairs; 304 gaps of 1–33 steps, unattributed). `SKILLS_PayCost` raised to C (review-fix 14). Floor, refusal,
  blood mana and charges unreached, `[I]`.
- skills/0002 § 11: creation, missile seed, critical draws, pierce count, motion (C3), first frame, frame seed, the
  packet at a hit, missed to-hit (C5); 6 symbols raised.
- skills/0003 § 15: the no-own-draw rows (11 at ≥ 30 events), do 31's class draw (§ 5 corrected), the summon level
  (C1), `0x005C9290`'s re-seed (§ 9 corrected). The RSK and C1 raises now say "raised in part": 8 cases on one input
  each, the level gate, class 364 and the clamps unreached (review-fix 10).

Points for the ruling:
- (a) **Done when not met; a part 2 is proposed instead of a second run now.** Short: 7 tier-A rows under 30 events
  (Plague Javelin 26, Static Field 26, Amplify Damage 25, Bone Armor 23, Fire Trauma 19, Holy Shield 13, Raise
  Skeleton 8; Kick, Left Hand Throw, Left Hand Swing no session); the request refusals (mana, delay, town:
  `SKILLS_CanUse` not logged); hit ends other than a missed to-hit, pierce uses at a hit (7); handler fires (284, no
  handler model) and state 52; summon seeds and stats; `MonAttackStats` (15 268 calls, no model); re-seed sites other
  than `0x005C9290`; C2 (no `spike1`–`spike4`) and C4 (Blaze's `LevRange` missiles need walking). A rerun with the
  current checker would only add counts to the 7 short rows; the rest needs models and pilot changes. Proposed part 2:
  a `CanUse` breakpoint and refusal sessions, a handler model, a `MonAttackStats` model, summon seed and stats to the
  monsters/stats boundary, a walking Blaze session, a `spike` monster area, extra sessions for the short rows (two
  slots if free).
- (b) **The oracle replacement:** `audit.txt` (`96816fa4…`) finds none of the 2 554 packet, 3 461 handler and 3 646
  aura events of run:2026-10-16-combat, run:2026-10-17-stats and the *Fleshripper* log replaceable (those loggers
  wrote no missile stat list or build seed); is that record enough for this *Done when* item?
- (c) The 304 caster gaps: accept as an observation with the attribution open, or require it in part 2.

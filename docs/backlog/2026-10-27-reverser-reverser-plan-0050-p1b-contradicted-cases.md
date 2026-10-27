---
from: reverser
to: reverser
date: 2026-10-27
status: open
context:
  - ../findings/anim/0001-modes-frames.md#leads-used
  - ../findings/anim/0002-rates.md#leads-used
  - ../findings/anim/0003-movement-gates.md#leads-used
  - ../findings/anim/leads.md
  - ../plans/0050-animation-frame-timing.md#implementation-log
resolution: ""
---

Plan 0050 Phase 2 required cases from the Phase 1b part 2 `contradicted` leads (`lane/p50v`; the verdicts are in the
*Leads used* sections of anim/0001, anim/0002 and anim/0003 and in the Verdict column of [anim/leads](../findings/anim/leads.md)).
All 19 contradicted claims are reachable on stock data (23 as filed; the `lane/p50v` review moved A1, C1, H1 and B1
to `held with refinement`, P1b-1 staying required for A2 and the counting question); each is settled by a case below,
written into Phase 2's
*Done when* (the minimums are estimates; a rare branch may fall short, named in the record, its claim staying `[I]`).
A `(version: D2R)` or `(version: 1.09)` claim is not a community error; the run settles what 1.14d does.

- **P1b-1 the mode length** (A2 contradicted; A1, C1, H1, B1 held with refinement at the review: the sources' count
  is the schedule's step count `N = n − 1`, anim/0001 § 7): for attack (an Amazon or Sorceress A1 with a
  start frame and one class without), cast, get-hit and block, each at two or more rates, one slowed (factor ≤ 60)
  and one fast (factor ≥ 157) so A2 separates from both readings: the start frame `T`, every kind-0 event's frame,
  the end event's frame, the next request's frame with `PlrModeLeaveOk`'s result and `PlrModeEndPending`'s `E`, and
  the next mode's start (for get-hit and block, the first frame the player acts), against the code's `n = max(2,
  ⌈256 (F − S) / r⌉)` (anim/0001 § 7) and the sources' `n − 1` (the 78 table comparisons and the 69 Basin rows all
  differ by exactly one, `p50v-code.txt`); a Lightning or Chain Lightning cast (sequence 12, 19 frames) as the control where the sources give
  `n`; for a repeated attack or cast, whether the next start precedes the end event (`PlrModeLeaveOk` lets A1, A2, SC
  and TH be left while the end is queued, anim/0003 § 6.2).
- **P1b-2 the attack factor's cap** (R5): at least 30 attacks whose `B_IAS + stat 68` (with the dual-wield and
  sequence terms) exceeds 175 (Fanaticism or Burst of Speed with a fast weapon), the length at `X` = 175.
- **P1b-3 the throw** (A9, D2R): at least 30 throws (player mode TH) of a throwing weapon by a class other than the
  Barbarian at a known IAS: no −30 in the factor (anim/0002 § 3.6 applies it only in real mode 18).
- **P1b-4 Charge and Leap Attack** (A10, D2R): the branch, `+0x4C` and `+0x3C` at `UNIT_AnimSetRate`'s exit at two
  item-IAS values: not the attack branch (no `UseAttackRate`), so item IAS leaves the rate unchanged.
- **P1b-5 Double Swing and Frenzy** (A12, A13, D2R): a Barbarian with two weapons of different `speed`, at least 30
  of each: one rate for the 17-frame sequence 11 from the start, factor base 70 (100 − 30) with the hands' mean;
  Frenzy's second swing at that rate, also after a missed first swing.
- **P1b-6 the shapeshifted attack** (A14, D2R): werewolf and werebear A1 with no weapon and with two weapon classes,
  at two IAS values: `+0x4C` against `w · X / 100`, `w = (+0x48 & ~0xFF) / D`, `D` from the human A1 record of the
  weapon's class (19 with no weapon) (anim/0002 § 3.6).
- **P1b-7 the Druid, form, vampire and Necromancer casts** (C2, C4, D2R): the length and the do frame at two or more
  FCR values for each of the records `DZSC*` (15 frames, speed 208, event at 8), `40SCHTH` (11, 168, 5), `TGSCHTH`
  (10, 152, 5), `VASCHTH` (15, 160, 3) and `NESC*` (16, 256, 8).
- **P1b-8 the one-handed swing class** (H4): a Druid's get-hit with a one-handed hammer (`DZGH1HS`, speed 248) and
  with a two-handed sword or axe (speed 256); an Amazon's block with a wand (`AMBL1HS`, speed 88); 30 each.
- **P1b-9 the get-hit threshold** (H6), inside the `GetHitRoll` case: at least one get-hit with the total in
  `[hp/16, hp/12)` and one refusal above `hp/12`, at a hit class with `D` 16.
- **P1b-10 the player's knockback end** (H10): at least 10 of the 30 knockbacks on a player, the mode after the path
  ends logged (neutral, no get-hit; anim/0001 § 9.1), from the stock source, Blood Raven in Hell (MonProp
  `bloodraven` `prop1 (H)` `knock`); not conditional (the `lane/p50v` review), a shortfall is named in the record.
- **P1b-11 the block animation's gate** (B5): blocked hits on a player within `⌊stat 102 / 8⌋ + 15` frames of the last
  block start, the second starting no block mode and leaving stat 95; at least 30 blocked hits, ten inside the window.
- **P1b-12 the delay interval** (D2): at least 30 repeated casts of a delay skill whose delay outlasts the cast (Frozen
  Orb, `delay` 25): the do frame, state 121's start and end and the next do, against "do offset + delay" (D1) and
  "length + delay" (D2).
- **P1b-13 Slows Target** (M6, M7 (version: 1.09), M8): a unit under stat 150's slow (handler 19, or the Clay Golem's,
  handler 27): its path speed `+0x7C` unchanged and its attack or default rate lowered by `v` at its cap (50, 75 or
  90); 30 events and one movement window.
- **P1b-14 the moving floor** (M11, 1.09): a unit whose moving factor falls below 25 (a monster under chill and a
  stat-67 curse), `+0x4C` and `+0x7C` at `X` = 25, and a player's run at the animation base `0x65`, in the movement
  windows.
- **P1b-15 Charge's speed** (M12, 1.09): at least 30 Charge starts with the path speed `MulDiv(RunVelocity << 8,
  max(stat 67, 50) + 150, 100)` logged at start 31 (skills/0011 § 5), one at stat 67 ≤ 50.

Not blocking: Phase 1b lands before Phase 2's last session batch (plan 0050 § Phase 1b).

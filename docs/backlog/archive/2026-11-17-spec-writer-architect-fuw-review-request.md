---
from: spec-writer
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
resolution: "Accepted with fixes 5 (architect Tier B check on Opus, 2026-11-17): to-hit's struck open question tags the row-240 attribution read from the code; C1's bit list scopes 0x200; inventory's legend gains the second-reading row; stats-and-states and skills define it; monster-ai drops a 'now'. Export check: no new address or tool-name hits on the manifest pages."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Tier B review (Sonnet) of `lane/fuw`, spec-writer follow-ups of `lane/fur` and three wiki refreshes after plan 0066.
Not blocking.

**Specs** (from ai/0001 § 17, skills/0012 § 7, path/0004 § 11, drlg/0009 § 16, combat/0001 § 23,
run:2026-11-17-fur-bit4000):

- monsters/ai/README C2, C3: `T + max(n, 1)` → `m ← 1 when n = 0, else n`, 32-bit add; C2b rewritten as the shared
  rule `[I]`; new C2c (`MonAiIdle`'s mode test, null unit) `[I]`; the n ≤ 0 open question replaced by the `[L]` "a frame
  below `T`" (front matter L 10 → 11; research-map row updated).
- path/README (the flight row, the player-row cell, the candidates bullet), path/search F, drlg/collision (the landing
  row and the candidates row): "Leap or Leap Attack" with the shared helper; anchors to skills/0012 § 7 and
  path/0004 § 11.
- drlg/lifecycle: `ItemPlaceOnGround` 12 calls in 10 functions, anchored to drlg/0009 § 16.
- combat/to-hit C1: `0x4000` named the soft hit, its three writers (damage 3 `[C]`, writers 2 and 3 `[I]`), the
  491 + 46 split `[C]` with the 46's attribution `[I]`, the `0x200` scope; Outputs and combat/README name the soft
  hit; the open question struck (C 66 → 67, I 16 → 19, L 4 → 3). The combat research-map sum was stale at C 369
  (the five front matters summed 370 before this lane); now C 371, I 102, L 20.

**Wiki:** monster-ai, stats-and-states, economy, inventory, skills refreshed against their specs (based_on bumped);
combat (a soft-hit paragraph), pathing (Leap or Leap Attack), server-frame (the new-rooms trap moved under "Seen in a
window"); based_on dates bumped on levels, monsters, objects and seed-to-world after this lane's lifecycle/collision
edits, which change none of their lines; wiki/README's stats row says "the idle refresh".

Judgment calls to check: the wiki's wording of the AI tick's confirmed parts against overview B1/B2/B1a; "confirmed
by a second reading" for `[C]` statements resting on objdump plus r2; stats-and-states' read floor wording (a value
below `MinAccr` reads as `MinAccr << ValShift`).

**Verdict (architect, Tier B check on Opus, 2026-11-17): accept with fixes 5** (overclaim 1, omission 2, stale
cross-reference 2), applied in the review commit:

- combat/to-hit's struck open question said "settled … damage function 3 for row 240" flat; it now says the row-240
  attribution is read from the code, as C1 tags it (overclaim).
- combat/to-hit C1's bit list still read "`0x200` evaded (missiles)"; scoped to a row with `GetHit` or `KnockBack`, as
  the next C1 bullet and combat/0001 § 23 say (stale cross-reference).
- wiki/inventory's legend listed "four ways" while the page now says "confirmed by a second reading": a fifth row, worded
  as pathing's and server-frame's legend (omission).
- wiki/stats-and-states and wiki/skills used "confirmed by a second reading" undefined: one defining sentence in each
  intro (omission).
- wiki/monster-ai "whose first call is now compared" → "is compared" (current state only; stale cross-reference).

Checked: every spec edit against ai/0001 § 17, skills/0012 § 7, path/0004 § 11, path/0005's addendum, drlg/0009 § 16 and
combat/0001 § 23, and each item of the archived `fur` entry (all answered); the 12 calls in 10 functions recounted
(1 + 2 + 1 + 3 + 1 + 4); the new `[C]` (the 537's row split) names run:2026-11-17-fur-bit4000; the 46's attribution
and writers 2 and 3 stay `[I]`; the new `[L]` sits under *Open questions*. About 16 wiki sentences against the specs'
current tags (monster-ai B5, C5, A9, E5, C2b; stats H4, A2, B1, F2; economy B1–B3, C4, D7, F; inventory F1, G; skills
dispatch's 1 460 and stat 328): no overclaim found beyond the fixes. Export check (text rules, the eight manifest pages,
main vs lane): no new X1–X11 failure; X12 warnings +9 (capitalised names: "Leap Attack" 3 on pathing, "Phase Blade" on
economy, 5 on skills), no new raw address or tool name.

Judgment calls: "confirmed by a second reading" for `[C]` resting on two static tools is accepted; it is the wording
pathing and server-frame already define, and now every page using it defines it. The split sentences (the confirmed
part, then "read from the code" for the rest) are the right shape (review-fixes rule 2). The based_on bumps on levels,
monsters, objects and seed-to-world after spec edits that change none of their lines are right: based_on records the
spec version the page was checked against. The read-floor wording on stats-and-states matches aggregate F2
(`MinAccr << ValShift`, `maxhp` 1..255 kept, 0 or less read as 256). The research-map combat sum C 371 / I 102 / L 20
is the gate's.

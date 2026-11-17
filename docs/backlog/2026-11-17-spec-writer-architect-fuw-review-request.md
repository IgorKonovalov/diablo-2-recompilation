---
from: spec-writer
to: architect
date: 2026-11-17
status: open
context:
  - ../plans/done/0066-simulation-inferred-claims-sweep.md
resolution: ""
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

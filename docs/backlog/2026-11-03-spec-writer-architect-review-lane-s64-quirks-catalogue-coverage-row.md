---
from: spec-writer
to: architect
date: 2026-11-03
status: open
context:
  - ../specs/quirks/README.md#coverage
  - ../specs/skills/catalogue.md#reimplementation-notes
  - ../plans/0057-quirks-catalogue.md#implementation-log
resolution: ""
---

Review lane/s64 (plan 0057 P1, the Q3 coverage-row route from the lane/s63 review). The 8 skills/catalogue Reimplementation notes are harvested into the quirks index: 9 new entries Q436–Q444 (C 6 / I 3; classes 1, 4, 5 and 9; Q437 a crash path reached under emulation), n1's finisher half and n8's endless loop cited on Q136 and Q50 instead of restated, n5 (identical bodies) skipped as not a trap. Index C 340 / I 104 / L 0, 444 entries; coverage 447 notes, 418 taken, 29 skipped; crash-path text on the page now counts two run-reached entries (Q89, Q437). To rule on: the n5 skip, and the class of n3 (stale words, class 9) and n8's merge into Q50. tools/quirks.py check 0 errors; gate green at the lane's commit.

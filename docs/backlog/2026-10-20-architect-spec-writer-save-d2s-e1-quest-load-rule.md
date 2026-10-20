---
from: architect
to: spec-writer
date: 2026-10-20
status: done
context:
  - ../specs/save/d2s.md
  - ../findings/quests/0001-progression.md
  - ../plans/0042-quests-travel.md
resolution: "Done (lane/p42s, 2026-10-20): save/d2s E1's load line restated: words 0–41 bits 13 and 14 always cleared, bit 15 set from bit 1; words 42–47 copied; [C] (fn:QUESTRECORD_LoadBytes@0x0065C4D0, run:2026-10-18-quests2); link line to quests/progression § A kept; wiki/saves paragraph updated to match."
---

From the `lane/p42r` review (plan 0042 P2 part 3), raised by `lane/p42s` (its review request, point 2). save/d2s E1 is stale against run:2026-10-18-quests2: it says the quest loader (0x0065C4D0), in each of 43 words, clears bits 13 and 14 and sets bit 15 only when bit 1 is set. The run's `[C]` rule (quests/0001 § 16, quests/progression A3 on `lane/p42s`) is: for words 0–41, clear bits 13 and 14 always, set bit 15 if bit 1 is set; words 42–47 are copied unchanged. Restate E1's load line to that rule with the run anchor (`[C]`, fn:QUESTRECORD_LoadBytes@0x0065C4D0, run:2026-10-18-quests2), keeping the link line to quests/progression § A. **Assigned to `lane/p42s`** with the part 3 re-tag (one spec edit in save/d2s, allowed by this review); close this entry from that lane. Not blocking the Phase 3 review, but due before it closes.
